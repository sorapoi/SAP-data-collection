#!/bin/bash

# 创建项目目录
mkdir -p /app/materials
cd /app/materials

# 克隆代码（如果是首次部署）
if [ ! -d ".git" ]; then
    git clone <your-repository-url> .
fi

# 创建必要的目录
mkdir -p data

# 确保有正确的环境变量文件
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << EOF
SECRET_KEY=your-secret-key
CORS_ORIGINS=["http://localhost:80"]
EOF
fi

# 拉取最新代码（如果不是首次部署）
git pull

# 构建和启动服务
docker-compose pull
docker-compose up -d --build 