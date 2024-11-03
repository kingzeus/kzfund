# 基金持仓分析系统

这是一个使用Dash框架开发的基金投资组合的可视化分析系统，提供基金投资组合的可视化分析功能。

## 功能特点

- 持仓分析展示
  - 总资产概览
  - 基金持仓数量统计
  - 资产配置饼图
  - 收益走势图
  - 基金持仓明细表
- 基金净值走势
- 投资组合分析

## 界面布局

1. **顶部导航栏**
   - 系统标题
   - 数据导入按钮
   - 数据刷新按钮

2. **左侧菜单**
   - 持仓分析
   - 收益分析
   - 风险评估

3. **数据概览区**
   - 总资产卡片（含日收益）
   - 持仓基金数卡片（含活跃基金数）

4. **图表展示区**
   - 资产配置饼图
   - 收益走势折线图

5. **基金列表**
   - 基金代码
   - 基金名称
   - 持仓份额
   - 最新净值
   - 持仓市值
   - 收益率

## 技术栈

- Python 3.10
- Dash 2.18.1
- Feffery Antd Components
- Flask 3.0.3
- Pandas, Numpy, Plotly
- 代码质量工具：black, flake8, mypy

## 环境要求

- Anaconda 或 Miniconda
- Git

## 安装说明

1. 克隆项目到本地：
```bash
git clone https://github.com/kingzeus/kzfund.git
```

2. 进入项目目录：
```bash
cd kzfund
```

3. 设置启动脚本权限：
```bash
chmod +x start.sh
```

4. 运行启动脚本：
```bash
./start.sh
```

启动脚本会自动：
- 检查并创建conda环境(fund)
- 安装所有必要依赖
- 运行代码质量检查
- 启动应用程序

## 项目结构

```
project/
│
├── app.py              # 主应用文件
├── requirements.txt    # 项目依赖
├── start.sh           # 环境配置和启动脚本
└── README.md          # 项目文档
```

## 依赖包列表

```
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
```

## 使用说明

1. 首次运行，执行 `./start.sh`，脚本会自动设置环境并启动应用
2. 启动成功后，访问 http://localhost:8050
3. 使用顶部的"数据导入"按钮导入基金数据
4. 使用"刷新数据"按钮更新显示
5. 在左侧导航栏切换不同的分析视图

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