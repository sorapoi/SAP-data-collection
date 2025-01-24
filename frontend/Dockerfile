# 构建阶段
FROM node:18-alpine as build-stage

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# 使用生产环境变量构建
RUN npm run build

# 生产阶段
FROM nginx:stable-alpine as production-stage

# 复制构建产物
COPY --from=build-stage /app/dist /usr/share/nginx/html
RUN ls -la /usr/share/nginx/html/

# 复制 nginx 配置
COPY ./frontend/nginx.conf /etc/nginx/conf.d/default.conf

# 设置权限
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chmod -R 755 /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"] 