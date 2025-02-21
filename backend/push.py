import requests
import toml
import os
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
import logging

# 设置日志记录
logger = logging.getLogger(__name__)

class DingTalkBot:
    def __init__(self):
        # 读取配置文件
        try:
            config = toml.load('init.toml')
            self.webhook_url = config['push']['dingding']['url']
            self.keywords = config['push']['dingding'].get('keywords', ['SAP'])  # 默认关键词
        except Exception as e:
            print(f"读取配置文件失败: {str(e)}")
            self.webhook_url = None
            self.keywords = ['SAP']

    def send_message(self, content, msg_type="text"):
        """
        发送消息到钉钉机器人
        
        Args:
            content: 消息内容
            msg_type: 消息类型，支持 text、markdown 等
        
        Returns:
            bool: 是否发送成功
        """
        if not self.webhook_url:
            print("未配置钉钉机器人 webhook URL")
            return False

        try:
            # 确保消息包含关键词
            has_keyword = any(keyword in content for keyword in self.keywords)
            if not has_keyword:
                # 在消息开头添加第一个关键词
                content = f"{self.keywords[0]}通知\n{content}"

            # 构建请求数据
            if msg_type == "text":
                data = {
                    "msgtype": "text",
                    "text": {
                        "content": content
                    }
                }
            elif msg_type == "markdown":
                # 从消息内容中提取第一行作为标题

                data = {
                    "msgtype": "markdown",
                    "markdown": {
                        "title": f"[{self.keywords[0]}] SAP数据更新通知",  # 组合关键词和标题
                        "text": content
                    }
                }
            else:
                print(f"不支持的消息类型: {msg_type}")
                return False

            # 发送请求
            response = requests.post(
                self.webhook_url,
                json=data,
                headers={'Content-Type': 'application/json'}
            )

            # 检查响应
            if response.status_code == 200:
                result = response.json()
                if result.get('errcode') == 0:
                    print(f"消息发送成功，类型: {msg_type}")
                    return True
                else:
                    print(f"发送失败: {result.get('errmsg')}")
                    return False
            else:
                print(f"请求失败: {response.status_code}")
                return False

        except Exception as e:
            print(f"发送消息时出错: {str(e)}")
            return False


async def notify_material_import(success_count, user_info):
    """
    发送物料导入通知（钉钉和邮件）
    """
    try:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message = f"""
### SAP物料数据导入通知
- **成功导入**: {success_count} 条
- **操作人**: {user_info.get('username')}
- **部门**: {user_info.get('department')}
- **时间**: {now}
        """
        
        # 发送钉钉通知
        bot = DingTalkBot()
        ding_result = bot.send_message(message, msg_type="markdown")
        
        # 获取邮件接收者并发送邮件
        from utils import get_email_recipients
        email_recipients = await get_email_recipients()
        
        email_result = send_email(
            subject="SAP物料数据导入通知",
            body=message,
            recipients=[{'email': r[1]} for r in email_recipients]
        )
        
        return ding_result or email_result
        
    except Exception as e:
        logger.error(f"发送导入通知失败: {str(e)}")
        return False

def notify_material_complete(completed_count, user_info):
    """
    发送物料完成通知
    
    Args:
        completed_count: int, 成功完成的物料数量
        user_info: dict, 包含用户信息
    """
    bot = DingTalkBot()
    
    # 构建 Markdown 格式的消息
    message = f"""
### SAP物料完成通知
- **成功完成**: {completed_count} 条
- **操作人**: {user_info.get('username')}
- **部门**: {user_info.get('department')}
- **时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """
    
    return bot.send_message(message, msg_type="markdown")

def notify_material_status(status_info):
    """发送状态通知（钉钉和邮件）"""
    success = True
    try:
        # 发送钉钉通知
        bot = DingTalkBot()
        message = f"""
### SAP物料数据统计
- **未完成物料总数**: {status_info['count']}
- **财务部待处理**: {status_info['finance_incomplete']}
- **运营部待处理**: {status_info['operation_incomplete']}
- **统计时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        ding_result = bot.send_message(message, msg_type="markdown")
        if not ding_result:
            logger.warning("钉钉通知发送失败")
            success = False
        
        # 发送邮件通知
        if 'email_recipients' in status_info and status_info['email_recipients']:
            try:
                send_email(
                    subject="SAP物料数据统计",
                    body=message,
                    recipients=[{'email': r['email']} for r in status_info['email_recipients']]
                )
                logger.info("邮件通知发送成功")
            except Exception as e:
                logger.error(f"邮件通知发送失败: {str(e)}")
                success = False
        
        return success
    except Exception as e:
        logger.error(f"发送通知失败: {str(e)}")
        return False

def send_email(subject, body, recipients, is_html=False):
    """发送邮件通知"""
    try:
        config = toml.load('init.toml')
        email_config = config.get('push', {}).get('email', {})
        
        if not email_config:
            logger.error("未找到邮件配置")
            return False
            
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = email_config.get('smtp_user')
        msg['To'] = ', '.join(r['email'] for r in recipients)
        
        msg.attach(MIMEText(body, 'html' if is_html else 'plain', 'utf-8'))
            
        with smtplib.SMTP(
            host=email_config.get('smtp_server'),
            port=email_config.get('smtp_port', 25)
        ) as server:
            if email_config.get('smtp_user') and email_config.get('smtp_password'):
                server.login(
                    email_config.get('smtp_user'),
                    email_config.get('smtp_password')
                )
            server.send_message(msg)
            
        return True
        
    except Exception as e:
        logger.error(f"发送邮件失败: {str(e)}")
        return False





