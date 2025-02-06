from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
import jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
import os
import mysql.connector
from mysql.connector import Error
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()

load_dotenv()

# JWT配置
SECRET_KEY = os.getenv("SECRET_KEY")
security = HTTPBearer()

# 从环境变量获取 CORS 配置
CORS_ORIGINS = eval(os.getenv("CORS_ORIGINS", '["*"]'))  # 允许所有源，仅用于测试

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
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
    物料组: Optional[str] = None
    市场: Optional[str] = None
    备注1: Optional[str] = None
    备注2: Optional[str] = None
    生产厂商: Optional[str] = None
    评估分类: Optional[str] = None
    销售订单库存: Optional[str] = None
    价格确定: Optional[str] = None
    价格控制: Optional[str] = None
    标准价格: Optional[str] = None
    价格单位: Optional[str] = None
    用QS的成本核算: Optional[str] = None
    物料来源: Optional[str] = None
    差异码: Optional[str] = None
    物料状态: Optional[str] = None
    成本核算批量: Optional[str] = None
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

# 添加用户设置相关的模型
class UserSettings(BaseModel):
    newPassword: Optional[str] = None
    email: Optional[str] = None

# 添加用户模型
class NewUser(BaseModel):
    username: str
    department: str
    email: Optional[str] = None

# 添加API认证密钥模型
class APIAuth(BaseModel):
    api_key: str

# 数据库连接函数
def get_db_connection():
    try:
        # 根据环境选择不同的数据库
        db_name = 'Sap_test' if os.getenv('ENV') != 'production' else 'Sap'
        
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', '192.168.3.5'),
            port=int(os.getenv('DB_PORT', '3306')),
            database=db_name,
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', '19931225Yfl'),
            charset='utf8mb4',
            collation='utf8mb4_general_ci'
        )
        logger.info(f"Connected to database: {db_name}")
        return connection
    except Error as e:
        logger.error(f"Database connection error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database connection error")

