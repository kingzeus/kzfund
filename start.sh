#!/bin/bash

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查并创建必要的目录
ensure_directories() {
    local dirs=("database" "migrations" "logs")

    for dir in "${dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            echo -e "${YELLOW}创建${dir}目录...${NC}"
            mkdir -p "$dir"
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}${dir}目录创建成功${NC}"
            else
                echo -e "${RED}${dir}目录创建失败${NC}"
                return 1
            fi
        fi
    done
    return 0
}

# 检查conda是否已安装
check_conda() {
    if ! command -v conda &> /dev/null; then
        echo -e "${RED}错误: 未找到conda，请先安装Anaconda或Miniconda${NC}"
        exit 1
    fi
}

# 检查并创建conda环境
setup_conda_env() {
    if ! conda env list | grep -q "^fund "; then
        echo -e "${YELLOW}创建新的conda环境: fund${NC}"
        if ! conda create -n fund python=3.10 -y; then
            echo -e "${RED}创建conda环境失败${NC}"
            read -p "按回车键继续..."
            return 1
        fi
        echo -e "${GREEN}conda环境创建成功${NC}"
    else
        echo -e "${GREEN}fund环境已存在${NC}"
    fi
    return 0
}

# 激活conda环境
activate_conda_env() {
    echo -e "${YELLOW}激活fund环境${NC}"
    source "$(conda info --base)/etc/profile.d/conda.sh"
    if ! conda activate fund; then
        echo -e "${RED}激活conda环境失败${NC}"
        read -p "按回车键继续..."
        return 1
    fi
    echo -e "${GREEN}conda环境激活成功${NC}"
    return 0
}

# 安装依赖
install_dependencies() {
    echo -e "${YELLOW}检查并安装依赖${NC}"
    if [ -f "requirements.txt" ]; then
        if ! pip install -r requirements.txt; then
            echo -e "${RED}安装依赖失败${NC}"
            read -p "按回车键继续..."
            return 1
        fi
        echo -e "${GREEN}依赖安装成功${NC}"
    else
        echo -e "${RED}错误: 未找到requirements.txt文件${NC}"
        read -p "按回车键继续..."
        return 1
    fi
    return 0
}

# 初始化数据库
init_database() {
    echo -e "${YELLOW}迁移数据库...${NC}"

    # 确保必要的目录存在
    ensure_directories || return 1

    # 运行数据库迁移
    if ! python -m migrations.migrate; then
        echo -e "${RED}数据库迁移失败！${NC}"
        read -p "按回车键继续..."
        return 1
    fi

    echo -e "${GREEN}数据库迁移完成！${NC}"
    return 0
}

# 运行代码格式检查
run_code_check() {
    echo -e "${YELLOW}运行代码格式检查...${NC}"
    local has_error=0

    if ! black app.py; then
        echo -e "${RED}black 格式化失败${NC}"
        has_error=1
    fi

    if ! flake8 app.py; then
        echo -e "${RED}flake8 检查失败${NC}"
        has_error=1
    fi

    if ! mypy app.py; then
        echo -e "${RED}mypy 类型检查失败${NC}"
        has_error=1
    fi

    if [ $has_error -eq 1 ]; then
        read -p "代码检查发现错误，按回车键继续..."
        return 1
    fi

    echo -e "${GREEN}代码检查完成${NC}"
    return 0
}

# 启动应用
start_app() {
    echo -e "${YELLOW}启动基金分析应用...${NC}"
    if ! python app.py; then
        echo -e "${RED}应用启动失败${NC}"
        read -p "按回车键继续..."
        return 1
    fi
    return 0
}

# 显示菜单
show_menu() {
    clear
    echo -e "${GREEN}基金分析系统管理脚本${NC}"
    echo "------------------------"
    echo "1) 初始化环境"
    echo "2) 迁移数据库"
    echo "3) 运行代码检查"
    echo "4) 启动应用"
    echo "5) 完整安装(1-4步骤)"
    echo "0) 退出"
    echo "------------------------"
}

# 执行完整安装
do_full_install() {
    echo -e "${YELLOW}开始完整安装...${NC}"

    ensure_directories || return 1
    check_conda || return 1
    setup_conda_env || return 1
    activate_conda_env || return 1
    install_dependencies || return 1
    init_database || return 1
    run_code_check || return 1
    start_app || return 1

    return 0
}

# 主循环
while true; do
    show_menu
    read -p "请选择操作 (0-5): " choice

    case $choice in
        1)
            echo -e "${YELLOW}开始初始化环境...${NC}"
            ensure_directories
            check_conda
            setup_conda_env
            activate_conda_env
            install_dependencies
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}环境初始化完成！${NC}"
            fi
            ;;
        2)
            echo -e "${YELLOW}开始迁移数据库...${NC}"
            init_database
            ;;
        3)
            echo -e "${YELLOW}开始运行代码检查...${NC}"
            run_code_check
            ;;
        4)
            echo -e "${YELLOW}开始启动应用...${NC}"
            ensure_directories
            activate_conda_env
            start_app
            ;;
        5)
            do_full_install
            ;;
        0)
            echo -e "${GREEN}再见！${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}无效的选择，请重试${NC}"
            read -p "按回车键继续..."
            ;;
    esac

    # 如果不是启动应用，则等待用户按回车继续
    if [ "$choice" != "4" ] && [ "$choice" != "5" ]; then
        echo
        read -p "按回车键继续..."
    fi
done