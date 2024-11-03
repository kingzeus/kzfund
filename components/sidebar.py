import feffery_antd_components as fac


def create_sidebar():
    return fac.AntdCol(
        fac.AntdMenu(
            menuItems=[
                {
                    "component": "Item",
                    "props": {
                        "key": "portfolio",
                        "title": "持仓分析",
                        "icon": "fund",
                    },
                },
                {
                    "component": "Item",
                    "props": {
                        "key": "performance",
                        "title": "收益分析",
                        "icon": "line-chart",
                    },
                },
                {
                    "component": "Item",
                    "props": {
                        "key": "risk",
                        "title": "风险评估",
                        "icon": "warning",
                    },
                },
            ],
            mode="inline",
            style={"height": "100%"},
        ),
        span=4,
        style={
            "borderRight": "1px solid #f0f0f0",
            "minHeight": "calc(100vh - 100px)",
        },
    )
