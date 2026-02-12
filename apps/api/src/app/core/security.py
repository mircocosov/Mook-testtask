from datetime import UTC, datetime, timedelta

from itsdangerous import URLSafeSerializer
from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
guest_serializer = URLSafeSerializer(settings.guest_token_secret, salt="wishlist-guest")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def create_token(subject: str, token_type: str, expires_delta: timedelta) -> str:
    payload = {
        "sub": subject,
        "type": token_type,
        "exp": datetime.now(UTC) + expires_delta,
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=["HS256"])


def issue_guest_token(seed: str) -> str:
    return guest_serializer.dumps({"seed": seed})


def validate_guest_token(token: str) -> str:
    data = guest_serializer.loads(token)
    return str(data["seed"])
