# FoodTime Backend Rules

本文档定义 `FoodTime-backend` 的后端开发规范，覆盖技术选型、分层架构、接口设计、数据库管理、日志监控、安全要求、测试策略与 CI/CD 门禁，确保所有后端代码在合并前具备一致性、可维护性与可验证性。

## 1. 技术栈基线

### 1.1 运行时与依赖管理

- Python: `3.11.x`
- 虚拟环境: 统一使用 `.venv`
- 依赖管理: `pip + requirements.txt`
- 环境变量加载: `python-dotenv`

### 1.2 核心框架与基础设施

- Flask: `3.1.x`
- Flask-SQLAlchemy: `3.1.x`
- Flask-Migrate: `4.x`
- SQLite: 本地开发默认数据库
- Redis: 缓存、会话、限流、异步任务辅助
- LangChain: `0.3.x`
- OpenAI SDK: `1.x`

### 1.3 推荐开发工具

- pytest
- pytest-cov
- pytest-mock
- fakeredis
- black
- ruff
- bandit
- pip-audit

### 1.4 核心原则

- 所有后端代码必须围绕 `Flask + Service + Repository` 分层设计。
- 禁止在控制器中直接写复杂业务逻辑。
- 禁止在服务层直接拼接 SQL，统一交由 ORM 或 Repository 层处理。
- 所有配置必须从环境变量或配置类读取，禁止硬编码敏感信息。

## 2. 分层架构约定

当前项目目录已有 `app/`、`routes/`、`repositories/`、`utils/` 等结构。后续统一按以下职责扩展：

```text
app/
├── routes/           # Controller 层，负责接收请求、参数校验、返回响应
├── services/         # Service 层，负责业务编排与事务边界
├── repositories/     # Repository 层，负责数据库访问
├── entities/         # Entity/Model 层，负责 ORM 模型定义
├── schemas/          # DTO/序列化结构，可选
├── utils/            # 工具方法、通用封装
├── extensions.py     # db、redis、cache 等扩展初始化
└── __init__.py       # 应用工厂与蓝图注册
```

当前仓库尚未全部创建上述目录，但新增时必须遵循本规范。

### 2.1 分层职责

- Controller:
  - 定义 Blueprint
  - 接收请求参数
  - 调用 Service
  - 转换为统一响应格式
- Service:
  - 编排业务流程
  - 校验业务规则
  - 处理事务边界
  - 调用多个 Repository / 外部服务
- Repository:
  - 负责 ORM 查询、持久化、分页、过滤
  - 不处理 HTTP 相关逻辑
- Entity:
  - 定义数据库模型、字段、关系、索引
  - 不承载复杂业务流程

### 2.2 命名规范

- Controller 文件: `xxx_controller.py` 或按蓝图领域命名，如 `order_routes.py`
- Service 文件: `xxx_service.py`
- Repository 文件: `xxx_repository.py`
- Entity/Model 类名: `PascalCase`，如 `Order`, `UserProfile`
- 表名: `snake_case` + 复数，如 `orders`, `user_profiles`

## 3. RESTful API 设计规范

### 3.1 URL 规范

- API 统一前缀: `/api/v1`
- 资源名称使用复数名词
- URL 使用 `kebab-case` 或 `snake_case` 中的一种，项目内必须统一，默认采用 `kebab-case`
- URL 不体现动词，动作用 HTTP Method 表达

示例：

```text
GET    /api/v1/orders
GET    /api/v1/orders/{order_id}
POST   /api/v1/orders
PATCH  /api/v1/orders/{order_id}
DELETE /api/v1/orders/{order_id}
```

### 3.2 请求与响应规范

- `GET`: 查询资源
- `POST`: 新建资源
- `PUT`: 全量更新
- `PATCH`: 部分更新
- `DELETE`: 删除资源

统一响应结构：

```json
{
  "code": 0,
  "message": "success",
  "data": {},
  "trace_id": "6f6f6474696d65"
}
```

