from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_staff
from app.database import get_db
from app.models.feed_type import FeedType
from app.models.user import User
from app.schemas.feed_type import FeedTypeCreate, FeedTypeOut, FeedTypeUpdate

router = APIRouter(prefix="/api/feed-types", tags=["feed-types"])


def active_types_conflict_detail(db: Session) -> str:
    """构造 409 正文:列出当前全部启用类型及其单次上限。"""
    rows = (
        db.query(FeedType)
        .filter(FeedType.is_active.is_(True))
        .order_by(FeedType.id)
        .all()
    )
    if not rows:
        return "饵料类型未命中启用白名单;当前没有启用的饵料类型"
    listed = "、".join(f"{r.name}(单次≤{r.max_amount_kg:g}kg)" for r in rows)
    return f"饵料类型未命中启用白名单或超过该类型最大单次千克;当前启用类型:{listed}"


def ensure_allowed_feed(db: Session, feed_type: str, amount_kg: float) -> None:
    """投喂新建 / 更新 / 改类型共用的白名单闸门。

    类型名必须命中启用项,且千克不超过该项最大单次千克;否则 409,
    正文列出当前启用类型。停用类型一律不可再用于新投喂或改类型。
    """
    matched = (
        db.query(FeedType)
        .filter(FeedType.name == feed_type, FeedType.is_active.is_(True))
        .first()
    )
    if matched is None or amount_kg > matched.max_amount_kg:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=active_types_conflict_detail(db),
        )


@router.get("", response_model=List[FeedTypeOut])
def list_feed_types(
    active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(FeedType)
    if active is not None:
        q = q.filter(FeedType.is_active.is_(active))
    return q.order_by(FeedType.id).all()


@router.post("", response_model=FeedTypeOut, status_code=status.HTTP_201_CREATED)
def create_feed_type(
    payload: FeedTypeCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
):
    item = FeedType(
        name=payload.name,
        is_active=payload.is_active,
        max_amount_kg=payload.max_amount_kg,
    )
    db.add(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=f"类型名已存在:{payload.name}")
    db.refresh(item)
    return item


@router.put("/{type_id}", response_model=FeedTypeOut)
def update_feed_type(
    type_id: int,
    payload: FeedTypeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    item = db.query(FeedType).filter(FeedType.id == type_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="饵料类型不存在")

    data = payload.model_dump(exclude_unset=True)

    # 技术员可增改白名单;但把启用项停用(True -> False)仅场长可操作。
    # 重新启用不受此限。
    if data.get("is_active") is False and item.is_active:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="停用饵料类型仅场长可操作")

    for k, v in data.items():
        setattr(item, k, v)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=f"类型名已存在:{payload.name}")
    db.refresh(item)
    return item
