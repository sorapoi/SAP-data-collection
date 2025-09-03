import logging
from datetime import datetime

logger = logging.getLogger(__name__)

async def get_materials_status(user=None):
    """获取物料状态统计"""
    from main import get_db_connection  # 动态导入避免循环引用
    
    conn = get_db_connection()
    c = conn.cursor()
    
    try:
        # 获取未完成的物料总数
        c.execute('SELECT COUNT(*) FROM materials WHERE 完成时间 IS NULL')
        total_incomplete = c.fetchone()[0]
        
        # 获取制剂财务部待处理的数量（完成时间为空且标准价格为空且工厂为5000）
        c.execute('''
            SELECT COUNT(*) FROM materials 
            WHERE 完成时间 IS NULL 
            AND (标准价格 IS NULL OR 标准价格 = '')
            AND 工厂 = '5000'
        ''')
        finance_5000_incomplete = c.fetchone()[0]

        # 获取制药科技财务部待处理的数量（完成时间为空且标准价格为空且工厂为5300）
        c.execute('''
            SELECT COUNT(*) FROM materials 
            WHERE 完成时间 IS NULL 
            AND (标准价格 IS NULL OR 标准价格 = '')
            AND 工厂 = '5300'
        ''')
        finance_5300_incomplete = c.fetchone()[0]

        # 获取运营部待处理的数量（完成时间为空且相关字段为空）
        c.execute('''
            SELECT COUNT(*) FROM materials 
            WHERE 完成时间 IS NULL 
            AND (
                检测时间QC IS NULL OR 检测时间QC = '' OR
                最小批量大小PUR IS NULL OR 最小批量大小PUR = '' OR
                舍入值PUR IS NULL OR 舍入值PUR = '' OR
                计划交货时间PUR IS NULL OR 计划交货时间PUR = '' OR
                MRP控制者 IS NULL OR MRP控制者 = ''
            )
        ''')
        operation_incomplete = c.fetchone()[0]
        
        return {
            "count": total_incomplete,
            "finance_incomplete": finance_5000_incomplete + finance_5300_incomplete,
            "operation_incomplete": operation_incomplete,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "finance_5300_incomplete": finance_5300_incomplete,
            "finance_5000_incomplete": finance_5000_incomplete

        }
        
    except Exception as e:
        logger.error(f"获取物料状态统计失败: {str(e)}")
        raise
    finally:
        conn.close()

async def get_email_recipients():
    """获取需要接收邮件的用户列表"""
    from main import get_db_connection  # 动态导入避免循环引用
    
    conn = get_db_connection()
    c = conn.cursor()
    
    try:
        # 获取所有启用邮件推送且设置了邮箱的用户
        c.execute('''
            SELECT username, email, department 
            FROM users 
            WHERE email_push = TRUE 
            AND email IS NOT NULL 
            AND email != ''
        ''')
        return c.fetchall()
    finally:
        conn.close() 