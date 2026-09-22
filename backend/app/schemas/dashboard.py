from pydantic import BaseModel, ConfigDict, Field


class DashboardStats(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pond_total: int = Field(serialization_alias="pondTotal")
    quarantine_count: int = Field(serialization_alias="quarantineCount")
    samples_last_24h: int = Field(serialization_alias="samplesLast24h")
    feed_kg_last_7d: float = Field(serialization_alias="feedKgLast7d")
    # 启用饵料类型数,与白名单 is_active=True 行数一致
    active_feed_type_count: int = Field(serialization_alias="activeFeedTypeCount")
