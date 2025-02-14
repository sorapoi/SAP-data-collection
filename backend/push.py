import requests
import toml
import os
from datetime import datetime

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


def notify_material_import(success_count, user_info):
    """
    发送物料导入通知
    """
    bot = DingTalkBot()
    
    # 构建 Markdown 格式的消息
    message = f"""
### SAP物料数据导入通知
- **成功导入**: {success_count} 条
- **操作人**: {user_info.get('username')}
- **部门**: {user_info.get('department')}
- **时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """
    
    return bot.send_message(message, msg_type="markdown")

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
    """
    发送物料状态统计通知
    
    Args:
        status_info: dict, 包含统计信息
    """
    bot = DingTalkBot()
    
    # 构建 Markdown 格式的消息
    message = f"""
### SAP物料未完成状态统计
- **未完成物料**: {status_info.get('count')} 条
- **财务部待处理**: {status_info.get('finance_incomplete')} 条
- **运营部待处理**: {status_info.get('operation_incomplete')} 条
- **统计时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """
    
    return bot.send_message(message, msg_type="markdown")





