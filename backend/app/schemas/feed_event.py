from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FeedEventBase(BaseModel):
    # 类型名统一去首尾空白后再去白名单匹配
    feed_type: str = Field(..., min_length=1, max_length=64, alias="feedType")
    amount_kg: float = Field(..., gt=0, alias="amountKg")
    # 可选混喂比例百分数:不填为空;填写则必须为 1-100 的整数
    mix_ratio_pct: Optional[int] = Field(
        None, ge=1, le=100, alias="mixRatioPct"
    )

    @field_validator("feed_type")
    @classmethod
    def strip_feed_type(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("饵料类型不能为空")
        return v

    model_config = ConfigDict(populate_by_name=True)


class FeedEventCreate(FeedEventBase):
    pond_id: int = Field(..., alias="pondId")
    fed_at: datetime = Field(..., alias="fedAt")
    operator_name: str = Field(..., min_length=1, max_length=64, alias="operatorName")


class FeedEventUpdate(FeedEventBase):
    pond_id: int = Field(..., alias="pondId")
    fed_at: datetime = Field(..., alias="fedAt")
    operator_name: str = Field(..., min_length=1, max_length=64, alias="operatorName")


class FeedEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    pond_id: int = Field(serialization_alias="pondId")
    fed_at: datetime = Field(serialization_alias="fedAt")
    feed_type: str = Field(serialization_alias="feedType")
    amount_kg: float = Field(serialization_alias="amountKg")
    operator_name: str = Field(serialization_alias="operatorName")
    mix_ratio_pct: Optional[int] = Field(serialization_alias="mixRatioPct")
