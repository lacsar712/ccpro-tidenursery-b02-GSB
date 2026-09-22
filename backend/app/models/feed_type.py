from sqlalchemy import String, Integer, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class FeedType(Base):
    """全场饵料类型白名单。投喂只允许引用 is_active=True 的类型。"""

    __tablename__ = "feed_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    # 类型名去空白后唯一，由应用层保证 strip 后写入
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    max_amount_kg: Mapped[float] = mapped_column(Float, nullable=False)
