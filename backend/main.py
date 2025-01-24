from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
import sqlite3
import jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
import os

app = FastAPI()

load_dotenv()

# JWT配置
SECRET_KEY = os.getenv("SECRET_KEY")
security = HTTPBearer()

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:80", "http://frontend"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据模型
class User(BaseModel):
    username: str
    password: str

class Material(BaseModel):
    物料: str
    物料描述: str
    市场: Optional[str] = None
    备注1: Optional[str] = None
    备注2: Optional[str] = None
    生产厂商: Optional[str] = None
    检测时间QC: Optional[str] = None
    最小批量大小PUR: Optional[str] = None
    舍入值PUR: Optional[str] = None
    计划交货时间PUR: Optional[str] = None
    MRP控制者: Optional[str] = None
    MRP类型: Optional[str] = None
    批量程序: Optional[str] = None
    固定批量: Optional[str] = None
    再订货点: Optional[str] = None
    安全库存: Optional[str] = None
    批量大小: Optional[str] = None
    舍入值: Optional[str] = None
    采购类型: Optional[str] = None
    收货处理时间: Optional[str] = None
    计划交货时间: Optional[str] = None
    MRP区域: Optional[str] = None
    反冲: Optional[str] = None
    批量输入: Optional[str] = None
    自制生产时间: Optional[str] = None
    策略组: Optional[str] = None
    综合MRP: Optional[str] = None
    消耗模式: Optional[str] = None
    向后跨期期间: Optional[str] = None
    向后跨期时间: Optional[str] = None
    独立集中: Optional[str] = None
    计划时间界: Optional[str] = None
    生产评估: Optional[str] = None
    生产计划: Optional[str] = None
    新建时间: Optional[str] = None
    完成时间: Optional[str] = None

# 添加新的请求体模型
class UpdateMaterial(BaseModel):
    field: str
    value: str

# 数据库初始化
def init_db():
    conn = sqlite3.connect('materials.db')
    c = conn.cursor()
    
    # 创建用户表
    c.execute('''
    CREATE TABLE IF NOT EXISTS users
    (username TEXT PRIMARY KEY, password TEXT, department TEXT)
    ''')
    
    # 创建物料表
    c.execute('''
    CREATE TABLE IF NOT EXISTS materials
    (id INTEGER PRIMARY KEY AUTOINCREMENT,
     物料 TEXT,
     物料描述 TEXT,
     市场 TEXT,
     备注1 TEXT,
     备注2 TEXT,
     生产厂商 TEXT,
     检测时间QC TEXT,
     最小批量大小PUR TEXT,
     舍入值PUR TEXT,
     计划交货时间PUR TEXT,
     MRP控制者 TEXT,
     MRP类型 TEXT,
     批量程序 TEXT,
     固定批量 TEXT,
     再订货点 TEXT,
     安全库存 TEXT,
     批量大小 TEXT,
     舍入值 TEXT,
     采购类型 TEXT,
     收货处理时间 TEXT,
     计划交货时间 TEXT,
     MRP区域 TEXT,
     反冲 TEXT,
     批量输入 TEXT,
     自制生产时间 TEXT,
     策略组 TEXT,
     综合MRP TEXT,
     消耗模式 TEXT,
     向后跨期期间 TEXT,
     向后跨期时间 TEXT,
     独立集中 TEXT,
     计划时间界 TEXT,
     生产评估 TEXT,
     生产计划 TEXT,
     新建时间 TEXT,
     完成时间 TEXT)
    ''')
    
    # 插入默认用户
    c.execute('''
    INSERT OR IGNORE INTO users (username, password, department) VALUES 
    ('op1', 'password', '运营管理部'),
    ('pur1', 'password', '采购部'),
    ('it1', 'password', '信息部'),
    ('qc1', 'password', 'QC检测室')
    ''')
    
    conn.commit()
    conn.close()

init_db()

# 用户认证
def authenticate_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        return payload
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc

# 登录接口
@app.post("/login")
async def login(user: User):
    conn = sqlite3.connect('materials.db')
    c = conn.cursor()
    c.execute('SELECT department FROM users WHERE username=? AND password=?',
              (user.username, user.password))
    result = c.fetchone()
    conn.close()
    
    if result:
        token = jwt.encode(
            {"username": user.username, "department": result[0]},
            SECRET_KEY,
            algorithm="HS256"
        )
        return {"token": token, "department": result[0]}
    raise HTTPException(status_code=401, detail="Invalid credentials")

