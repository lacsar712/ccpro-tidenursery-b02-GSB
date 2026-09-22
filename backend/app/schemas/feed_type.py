from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FeedTypeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    is_active: bool = Field(default=True, alias="isActive")
    max_amount_kg: float = Field(..., gt=0, alias="maxAmountKg")

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("类型名不能为空")
        return v


class FeedTypeUpdate(BaseModel):
    # 增改白名单由技术员完成；停用(is_active=False)仅场长，权限在路由层判定
    name: Optional[str] = Field(None, min_length=1, max_length=64)
    is_active: Optional[bool] = Field(None, alias="isActive")
    max_amount_kg: Optional[float] = Field(None, gt=0, alias="maxAmountKg")

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("类型名不能为空")
        return v


class FeedTypeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    name: str
    is_active: bool = Field(serialization_alias="isActive")
    max_amount_kg: float = Field(serialization_alias="maxAmountKg")
