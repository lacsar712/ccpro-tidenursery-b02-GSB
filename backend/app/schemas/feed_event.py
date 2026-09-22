from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _validate_mix(v: Optional[int]) -> Optional[int]:
    # 选填；一旦填写必须为 1..100 的整数
    if v is not None and (v < 1 or v > 100):
        raise ValueError("混喂比例百分数必须为 1 到 100 的整数")
    return v


class FeedEventCreate(BaseModel):
    pond_id: int = Field(..., alias="pondId")
    fed_at: datetime = Field(..., alias="fedAt")
    feed_type: str = Field(..., min_length=1, max_length=64, alias="feedType")
    amount_kg: float = Field(..., gt=0, alias="amountKg")
    operator_name: str = Field(..., min_length=1, max_length=64, alias="operatorName")
    mix_ratio_pct: Optional[int] = Field(None, alias="mixRatioPct")

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("feed_type")
    @classmethod
    def strip_feed_type(cls, v: str) -> str:
        return v.strip()

    @field_validator("mix_ratio_pct")
    @classmethod
    def validate_mix_create(cls, v: Optional[int]) -> Optional[int]:
        return _validate_mix(v)


class FeedEventUpdate(BaseModel):
    pond_id: Optional[int] = Field(None, alias="pondId")
    fed_at: Optional[datetime] = Field(None, alias="fedAt")
    feed_type: Optional[str] = Field(None, min_length=1, max_length=64, alias="feedType")
    amount_kg: Optional[float] = Field(None, gt=0, alias="amountKg")
    operator_name: Optional[str] = Field(None, min_length=1, max_length=64, alias="operatorName")
    # None 表示字段未提供；显式清空混喂比例不在本期需求内，保持简单
    mix_ratio_pct: Optional[int] = Field(None, alias="mixRatioPct")

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("feed_type")
    @classmethod
    def strip_feed_type(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if v is not None else v

    @field_validator("mix_ratio_pct")
    @classmethod
    def validate_mix_update(cls, v: Optional[int]) -> Optional[int]:
        return _validate_mix(v)


class FeedEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    pond_id: int = Field(serialization_alias="pondId")
    fed_at: datetime = Field(serialization_alias="fedAt")
    feed_type: str = Field(serialization_alias="feedType")
    amount_kg: float = Field(serialization_alias="amountKg")
    operator_name: str = Field(serialization_alias="operatorName")
    mix_ratio_pct: Optional[int] = Field(None, serialization_alias="mixRatioPct")