# 修改数据库初始化函数
def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    try:
        # 创建用户表
        c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username VARCHAR(50) PRIMARY KEY,
            password VARCHAR(100),
            department VARCHAR(50),
            email VARCHAR(100),
            need_change_password BOOLEAN DEFAULT TRUE
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci
        ''')
        
        # 创建物料表
        c.execute('''
        CREATE TABLE IF NOT EXISTS materials (
            id INT AUTO_INCREMENT PRIMARY KEY,
            物料 VARCHAR(50),
            物料描述 TEXT,
            物料组 VARCHAR(50),
            市场 VARCHAR(50),
            备注1 TEXT,
            备注2 TEXT,
            生产厂商 TEXT,
            评估分类 VARCHAR(20),
            销售订单库存 VARCHAR(20),
            价格确定 VARCHAR(10),
            价格控制 VARCHAR(10),
            标准价格 VARCHAR(20),
            价格单位 VARCHAR(10),
            用QS的成本核算 VARCHAR(10),
            物料来源 VARCHAR(10),
            差异码 VARCHAR(20),
            物料状态 VARCHAR(10),
            成本核算批量 VARCHAR(20),
            检测时间QC VARCHAR(20),
            最小批量大小PUR VARCHAR(20),
            舍入值PUR VARCHAR(20),
            计划交货时间PUR VARCHAR(20),
            MRP控制者 VARCHAR(10),
            MRP类型 VARCHAR(10),
            批量程序 VARCHAR(20),
            固定批量 VARCHAR(20),
            再订货点 VARCHAR(20),
            安全库存 VARCHAR(20),
            批量大小 VARCHAR(20),
            舍入值 VARCHAR(20),
            采购类型 VARCHAR(20),
            收货处理时间 VARCHAR(20),
            计划交货时间 VARCHAR(20),
            MRP区域 VARCHAR(10),
            反冲 VARCHAR(10),
            批量输入 VARCHAR(20),
            自制生产时间 VARCHAR(20),
            策略组 VARCHAR(20),
            综合MRP VARCHAR(10),
            消耗模式 VARCHAR(20),
            向后跨期期间 VARCHAR(20),
            向后跨期时间 VARCHAR(20),
            独立集中 VARCHAR(20),
            计划时间界 VARCHAR(20),
            生产评估 VARCHAR(20),
            生产计划 VARCHAR(20),
            新建时间 VARCHAR(30),
            完成时间 VARCHAR(30)
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci
        ''')
        
        # 检查是否已存在默认用户
        c.execute('SELECT username FROM users WHERE username=%s', ('admin',))
        if not c.fetchone():
            # 添加默认管理员用户
            c.execute('''
                INSERT INTO users (username, password, department, need_change_password)
                VALUES (%s, %s, %s, %s)
            ''', ('admin', 'admin', '信息部', True))
        
        conn.commit()
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")
        conn.rollback()
        raise
    
    finally:
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
    conn = get_db_connection()
    c = conn.cursor()
    

    # MariaDB 使用 %s 作为参数占位符
    c.execute('''
        SELECT department, need_change_password 
        FROM users 
        WHERE username=%s AND password=%s
    ''', (user.username, user.password))
    
    result = c.fetchone()
    conn.close()
    
    if result:
        token = jwt.encode(
            {
                "username": user.username, 
                "department": result[0],
                "need_change_password": bool(result[1])
            },
            SECRET_KEY,
            algorithm="HS256"
        )
        return {
            "token": token, 
            "department": result[0],
            "need_change_password": bool(result[1])
        }
    raise HTTPException(status_code=401, detail="Invalid credentials")

# 保存物料数据
@app.post("/materials")
async def save_materials(materials: List[Material], user = Depends(authenticate_user)):
    if user["department"] != "信息部":
        raise HTTPException(status_code=403, detail="无权导入数据")
    
    conn = get_db_connection()
    c = conn.cursor()
    
    try:
        # MariaDB 版本
        for material in materials:
            # 添加新建时间和计算字段
            material.新建时间 = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            calculate_fields(material)  # 计算自动填充字段
            
            # 检查物料是否已存在
            c.execute('SELECT 物料 FROM materials WHERE 物料=%s', (material.物料,))
            existing = c.fetchone()
            
            if existing:
                # 更新现有记录
                update_fields = []
                update_values = []
                
                for field, value in material.dict().items():
                    if field != '物料' and value is not None:  # 跳过主键和空值
                        update_fields.append(f"{field}=%s")
                        update_values.append(value)
                
                if update_fields:
                    update_values.append(material.物料)  # 添加 WHERE 条件的值
                    query = f'''
                        UPDATE materials 
                        SET {', '.join(update_fields)}
                        WHERE 物料=%s
                    '''
                    c.execute(query, update_values)
            else:
                # 插入新记录
                fields = []
                values = []
                placeholders = []
                
                for field, value in material.dict().items():
                    if value is not None:  # 跳过空值
                        fields.append(field)
                        values.append(value)
                        placeholders.append('%s')
                
                query = f'''
                    INSERT INTO materials 
                    ({', '.join(fields)})
                    VALUES ({', '.join(placeholders)})
                '''
                c.execute(query, values)
        
        conn.commit()
        return {"message": "数据保存成功"}
        
    except Exception as e:
        print(f"Error saving materials: {str(e)}")
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        conn.close()

# 获取物料数据
@app.get("/materials")
async def get_materials(
    user = Depends(authenticate_user),
    page: int = 1,
    page_size: int = 15
):
    conn = get_db_connection()
    c = conn.cursor()
    
    try:
        # 获取总记录数
        c.execute('SELECT COUNT(*) FROM materials')
        total = c.fetchone()[0]
        
        # 计算偏移量
        offset = (page - 1) * page_size
        
        # 根据部门筛选可见字段
        if user["department"] == "信息部":
            # 信息部可以看到所有字段
            fields = "*"
        elif user["department"] == "财务部":
            # 财务部能看到基础字段、财务相关字段、以及时间字段
            fields = '''
                id, 物料, 物料描述, 物料组, 市场, 备注1, 备注2, 生产厂商,
                评估分类, 销售订单库存, 价格确定, 价格控制, 标准价格, 价格单位,
                用QS的成本核算, 物料来源, 差异码, 物料状态, 成本核算批量,
                新建时间, 完成时间
            '''
        else:
            # 其他部门看不到财务相关字段
            fields = '''
                id, 物料, 物料描述, 物料组, 市场, 备注1, 备注2, 生产厂商,
                检测时间QC, 最小批量大小PUR, 舍入值PUR, 计划交货时间PUR,
                MRP控制者, MRP类型, 批量程序, 固定批量, 再订货点,
                安全库存, 批量大小, 舍入值, 采购类型, 收货处理时间,
                计划交货时间, MRP区域, 反冲, 批量输入, 自制生产时间,
                策略组, 综合MRP, 消耗模式, 向后跨期期间, 向后跨期时间,
                独立集中, 计划时间界, 生产评估, 生产计划, 新建时间, 完成时间
            '''
        
        # 构建完整的 SQL 查询
        query = f'SELECT {fields} FROM materials LIMIT %s OFFSET %s'
        c.execute(query, (int(page_size), int(offset)))
        
        columns = [description[0] for description in c.description]
        result = [dict(zip(columns, row)) for row in c.fetchall()]
        
        return {
            "total": total,
            "items": result,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
        
    except Exception as e:
        logger.error(f"Error getting materials: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        conn.close()

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
        'QC检测室': ['检测时间QC'],
        '财务部': ['评估分类', '销售订单库存', '价格确定', '价格控制', '标准价格', 
                '价格单位', '用QS的成本核算', '物料来源', '差异码', '物料状态', '成本核算批量']
    }
    
    if user["department"] not in allowed_fields or update_data.field not in allowed_fields[user["department"]]:
        raise HTTPException(status_code=403, detail="无权修改该字段")
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 更新字段
        c.execute(f'UPDATE materials SET {update_data.field} = %s WHERE 物料 = %s', 
                 (update_data.value, material_id))
        
        if c.rowcount == 0:
            raise HTTPException(status_code=404, detail="物料不存在")
        
        conn.commit()
        return {"message": "更新成功"}
        
    except Exception as e:
        logger.error(f"Error updating material: {str(e)}")
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        conn.close()

# 获取待导出的数据
@app.get("/materials/export")
async def get_export_materials(user = Depends(authenticate_user)):
    if user["department"] != "信息部":
        raise HTTPException(status_code=403, detail="无权导出数据")
        
    try:
        conn = get_db_connection()
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
            AND 标准价格 IS NOT NULL
            AND 标准价格 != ''
            AND (完成时间 IS NULL OR 完成时间 = '')
        ''')
        
        columns = [description[0] for description in c.description]
        result = [dict(zip(columns, row)) for row in c.fetchall()]
        
        # 更新完成时间
        if result:
            material_ids = [row['物料'] for row in result]
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 修改这里，使用 MariaDB 语法
            placeholders = ','.join(['%s' for _ in material_ids])
            c.execute(f'''
                UPDATE materials 
                SET 完成时间 = %s 
                WHERE 物料 IN ({placeholders})
            ''', [current_time] + material_ids)
            
            conn.commit()
            
        return result
        
    except Exception as e:
        logger.error(f"Error exporting materials: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        conn.close()

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
        conn = get_db_connection()
        c = conn.cursor()
        
        # 构建更新语句
        update_fields = ', '.join([f"{k} = %s" for k in calculated_fields.keys()])
        query = f'UPDATE materials SET {update_fields} WHERE 物料 = %s'
        
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

def calculate_fields(material: Material):
    # 获取物料号第一个数字
    first_char = material.物料[0] if material.物料 else ''
    material_group = material.物料组[:2] if material.物料组 else ''
    
    # 设置默认值
    material.价格确定 = "3"
    material.价格控制 = "S"
    material.价格单位 = "1"
    material.用QS的成本核算 = "X"
    material.物料来源 = "X"
    
    # 差异码逻辑
    if first_char in ['4', '5']:
        material.差异码 = "000001"
    else:
        material.差异码 = "NA"
    
    # 物料状态逻辑
    if first_char in ['4', '5']:
        material.物料状态 = "Z1"
    else:
        material.物料状态 = "NA"
    
    # 成本核算批量逻辑
    if first_char in ['1', '2', '5']:
        material.成本核算批量 = "10000"
    else:
        material.成本核算批量 = "NA"
    
    # 评估类和销售订单库存逻辑
    has_processing = "进料加工" in (material.物料描述 or "")
    
    # 初始化销售订单库存为 NA
    material.销售订单库存 = "NA"
    
    if first_char == '1':
        if material_group == '11':
            material.评估分类 = "3010" if has_processing else "3000"
        elif material_group == '12':
            material.评估分类 = "3100"
    elif first_char == '2':
        material.评估分类 = "3200"
    elif first_char == '4':
        material.评估分类 = "7910" if has_processing else "7900"
    elif first_char == '5':
        if has_processing:
            material.评估分类 = "7940"
            material.销售订单库存 = "7940"
        else:
            material.评估分类 = "7930"
            material.销售订单库存 = "7930"
    
    return material  # 确保返回修改后的对象

# 获取用户设置
@app.get("/user/settings")
async def get_user_settings(user = Depends(authenticate_user)):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT email FROM users WHERE username = %s', (user["username"],))
    result = c.fetchone()
    conn.close()
    return {"email": result[0] if result else None}


# 更新用户设置
@app.put("/user/settings")
async def update_user_settings(settings: UserSettings, user = Depends(authenticate_user)):
    conn = get_db_connection()
    c = conn.cursor()
    
    updates = []
    values = []
    
    if settings.newPassword:
        updates.append("password = %s")
        values.append(settings.newPassword)
        updates.append("need_change_password = %s")
        values.append(False)

    
    if settings.email is not None:
        updates.append("email = %s")
        values.append(settings.email)
    

    if updates:
        query = f"UPDATE users SET {', '.join(updates)} WHERE username = %s"
        values.append(user["username"])
        c.execute(query, values)
        conn.commit()

    
    conn.close()
    return {"message": "设置更新成功"}

# 获取用户列表（仅信息部可用）
@app.get("/users")
async def get_users(user = Depends(authenticate_user)):
    if user["department"] != "信息部":
        raise HTTPException(status_code=403, detail="无权访问")
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT username, department FROM users')
    users = [{"username": row[0], "department": row[1]} for row in c.fetchall()]
    conn.close()
    return users

# 重置用户密码（仅信息部可用）
@app.post("/users/{username}/reset-password")
async def reset_user_password(username: str, user = Depends(authenticate_user)):
    if user["department"] != "信息部":
        raise HTTPException(status_code=403, detail="无权操作")
    
    conn = get_db_connection()
    c = conn.cursor()
    
    # 重置密码并设置需要修改密码标志
    c.execute('''
        UPDATE users 
        SET password = %s, need_change_password = %s 
        WHERE username = %s
    ''', ("password", True, username))

    
    if c.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="用户不存在")
    
    conn.commit()
    conn.close()
    return {"message": "密码重置成功"}

