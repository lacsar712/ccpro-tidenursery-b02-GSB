# TideNursery-01 · 潮汐育苗台账

海水育苗场「塘口水质采样与投喂事件」台账种子项目（非库存 / 电商 / 医院）。

## 技术栈

| 层 | 技术 |
| --- | --- |
| 后端 | Python 3.11 · FastAPI · SQLAlchemy 2 · Pydantic v2 · python-jose · passlib(bcrypt) · uvicorn |
| 前端 | React 18 · Vite · TypeScript · React Router v6 |
| 数据库 | PostgreSQL 15 |
| 部署 | docker-compose · 前端 Nginx 反代 `/api` |

## 端口与账号

| 服务 | 端口 |
| --- | --- |
| 前端 | **3400** |
| 后端 API | **8400** |
| PostgreSQL | **5434** |

| 用户名 | 密码 | 角色 |
| --- | --- | --- |
| `admin` | `123456` | 场长 |
| `technician` | `123456` | 水质技术员 |

## 一键启动

```bash
cd TideNursery-01
docker compose up --build
```

启动后访问：

- 前端：http://localhost:3400
- 后端健康检查：http://localhost:8400/api/health
- API 文档：http://localhost:8400/docs

后端 entrypoint 流程：等待数据库就绪 → `create_all` 建表 → seed 初始数据 → 启动 uvicorn。

## 功能模块

1. **Auth**：JWT 登录（OAuth2 Password），`/api/auth/login`、`/api/auth/me`
2. **Hatchery 育苗场**：`name`、`seawaterSource`、`notes`
3. **Pond 育苗塘**：`hatcheryId`、`pondCode`、`species`、`volumeM3`、`status(stocked|dry|quarantine)`；同场 `pondCode` 唯一
4. **WaterSample 水质样**：`pondId`、`sampledAt`、`tempC`、`salinityPpt`、`doMgL`、`ph`、`notes`；`doMgL > 0` 且 `ph ∈ [6,9]`，否则返回 **400**
5. **FeedEvent 投喂**：`pondId`、`fedAt`、`feedType`、`amountKg`、`operatorName`、可选 `mixRatioPct`
6. **FeedType 饵料类型白名单**：全场维护；字段 `name`（去空白后唯一）、`isActive`、`maxAmountKg`（>0）
7. **Dashboard**：塘总数、quarantine 数、近 24h 采样数、近 7 日投喂总量 kg、**启用饵料类型数**（与白名单启用行数一致）

### 饵料类型白名单规则

- 白名单字段：**类型名**（去首尾空白后唯一）、**是否启用**、**最大单次千克**（必须为正）。
- **技术员**可新增、修改白名单条目（改名、改最大单次千克）；**停用某类型仅场长（admin）**。
- 新建投喂（`POST /api/feed-events`）与更新投喂（`PUT /api/feed-events/{id}`，含改类型）时：
  - 类型名必须命中一个**启用**白名单项；
  - `amountKg` 不得超过该项的最大单次千克。
  - 任一不满足返回 **409**，响应正文 `detail` 列出当前所有启用类型及各自上限，例如：
    `{"detail":"单次投喂 9.9kg 超过「轮虫」最大允许 5kg；当前启用类型：轮虫(≤5kg)、卤虫无节幼体(≤3kg)、微藻饲料(≤10kg)"}`
- 停用某类型后：**旧投喂仍可读**；新投喂与任何“改类型为该类型”的更新都会被拒（409）。
- 即使前端下拉只展示启用类型，**接口层仍强制校验**，直接调用停用类型同样 409（前端隐藏不代表放行）。
- 可选**混喂比例百分数** `mixRatioPct`：留空表示单喂；填写时必须是 1 到 100 的整数，否则 400。
- 投喂页饵料下拉只列出启用类型，并按所选类型限制最大投喂千克；白名单管理页为「饵料白名单」。

### 种子数据与失败样例

种子内置三种启用类型（`轮虫`≤5kg、`卤虫无节幼体`≤3kg、`微藻饲料`≤10kg）与一种已停用类型（`桡足类`，保留一条旧投喂可读）。可直接复现的失败样例：

```bash
# 1) 超最大单次千克 → 409（轮虫上限 5kg）
curl -i -X POST localhost:8400/api/feed-events \
  -H "Authorization: Bearer <token>" -H "Content-Type: application/json" \
  -d '{"pondId":1,"fedAt":"2026-09-22T08:00:00Z","feedType":"轮虫","amountKg":9.9,"operatorName":"x"}'

# 2) 停用后再用 → 409（桡足类已停用）
curl -i -X POST localhost:8400/api/feed-events \
  -H "Authorization: Bearer <token>" -H "Content-Type: application/json" \
  -d '{"pondId":1,"fedAt":"2026-09-22T08:00:00Z","feedType":"桡足类","amountKg":1,"operatorName":"x"}'

# 3) 混喂比例越界 → 400（须为 1..100 整数）
#    在上例 body 中加入 "mixRatioPct": 0 或 120
```

## 前端页面

Login · Dashboard · Hatcheries · Ponds · WaterSamples · FeedTypes（饵料白名单） · FeedEvents

## 本地开发（可选）

```bash
# 数据库（或用 compose 只起 db）
docker compose up -d db

# 后端
cd backend
pip install -r requirements.txt
set DATABASE_URL=postgresql+psycopg2://tidenursery:tidenursery@localhost:5434/tidenursery
python -c "from app.database import Base, engine; from app import models; Base.metadata.create_all(bind=engine)"
python -c "from app.seed import seed; seed()"
uvicorn app.main:app --reload --port 8400

# 前端
cd frontend
npm install
npm run dev
```

## 目录结构

```
TideNursery-01/
├── docker-compose.yml
├── README.md
├── .gitignore
├── backend/
│   ├── Dockerfile
│   ├── entrypoint.sh
│   ├── requirements.txt
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── database.py
│       ├── auth.py
│       ├── seed.py
│       ├── models/
│       ├── schemas/
│       └── routers/
└── frontend/
    ├── Dockerfile
    ├── nginx.conf
    ├── package.json
    ├── vite.config.ts
    └── src/
        ├── pages/
        ├── components/
        └── api/
```
