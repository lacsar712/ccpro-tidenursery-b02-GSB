from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.feed_event import FeedEvent
from app.models.feed_type import FeedType
from app.models.pond import Pond
from app.models.user import User
from app.schemas.feed_event import FeedEventCreate, FeedEventUpdate, FeedEventOut

router = APIRouter(prefix="/api/feed-events", tags=["feed-events"])


def _active_types_text(db: Session) -> str:
    actives = (
        db.query(FeedType)
        .filter(FeedType.is_active.is_(True))
        .order_by(FeedType.id)
        .all()
    )
    if not actives:
        return "（白名单暂无启用类型）"
    return "、".join(f"{t.name}(≤{t.max_amount_kg:g}kg)" for t in actives)


def _resolve_feed_type(db: Session, name: str, amount_kg: float) -> FeedType:
    """命中启用项且不超最大单次千克，否则抛 409，正文列出当前启用类型。"""
    feed_type = (
        db.query(FeedType)
        .filter(FeedType.name == name, FeedType.is_active.is_(True))
        .first()
    )
    active_list = _active_types_text(db)
    if feed_type is None:
        raise HTTPException(
            status_code=409,
            detail=f"饵料类型「{name}」不在启用白名单中；当前启用类型：{active_list}",
        )
    if amount_kg > feed_type.max_amount_kg:
        raise HTTPException(
            status_code=409,
            detail=(
                f"单次投喂 {amount_kg:g}kg 超过「{name}」最大允许 "
                f"{feed_type.max_amount_kg:g}kg；当前启用类型：{active_list}"
            ),
        )
    return feed_type


@router.get("", response_model=List[FeedEventOut])
def list_events(
    pond_id: Optional[int] = Query(None, alias="pondId"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(FeedEvent)
    if pond_id is not None:
        q = q.filter(FeedEvent.pond_id == pond_id)
    return q.order_by(FeedEvent.fed_at.desc()).all()


@router.post("", response_model=FeedEventOut, status_code=status.HTTP_201_CREATED)
def create_event(
    payload: FeedEventCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    pond = db.query(Pond).filter(Pond.id == payload.pond_id).first()
    if not pond:
        raise HTTPException(status_code=400, detail="塘口不存在")
    _resolve_feed_type(db, payload.feed_type, payload.amount_kg)
    item = FeedEvent(
        pond_id=payload.pond_id,
        fed_at=payload.fed_at,
        feed_type=payload.feed_type,
        amount_kg=payload.amount_kg,
        operator_name=payload.operator_name,
        mix_ratio_pct=payload.mix_ratio_pct,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{event_id}", response_model=FeedEventOut)
def update_event(
    event_id: int,
    payload: FeedEventUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    item = db.query(FeedEvent).filter(FeedEvent.id == event_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="投喂记录不存在")

    data = payload.model_dump(exclude_unset=True)

    if "pond_id" in data:
        pond = db.query(Pond).filter(Pond.id == data["pond_id"]).first()
        if not pond:
            raise HTTPException(status_code=400, detail="塘口不存在")

    # 更新时类型名（含改类型）须命中启用项，且千克受该项最大单次约束
    effective_name = data.get("feed_type", item.feed_type)
    effective_amount = data.get("amount_kg", item.amount_kg)
    _resolve_feed_type(db, effective_name, effective_amount)

    for k, v in data.items():
        setattr(item, k, v)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    item = db.query(FeedEvent).filter(FeedEvent.id == event_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="投喂记录不存在")
    db.delete(item)
    db.commit()
