# 物料主数据管理系统

基于 Vue 3 + TypeScript + FastAPI 的物料主数据管理系统。

## 功能介绍

### 用户权限
- 信息部：导入/导出数据
- 运营管理部：编辑 MRP控制者
- 采购部：编辑最小批量大小、舍入值、计划交货时间
- QC检测室：编辑检测周期

### 主要功能
- Excel数据导入（自动去重和过滤空值）
- 分页显示数据（每页15条）
- 实时数据验证和保存
- 条件导出（仅导出已完成必填且未完成的数据）

## 开发环境

### 前端
- Vue 3
- TypeScript
- Vite
- xlsx-js
- Axios

### 后端
- FastAPI
- SQLite
- PyJWT

## 快速开始

### 1. 启动后端

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务器
uvicorn main:app --reload
```

### 2. 启动前端

```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 3. 默认用户
- 信息部：it1/password
- 运营管理部：op1/password
- 采购部：pur1/password
- QC检测室：qc1/password

## 使用说明

### 数据导入
1. 使用信息部账号登录
2. 点击"选择文件"上传Excel
3. 系统自动过滤无效数据和重复数据

### 数据编辑
1. 各部门登录后只能编辑其权限范围内的字段
2. 编辑后系统自动保存
3. 输入时进行实时验证

### 数据导出
1. 使用信息部账号登录
2. 点击"导出Excel"
3. 系统仅导出：
   - 检测周期已填
   - 最小批量大小已填
   - 舍入值已填
   - 计划交货时间已填
   - MRP控制者已填
   - 且完成时间为空的数据
4. 导出后自动更新这些数据的完成时间

## 注意事项

1. 后端默认端口：8000
2. 前端默认端口：5173
3. 首次运行自动初始化数据库
4. 物料编号不可重复

## CI/CD

本项目使用 GitHub Actions 进行持续集成和部署：

### 自动化测试
- 后端：Python 单元测试
- 前端：TypeScript 类型检查
- 代码质量：Flake8 代码风格检查

### 自动部署
- 提交到 main 分支自动触发部署
- 部署需要配置以下 secrets:
  - DEPLOY_KEY: 服务器 SSH 密钥
  - SERVER_IP: 服务器 IP
  - SERVER_USER: 服务器用户名
