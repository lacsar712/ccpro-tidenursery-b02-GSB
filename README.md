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
5. **FeedEvent 投喂**：`pondId`、`fedAt`、`feedType`、`amountKg`、`operatorName`、可选 `mixRatioPct`（混喂比例百分数，填写则必须为 1–100 的整数）
6. **FeedType 饵料类型白名单（全场）**：`name`（类型名，去首尾空白后唯一）、`isActive`（是否启用）、`maxAmountKg`（最大单次千克，必须为正）
7. **Dashboard**：塘总数、quarantine 数、近 24h 采样数、近 7 日投喂总量 kg、启用饵料类型数（与白名单启用行数一致）

### 饵料白名单规则（强制）

- 白名单由技术员（及场长）维护：可新增类型、改类型名 / 调整最大单次千克 / 重新启用；**停用某类型仅场长可操作**。
- **新建投喂、更新投喂（含仅改类型）时**：`feedType` 必须命中一条**启用**白名单，且 `amountKg ≤ maxAmountKg`；否则返回 **409**，正文列出当前全部启用类型及各自上限，例如：
  `饵料类型未命中启用白名单或超过该类型最大单次千克;当前启用类型:轮虫(单次≤3kg)、卤虫无节幼体(单次≤2kg)、微藻饲料(单次≤5kg)`
- 类型**停用后**：历史投喂仍可正常读取（投喂列表、看板统计不受影响）；但新投喂与更新 / 改类型均不可再使用该类型，接口同样返回 409（即使前端下拉隐藏停用项，接口也不会放行）。
- 可选混喂比例 `mixRatioPct`：不填即可；填写时必须为 1–100 的整数，否则返回 400。
- 投喂页饵料类型为**仅含启用类型的下拉框**（并显示该类型单次上限）；白名单管理页可查看全部类型（含停用项）。
- 内置失败样例（种子含启用类型 `轮虫(≤3kg)`、`卤虫无节幼体(≤2kg)`、`微藻饲料(≤5kg)` 与停用类型 `蛋黄浆`）：
  - **超限**：`轮虫` 投喂 `4kg` → 409；
  - **停用后再用**：`蛋黄浆` 新建 / 改入投喂 → 409。

## 前端页面

Login · Dashboard · Hatcheries · Ponds · WaterSamples · FeedEvents · FeedTypes（饵料白名单）

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