# 添加创建用户接口
@app.post("/users")
async def create_user(new_user: NewUser, user = Depends(authenticate_user)):
    if user["department"] != "信息部":
        raise HTTPException(status_code=403, detail="无权操作")
    
    conn = get_db_connection()
    c = conn.cursor()
    
    try:
        # 检查用户名是否已存在
        c.execute('SELECT username FROM users WHERE username=%s', (new_user.username,))
        if c.fetchone():
            raise HTTPException(status_code=409, detail="用户名已存在")
        
        # 创建新用户，设置默认密码为 "password"
        c.execute('''
            INSERT INTO users (username, password, department, email, need_change_password)
            VALUES (%s, %s, %s, %s, %s)
        ''', (
            new_user.username,
            "password",  # 默认密码
            new_user.department,
            new_user.email,
            True  # 需要修改密码
        ))
        
        conn.commit()
        return {"message": "用户创建成功"}
        
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        conn.close()

# 添加API认证中间件
def verify_api_key(api_auth: APIAuth):
    # 从环境变量获取API密钥，如果没有设置则使用默认值
    valid_api_key = os.getenv('API_KEY', 'your-api-key-here')
    if api_auth.api_key != valid_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True

# 添加API接口，供其他程序调用
@app.post("/api/materials/export")
async def api_export_materials(api_auth: APIAuth):
    # 验证API密钥
    verify_api_key(api_auth)
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 获取所有需要的字段都已填写的数据
        c.execute('''
            SELECT 
                物料,
                物料描述,
                物料组,
                市场,
                备注1,
                备注2,
                生产厂商,
                评估分类,
                销售订单库存,
                价格确定,
                价格控制,
                标准价格,
                价格单位,
                用QS的成本核算,
                物料来源,
                差异码,
                物料状态,
                成本核算批量,
                检测时间QC,
                最小批量大小PUR,
                舍入值PUR,
                计划交货时间PUR,
                MRP控制者,
                MRP类型,
                批量程序,
                固定批量,
                再订货点,
                安全库存,
                批量大小,
                舍入值,
                采购类型,
                收货处理时间,
                计划交货时间,
                MRP区域,
                反冲,
                批量输入,
                自制生产时间,
                策略组,
                综合MRP,
                消耗模式,
                向后跨期期间,
                向后跨期时间,
                独立集中,
                计划时间界,
                生产评估,
                生产计划,
                新建时间,
                完成时间
            FROM materials 
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
            AND 标准价格 IS NOT NULL
            AND 标准价格 != ''
            AND (完成时间 IS NULL OR 完成时间 = '')
        ''')
        
        columns = [description[0] for description in c.description]
        result = [dict(zip(columns, row)) for row in c.fetchall()]
        
        # 更新完成时间
        if result:
            material_ids = [row['物料'] for row in result]
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            placeholders = ','.join(['%s' for _ in material_ids])
            c.execute(f'''
                UPDATE materials 
                SET 完成时间 = %s 
                WHERE 物料 IN ({placeholders})
            ''', [current_time] + material_ids)


            
            conn.commit()
        
        conn.close()
        
        # 返回JSON格式的响应
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "total_count": len(result),
            "data": result
        }
        
    except Exception as e:
        print(f"Error in API export: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))