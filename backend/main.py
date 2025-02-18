from fastapi import FastAPI, HTTPException, Depends, Request
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
import socket
import toml
import os.path

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
    物料描述: str | None = None
    物料组: str | None = None
    市场: str | None = None
    基本计量单位: str | None = None  # 添加基本计量单位字段
    备注1: str | None = None
    备注2: str | None = None
    生产厂商: str | None = None
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

# 添加完成请求模型
class CompleteRequest(BaseModel):
    api_key: str
    material_ids: List[str]

# 修改系统设置模型
class SystemSettings(BaseModel):
    dingTalkUrl: str
    keywords: List[str]

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
        # 创建用户表，添加设置相关字段
        c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username VARCHAR(50) PRIMARY KEY,
            password VARCHAR(100),
            department VARCHAR(50),
            email VARCHAR(100),
            need_change_password BOOLEAN DEFAULT TRUE,
            show_completed BOOLEAN DEFAULT FALSE,
            page_size INT DEFAULT 15
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci
        ''')
        
        # 创建物料表，添加基本计量单位字段
        c.execute('''
        CREATE TABLE IF NOT EXISTS materials (
            id INT AUTO_INCREMENT PRIMARY KEY,
            物料 VARCHAR(50),
            物料描述 TEXT,
            物料组 VARCHAR(50),
            市场 VARCHAR(50),
            基本计量单位 VARCHAR(10),  # 添加基本计量单位字段
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
        
        # 创建操作日志表
        c.execute('''
        CREATE TABLE IF NOT EXISTS operation_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50),
            department VARCHAR(50),
            ip_address VARCHAR(50),
            hostname VARCHAR(100),
            operation_time DATETIME,
            material_id VARCHAR(50),
            field_name VARCHAR(50),
            old_value TEXT,
            new_value TEXT,
            operation_type VARCHAR(20)
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci
        ''')
        
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
async def login(user_data: User):
    conn = get_db_connection()
    c = conn.cursor()
    
    try:
        c.execute(
            'SELECT username, department, need_change_password, show_completed, page_size FROM users WHERE username = %s AND password = %s',
            (user_data.username, user_data.password)
        )
        result = c.fetchone()
        
        if result:
            username, department, need_change_password, show_completed, page_size = result
            token = jwt.encode(
                {
                    "username": username, 
                    "department": department,
                    "need_change_password": need_change_password,
                    "show_completed": show_completed,
                    "page_size": page_size
                },
                SECRET_KEY,
                algorithm="HS256"
            )
            
            return {
                "token": token,
                "department": department,
                "need_change_password": need_change_password,
                "settings": {
                    "show_completed": show_completed,
                    "page_size": page_size
                }
            }
            
        raise HTTPException(status_code=401, detail="用户名或密码错误")
        
    finally:
        conn.close()

# 保存物料数据
@app.post("/materials")
async def save_materials(materials: List[Material], user = Depends(authenticate_user)):
    if user["department"] != "信息部":
        raise HTTPException(status_code=403, detail="无权导入数据")
    
    conn = get_db_connection()
    c = conn.cursor()
    
    skipped_materials = []  # 记录被跳过的物料号
    success_count = 0  # 记录成功导入的数量
    
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
                # 记录被跳过的物料号
                skipped_materials.append(material.物料)
                continue  # 跳过已存在的物料
            
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
            success_count += 1
        
        conn.commit()
        
        # 添加导入成功通知
        try:
            from push import notify_material_import
            notify_material_import(
                success_count=success_count,  # 成功导入的数量
                user_info={
                    'username': user['username'],
                    'department': user['department']
                }
            )
        except Exception as e:
            logger.error(f"发送导入通知失败: {str(e)}")
            
        # 返回导入结果
        return {
            "message": f"成功导入 {success_count} 条数据",
            "skipped": skipped_materials,  # 返回被跳过的物料号列表
            "success_count": success_count
        }
        
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
    page_size: int = 15,
    show_completed: bool = False,
    物料: str = None,
    物料描述: str = None,
    物料组: str = None
):
    conn = get_db_connection()
    c = conn.cursor()
    
    try:
        where_conditions = []
        where_params = []
        
        # 添加搜索条件
        if 物料:
            where_conditions.append("物料 LIKE %s")
            where_params.append(f"%{物料}%")
        
        if 物料描述:
            where_conditions.append("物料描述 LIKE %s")
            where_params.append(f"%{物料描述}%")
            
        if 物料组:
            where_conditions.append("物料组 LIKE %s")
            where_params.append(f"%{物料组}%")
        
        # 采购部不显示物料编号首位为4和5的记录
        if user["department"] == "采购部":
            where_conditions.append("物料 NOT LIKE '4%' AND 物料 NOT LIKE '5%'")
        
        # 只有在勾选时才显示已完成物料
        if not show_completed:
            where_conditions.append("(完成时间 IS NULL OR 完成时间 = '')")
        
        # 构建完整的 WHERE 子句
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        # 获取总记录数
        count_query = f'SELECT COUNT(*) FROM materials WHERE {where_clause}'
        c.execute(count_query, where_params)
        total = c.fetchone()[0]
        
        # 计算偏移量
        offset = (page - 1) * page_size
        
        # 根据部门筛选可见字段
        if user["department"] == "信息部":
            fields = "*"
        elif user["department"] == "财务部":
            fields = '''
                id, 物料, 物料描述, 物料组, 市场, 备注1, 备注2, 生产厂商, 基本计量单位,
                评估分类, 销售订单库存, 价格确定, 价格控制, 标准价格, 价格单位,
                用QS的成本核算, 物料来源, 差异码, 物料状态, 成本核算批量,
                新建时间, 完成时间
            '''
        else:
            fields = '''
                id, 物料, 物料描述, 物料组, 市场, 备注1, 备注2, 生产厂商, 基本计量单位,
                检测时间QC, 最小批量大小PUR, 舍入值PUR, 计划交货时间PUR,
                MRP控制者, MRP类型, 批量程序, 固定批量, 再订货点,
                安全库存, 批量大小, 舍入值, 采购类型, 收货处理时间,
                计划交货时间, MRP区域, 反冲, 批量输入, 自制生产时间,
                策略组, 综合MRP, 消耗模式, 向后跨期期间, 向后跨期时间,
                独立集中, 计划时间界, 生产评估, 生产计划, 新建时间, 完成时间
            '''
        
        # 构建完整的 SQL 查询，包含 WHERE 子句和排序
        query = f'''
            SELECT {fields} 
            FROM materials 
            WHERE {where_clause}
            ORDER BY 新建时间 DESC 
            LIMIT %s OFFSET %s
        '''
        
        # 合并所有参数
        all_params = where_params + [int(page_size), int(offset)]
        c.execute(query, all_params)
        
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
    request: Request,  # 添加 request 参数用于获取客户端信息
    material_id: str,
    update_data: UpdateMaterial,
    user = Depends(authenticate_user)
):
    # 检查权限
    allowed_fields = {
        '运营管理部': ['MRP控制者', '最小批量大小PUR', '舍入值PUR', '计划交货时间PUR', '检测时间QC'],  # 运营管理部可以修改采购部字段
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
        
        # 获取旧值
        c.execute(f'SELECT {update_data.field} FROM materials WHERE 物料 = %s', (material_id,))
        result = c.fetchone()
        old_value = result[0] if result else None
        
        # 更新字段
        c.execute(f'UPDATE materials SET {update_data.field} = %s WHERE 物料 = %s', 
                 (update_data.value, material_id))
        
        if c.rowcount == 0:
            raise HTTPException(status_code=404, detail="物料不存在")
        
        conn.commit()
        
        # 记录操作日志，各个值的来源如下：
        await log_operation(
            request=request,  # 用于获取客户端IP和主机名
            user=user,        # 从 JWT token 中获取用户名和部门
            material_id=material_id,  # 从URL参数获取
            field_name=update_data.field,  # 从请求体获取修改的字段名
            old_value=str(old_value),  # 从数据库查询获取的原值
            new_value=update_data.value,  # 从请求体获取的新值
            operation_type="UPDATE"  # 固定值表示更新操作
        )
        
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
    
    # 如果物料编号首位为4或5，设置相关字段为NA
    if first_char in ['4', '5']:
        material.最小批量大小PUR = "NA"
        material.舍入值PUR = "NA"
        material.计划交货时间PUR = "NA"
    
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
    
    # 修改成本核算批量逻辑
    if first_char in ['2', '5']:  # 移除了 '1'
        material.成本核算批量 = "10000"
    else:
        material.成本核算批量 = "1"
    
    # 评估类和销售订单库存逻辑
    has_processing = "进料加工" in (material.物料描述 or "")
    
    # 初始化销售订单库存为 NA
    material.销售订单库存 = "NA"
    
    if first_char == '1':
        if material.物料组[:2] == '11':
            material.评估分类 = "3010" if has_processing else "3000"
        elif material.物料组[:2] == '12':
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
    
    try:
        c.execute('''
            SELECT show_completed, page_size 
            FROM users 
            WHERE username = %s
        ''', (user["username"],))
        
        result = c.fetchone()
        if result:
            show_completed, page_size = result
            return {
                "show_completed": bool(show_completed),  # 确保返回布尔值
                "page_size": int(page_size)  # 确保返回整数
            }
        
        return {
            "show_completed": False,
            "page_size": 15
        }
        
    except Exception as e:
        logger.error(f"Error getting user settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        conn.close()

# 更新用户设置
@app.post("/user/settings")
async def save_settings(
    settings: dict,
    user = Depends(authenticate_user)
):
    conn = get_db_connection()
    c = conn.cursor()
    
    try:
        c.execute('''
            UPDATE users 
            SET show_completed = %s,
                page_size = %s
            WHERE username = %s
        ''', (
            settings["show_completed"],
            settings["page_size"],
            user["username"]
        ))
        
        conn.commit()
        return {"message": "设置保存成功"}
        
    except Exception as e:
        logger.error(f"Error saving settings: {str(e)}")
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        conn.close()

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

# 修改 API 导出接口
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
                基本计量单位,
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
        result = []
        
        # 改为一次性返回所有数据
        while True:
            row = c.fetchone()
            if row is None:
                break
                
            material_data = dict(zip(columns, row))
            result.append(material_data)
        
        conn.close()
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "data": result
        }
        
    except Exception as e:
        print(f"Error in API export: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 添加更新完成时间的接口
@app.post("/api/materials/complete")
async def api_complete_materials(request: CompleteRequest):
    # 验证API密钥
    verify_api_key(APIAuth(api_key=request.api_key))
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 更新完成时间
        placeholders = ','.join(['%s' for _ in request.material_ids])
        c.execute(f'''
            UPDATE materials 
            SET 完成时间 = %s 
            WHERE 物料 IN ({placeholders})
        ''', [current_time] + request.material_ids)
        
        conn.commit()
        conn.close()
        
        # 添加完成通知
        try:
            from push import notify_material_complete
            notify_material_complete(
                completed_count=len(request.material_ids),  # 完成的数量
                user_info={
                    'username': request.api_key,
                    'department': '信息部'
                }
            )
        except Exception as e:
            logger.error(f"发送完成通知失败: {str(e)}")
        

        return {
            "status": "success",
            "message": f"已更新 {len(request.material_ids)} 条记录的完成时间",
            "timestamp": current_time
        }
        
    except Exception as e:
        print(f"Error updating completion time: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 记录操作日志的函数
async def log_operation(
    request: Request,
    user: dict,
    material_id: str,
    field_name: str,
    old_value: str,
    new_value: str,
    operation_type: str
):
    conn = get_db_connection()
    c = conn.cursor()
    
    try:
        # 获取客户端IP
        client_ip = request.client.host
        
        # 尝试获取客户端主机名
        try:
            hostname = socket.gethostbyaddr(client_ip)[0]
        except:
            hostname = 'unknown'
        
        # 记录操作日志
        c.execute('''
            INSERT INTO operation_logs (
                username, department, ip_address, hostname,
                operation_time, material_id, field_name,
                old_value, new_value, operation_type
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            user["username"],
            user["department"],
            client_ip,
            hostname,
            datetime.now(),
            material_id,
            field_name,
            old_value,
            new_value,
            operation_type
        ))
        
        conn.commit()
        
    except Exception as e:
        logger.error(f"Error logging operation: {str(e)}")
        conn.rollback()
        
    finally:
        conn.close()

@app.put("/user/password")
async def update_password(
    password_data: dict,
    user = Depends(authenticate_user)
):
    conn = get_db_connection()
    c = conn.cursor()
    
    try:
        # 更新用户密码
        c.execute('''
            UPDATE users 
            SET password = %s,
                need_change_password = FALSE
            WHERE username = %s
        ''', (password_data["newPassword"], user["username"]))
        
        conn.commit()
        return {"message": "密码修改成功"}
        
    except Exception as e:
        logger.error(f"Error updating password: {str(e)}")
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        conn.close()

# 获取系统设置
@app.get("/system/settings")
async def get_system_settings(user = Depends(authenticate_user)):
    if user["department"] != "信息部":
        raise HTTPException(status_code=403, detail="无权访问系统设置")
    
    try:
        config = toml.load('init.toml')
        return {
            "dingTalkUrl": config['push']['dingding']['url'],
            "keywords": config['push']['dingding'].get('keywords', ['SAP'])
        }
    except Exception as e:
        logger.error(f"读取系统设置失败: {str(e)}")
        raise HTTPException(status_code=500, detail="读取系统设置失败")

# 保存系统设置
@app.post("/system/settings")
async def save_system_settings(
    settings: SystemSettings,
    user = Depends(authenticate_user)
):
    if user["department"] != "信息部":
        raise HTTPException(status_code=403, detail="无权修改系统设置")
    
    try:
        config = {}
        try:
            config = toml.load('init.toml')
        except:
            pass
        
        # 确保配置结构存在
        if 'push' not in config:
            config['push'] = {}
        if 'dingding' not in config['push']:
            config['push']['dingding'] = {}
        
        # 更新钉钉机器人 URL
        config['push']['dingding']['url'] = settings.dingTalkUrl
        config['push']['dingding']['keywords'] = settings.keywords
        
        # 保存配置
        with open('init.toml', 'w', encoding='utf-8') as f:
            toml.dump(config, f)
        
        return {"message": "系统设置保存成功"}
        
    except Exception as e:
        logger.error(f"保存系统设置失败: {str(e)}")
        raise HTTPException(status_code=500, detail="保存系统设置失败")

# 添加获取物料状态统计接口
@app.get("/materials/status")
async def get_materials_status(user = Depends(authenticate_user)):
    if user["department"] != "信息部":
        raise HTTPException(status_code=403, detail="无权访问")
        
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 查询未完成的物料总数
        c.execute('''
            SELECT COUNT(*) 
            FROM materials 
            WHERE 完成时间 IS NULL OR 完成时间 = ''
        ''')
        total_incomplete = c.fetchone()[0]
        
        # 查询财务部未完成的物料数量
        c.execute('''
            SELECT COUNT(*) 
            FROM materials 
            WHERE (完成时间 IS NULL OR 完成时间 = '')
            AND (
                标准价格 IS NULL OR 标准价格 = '' 
            )
        ''')
        finance_incomplete = c.fetchone()[0]
        
        # 查询运营部未完成的物料数量
        c.execute('''
            SELECT COUNT(*) 
            FROM materials 
            WHERE (完成时间 IS NULL OR 完成时间 = '')
            AND (
                MRP控制者 IS NULL OR MRP控制者 = '' OR
                最小批量大小PUR IS NULL OR 最小批量大小PUR = '' OR
                舍入值PUR IS NULL OR 舍入值PUR = '' OR
                计划交货时间PUR IS NULL OR 计划交货时间PUR = '' OR
                检测时间QC IS NULL OR 检测时间QC = ''
            )
        ''')
        operation_incomplete = c.fetchone()[0]
        
        return {
            "count": total_incomplete,
            "finance_incomplete": finance_incomplete,
            "operation_incomplete": operation_incomplete
        }
        
    except Exception as e:
        logger.error(f"获取物料状态统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取物料状态统计失败")
        
    finally:
        conn.close()

# 添加发送状态通知接口
@app.post("/notify/status")
async def send_status_notification(
    status_info: dict,
    user = Depends(authenticate_user)
):
    if user["department"] != "信息部":
        raise HTTPException(status_code=403, detail="无权发送通知")
        
    try:
        from push import notify_material_status
        success = notify_material_status(status_info)
        
        if success:
            return {"message": "通知发送成功"}
        else:
            raise HTTPException(status_code=500, detail="通知发送失败")
            
    except Exception as e:
        logger.error(f"发送状态通知失败: {str(e)}")
        raise HTTPException(status_code=500, detail="发送状态通知失败")

# 添加初始化配置文件函数
def init_config():
    """
    初始化配置文件
    如果配置文件不存在，创建默认配置
    """
    config_file = 'init.toml'
    
    # 检查配置文件是否存在
    if not os.path.exists(config_file):
        logger.info("配置文件不存在，创建默认配置")
        
        # 默认配置
        default_config = {
            'push': {
                'dingding': {
                    'url': '',  # 默认为空，需要通过系统设置配置
                    'keywords': ['SAP']  # 默认关键词
                }
            }
        }
        
        try:
            # 创建配置文件
            with open(config_file, 'w', encoding='utf-8') as f:
                toml.dump(default_config, f)
            logger.info("默认配置文件创建成功")
        except Exception as e:
            logger.error(f"创建配置文件失败: {str(e)}")
            raise Exception("无法创建配置文件")
    else:
        # 验证配置文件结构
        try:
            config = toml.load(config_file)
            # 确保必要的配置项存在
            if 'push' not in config:
                config['push'] = {}
            if 'dingding' not in config['push']:
                config['push']['dingding'] = {}
            if 'url' not in config['push']['dingding']:
                config['push']['dingding']['url'] = ''
            if 'keywords' not in config['push']['dingding']:
                config['push']['dingding']['keywords'] = ['SAP']
                
            # 保存更新后的配置
            with open(config_file, 'w', encoding='utf-8') as f:
                toml.dump(config, f)
                
            logger.info("配置文件验证完成")
        except Exception as e:
            logger.error(f"验证配置文件失败: {str(e)}")
            raise Exception("配置文件格式错误")

# 在应用启动时初始化配置
@app.on_event("startup")
async def startup_event():
    """
    应用启动时的初始化操作
    """
    try:
        # 初始化配置文件
        init_config()
        logger.info("应用启动初始化完成")
    except Exception as e:
        logger.error(f"应用启动初始化失败: {str(e)}")
        raise e



@app.post("/api/materials/update")
async def update_material_from_spider(
    material_data: dict,
    user = Depends(authenticate_user)
):
    """
    接收并更新物料详细信息
    """
    try:
        material_id = material_data.get('material_id')
        details = material_data.get('details', {})
        
        if not material_id or not details:
            raise HTTPException(status_code=400, detail="缺少必要的数据")
        
        # 获取数据库连接
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # 检查物料是否存在
            cursor.execute(
                'SELECT 物料 FROM materials WHERE 物料 = %s',
                (details.get('物料', ''),)
            )
            exists = cursor.fetchone()
            
            if not exists:
                # 构建插入数据
                insert_data = {
                    '物料': details.get('物料', ''),
                    '物料描述': details.get('物料描述', ''),
                    '物料组': details.get('物料组', ''),
                    '市场': details.get('市场', ''),
                    '基本计量单位': details.get('基本计量单位', ''),
                    '备注1': details.get('备注1', ''),
                    '备注2': details.get('备注2', ''),
                    '新建时间': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    '完成时间': None
                }
                
                # 构建 SQL 语句
                fields = ', '.join(insert_data.keys())
                placeholders = ', '.join(['%s'] * len(insert_data))
                sql = f'INSERT INTO materials ({fields}) VALUES ({placeholders})'
                
                # 执行插入
                cursor.execute(sql, list(insert_data.values()))
                conn.commit()
                
                logger.info(f"新增物料: {details.get('物料', '')}")
                return {"message": "物料信息已添加", "action": "insert"}
            else:
                logger.info(f"物料已存在: {details.get('物料', '')}")
                return {"message": "物料已存在", "action": "skip"}
                
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        logger.error(f"处理物料信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")
        