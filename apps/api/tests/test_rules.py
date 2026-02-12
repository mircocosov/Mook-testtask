from datetime import date

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.main import aggregate_items
from app.db.session import Base
from app.models import Contribution, Item, Reservation, User, Wishlist


@pytest.fixture()
def db():
    engine = create_engine('sqlite+pysqlite:///:memory:', future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, future=True)
    with SessionLocal() as session:
        yield session


def seed(db: Session):
    user = User(username='owner', email='owner@test.dev', password_hash='x')
    db.add(user); db.commit(); db.refresh(user)
    w = Wishlist(owner_id=user.id, public_id='public123', title='Birthday', description='desc', event_date=date.today())
    db.add(w); db.commit(); db.refresh(w)
    item = Item(wishlist_id=w.id, title='Phone', price_amount=10000, currency='EUR')
    db.add(item); db.commit(); db.refresh(item)
    return w, item


def test_reservation_race_unique_constraint(db: Session):
    _, item = seed(db)
    db.add(Reservation(item_id=item.id, guest_token='a', active=True)); db.commit()
    db.add(Reservation(item_id=item.id, guest_token='b', active=True))
    with pytest.raises(IntegrityError):
        db.commit()


def test_soft_delete_keeps_history(db: Session):
    _, item = seed(db)
    db.add(Contribution(item_id=item.id, guest_token='x', amount=500, active=True)); db.commit()
    item.status = 'archived'; db.commit()
    contrib = db.scalar(select(Contribution).where(Contribution.item_id == item.id))
    assert contrib is not None


def test_owner_aggregation_has_no_guest_data(db: Session):
    w, item = seed(db)
    db.add_all([
        Reservation(item_id=item.id, guest_token='secret1', active=True),
        Contribution(item_id=item.id, guest_token='secret2', amount=900, active=True),
    ])
    db.commit()
    rows = aggregate_items(db, w.id)
    assert rows[0].reserved is True
    assert rows[0].contributed_amount == 900
    dumped = rows[0].model_dump()
    assert 'guest_token' not in dumped
