from datetime import datetime

from sqlalchemy import String, Integer, Float, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class FeedEvent(Base):
    __tablename__ = "feed_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    pond_id: Mapped[int] = mapped_column(ForeignKey("ponds.id"), nullable=False, index=True)
    fed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # 存类型名而非外键:类型停用后旧投喂仍需可读
    feed_type: Mapped[str] = mapped_column(String(64), nullable=False)
    amount_kg: Mapped[float] = mapped_column(Float, nullable=False)
    operator_name: Mapped[str] = mapped_column(String(64), nullable=False)
    # 可选混喂比例百分数(1-100 的整数),为空表示不混喂
    mix_ratio_pct: Mapped[int | None] = mapped_column(Integer, nullable=True)

    pond: Mapped["Pond"] = relationship("Pond", back_populates="feed_events")
