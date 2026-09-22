from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_role
from app.database import get_db
from app.models.feed_type import FeedType
from app.models.user import User
from app.schemas.feed_type import FeedTypeCreate, FeedTypeUpdate, FeedTypeOut

router = APIRouter(prefix="/api/feed-types", tags=["feed-types"])

# 可增改白名单的角色；停用(is_active=False)进一步限制为场长
EDIT_ROLES = ("admin", "technician")


@router.get("", response_model=List[FeedTypeOut])
def list_feed_types(
    active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(FeedType)
    if active is not None:
        q = q.filter(FeedType.is_active == active)
    return q.order_by(FeedType.id).all()


@router.post("", response_model=FeedTypeOut, status_code=status.HTTP_201_CREATED)
def create_feed_type(
    payload: FeedTypeCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(*EDIT_ROLES)),
):
    # 技术员不能直接以停用状态建档
    if payload.is_active is False and user.role != "admin":
        raise HTTPException(status_code=403, detail="仅场长可停用饵料类型")
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
        raise HTTPException(status_code=409, detail="饵料类型名已存在")
    db.refresh(item)
    return item


@router.put("/{feed_type_id}", response_model=FeedTypeOut)
def update_feed_type(
    feed_type_id: int,
    payload: FeedTypeUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(*EDIT_ROLES)),
):
    item = db.query(FeedType).filter(FeedType.id == feed_type_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="饵料类型不存在")
    # 停用某类型仅场长：技术员把 is_active 改成 False 一律拒绝
    if payload.is_active is False and item.is_active and user.role != "admin":
        raise HTTPException(status_code=403, detail="仅场长可停用饵料类型")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(item, k, v)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="饵料类型名已存在")
    db.refresh(item)
    return item
