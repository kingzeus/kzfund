#!/bin/bash

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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
        exit 1
    fi
    echo -e "${GREEN}conda环境激活成功${NC}"
    return 0
}
# 检查poetry是否已安装
check_poetry() {
    if ! command -v poetry &> /dev/null; then
        echo -e "${RED}错误: 未找到poetry，正在安装...${NC}"
        # 获取当前conda环境信息
        conda_env=$(conda info --envs | grep "*" | awk '{print $1}')
        echo -e "${YELLOW}当前conda环境: ${conda_env}${NC}"
        if ! conda install -y poetry; then
            echo -e "${RED}安装poetry失败${NC}"
            exit 1
        fi
    fi
    return 0
}

# 创建并配置环境
setup_env() {
    echo -e "${YELLOW}配置开发环境...${NC}"
    # 获取poetry版本
    poetry_version=$(poetry --version | cut -d' ' -f3)
    echo -e "${GREEN}当前poetry版本: $poetry_version${NC}"

    # 配置poetry不使用虚拟环境
    echo -e "${YELLOW}配置poetry...${NC}"
    poetry config virtualenvs.create false

    # 安装项目依赖
    echo -e "${YELLOW}安装项目依赖...${NC}"
    if ! poetry install; then
        echo -e "${RED}安装依赖失败${NC}"
        echo -e "按回车键返回主菜单..."
        read
        return 1
    fi

    echo -e "${GREEN}环境配置成功${NC}"
    read -p "按回车键继续..."
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
    echo -e "${YELLOW}运行代码检查...${NC}"
    local has_error=0
    local python_files=$(find . -type f -name "*.py" ! -path "*/\.*" ! -path "*/migrations/*" ! -path "*/venv/*" ! -path "*/env/*")

    # 运行black检查代码格式
    echo -e "\n${YELLOW}[1/2] 运行black检查代码格式...${NC}"
    if ! black --check $python_files; then
        echo -e "${YELLOW}代码格式需要调整，正在格式化...${NC}"
        if ! black $python_files; then
            echo -e "${RED}black 格式化失败${NC}"
            has_error=1
        else
            echo -e "${GREEN}代码格式化完成${NC}"
        fi
    else
        echo -e "${GREEN}代码格式检查通过${NC}"
    fi

    # 运行pylint检查代码质量
    echo -e "\n${YELLOW}[2/2] 运行pylint检查代码质量...${NC}"

    # 创建临时文件存储pylint输出
    local temp_file=$(mktemp)
    local prev_rate=""
    local curr_rate=""
    local total_files=0
    local total_errors=0
    local total_warnings=0
    local total_conventions=0
    local total_refactors=0

    # 统计Python文件总数
    total_files=$(echo "$python_files" | wc -w)

    if ! pylint $python_files > "$temp_file" 2>&1; then
        echo -e "\n${RED}发现以下问题:${NC}"

        # 统计各类问题数量
        while IFS= read -r line; do
            if [[ $line =~ :[0-9]+:[0-9]+:[[:space:]][E] ]]; then
                ((total_errors++))
            elif [[ $line =~ :[0-9]+:[0-9]+:[[:space:]][W] ]]; then
                ((total_warnings++))
            elif [[ $line =~ :[0-9]+:[0-9]+:[[:space:]][C] ]]; then
                ((total_conventions++))
            elif [[ $line =~ :[0-9]+:[0-9]+:[[:space:]][R] ]]; then
                ((total_refactors++))
            fi
        done < "$temp_file"

        # 提取评分信息
        curr_rate=$(grep "Your code has been rated at" "$temp_file" | tail -n1)

        # 显示详细错误信息
        echo -e "\n${YELLOW}=== 详细错误信息 ===${NC}"
        while IFS= read -r line; do
            if [[ $line =~ ^\*+[[:space:]]Module[[:space:]] ]]; then
                # 提取模块名
                module_name=$(echo "$line" | sed 's/\*\+ Module //')
                echo -e "\n文件: ${module_name}"
            elif [[ $line =~ ^[[:space:]]*[A-Za-z0-9/_.-]+:[0-9]+:[0-9]+:[[:space:]] ]]; then
                # 格式化错误信息
                error_line=$(echo "$line" | sed -E 's/^[[:space:]]*([^:]+):([0-9]+):([0-9]+): ([A-Z][0-9]+): (.+)/  ✗ \1:\2:\3: \4: \5/')
                # 根据错误类型添加颜色
                if [[ $line =~ :[[:space:]][E][0-9] ]]; then
                    echo -e "${RED}$error_line${NC}"
                elif [[ $line =~ :[[:space:]][W][0-9] ]]; then
                    echo -e "${YELLOW}$error_line${NC}"
                elif [[ $line =~ :[[:space:]][R][0-9] ]]; then
                    echo -e "${BLUE}$error_line${NC}"
                else
                    echo -e "${GREEN}$error_line${NC}"
                fi
            fi
        done < "$temp_file"

        # 显示错误和警告汇总
        echo -e "\n${YELLOW}=== 错误和警告汇总 ===${NC}"
        # 创建临时文件存储汇总信息
        local summary_file=$(mktemp)
        grep -E "^[[:space:]]*[A-Za-z0-9/_.-]+:[0-9]+:[0-9]+:[[:space:]][EWCR][0-9]+" "$temp_file" | \
            sed -E 's/.*:[0-9]+:[0-9]+: ([A-Z][0-9]+): .*/\1/' | \
            sort | uniq -c | sort -nr > "$summary_file"

        if [ -s "$summary_file" ]; then
            while IFS= read -r line; do
                count=$(echo "$line" | awk '{print $1}')
                code=$(echo "$line" | awk '{print $2}')
                msg=$(grep -m 1 ": $code: " "$temp_file" | sed -E 's/.*: [A-Z][0-9]+: (.*)/\1/')

                # 根据错误代码类型添加颜色
                if [[ $code =~ ^E ]]; then
                    echo -e "${RED}$count 个 $code: $msg${NC}"
                elif [[ $code =~ ^W ]]; then
                    echo -e "${YELLOW}$count 个 $code: $msg${NC}"
                elif [[ $code =~ ^R ]]; then
                    echo -e "${BLUE}$count 个 $code: $msg${NC}"
                else
                    echo -e "${GREEN}$count 个 $code: $msg${NC}"
                fi
            done < "$summary_file"
        else
            echo -e "${GREEN}未发现错误和警告${NC}"
        fi

        # 清理临时文件
        rm -f "$summary_file"

        # 显示统计信息
        echo -e "\n${YELLOW}=== 问题统计 ===${NC}"
        printf "检查文件数: %8d\n" "${total_files}"
        printf "${RED}错误(E): %8d${NC}\n" "${total_errors}"
        printf "${YELLOW}警告(W): %8d${NC}\n" "${total_warnings}"
        printf "${GREEN}规范(C): %8d${NC}\n" "${total_conventions}"
        printf "${BLUE}重构(R): %8d${NC}\n" "${total_refactors}"
        printf "问题总数: %8d\n" "$((total_errors + total_warnings + total_conventions + total_refactors))"

        # 显示代码质量评分
        echo -e "\n${YELLOW}=== 代码质量评分 ===${NC}"
        if [ -n "$curr_rate" ]; then
            # 解析评分信息
            current=$(echo "$curr_rate" | sed -E 's/.*rated at ([0-9]+\.[0-9]+).*/\1/')
            previous=$(echo "$curr_rate" | sed -E 's/.*previous run: ([0-9]+\.[0-9]+).*/\1/')
            change=$(echo "$curr_rate" | sed -E 's/.*[0-9]+\.[0-9]+\/10 \((.*)\)/\1/' | grep -o '[+-][0-9.]\+')

            # 显示评分信息
            if [ -n "$previous" ] && [ -n "$change" ]; then
                if [[ "$change" == +* ]]; then
                    echo -e "${GREEN}当前评分: $current/10${NC}"
                    echo -e "${GREEN}评分提升: $change (上次: $previous/10)${NC}"
                elif [[ "$change" == -* ]]; then
                    echo -e "${RED}当前评分: $current/10${NC}"
                    echo -e "${RED}评分下降: $change (上次: $previous/10)${NC}"
                else
                    echo -e "${YELLOW}当前评分: $current/10${NC}"
                    echo -e "${YELLOW}评分未变 (上次: $previous/10)${NC}"
                fi
            else
                echo -e "${YELLOW}当前评分: $current/10${NC}"
                echo -e "${YELLOW}首次检查，无历史评分${NC}"
            fi

            # 根据评分显示状态
            if (( $(echo "$current >= 9.0" | bc -l) )); then
                echo -e "\n${GREEN}✨ 代码质量优秀！继续保持${NC}"
            elif (( $(echo "$current >= 8.0" | bc -l) )); then
                echo -e "\n${GREEN}👍 代码质量良好${NC}"
            elif (( $(echo "$current >= 7.0" | bc -l) )); then
                echo -e "\n${YELLOW}⚠️ 代码质量一般，建议改进${NC}"
            else
                echo -e "\n${RED}⚠️ 代码质量需要改进${NC}"
                echo -e "\n${YELLOW}改进建议:${NC}"
                echo -e "1. 优先修复 ${RED}错误(E)${NC} 级别问题"
                echo -e "2. 处理重要的 ${YELLOW}警告(W)${NC} 问题"
                echo -e "3. 考虑优化 ${GREEN}规范(C)${NC} 建议"
                echo -e "4. 关注需要 ${BLUE}重构(R)${NC} 的代码"
            fi
        else
            echo -e "${RED}无法解析评分信息${NC}"
        fi

        # 保存当前��分
        echo "$curr_rate" > .pylint_rate

        has_error=1
        echo -e "\n${YELLOW}提示: 使用 pylint --help-msg=<msg-id> 查看具体错误说明${NC}"
    else
        echo -e "${GREEN}代码质量检查通过${NC}"
        # 清除之前的评分记录
        rm -f .pylint_rate
    fi

    # 清理临时文件
    rm -f "$temp_file"

    if [ $has_error -eq 1 ]; then
        echo -e "\n${RED}代码检查发现问题，请根据上方提示进行修复${NC}"
        return 1
    fi

    echo -e "\n${GREEN}所有代码检查完成，未发现问题${NC}"
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

# 启动测试
start_test() {
    echo -e "${YELLOW}启动测试代码...${NC}"
    if ! python test.py; then
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
    echo "------------"
    echo "9) 测试"
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
    check_poetry || return 1
    setup_env || return 1
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
            ensure_directories || continue
            check_conda || continue
            setup_conda_env || continue
            activate_conda_env || continue
            check_poetry || continue
            setup_env || continue
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}环境初始化完成！${NC}"
            fi
            ;;
        2)
            echo -e "${YELLOW}开始迁移数据库...${NC}"
            init_database || continue
            ;;
        3)
            echo -e "${YELLOW}开始运行代码检查...${NC}"
            run_code_check || continue
            ;;
        4)
            echo -e "${YELLOW}开始启动应用...${NC}"
            ensure_directories || continue
            activate_conda_env || continue
            start_app || continue
            ;;
        5)
            do_full_install || continue
            ;;
        9)
            start_test || continue
            ;;
        0)
            echo -e "${GREEN}再见！${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}无效的选择，请重试${NC}"
            echo -e "按回车键返回主菜单..."
            ;;
    esac

    # 如果不是启动应用，则等待用户按回车继续
    if [ "$choice" != "4" ] && [ "$choice" != "5" ]; then
        echo
        echo -e "按回车键返回主菜单..."
    fi
done
