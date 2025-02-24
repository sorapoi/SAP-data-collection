from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import toml
import logging
import requests
from push import notify_material_status
from utils import get_materials_status, get_email_recipients

logger = logging.getLogger(__name__)

_scheduler = None  # 全局变量存储调度器实例

def is_holiday():
    """检查今天是否是节假日"""
    try:
        # 使用第三方API检查是否为节假日
        today = datetime.now().strftime('%Y-%m-%d')
        response = requests.get(
            f'http://timor.tech/api/holiday/info/{today}',
            timeout=5,  # 添加超时设置
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        
        if response.status_code != 200:
            logger.error(f"节假日API返回错误: HTTP {response.status_code}")
            return False
            
        data = response.json()
        logger.info(f"节假日API响应: {data}")
        
        return data.get('type', {}).get('type') in [1, 2]  # 1=周末, 2=节假日
        
    except requests.exceptions.RequestException as e:
        logger.error(f"请求节假日API失败: {str(e)}")
        return False
    except ValueError as e:
        logger.error(f"解析节假日API响应失败: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"检查节假日时出错: {str(e)}")
        return False

async def send_daily_notification():
    """发送每日通知"""
    try:
        # 检查是否为节假日
        if is_holiday():
            logger.info("今天是节假日，跳过推送")
            return

        # 检查是否启用推送
        config = toml.load('init.toml')
        if not config.get('push', {}).get('schedule', {}).get('enabled', True):
            logger.info("自动推送已禁用")
            return

        # 获取物料状态统计
        status_info = await get_materials_status(None)
        
        # 获取邮件接收者列表
        email_recipients = await get_email_recipients()
        
        # 添加邮件接收者信息
        status_info['email_recipients'] = [
            {
                'username': recipient[0],
                'email': recipient[1],
                'department': recipient[2]
            }
            for recipient in email_recipients
        ]
        
        # 发送通知
        success = notify_material_status(status_info)
        
        if success:
            logger.info("自动推送成功")
        else:
            logger.error("自动推送失败")
            
    except Exception as e:
        logger.error(f"执行自动推送任务时出错: {str(e)}")

def init_scheduler():
    """初始化定时任务"""
    global _scheduler
    
    try:
        # 如果已经有调度器在运行，先停止它
        if _scheduler:
            _scheduler.shutdown()
            
        # 使用异步调度器
        _scheduler = AsyncIOScheduler()
        
        # 读取配置文件获取推送时间
        config = toml.load('init.toml')
        push_time = config.get('push', {}).get('schedule', {}).get('time', '09:00')
        hour, minute = map(int, push_time.split(':'))
        
        # 添加定时任务
        _scheduler.add_job(
            send_daily_notification,
            CronTrigger(hour=hour, minute=minute),
            id='daily_notification',
            replace_existing=True
        )
        
        # 启动调度器
        _scheduler.start()
        logger.info(f"定时推送任务已启动，推送时间: {push_time}")
        
    except Exception as e:
        logger.error(f"初始化定时任务失败: {str(e)}") 