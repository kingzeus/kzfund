#!/bin/bash

# 检查conda是否已安装
if ! command -v conda &> /dev/null; then
    echo "错误: 未找到conda，请先安装Anaconda或Miniconda"
    exit 1
fi

# 检查fund环境是否存在
if ! conda env list | grep -q "^fund "; then
    echo "创建新的conda环境: fund"
    conda create -n fund python=3.10 -y
else
    echo "fund环境已存在"
fi

# 激活fund环境
echo "激活fund环境"
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate fund

# 检查并安装/更新依赖
echo "检查并安装依赖"
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "错误: 未找到requirements.txt文件"
    exit 1
fi



# 运行代码格式检查
echo "运行代码格式检查..."
black app.py
flake8 app.py
mypy app.py

# 启动应用
echo "启动基金分析应用..."
python app.py