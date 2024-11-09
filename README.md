# 基金持仓分析系统

一个基于 Dash 和 Ant Design 构建的基金投资组合的可视化分析系统。

这是一个用于学习dash的练手项目，目前还在逐步开发中，请勿用于其他用途。


## 项目结构

    fund-analysis/
    ├── app.py                 # 主应用程序入口
    ├── backend/              # 后端API目录
    │   ├── __init__.py      # Flask应用初始化
    │   └── apis/            # API模块目录
    │       ├── account.py   # 账户相关API
    │       ├── portfolio.py # 组合相关API
    │       ├── fund.py      # 基金相关API
    │       ├── runtime.py   # 运行时API
    │       └── common.py    # 通用响应处理
    ├── components/          # 前端组件目录
    │   ├── __init__.py     # Python包标记文件
    │   ├── header.py       # 顶部导航栏组件
    │   └── sidebar.py      # 左侧菜单组件
    ├── models/             # 数据模型目录
    │   ├── __init__.py    # Python包标记文件
    │   ├── account.py     # 账户数据模型
    │   ├── database.py    # 数据库操作类
    │   ├── base.py        # 基础模型类
    │   └── fund.py        # 基金数据模型
    ├── pages/             # 页面组件目录
    │   ├── home.py       # 首页仪表盘
    │   └── account.py    # 账户管理页面
    ├── utils/             # 工具函数目录
    │   ├── db.py         # 数据库工具
    │   └── singleton.py  # 单例模式装饰器
    ├── config.py          # 应用配置文件
    ├── requirements.txt    # 项目依赖
    ├── start.sh           # 启动脚本
    ├── .flake8            # Flake8配置文件
    ├── mypy.ini           # MyPy配置文件
    ├── .gitignore         # Git忽略文件
    └── LICENSE            # 开源协议

## 技术栈

### 前端
- Dash Framework
- Plotly.js
- Feffery Ant Design Components

### 后端
- Flask
- Flask-RESTX
- SQLite3
- Peewee ORM

## API 文档

### 运行时 API
- `GET /api/runtime/status` - 获取系统运行状态
  - 返回：部署时间、运行时长、系统版本

### 账户管理 API
- `GET /api/accounts` - 获取所有账户列表
- `POST /api/accounts` - 创建新账户
- `GET /api/accounts/<id>` - 获取账户详情
- `PUT /api/accounts/<id>` - 更新账户信息
- `DELETE /api/accounts/<id>` - 删除账户

### 组合管理 API
- `GET /api/portfolios?account_id=<id>` - 获取投资组合列表
- `POST /api/portfolios` - 创建新投资组合
- `GET /api/portfolios/<id>` - 获取组合详情
- `PUT /api/portfolios/<id>` - 更新组合信息
- `DELETE /api/portfolios/<id>` - 删除组合

### 基金管理 API
- `GET /api/funds/positions/<portfolio_id>` - 获取组合持仓
- `POST /api/funds/positions/<portfolio_id>` - 添加基金持仓
- `PUT /api/funds/positions/<id>` - 更新持仓信息
- `DELETE /api/funds/positions/<id>` - 删除持仓
- `GET /api/funds/transactions/<portfolio_id>` - 获取交易记录

## 数据结构

### 账户体系
```
账户 (Account)
├── 基金组合 (Portfolio)
│   ├── 基金持仓 (FundPosition)
│   └── 交易记录 (FundTransaction)
└── 默认基金组合
    ├── 基金持仓
    └── 交易记录
```

## 安装和运行

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 运行应用：
```bash
python app.py
```

应用将在 http://localhost:8050 启动，API文档访问 http://localhost:8050/api/doc

## 开发计划

- [x] 基础框架搭建
- [x] 数据模型设计
- [x] RESTful API 实现
- [x] 统一响应格式
- [x] ORM 集成
- [x] 账户管理功能
- [ ] 基金数据导入
- [ ] 持仓分析
- [ ] 收益分析
- [ ] 风险评估

## 开发指南

### API 开发
1. 在 `backend/apis/` 下创建新的 API 模块
2. 在 `backend/__init__.py` 中注册 API 命名空间
3. 使用 common.response 确保响应格式统一
4. 实现相应的数据库操作方法

### 数据库开发
1. 在 `models/` 下定义数据模型
2. 使用 Peewee ORM 管理数据库操作
3. 在 `models/database.py` 中实现数据操作函数

### 前端开发
1. 在 `pages/` 下创建新的页面组件
2. 在 `app.py` 中添加路由处理
3. 在 `sidebar.py` 中添加菜单项

## 许可证

MIT License
