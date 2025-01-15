#!/bin/bash

# 创建项目目录和数据目录
mkdir -p /app/materials/data

# 确保有正确的环境变量文件
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << EOF
SECRET_KEY=your-secret-key
CORS_ORIGINS=["http://localhost:80"]
DATABASE_PATH=/app/materials/data/materials.db
EOF
fi
# 拉取最新代码（如果不是首次部署）
git pull

# 复制源代码到 /app/materials
cp -r . /app/materials

# 构建和启动服务
docker-compose pull
docker-compose up -d --build 