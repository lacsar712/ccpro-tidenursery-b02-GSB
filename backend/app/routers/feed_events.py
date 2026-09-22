from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.feed_event import FeedEvent
from app.models.pond import Pond
from app.models.user import User
from app.routers.feed_types import ensure_allowed_feed
from app.schemas.feed_event import FeedEventCreate, FeedEventOut, FeedEventUpdate

router = APIRouter(prefix="/api/feed-events", tags=["feed-events"])


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
    # 白名单闸门:类型须启用且不超该类型最大单次千克
    ensure_allowed_feed(db, payload.feed_type, payload.amount_kg)
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
    pond = db.query(Pond).filter(Pond.id == payload.pond_id).first()
    if not pond:
        raise HTTPException(status_code=400, detail="塘口不存在")
    # 改类型 / 改量同样过白名单;即使仅改时间或塘口,也按当前提交内容校验,
    # 保证不能借更新绕过闸门(停用类型一律改不回去)。
    ensure_allowed_feed(db, payload.feed_type, payload.amount_kg)

    item.pond_id = payload.pond_id
    item.fed_at = payload.fed_at
    item.feed_type = payload.feed_type
    item.amount_kg = payload.amount_kg
    item.operator_name = payload.operator_name
    item.mix_ratio_pct = payload.mix_ratio_pct
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
