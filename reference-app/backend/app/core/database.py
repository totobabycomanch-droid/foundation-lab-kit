from fastapi import HTTPException


async def get_tenant_db():
    raise HTTPException(status_code=503, detail="참조 앱은 실제 DB에 연결하지 않습니다.")


def get_system_db():
    raise RuntimeError("참조 앱은 실제 DB에 연결하지 않습니다.")