分页响应结构：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [],
    "page": 1,
    "page_size": 20,
    "total": 100
  },
  "trace_id": "6f6f6474696d65"
}
```

### 3.3 状态码规范

- `200`: 查询、更新成功
- `201`: 创建成功
- `204`: 删除成功且无返回体
- `400`: 参数错误
- `401`: 未认证
- `403`: 无权限
- `404`: 资源不存在
- `409`: 资源冲突
- `422`: 业务校验失败
- `429`: 请求过频
- `500`: 服务端未知错误
- `503`: 下游依赖不可用

### 3.4 响应约束

- 成功响应必须包含 `code`、`message`、`data`
- 错误响应必须包含 `code`、`message`、`trace_id`
- 不得直接把 Python 异常栈回传给前端

## 4. 统一响应与异常处理

### 4.1 错误码定义

错误码格式建议：`模块_状态码_序号`

```text
AUTH_401_001   Token 无效
AUTH_403_001   权限不足
ORDER_404_001  订单不存在
ORDER_422_001  订单状态不允许变更
SYSTEM_500_001 未知系统异常
```

### 4.2 全局异常拦截

- 所有未捕获异常必须进入统一异常处理器
- 业务异常使用自定义异常类，如 `BusinessError`
- 参数校验错误与数据库异常必须转成统一响应
- 记录完整日志，但仅向客户端暴露可理解的错误信息

参考示例：

```python
class BusinessError(Exception):
    def __init__(self, code, message, status_code=400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def success_response(data=None, message='success'):
    return {
        'code': 0,
        'message': message,
        'data': data or {},
    }
```

## 5. 数据库规范

### 5.1 命名规则

- 表名: `snake_case` 复数，如 `orders`
- 字段名: `snake_case`，如 `created_at`
- 主键: 统一 `id`
- 外键: `xxx_id`
- 时间字段:
  - `created_at`
  - `updated_at`
  - 可选 `deleted_at`

### 5.2 索引策略

- 高频过滤字段必须建立索引
- 唯一业务字段必须建立唯一索引
- 联合查询高频条件应考虑联合索引
- 冷门字段禁止滥建索引，避免影响写入性能

### 5.3 迁移脚本要求

- 数据结构变更必须走迁移脚本，禁止手改生产库
- 迁移描述要可读，例如：

```text
flask db migrate -m "add_order_status_index"
flask db migrate -m "create_user_profiles_table"
```

- 迁移脚本命名建议：`<时间戳>_<动作>_<对象>`
- 单个迁移只处理一类结构变更，避免过大补丁

### 5.4 SQLite 使用约定

- SQLite 仅用于本地开发与轻量测试
- 生产环境如并发与数据量增长，需迁移到更稳定的关系型数据库
- 不依赖 SQLite 特有语法编写关键业务逻辑

## 6. 日志与监控

### 6.1 日志规范

- 日志格式统一为结构化 JSON
- 每次请求必须生成并透传 `trace_id`
- 日志字段至少包含：
  - `timestamp`
  - `level`
  - `trace_id`
  - `request_path`
  - `method`
  - `status_code`
  - `latency_ms`
  - `message`

### 6.2 日志级别

- `DEBUG`: 本地调试信息，不进入生产默认日志
- `INFO`: 正常业务流程
- `WARNING`: 可恢复异常、性能抖动、外部依赖波动
- `ERROR`: 当前请求失败但系统仍可服务
- `CRITICAL`: 系统性故障，需要立即告警

### 6.3 监控与告警阈值

- API P95 延迟 `> 500 ms` 触发告警
- API P95 延迟 `> 1000 ms` 触发严重告警
- 5xx 比例 `> 1%` 触发告警
- Redis 连接错误连续 `3` 分钟触发告警
- OpenAI / LLM 调用失败率 `> 5%` 触发告警

## 7. 安全规范

### 7.1 鉴权与授权

- API 默认采用 `JWT Bearer Token`
- 管理后台或特殊场景可增加 RBAC 权限控制
- 鉴权逻辑必须在统一中间件或装饰器中处理

### 7.2 敏感信息保护

- `.env` 中保存密钥、数据库连接、OpenAI Key、Redis 密码
- `.env` 禁止提交至远程仓库
- 密码统一使用强哈希算法，例如 `bcrypt`
- 不得在日志中打印完整 token、密码、密钥

### 7.3 注入与输入校验

- 严禁拼接原始 SQL
- 数据访问统一使用 SQLAlchemy 或参数化查询
- 所有入参必须进行长度、类型、格式校验
- 文件上传必须限制扩展名、大小、MIME 类型

### 7.4 安全增强建议

- 配置 CORS 白名单
- 高风险接口增加限流
- 关键写接口增加幂等性校验
- 外部模型调用结果需要做内容审查与异常兜底

## 8. 测试策略

### 8.1 单元测试

- 推荐使用 `pytest`
- Service、Repository、Utils 必须有单元测试
- 覆盖率阈值：
  - lines: `>= 85%`
  - statements: `>= 85%`
  - branches: `>= 75%`
  - functions: `>= 85%`

### 8.2 集成测试

- Controller 层必须提供接口级集成测试
- 数据库集成测试默认使用临时 SQLite 数据库
- Redis 集成测试建议使用 `fakeredis`
- OpenAI / LangChain 相关调用必须用 Mock 替代真实外部网络请求

### 8.3 Mock 策略

- 单元测试中禁止真实访问数据库、Redis、OpenAI
- 外部依赖统一 Mock
- 仅在受控集成环境中执行真实依赖联调

### 8.4 测试命名

- 单元测试文件: `test_xxx.py`
- 集成测试文件: `test_xxx_api.py`
- 场景测试命名必须体现 Given / When / Then 语义

## 9. CI/CD 质量门禁

CI 在合并前必须完成：

1. 依赖安装成功
2. 静态扫描通过
3. 单元测试通过率 `100%`
4. 覆盖率达到阈值
5. 集成测试通过
6. 安全扫描无高危漏洞
7. 镜像构建成功
8. 镜像体积满足要求

门禁阈值建议：

- Ruff / Black / Bandit 全通过
- pytest 通过率: `100%`
- 覆盖率: 满足第 8 节阈值
- Docker 镜像体积: `<= 400 MB`
- 高危与严重漏洞数: `0`
- 单次 CI 总耗时目标: `<= 10 min`

## 10. 本地校验命令

建议维护如下命令：

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
pip install pytest pytest-cov pytest-mock fakeredis black ruff bandit pip-audit

ruff check .
black --check .
pytest --cov=app --cov-report=term-missing
bandit -r app
pip-audit
```

如果使用 Windows PowerShell，可参考：

```powershell
python -m venv .venv
.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
pip install pytest pytest-cov pytest-mock fakeredis black ruff bandit pip-audit

ruff check .
black --check .
pytest --cov=app --cov-report=term-missing
bandit -r app
pip-audit
```

## 11. 本地预提交钩子脚本

推荐使用 Git Hook 或 `pre-commit` 工具，至少在本地执行静态检查和测试。

`.git/hooks/pre-commit` 参考脚本：

```bash
#!/usr/bin/env sh
set -e

echo "[pre-commit] Ruff check"
ruff check .

echo "[pre-commit] Black check"
black --check .

echo "[pre-commit] Pytest"
pytest --maxfail=1 --disable-warnings

echo "[pre-commit] Bandit"
bandit -r app
```

Windows PowerShell 参考：

```powershell
Write-Host "[pre-commit] Ruff check"
ruff check .
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[pre-commit] Black check"
black --check .
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[pre-commit] Pytest"
pytest --maxfail=1 --disable-warnings
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[pre-commit] Bandit"
bandit -r app
exit $LASTEXITCODE
```

## 12. 参考实现示例

Controller 示例：

```python
from flask import Blueprint, jsonify, request

from app.services.order_service import OrderService

order_bp = Blueprint('orders', __name__, url_prefix='/api/v1/orders')


@order_bp.get('')
def list_orders():
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 20))
    data = OrderService().list_orders(page=page, page_size=page_size)
    return jsonify({
        'code': 0,
        'message': 'success',
        'data': data,
    }), 200
```

Service 示例：

```python
class OrderService:
    def __init__(self, repository=None):
        self.repository = repository or OrderRepository()

    def list_orders(self, page=1, page_size=20):
        return self.repository.paginate(page=page, page_size=page_size)
```

Repository 示例：

```python
class OrderRepository:
    def paginate(self, page=1, page_size=20):
        query = Order.query.order_by(Order.created_at.desc())
        pagination = query.paginate(page=page, per_page=page_size, error_out=False)
        return {
            'items': [item.to_dict() for item in pagination.items],
            'page': pagination.page,
            'page_size': pagination.per_page,
            'total': pagination.total,
        }
```

## 13. 项目架构规范

本章节用于补充后端工程的架构要求，确保 `FoodTime-backend` 在 Flask 技术栈下依然具备良好的分层设计、可测试性、可扩展性、可部署性与可观测性。

### 13.1 分层架构设计原则

- 后端必须采用明确分层，至少区分 `controller / service / repository / entity`。
- Controller 仅负责请求接入、参数校验、调用服务、返回统一响应。
- Service 负责业务编排、事务控制、领域规则校验，不处理 HTTP 细节。
- Repository 负责数据库访问与查询封装，不掺杂业务编排逻辑。
- Entity / Model 负责数据结构、关系与约束定义，不承载复杂控制流。
- 工具类、扩展初始化、配置管理等基础设施能力必须独立于业务层。

推荐调用链：

```text
Route/Controller -> Service -> Repository -> Database/External Service
```

### 13.2 模块划分规范

- 模块优先按业务域拆分，如 `auth`、`user`、`order`、`menu`。
- 每个业务模块应在目录上具备稳定边界，避免横向散落。
- 同一业务的路由、服务、仓储、模型命名需保持一致前缀。
- 公共基础能力统一放在 `utils/`、`extensions.py`、`common/` 等基础设施目录。
- AI、缓存、外部平台集成建议独立为 `integrations/` 或 `clients/` 目录，避免污染核心业务逻辑。

建议结构：

```text
app/
├── routes/
├── services/
├── repositories/
├── entities/
├── schemas/
├── integrations/
├── utils/
├── extensions.py
└── __init__.py
```

### 13.3 依赖管理规则

- 项目统一使用 `requirements.txt` 管理运行时依赖。
- 开发、测试、质量工具可进一步拆分为 `requirements-dev.txt`，但需与主依赖保持一致来源。
- 新增依赖前必须评估必要性、维护成本、安全风险与体积影响。
- 禁止同时引入多个职责重复的框架或库。
- 外部 SDK 必须通过服务封装使用，不得在多个模块中直接散落调用。

### 13.4 接口定义标准

- 所有 API 必须使用统一前缀，如 `/api/v1`。
- 路由定义集中于 `routes/`，业务处理集中于 `services/`。
- 接口输入必须做参数校验，输出必须使用统一响应结构。
- 对外接口字段命名必须稳定，重大字段变更需要版本或兼容策略。
- OpenAI、Redis、数据库等外部依赖的异常不得直接透传给客户端。

### 13.5 配置管理规范

- 所有配置必须来自环境变量、`.env` 或配置类，禁止硬编码。
- 配置分层至少包括：开发、测试、生产。
- 数据库连接、Redis 地址、OpenAI Key、JWT Secret 等必须集中定义。
- 不同环境配置需可通过启动参数或环境变量显式切换。
- 配置模块必须提供默认值策略、必填校验与缺失时的失败提示。

推荐配置分类：

- `DATABASE_URL`
- `REDIS_URL`
- `OPENAI_API_KEY`
- `JWT_SECRET_KEY`
- `LOG_LEVEL`
- `APP_ENV`

### 13.6 数据库设计准则

- 数据表必须遵循范式与业务平衡原则，避免无约束冗余字段。
- 主键统一使用 `id`，外键统一 `xxx_id`。
- 必须保留审计字段，如 `created_at`、`updated_at`。
- 高频检索、唯一性约束、关联查询字段必须考虑索引。
- 迁移脚本必须和模型变更同步提交，禁止只改模型不改迁移。
- SQLite 仅作为开发与测试基座，设计时不得过度依赖其方言特性。

### 13.7 安全性架构要求

- 鉴权、授权、限流、审计必须作为架构级能力设计，而非散点补丁。
- 涉及身份认证的接口必须统一在中间件、装饰器或认证模块处理。
- 所有敏感配置禁止写入源码和日志。
- 数据访问必须使用 ORM 或参数化查询，杜绝 SQL 注入。
- 与 LLM、OpenAI 等外部模型交互时，需增加超时、降级、输出校验与审计日志。

### 13.8 性能优化指导原则

- 高并发热点接口应优先评估缓存、索引、批量查询与分页策略。
- Repository 层必须避免 N+1 查询。
- 对大对象序列化、复杂聚合、外部模型调用要增加超时与性能监控。
- 长耗时任务应考虑异步化或任务队列化，不阻塞请求线程。
- Redis 只缓存高收益数据，必须定义失效策略与一致性策略。

### 13.9 可扩展性设计规范

- 新增业务域时应通过新增模块扩展，而非在既有模块追加大量条件分支。
- 外部集成必须通过适配器或客户端封装，降低供应商耦合。
- 核心业务逻辑必须对存储、缓存、模型服务保持可替换性。
- 统一响应、异常处理、认证、日志、配置应作为横切关注点抽象复用。
- 对未来迁移到 MySQL/PostgreSQL、消息队列、任务调度应预留扩展空间。

### 13.10 可维护性标准

- 单个 Service 应聚焦单一业务职责。
- 单个方法逻辑过深、分支过多时必须拆分私有方法或子服务。
- 业务规则必须集中表达，不得散落在多个 Controller 中。
- 公共枚举、错误码、常量、响应结构必须集中定义。
- 每个关键模块都应具备测试入口、日志定位能力与必要注释。

### 13.11 可测试、可部署、可监控要求

- 所有 Service、Repository 必须支持依赖注入或替换，便于单元测试。
- 应用必须支持通过环境变量无交互启动。
- 构建、测试、扫描必须可在 CI 中自动执行。
- 每个请求应具备 `trace_id` 并进入统一日志链路。
- 核心外部依赖如 Redis、OpenAI 调用必须有超时、重试或失败降级策略。

## 14. 类与方法注释规范

本章节定义后端代码的注释标准，适用于控制器、服务类、仓储类、模型类、工具类以及公共函数，确保代码具备工程级文档支持。

### 14.1 注释总体原则

- 注释必须解释职责、边界、约束和设计原因，而不是简单复述代码。
- 公共类、服务类、仓储类、复杂方法必须有文档注释。
- 修改接口、参数、异常行为时，必须同步更新注释。
- 注释缺失或与实现不一致，视为代码质量问题。

### 14.2 类注释必须包含的内容

适用于 Service、Repository、Model、Client、Manager 等类：

- 类职责描述
- 作者或团队信息
- 创建时间
- 使用场景
- 上下游依赖关系
- 是否采用某种设计模式
- 线程安全性或状态特征
- 性能与使用注意事项

推荐模板：

```python
class OrderService:
    """
    类职责：负责订单查询、创建与状态流转的业务编排。
    作者：FoodTime Backend Team
    创建时间：2026-04-17
    使用场景：订单列表、订单详情、订单状态更新接口。
    依赖关系：OrderRepository、RedisClient、OpenAIClient（可选）。
    设计说明：采用 Service + Repository 分层，避免 Controller 直接操作数据库。
    线程安全性：无共享可变状态，请按请求级实例使用。
    性能注意事项：批量查询时应避免循环访问数据库。
    """
```

### 14.3 方法注释必须涵盖的要素

适用于公共方法、服务方法、仓储方法、复杂工具函数：

- 方法功能描述
- 参数说明
- 返回值说明
- 可能抛出的异常
- 使用示例
- 时间复杂度或空间复杂度
- 副作用说明
- 线程安全性说明
- 性能注意事项

推荐模板：

```python
def list_orders(page: int = 1, page_size: int = 20) -> dict:
    """
    功能描述：分页查询订单列表。
    参数说明：
        page: 当前页码，最小为 1。
        page_size: 每页条数，建议不超过 100。
    返回值说明：
        返回包含 items、page、page_size、total 的分页字典。
    异常抛出：
        BusinessError: 当分页参数非法时抛出。
        RepositoryError: 当数据库查询失败时抛出。
    使用示例：
        result = service.list_orders(page=1, page_size=20)
    复杂度：
        时间复杂度通常取决于数据库分页查询与索引命中情况。
    线程安全性：
        方法本身无共享状态，线程安全依赖外部依赖实现。
    性能注意事项：
        必须配合索引和分页，禁止无条件查询全表。
    """
```

### 14.4 Flask 路由与模型注释要求

- 路由函数必须说明接口用途、权限要求、关键参数和响应含义。
- 模型类必须说明实体业务含义、关键字段、关联关系和约束。
- 复杂序列化、钩子函数、缓存逻辑必须注明触发条件和副作用。

路由示例：

```python
@order_bp.get('')
def list_orders():
    """
    接口说明：获取订单分页列表。
    权限要求：需要用户登录。
    请求参数：page、page_size。
    返回说明：返回订单分页结构。
    异常说明：参数错误返回 400，未认证返回 401。
    """
```

### 14.5 注释格式标准

- Python 统一使用文档字符串 `""" ... """`
- 类与方法注释采用多行 docstring
- 可结合 `Args`、`Returns`、`Raises` 风格，也可使用中文分节，但项目内必须统一
- 对公共接口、公共类、关键业务方法强制书写 docstring
- 行内注释仅用于解释边界条件、兼容逻辑或反直觉实现

### 14.6 强制注释范围

以下内容必须具备文档注释：

- `routes/` 下所有公开路由函数
- `services/` 下所有公开类与公开方法
- `repositories/` 下所有公开类与公开方法
- `models.py` 或 `entities/` 中的重要模型类
- `utils/` 中被多个模块复用的公共函数
- 含事务控制、缓存、重试、LLM 调用、权限判断的复杂方法

### 14.7 注释同步更新机制

- 方法参数调整时，必须同步更新参数说明
- 返回结构变化时，必须同步更新返回值说明和示例
- 异常策略调整时，必须同步更新 `Raises` 或异常说明
- Code Review 需同时审查代码与注释是否一致

### 14.8 注释质量检查规则

- 注释必须能解释业务背景和调用约束
- 注释不得只写“查询数据”“返回结果”这类空泛描述
- 对复杂方法至少应包含异常与性能注意事项
- 对公共类至少应说明职责、依赖与使用场景
- 注释与实现冲突时，以实现为准并要求立即修正注释

### 14.9 自动化验证流程

- 可使用 `pydocstyle`、`ruff` 的 docstring 规则校验文档字符串完整性
- CI 中应增加 docstring 检查步骤
- 对公开 API、Service、Repository 可增加脚本扫描缺失注释的方法
- 自动化工具负责检查“是否存在”，Code Review 负责检查“是否准确”

建议命令：

```bash
ruff check .
pydocstyle app
pytest --cov=app --cov-report=term-missing
```

## 15. 执行要求

- 新增接口前必须先确认资源命名、状态码和响应格式是否符合规范
- 所有数据库变更必须附带迁移脚本
- 所有合并请求必须附带测试结果、影响分析和回滚说明
- 未通过静态检查、测试或安全扫描的代码禁止合并
