import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

import httpx
from bs4 import BeautifulSoup
from fastapi import Cookie, Depends, FastAPI, HTTPException, Request, Response, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_token,
    decode_token,
    hash_password,
    issue_guest_token,
    validate_guest_token,
    verify_password,
)
from app.db.session import Base, engine, get_db
from app.models import Contribution, Item, ItemStatus, Reservation, UnfurlCache, User, Wishlist
from app.schemas.common import (
    ContributionCreate,
    ContributionUpdate,
    ItemCreate,
    ItemPublicView,
    ItemUpdate,
    UnfurlRequest,
    UserCreate,
    UserLogin,
    WishlistCreate,
    WishlistUpdate,
)
from app.services.rate_limit import rate_limiter
from app.services.realtime import hub

app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(401, "Not authenticated")
    payload = decode_token(token)
    user = db.get(User, UUID(payload["sub"]))
    if not user:
        raise HTTPException(401, "Invalid user")
    return user


def ensure_owner_wishlist(wishlist_id: UUID, user: User, db: Session) -> Wishlist:
    wishlist = db.get(Wishlist, wishlist_id)
    if not wishlist or wishlist.owner_id != user.id:
        raise HTTPException(404, "Wishlist not found")
    return wishlist


def aggregate_items(db: Session, wishlist_id: UUID) -> list[ItemPublicView]:
    items = db.scalars(select(Item).where(Item.wishlist_id == wishlist_id).order_by(Item.created_at.desc())).all()
    out = []
    for it in items:
        reserved = (
            db.scalar(
                select(func.count()).select_from(Reservation).where(
                    Reservation.item_id == it.id,
                    Reservation.active.is_(True),
                )
            )
            > 0
        )
        contributed = (
            db.scalar(
                select(func.coalesce(func.sum(Contribution.amount), 0)).where(
                    Contribution.item_id == it.id,
                    Contribution.active.is_(True),
                )
            )
            or 0
        )
        out.append(
            ItemPublicView(
                id=it.id,
                title=it.title,
                url=it.url,
                image_url=it.image_url,
                price_amount=it.price_amount,
                currency=it.currency,
                notes=it.notes,
                status=it.status.value,
                reserved=reserved,
                contributed_amount=contributed,
            )
        )
    return out


