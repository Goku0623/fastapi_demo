from passlib.context import CryptContext
from src.config import Config
import uuid
from itsdangerous import URLSafeTimedSerializer
from datetime import datetime, timedelta
import jwt
import logging

ACCESS_TOKEN_EXPIRY = 3600  

pwd_context = CryptContext(
    schemes=["bcrypt"]
)


def generate_pwd_hash(password: str) -> str:
    hash = pwd_context.hash(password)
    return hash


def verify_pwd(password: str, hash: str) -> bool:
    return pwd_context.verify(password, hash)


def create_access_token(user_data: dict, expiry: timedelta = None, refresh: bool=False):
    payload = {}
    payload["user"] = user_data
    payload["exp"] = datetime.now() + (
        expiry if expiry is not None else timedelta(seconds=ACCESS_TOKEN_EXPIRY)
    )
    payload["jti"] = str(uuid.uuid4())
    payload["refresh"] = refresh

    token = jwt.encode(
        payload=payload,
        key=Config.JWT_SECRET,
        algorithm=Config.JWT_ALGORITHM
    )
    return token


def decode_token(token: str) -> dict:
    try:
        token_data = jwt.decode(
            jwt = token,
            key=Config.JWT_SECRET,
            algorithms=[Config.JWT_ALGORITHM]
        )
        return token_data
    except jwt.PyJWKError as e:
        logging.exception(e)
        return None


serializer = URLSafeTimedSerializer(
        secret_key=Config.JWT_SECRET
    )

def create_url_safe_token(data: dict):   
    token = serializer.dumps(data, salt="email-configuration")
    return token


def decode_url_safe_token(token: str):
    try:
        token_data = serializer.loads(token, salt="email-configuration")
        return token_data
    except Exception as e:
        logging.error(str(e))
