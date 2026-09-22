from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FeedTypeBase(BaseModel):
    """白名单字段公共校验:类型名去空白后唯一、最大单次千克为正。"""

    name: str = Field(..., min_length=1, max_length=64)
    max_amount_kg: float = Field(..., gt=0, alias="maxAmountKg")

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("类型名不能为空")
        return v

    model_config = ConfigDict(populate_by_name=True)


class FeedTypeCreate(FeedTypeBase):
    is_active: bool = Field(default=True, alias="isActive")


class FeedTypeUpdate(BaseModel):
    """技术员可改名 / 调整上限 / 启用;停用(is_active=False)仅场长,在路由层拦截。"""

    model_config = ConfigDict(populate_by_name=True)

    name: Optional[str] = Field(None, min_length=1, max_length=64)
    max_amount_kg: Optional[float] = Field(None, gt=0, alias="maxAmountKg")
    is_active: Optional[bool] = Field(None, alias="isActive")

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
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
