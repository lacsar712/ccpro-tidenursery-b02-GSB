from sqlalchemy import String, Integer, Float, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class FeedType(Base):
    """全场饵料类型白名单。

    name 为去首尾空白后的类型名,全局唯一;仅 is_active=True 的类型
    可用于新建/更新投喂,且投喂量受 max_amount_kg 约束。
    """

    __tablename__ = "feed_types"
    __table_args__ = (UniqueConstraint("name", name="uq_feed_types_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    max_amount_kg: Mapped[float] = mapped_column(Float, nullable=False)
