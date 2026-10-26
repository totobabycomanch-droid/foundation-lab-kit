from pydantic import BaseModel, Field, field_validator


class OrderInput(BaseModel):
    item_name: str = Field(min_length=1, max_length=80)
    quantity: int = Field(strict=True, ge=1, le=9999)

    @field_validator("item_name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("품명을 입력하세요.")
        return value
