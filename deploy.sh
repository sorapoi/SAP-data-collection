#!/bin/bash

# 创建必要的目录
mkdir -p /app/materials/data

# 复制配置文件
cp docker-compose.yml /app/materials/
cp .env /app/materials/

# 启动服务
cd /app/materials
docker-compose pull
docker-compose up -d 