from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class WishlistCreate(BaseModel):
    title: str
    description: str | None = None
    event_date: date | None = None


class WishlistUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    event_date: date | None = None


class ItemCreate(BaseModel):
    title: str
    url: HttpUrl | None = None
    image_url: HttpUrl | None = None
    price_amount: int | None = Field(default=None, ge=0)
    currency: str = "EUR"
    notes: str | None = None


class ItemUpdate(BaseModel):
    title: str | None = None
    url: HttpUrl | None = None
    image_url: HttpUrl | None = None
    price_amount: int | None = Field(default=None, ge=0)
    currency: str | None = None
    notes: str | None = None


class ContributionCreate(BaseModel):
    amount: int = Field(ge=100)


class ContributionUpdate(BaseModel):
    amount: int = Field(ge=100)


class UnfurlRequest(BaseModel):
    url: HttpUrl


class ItemPublicView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    url: str | None
    image_url: str | None
    price_amount: int | None
    currency: str
    notes: str | None
    status: str
    reserved: bool
    contributed_amount: int


class WishlistPublicView(BaseModel):
    id: UUID
    public_id: str
    title: str
    description: str | None
    event_date: date | None
    items: list[ItemPublicView]


class WishlistOwnerView(WishlistPublicView):
    created_at: datetime
