from datetime import datetime, timedelta, timezone

from sqlalchemy import text

from app.auth import hash_password
from app.database import SessionLocal
from app.models.feed_event import FeedEvent
from app.models.feed_type import FeedType
from app.models.hatchery import Hatchery
from app.models.pond import Pond
from app.models.user import User
from app.models.water_sample import WaterSample


def ensure_fresh_install_columns(db) -> None:
    """对旧快照建过的库做幂等补列(create_all 不会给已存在的表加列)。

    用 inspector 判断列是否存在,兼容 PostgreSQL 与旧版 SQLite。
    """
    from sqlalchemy import inspect

    inspector = inspect(db.bind)
    existing = {c["name"] for c in inspector.get_columns("feed_events")}
    if "mix_ratio_pct" not in existing:
        db.execute(text("ALTER TABLE feed_events ADD COLUMN mix_ratio_pct INTEGER"))
        db.commit()


def seed_feed_types(db) -> None:
    """全场饵料类型白名单:至少两种启用类型,另含一种已停用类型。"""
    if db.query(FeedType).count() > 0:
        return
    db.add_all(
        [
            FeedType(name="轮虫", is_active=True, max_amount_kg=3.0),
            FeedType(name="卤虫无节幼体", is_active=True, max_amount_kg=2.0),
            FeedType(name="微藻饲料", is_active=True, max_amount_kg=5.0),
            # 已停用类型:旧投喂仍可读,但新投喂/改类型不得再用
            FeedType(name="蛋黄浆", is_active=False, max_amount_kg=0.5),
        ]
    )
    db.commit()


def seed() -> None:
    db = SessionLocal()
    try:
        ensure_fresh_install_columns(db)

        if db.query(User).count() == 0:
            db.add_all(
                [
                    User(
                        username="admin",
                        hashed_password=hash_password("123456"),
                        role="admin",
                        display_name="场长",
                    ),
                    User(
                        username="technician",
                        hashed_password=hash_password("123456"),
                        role="technician",
                        display_name="水质技术员",
                    ),
                ]
            )
            db.commit()

        seed_feed_types(db)

        if db.query(Hatchery).count() == 0:
            h1 = Hatchery(
                name="东港潮汐一号场",
                seawater_source="近海沙滤井水",
                notes="主养中国对虾苗",
            )
            h2 = Hatchery(
                name="盐田青湾育苗场",
                seawater_source="潮间带取水井",
                notes="轮虫与卤虫同步供应",
            )
            db.add_all([h1, h2])
            db.flush()

            p1 = Pond(
                hatchery_id=h1.id,
                pond_code="A-01",
                species="中国对虾",
                volume_m3=80.0,
                status="stocked",
            )
            p2 = Pond(
                hatchery_id=h1.id,
                pond_code="A-02",
                species="日本对虾",
                volume_m3=60.0,
                status="quarantine",
            )
            p3 = Pond(
                hatchery_id=h2.id,
                pond_code="B-01",
                species="凡纳滨对虾",
                volume_m3=100.0,
                status="stocked",
            )
            p4 = Pond(
                hatchery_id=h2.id,
                pond_code="B-02",
                species="梭子蟹苗",
                volume_m3=45.0,
                status="dry",
            )
            db.add_all([p1, p2, p3, p4])
            db.flush()

            now = datetime.now(timezone.utc)
            db.add_all(
                [
                    WaterSample(
                        pond_id=p1.id,
                        sampled_at=now - timedelta(hours=3),
                        temp_c=26.5,
                        salinity_ppt=28.0,
                        do_mg_l=6.8,
                        ph=8.1,
                        notes="晨检正常",
                    ),
                    WaterSample(
                        pond_id=p2.id,
                        sampled_at=now - timedelta(hours=5),
                        temp_c=25.2,
                        salinity_ppt=30.0,
                        do_mg_l=5.4,
                        ph=7.9,
                        notes="隔离塘加强监测",
                    ),
                    WaterSample(
                        pond_id=p3.id,
                        sampled_at=now - timedelta(hours=10),
                        temp_c=27.0,
                        salinity_ppt=27.5,
                        do_mg_l=7.1,
                        ph=8.0,
                        notes=None,
                    ),
                    FeedEvent(
                        pond_id=p1.id,
                        fed_at=now - timedelta(hours=8),
                        feed_type="轮虫",
                        amount_kg=1.2,
                        operator_name="水质技术员",
                        mix_ratio_pct=None,
                    ),
                    FeedEvent(
                        pond_id=p1.id,
                        fed_at=now - timedelta(days=1),
                        feed_type="卤虫无节幼体",
                        amount_kg=0.8,
                        operator_name="场长",
                        mix_ratio_pct=60,
                    ),
                    FeedEvent(
                        pond_id=p3.id,
                        fed_at=now - timedelta(days=2),
                        feed_type="微藻饲料",
                        amount_kg=2.5,
                        operator_name="水质技术员",
                        mix_ratio_pct=None,
                    ),
                    # 停用类型的历史投喂:停用后仍可在列表/看板中读到
                    FeedEvent(
                        pond_id=p2.id,
                        fed_at=now - timedelta(days=20),
                        feed_type="蛋黄浆",
                        amount_kg=0.3,
                        operator_name="场长",
                        mix_ratio_pct=None,
                    ),
                ]
            )
            db.commit()
            print("Seed data inserted.")
        else:
            print("Seed skipped (data exists).")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
