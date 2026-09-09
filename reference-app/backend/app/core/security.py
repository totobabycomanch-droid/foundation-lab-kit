import bcrypt
from fastapi import HTTPException


async def verify_token(token=None):
    if not token:
        raise HTTPException(status_code=401, detail="인증 토큰이 필요합니다.")
    return {
        "user_id": "reference-user",
        "corp_id": "admin",
        "corp_category": "10",
        "role": "MANAGER",
        "user_type": "company",
    }


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

