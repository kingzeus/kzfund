# 基金持仓分析系统

一个基于 Dash 和 Ant Design 构建的基金投资组合的可视化分析系统。

## 项目结构

    fund-analysis/
    ├── app.py                 # 主应用程序入口
    ├── backend/               # 后端API目录
    ├── components/            # 前端组件目录
    ├── models/                # 数据模型目录
    ├── pages/                 # 页面组件目录
    ├── utils/                 # 工具函数目录
    ├── config.py              # 应用配置文件
    ├── requirements.txt       # 项目依赖
    ├── start.sh               # 启动脚本
    ├── .flake8                # Flake8配置文件
    ├── mypy.ini               # MyPy配置文件
    ├── .gitignore             # Git忽略文件
    └── LICENSE                # 开源协议

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


## 安装和运行

运行 start.sh


应用将在 http://localhost:8050 启动，API文档访问 http://localhost:8050/api/doc

## 开发计划

- [x] 基础框架搭建
- [x] 数据模型设计
- [x] RESTful API 实现
- [x] 统一响应格式
- [x] ORM 集成
- [x] 账户管理功能
- [x] 数据库迁移
- [ ] 基金数据导入
- [ ] 持仓分析
- [ ] 收益分析
- [ ] 风险评估


## 许可证

MIT License