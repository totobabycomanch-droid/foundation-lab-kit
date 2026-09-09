import functools
import hashlib
import json
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from app.core.database import get_system_db
from app.core.security import verify_token


def _normalize_key(raw_key):
    try:
        return str(UUID(str(raw_key).strip()))
    except (AttributeError, TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Idempotency-Key는 유효한 UUID여야 합니다.")


async def _request_hash(request: Request) -> str:
    body = await request.body()
    try:
        canonical = json.dumps(
            json.loads(body), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode()
    except (json.JSONDecodeError, UnicodeDecodeError):
        canonical = body
    return hashlib.sha256(canonical).hexdigest()


def _load(db, key):
    response = db.table("idempotency_keys").select("*").eq("idempotency_key", key).limit(1).execute()
    return response.data[0] if response.data else None


def idempotent(require_key=False):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get("req") or next(
                (value for value in args if isinstance(value, Request)), None
            )
            raw_key = kwargs.get("idempotency_key")
            if not raw_key and require_key:
                raise HTTPException(status_code=400, detail="Idempotency-Key 헤더가 필요합니다.")
            if not raw_key:
                return await func(*args, **kwargs)

            key = _normalize_key(raw_key)
            auth = await verify_token(kwargs.get("token"))
            corp_id = str(auth.get("corp_id") or "")
            user_id = str(auth.get("user_id") or "")
            fingerprint = await _request_hash(request)
            db = get_system_db()
            existing = _load(db, key)

            if existing:
                stored = (
                    str(existing.get("corp_id") or ""),
                    str(existing.get("user_id") or ""),
                    str(existing.get("request_hash") or ""),
                )
                if stored != (corp_id, user_id, fingerprint):
                    raise HTTPException(
                        status_code=409,
                        detail="같은 Idempotency-Key를 다른 요청에 사용할 수 없습니다.",
                    )
                if existing.get("status") == "COMPLETED":
                    return JSONResponse(
                        content=existing.get("response_body") or {},
                        headers={"Idempotency-Replayed": "true"},
                    )
                raise HTTPException(status_code=409, detail="동일한 요청이 이미 처리 중입니다.")

            db.table("idempotency_keys").insert(
                {
                    "idempotency_key": key,
                    "corp_id": corp_id,
                    "user_id": user_id,
                    "request_method": request.method,
                    "request_path": request.url.path,
                    "request_hash": fingerprint,
                    "status": "IN_PROGRESS",
                    "expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
                }
            ).execute()

            result = await func(*args, **kwargs)
            body = result if isinstance(result, dict) else json.loads(result.body)
            (
                db.table("idempotency_keys")
                .update({"status": "COMPLETED", "response_body": body, "response_status": 200})
                .eq("idempotency_key", key)
                .execute()
            )
            return result

        return wrapper

    return decorator