# 保存物料数据
@app.post("/materials")
async def save_materials(materials: List[Material], user = Depends(authenticate_user)):
    try:
        if user["department"] not in ["信息部", "运营管理部", "采购部", "QC检测室"]:
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        conn = sqlite3.connect('materials.db')
        c = conn.cursor()
        
        # 过滤掉物料为空的数据
        valid_materials = [m for m in materials if m.物料.strip()]
        
        # 检查重复数据
        duplicates = []
        for material in valid_materials:
            c.execute('SELECT 物料 FROM materials WHERE 物料 = ?', (material.物料,))
            if c.fetchone():
                duplicates.append(material.物料)
        
        if duplicates:
            conn.close()
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "发现重复数据",
                    "duplicates": duplicates
                }
            )
        
        # 保存数据
        for material in valid_materials:
            material.新建时间 = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute('''
            INSERT INTO materials (
                物料, 物料描述, 市场, 备注1, 备注2, 生产厂商, 检测时间QC, 最小批量大小PUR, 
                舍入值PUR, 计划交货时间PUR, MRP控制者, MRP类型, 批量程序, 固定批量, 再订货点, 
                安全库存, 批量大小, 舍入值, 采购类型, 收货处理时间, 计划交货时间, MRP区域, 反冲, 批量输入, 
                自制生产时间, 策略组, 综合MRP, 消耗模式, 向后跨期期间, 向后跨期时间, 
                独立集中, 计划时间界, 生产评估, 生产计划, 新建时间, 完成时间
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                     ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                material.物料, material.物料描述, material.市场, material.备注1, material.备注2,
                material.生产厂商, material.检测时间QC, material.最小批量大小PUR, material.舍入值PUR,
                material.计划交货时间PUR, material.MRP控制者, material.MRP类型, material.批量程序,
                material.固定批量, material.再订货点, material.安全库存, material.批量大小,
                material.舍入值, material.采购类型, material.收货处理时间, material.计划交货时间,
                material.MRP区域, material.反冲, material.批量输入, material.自制生产时间,
                material.策略组, material.综合MRP, material.消耗模式, material.向后跨期期间,
                material.向后跨期时间, material.独立集中, material.计划时间界, material.生产评估,
                material.生产计划, material.新建时间, material.完成时间
            ))
            
        conn.commit()
        conn.close()
        return {"message": f"成功导入 {len(valid_materials)} 条数据"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error saving materials: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 获取物料数据
@app.get("/materials")
async def get_materials(
    user = Depends(authenticate_user),
    page: int = 1,
    page_size: int = 15
):
    conn = sqlite3.connect('materials.db')
    c = conn.cursor()
    
    # 获取总记录数
    c.execute('SELECT COUNT(*) FROM materials')
    total = c.fetchone()[0]
    
    # 计算偏移量
    offset = (page - 1) * page_size
    
    # 获取分页数据
    c.execute('SELECT * FROM materials LIMIT ? OFFSET ?', (page_size, offset))
    columns = [description[0] for description in c.description]
    result = [dict(zip(columns, row)) for row in c.fetchall()]
    conn.close()
    
    return {
        "total": total,
        "items": result,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    } 

# 修改更新物料数据的接口
@app.put("/materials/{material_id}")
async def update_material(
    material_id: str,
    update_data: UpdateMaterial,
    user = Depends(authenticate_user)
):
    # 检查权限
    allowed_fields = {
        '运营管理部': ['MRP控制者'],
        '采购部': ['最小批量大小PUR', '舍入值PUR', '计划交货时间PUR'],
        'QC检测室': ['检测时间QC']
    }
    
    if user["department"] not in allowed_fields or update_data.field not in allowed_fields[user["department"]]:
        raise HTTPException(status_code=403, detail="无权修改该字段")
    
    try:
        conn = sqlite3.connect('materials.db')
        c = conn.cursor()
        
        # 更新字段
        c.execute(f'UPDATE materials SET {update_data.field} = ? WHERE 物料 = ?', 
                 (update_data.value, material_id))
        
        if c.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=404, detail="物料不存在")
        
        conn.commit()
        conn.close()
        return {"message": "更新成功"}
        
    except Exception as e:
        print(f"Error updating material: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 

# 获取待导出的数据
@app.get("/materials/export")
async def get_export_materials(user = Depends(authenticate_user)):
    if user["department"] != "信息部":
        raise HTTPException(status_code=403, detail="无权导出数据")
        
    try:
        conn = sqlite3.connect('materials.db')
        c = conn.cursor()
        
        # 获取所有需要的字段都已填写但完成时间为空的数据
        c.execute('''
            SELECT * FROM materials 
            WHERE 检测时间QC IS NOT NULL 
            AND 检测时间QC != ''
            AND 最小批量大小PUR IS NOT NULL 
            AND 最小批量大小PUR != ''
            AND 舍入值PUR IS NOT NULL 
            AND 舍入值PUR != ''
            AND 计划交货时间PUR IS NOT NULL 
            AND 计划交货时间PUR != ''
            AND MRP控制者 IS NOT NULL 
            AND MRP控制者 != ''
            AND (完成时间 IS NULL OR 完成时间 = '')
        ''')
        
        columns = [description[0] for description in c.description]
        result = [dict(zip(columns, row)) for row in c.fetchall()]
        
        # 更新完成时间
        if result:
            material_ids = [row['物料'] for row in result]
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            placeholders = ','.join(['?' for _ in material_ids])
            c.execute(f'''
                UPDATE materials 
                SET 完成时间 = ? 
                WHERE 物料 IN ({placeholders})
            ''', [current_time] + material_ids)
            
            conn.commit()
            
        conn.close()
        return result
        
    except Exception as e:
        print(f"Error exporting materials: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 

# 添加健康检查端点
@app.get("/health")
async def health_check():
    return {"status": "healthy"} 

# 修改计算字段更新的权限检查
@app.put("/materials/{material_id}/calculated-fields")
async def update_calculated_fields(
    material_id: str,
    calculated_fields: dict,
    user = Depends(authenticate_user)
):
    # 允许所有部门在计算时更新字段
    if user["department"] not in ["信息部", "运营管理部", "采购部", "QC检测室"]:
        raise HTTPException(status_code=403, detail="无权修改计算字段")
    
    try:
        conn = sqlite3.connect('materials.db')
        c = conn.cursor()
        
        # 构建更新语句
        update_fields = ', '.join([f"{k} = ?" for k in calculated_fields.keys()])
        query = f'UPDATE materials SET {update_fields} WHERE 物料 = ?'
        
        # 执行更新
        c.execute(query, list(calculated_fields.values()) + [material_id])
        
        if c.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=404, detail="物料不存在")
        
        conn.commit()
        conn.close()
        return {"message": "更新成功"}
        
    except Exception as e:
        print(f"Error updating calculated fields: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 