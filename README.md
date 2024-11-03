# 基金持仓分析系统

一个基于 Dash 和 Ant Design 构建的基金持仓分析系统。

## 项目结构

    fund-analysis/
    ├── app.py                 # 主应用程序入口
    ├── components/            # 组件目录
    │   ├── __init__.py       # Python包标记文件
    │   ├── header.py         # 顶部导航栏组件
    │   └── sidebar.py        # 左侧菜单组件
    ├── requirements.txt       # 项目依赖
    └── start.sh              # 启动脚本

## 依赖包列表

    dash==2.18.1
    feffery_antd_components>=0.3.8
    feffery_dash_utils>=0.1.4
    feffery_markdown_components>=0.3.0rc3
    feffery_utils_components>=0.2.0rc20
    Flask==3.0.3
    pandas>=2.0.0
    numpy>=1.24.0
    plotly>=5.18.0
    dash-bootstrap-components>=1.5.0
    mypy>=1.8.0
    black>=24.2.0
    flake8>=7.0.0

## 主要功能

- 基金持仓数据可视化
- 资产配置分析
- 收益走势分析
- 风险评估

## 技术栈

- Python
- Dash
- Plotly
- Feffery Ant Design Components

## 安装和运行

1. 安装依赖：

    pip install -r requirements.txt

2. 运行应用：

    python app.py

或者使用启动脚本：

    sh start.sh

应用将在 http://localhost:8050 启动。

## 开发说明

- `app.py`: 主应用程序文件，包含应用初始化和主要布局
- `components/`: 包含所有可重用的UI组件
  - `header.py`: 实现顶部导航栏
  - `sidebar.py`: 实现左侧菜单栏

## 开发计划

- [ ] 添加基金数据导入功能
- [ ] 实现基金收益分析
- [ ] 添加风险评估功能
- [ ] 添加数据导出功能
- [ ] 优化图表交互体验

## 贡献指南

欢迎提交 Issue 和 Pull Request 来帮助改进项目。

## 许可证

MIT License