@app.post("/auth/register")
def register(payload: UserCreate, response: Response, db: Session = Depends(get_db)):
    exists = db.scalar(select(User).where(User.email == payload.email.lower()))
    if exists:
        raise HTTPException(409, "Email already used")
    user = User(email=payload.email.lower(), password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    access = create_token(str(user.id), "access", timedelta(minutes=settings.access_token_minutes))
    response.set_cookie("access_token", access, httponly=True, samesite="lax")
    return {"id": str(user.id), "email": user.email}


@app.post("/auth/login")
def login(payload: UserLogin, response: Response, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    access = create_token(str(user.id), "access", timedelta(minutes=settings.access_token_minutes))
    response.set_cookie("access_token", access, httponly=True, samesite="lax")
    return {"id": str(user.id), "email": user.email}


@app.post("/auth/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"ok": True}


@app.get("/wishlists")
def owner_wishlists(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(Wishlist).where(Wishlist.owner_id == user.id, Wishlist.is_archived.is_(False))).all()
    return [{"id": str(w.id), "title": w.title, "public_id": w.public_id, "event_date": w.event_date} for w in rows]


@app.post("/wishlists")
def create_wishlist(payload: WishlistCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    w = Wishlist(
        owner_id=user.id,
        public_id=secrets.token_urlsafe(12),
        title=payload.title,
        description=payload.description,
        event_date=payload.event_date,
    )
    db.add(w)
    db.commit()
    db.refresh(w)
    return {"id": str(w.id), "public_id": w.public_id}


@app.get("/wishlists/{wishlist_id}")
def owner_wishlist(wishlist_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    w = ensure_owner_wishlist(wishlist_id, user, db)
    return {
        "id": str(w.id),
        "public_id": w.public_id,
        "title": w.title,
        "description": w.description,
        "event_date": w.event_date,
        "items": [i.model_dump() for i in aggregate_items(db, w.id)],
    }


@app.patch("/wishlists/{wishlist_id}")
def patch_wishlist(wishlist_id: UUID, payload: WishlistUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    w = ensure_owner_wishlist(wishlist_id, user, db)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(w, field, value)
    db.commit()
    return {"ok": True}


@app.delete("/wishlists/{wishlist_id}")
def delete_wishlist(wishlist_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    w = ensure_owner_wishlist(wishlist_id, user, db)
    w.is_archived = True
    db.commit()
    return {"ok": True}


@app.post("/wishlists/{wishlist_id}/items")
async def create_item(wishlist_id: UUID, payload: ItemCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    w = ensure_owner_wishlist(wishlist_id, user, db)
    item = Item(
        wishlist_id=w.id,
        title=payload.title,
        url=str(payload.url) if payload.url else None,
        image_url=str(payload.image_url) if payload.image_url else None,
        price_amount=payload.price_amount,
        currency=payload.currency,
        notes=payload.notes,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    await hub.broadcast(w.public_id, "item.updated", {"item_id": str(item.id)})
    return {"id": str(item.id)}


@app.patch("/items/{item_id}")
async def update_item(item_id: UUID, payload: ItemUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(404, "Not found")
    w = ensure_owner_wishlist(item.wishlist_id, user, db)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(item, field, str(value) if field in {"url", "image_url"} else value)
    db.commit()
    await hub.broadcast(w.public_id, "item.updated", {"item_id": str(item.id)})
    return {"ok": True}


@app.post("/items/{item_id}/archive")
async def archive_item(item_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(404, "Not found")
    w = ensure_owner_wishlist(item.wishlist_id, user, db)
    item.status = ItemStatus.archived
    db.commit()
    await hub.broadcast(w.public_id, "item.archived", {"item_id": str(item.id)})
    return {"ok": True}


@app.get("/public/w/{public_id}")
def public_wishlist(public_id: str, response: Response, guest_token: str | None = Cookie(default=None), db: Session = Depends(get_db)):
    wishlist = db.scalar(select(Wishlist).where(Wishlist.public_id == public_id, Wishlist.is_archived.is_(False)))
    if not wishlist:
        raise HTTPException(404, "Not found")
    if not guest_token:
        guest_token = issue_guest_token(secrets.token_urlsafe(16))
        response.set_cookie("guest_token", guest_token, httponly=True, samesite="lax", max_age=60 * 60 * 24 * 365)
    return {
        "id": str(wishlist.id),
        "public_id": wishlist.public_id,
        "title": wishlist.title,
        "description": wishlist.description,
        "event_date": wishlist.event_date,
        "items": [i.model_dump() for i in aggregate_items(db, wishlist.id)],
    }


def find_public_item(item_id: UUID, db: Session) -> tuple[Item, Wishlist]:
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(404, "Item not found")
    wishlist = db.get(Wishlist, item.wishlist_id)
    if not wishlist or wishlist.is_archived:
        raise HTTPException(404, "Wishlist not found")
    return item, wishlist


@app.post("/public/items/{item_id}/reserve")
async def reserve_item(item_id: UUID, request: Request, guest_token: str | None = Cookie(default=None), db: Session = Depends(get_db)):
    if not guest_token:
        raise HTTPException(401, "Missing guest token")
    validate_guest_token(guest_token)
    rate_limiter.hit(f"reserve:{guest_token}:{request.client.host}", 20, 60)
    item, wishlist = find_public_item(item_id, db)
    if item.status == ItemStatus.archived:
        raise HTTPException(400, "Item archived")
    reservation = Reservation(item_id=item.id, guest_token=guest_token, active=True)
    db.add(reservation)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Item already reserved")
    await hub.broadcast(wishlist.public_id, "reservation.changed", {"item_id": str(item.id)})
    return {"ok": True}


@app.post("/public/items/{item_id}/unreserve")
async def unreserve_item(item_id: UUID, guest_token: str | None = Cookie(default=None), db: Session = Depends(get_db)):
    if not guest_token:
        raise HTTPException(401, "Missing guest token")
    item, wishlist = find_public_item(item_id, db)
    reservation = db.scalar(
        select(Reservation).where(Reservation.item_id == item.id, Reservation.guest_token == guest_token, Reservation.active.is_(True))
    )
    if not reservation:
        raise HTTPException(403, "Only reservation owner can cancel")
    reservation.active = False
    reservation.canceled_at = datetime.now(UTC)
    db.commit()
    await hub.broadcast(wishlist.public_id, "reservation.changed", {"item_id": str(item.id)})
    return {"ok": True}


@app.post("/public/items/{item_id}/contribute")
async def contribute(item_id: UUID, payload: ContributionCreate, request: Request, guest_token: str | None = Cookie(default=None), db: Session = Depends(get_db)):
    if not guest_token:
        raise HTTPException(401, "Missing guest token")
    validate_guest_token(guest_token)
    rate_limiter.hit(f"contrib:{guest_token}:{request.client.host}", 40, 60)
    item, wishlist = find_public_item(item_id, db)
    if item.status == ItemStatus.archived:
        raise HTTPException(400, "Item archived")
    current = db.scalar(select(func.coalesce(func.sum(Contribution.amount), 0)).where(Contribution.item_id == item.id, Contribution.active.is_(True))) or 0
    target = item.price_amount or 0
    if target and current + payload.amount > target:
        raise HTTPException(400, "Amount exceeds target")
    c = Contribution(item_id=item.id, guest_token=guest_token, amount=payload.amount)
    db.add(c)
    db.commit()
    db.refresh(c)
    await hub.broadcast(wishlist.public_id, "contribution.changed", {"item_id": str(item.id)})
    return {"id": str(c.id)}


@app.patch("/public/contributions/{contribution_id}")
async def update_contribution(contribution_id: UUID, payload: ContributionUpdate, guest_token: str | None = Cookie(default=None), db: Session = Depends(get_db)):
    if not guest_token:
        raise HTTPException(401, "Missing guest token")
    c = db.get(Contribution, contribution_id)
    if not c or not c.active:
        raise HTTPException(404, "Contribution not found")
    if c.guest_token != guest_token:
        raise HTTPException(403, "Forbidden")
    item, wishlist = find_public_item(c.item_id, db)
    if item.price_amount:
        others = db.scalar(select(func.coalesce(func.sum(Contribution.amount), 0)).where(Contribution.item_id == item.id, Contribution.active.is_(True), Contribution.id != c.id)) or 0
        if others + payload.amount > item.price_amount:
            raise HTTPException(400, "Amount exceeds target")
    c.amount = payload.amount
    db.commit()
    await hub.broadcast(wishlist.public_id, "contribution.changed", {"item_id": str(item.id)})
    return {"ok": True}


@app.delete("/public/contributions/{contribution_id}")
async def delete_contribution(contribution_id: UUID, guest_token: str | None = Cookie(default=None), db: Session = Depends(get_db)):
    if not guest_token:
        raise HTTPException(401, "Missing guest token")
    c = db.get(Contribution, contribution_id)
    if not c or not c.active:
        raise HTTPException(404, "Not found")
    if c.guest_token != guest_token:
        raise HTTPException(403, "Forbidden")
    item, wishlist = find_public_item(c.item_id, db)
    c.active = False
    db.commit()
    await hub.broadcast(wishlist.public_id, "contribution.changed", {"item_id": str(item.id)})
    return {"ok": True}


@app.post("/unfurl")
async def unfurl(payload: UnfurlRequest, request: Request, db: Session = Depends(get_db)):
    rate_limiter.hit(f"unfurl:{request.client.host}", 30, 60)
    normalized = str(payload.url)
    cache = db.scalar(select(UnfurlCache).where(UnfurlCache.url == normalized))
    if cache and (datetime.now(UTC) - cache.created_at).total_seconds() < 86400:
        return {"title": cache.title, "image_url": cache.image_url, "price_amount": cache.price_amount, "currency": cache.currency, "source": cache.source}
    async with httpx.AsyncClient(timeout=8, follow_redirects=True, headers={"User-Agent": "WishlistBot/1.0"}) as client:
        res = await client.get(normalized)
    soup = BeautifulSoup(res.text, "html.parser")
    title = (soup.find("meta", property="og:title") or {}).get("content") or (soup.title.string if soup.title else None)
    image = (soup.find("meta", property="og:image") or {}).get("content") or (soup.find("meta", attrs={"name": "twitter:image"}) or {}).get("content")
    source = "opengraph"
    price_amount = None
    currency = None
    cached = cache or UnfurlCache(url=normalized)
    cached.title = title
    cached.image_url = image
    cached.price_amount = price_amount
    cached.currency = currency
    cached.source = source
    cached.created_at = datetime.now(UTC)
    db.add(cached)
    db.commit()
    return {"title": title, "image_url": image, "price_amount": price_amount, "currency": currency, "source": source}


@app.websocket("/ws/wishlists/{public_id}")
async def wishlist_ws(websocket: WebSocket, public_id: str):
    await hub.connect(public_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except Exception:
        hub.disconnect(public_id, websocket)
