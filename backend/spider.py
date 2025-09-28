import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict
import os
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import sqlite3
from contextlib import contextmanager
import time

class MaterialSpider:
    def __init__(self):
        self.base_url = "http://192.168.2.41:8081/material/data/material_data_main/materialDataMain.do?method=data&q.j_path=main&q.fdWerks=5000&q.fdWerks=5300&q.fdMtart=Z001&q.fdMtart=Z002&q.fdMtart=Z003&q.fdMtart=Z004&rowsize=30"
        self.detail_base_url = "http://192.168.2.41:8081/material/data/material_data_main/materialDataMain.do?method=view&fdId="
        self.login_url = "http://192.168.2.41:8081/login.jsp"
        
        # 初始化 headers（不包含 cookie）
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
            
        # 初始化 playwright
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True)
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        
        # 登录并获取 cookie
        self.login()
        
        # 添加选择器配置
        self.selectors = {
            '工厂': '#_xform_fdWerks',
            '物料': '#lui-id-10 table tbody tr:first-child td:nth-child(2)',
            '物料描述': '#_xform_fdMaktx',
            '物料组': '#_xform_fdMatkl',
            '市场': '#_xform_fdZa001',
            '备注1': '#_xform_fdZm016',
            '备注2': '#_xform_fdZm017',
            '生产厂商': '#_xform_fdMaktg1',
            '基本计量单位': '#_xform_fdMeins',
            '检验时间': '#_xform_fdMpdau',
            # 可以继续添加其他字段的选择器
            # '字段名': 'CSS选择器'
        }

        # 数据库文件路径
        self.db_path = "materials.db"
        # 初始化数据库
        self._init_db()

        # 添加后端 API 认证
        self.backend_token = self._get_backend_token()

    def __del__(self):
        # 确保关闭浏览器
        if hasattr(self, 'page'):
            self.page.close()
        if hasattr(self, 'context'):
            self.context.close()
        if hasattr(self, 'browser'):
            self.browser.close()
        if hasattr(self, 'playwright'):
            self.playwright.stop()

    def _init_db(self):
        """初始化数据库表"""
        # 检查数据库文件是否存在
        db_exists = os.path.exists(self.db_path)
        
        if db_exists:
            print(f"使用已存在的数据库: {self.db_path}")
        else:
            print(f"创建新数据库: {self.db_path}")
        
        try:
            with self._get_db() as (conn, cursor):
                # 检查表是否存在
                cursor.execute('''
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='material_details'
                ''')
                table_exists = cursor.fetchone() is not None
                
                if not table_exists:
                    print("创建 material_details 表...")
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS material_details (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            material_id TEXT NOT NULL UNIQUE,  -- 添加唯一约束
                            工厂 TEXT,  -- 添加工厂字段 
                            物料 TEXT,
                            物料描述 TEXT,
                            物料组 TEXT,
                            市场 TEXT,
                            备注1 TEXT,
                            备注2 TEXT,
                            基本计量单位 TEXT,
                            生产厂商 TEXT,
                            检验时间 TEXT,
                            fetch_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')
                    conn.commit()
                    print("表创建成功")
                else:
                    print("material_details 表已存在")
                    
                # 显示表结构
                cursor.execute('PRAGMA table_info(material_details)')
                columns = cursor.fetchall()
                print("\n当前表结构:")
                for col in columns:
                    print(f"- {col[1]} ({col[2]})")
                
        except sqlite3.Error as e:
            print(f"数据库初始化失败: {str(e)}")
            raise

    @contextmanager
    def _get_db(self):
        """数据库连接上下文管理器"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            yield conn, cursor
        finally:
            cursor.close()
            conn.close()

    def _get_backend_token(self):
        """获取后端 API 认证 token"""
        try:
            response = requests.post(
                'http://home.dandan.ink:8088/login',
                json={
                    "username": "yanfeilong",  # 使用有权限的账号
                    "password": "19931225"  # 使用正确的密码
                }
            )
            
            if response.status_code == 200:
                return response.json().get('token')
            else:
                print(f"获取后端 token 失败: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"获取后端 token 出错: {str(e)}")
            return None

    def check_and_fetch_details(self) -> None:
        """检查并获取最近三天的物料详细信息"""
        try:
            materials = self.fetch_materials()
            today = datetime.now().date()
            yesterday = today - timedelta(days=3)
            
            with self._get_db() as (conn, cursor):
                for material in materials:
                    try:
                        create_date = datetime.strptime(
                            material['新建时间'], 
                            "%Y-%m-%d %H:%M:%S"
                        ).date()
                        
                        # 只处理最近三天创建的物料
                        if not (yesterday <= create_date <= today):
                            continue

                        material_id = material['备注1'].replace('ID: ', '')
                        
                        # 检查是否已存在
                        cursor.execute(
                            'SELECT id FROM material_details WHERE material_id = ?', 
                            (material_id,)
                        )
                        if not cursor.fetchone():
                            print(f"获取物料 {material['物料']} 的详细信息...")
                            details = self.fetch_material_details(material_id)
                            details['检验时间'] = details['检验时间'].split('/')[0] if details['检验时间'] else details['检验时间'] 
                            if details:
                                # 先发送到后端
                                try:
                                    response = requests.post(
                                        'http://home.dandan.ink:8088/api/materials/update',
                                        json={
                                            'material_id': material_id,
                                            'details': details,
                                            'source': 'spider',
                                            'fetch_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                        },
                                        headers={
                                            **self.headers,
                                            'Authorization': f'Bearer {self.backend_token}'  # 添加认证头
                                        },
                                        verify=False
                                    )
                                    
                                    # 如果后端处理成功，再保存到本地数据库
                                    if response.status_code == 200:
                                        result = response.json()
                                        print(f"后端处理结果: {result.get('message')} (操作: {result.get('action', 'unknown')})")
                                        
                                        # 保存到本地数据库
                                        cursor.execute('''
                                            INSERT INTO material_details 
                                            (material_id, 工厂, 物料, 物料描述, 物料组, 市场, 备注1, 备注2, 基本计量单位, 生产厂商, 检验时间)
                                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                        ''', (
                                            material_id,
                                            details.get('工厂', ''),
                                            details.get('物料', ''),
                                            details.get('物料描述', ''),
                                            details.get('物料组', ''),
                                            details.get('市场', ''),
                                            details.get('备注1', ''),
                                            details.get('备注2', ''),
                                            details.get('基本计量单位', ''),
                                            details.get('生产厂商', ''),
                                            details.get('检验时间', '')
                                        ))
                                        conn.commit()
                                        print(f"已保存物料 {material['物料']} 的详细信息到本地数据库")
                                    else:
                                        print(f"同步到后端失败: HTTP {response.status_code}")
                                        print(f"错误信息: {response.text}")
                                
                                except Exception as e:
                                    print(f"处理物料 {material['物料']} 时出错:")
                                    print(f"错误类型: {type(e).__name__}")
                                    print(f"错误信息: {str(e)}")
                                    if hasattr(e, 'response'):
                                        print(f"服务器响应: {e.response.text}")
                            else:
                                print(f"获取物料 {material['物料']} 的详细信息失败")
                        else:
                            print(f"物料 {material['物料']} 已存在，跳过")
                    except Exception as e:
                        print(f"处理物料 {material.get('物料', 'unknown')} 时出错: {str(e)}")
                        continue
            
        except Exception as e:
            print(f"检查物料详细信息时出错: {str(e)}")

    def fetch_material_details(self, material_id: str) -> Dict:
        """
        获取单个物料的详细信息
        """
        try:
            url = f"{self.detail_base_url}{material_id}"
            
            # 使用 playwright 加载页面
            self.page.goto(url)
            
            # 等待表格加载完成
            self.page.wait_for_selector('#lui-id-10 > table')
            
            # 获取页面内容
            page_content = self.page.content()
            
            # 使用 BeautifulSoup 解析 HTML
            soup = BeautifulSoup(page_content, 'html.parser')
            
            # 提取所有配置的字段信息
            details = {}
            for field, selector in self.selectors.items():
                try:
                    target_cell = soup.select_one(selector)
                    if target_cell:
                        value = target_cell.get_text(strip=True)
                        details[field] = value
                        print(f"获取到{field}: {value}")
                    else:
                        print(f"未找到{field}的值")
                        details[field] = ""
                except Exception as e:
                    print(f"提取{field}时出错: {str(e)}")
                    details[field] = ""
            
            return details
            
        except Exception as e:
            print(f"获取物料 {material_id} 详细信息失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {}

    def fetch_materials(self) -> List[Dict]:
        """
        爬取物料信息并转换为标准格式
        
        Returns:
            List[Dict]: 转换后的物料信息列表
        """
        try:
            # 发送请求获取数据
            response = requests.get(
                self.base_url, 
                headers=self.headers,
                verify=False
            )
            response.raise_for_status()
            
            # 解析 JSON 数据
            raw_data = response.json()
            converted_materials = []
            
            # 检查数据格式
            if not isinstance(raw_data, dict) or 'datas' not in raw_data:
                print("Invalid data format: missing 'datas' field")
                return []
            
            # 处理每组物料数据
            for material_data in raw_data['datas']:
                # 将物料数据转换为字典
                material_dict = {}
                for item in material_data:
                    if isinstance(item, dict) and "col" in item and "value" in item:
                        material_dict[item["col"]] = item["value"]
                
                # 如果没有必要的字段，跳过
                if not material_dict.get("fdMatnr"):
                    continue
                
                # 转换为标准格式
                converted_material = {
                    "工厂": material_dict.get("fdWerks", ""),
                    "物料": material_dict.get("fdMatnr", ""),
                    "物料描述": material_dict.get("fdName", ""),
                    "基本计量单位": material_dict.get("fdMeins", ""),
                    "生产厂商": material_dict.get("fdMaktg1", ""),
                    "新建时间": self._format_datetime(material_dict.get("fdErsda", "")),
                    "完成时间": "",  # 默认为空
                    "备注1": f"ID: {material_dict.get('fdId', '')}",
                    "备注2": f"Index: {material_dict.get('index', '')}",
                    "检验时间": material_dict.get("fdMpdau", "").split('/')[0] if '/' in material_dict.get("fdMpdau", "") else material_dict.get("fdMpdau", "")
                }
                
                converted_materials.append(converted_material)
            
            return converted_materials
            
        except requests.RequestException as e:
            print(f"请求失败: {str(e)}")
            return []
        except json.JSONDecodeError as e:
            print(f"JSON 解析失败: {str(e)}")
            print("Response text:", response.text)
            return []
        except Exception as e:
            print(f"处理数据失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def _format_datetime(self, date_str: str) -> str:
        """
        格式化日期时间字符串
        
        Args:
            date_str: 原始日期时间字符串
            
        Returns:
            str: 格式化后的日期时间字符串
        """
        try:
            if not date_str:
                return ""
            # 解析日期时间
            dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
            # 转换为标准格式
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return ""

    def login(self):
        """登录系统并获取 cookie"""
        max_retries = 3  # 最大重试次数
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                print(f"开始登录系统... (尝试 {retry_count + 1}/{max_retries})")
                
                # 设置登录信息
                username = "yanfeilong"
                password = "19931225Yfl"
                
                # 访问登录页面
                print("访问登录页面...")
                self.page.set_default_timeout(60000)
                self.page.goto(self.login_url, wait_until='networkidle')
                
                # 打印页面内容用于调试
                print("当前页面标题:", self.page.title())
                print("当前页面 URL:", self.page.url)
                
                # 等待用户名输入框
                print("等待登录表单加载...")
                username_input = self.page.wait_for_selector('input[name="j_username"]')
                password_input = self.page.wait_for_selector('input[name="j_password"]')
                
                if not username_input or not password_input:
                    raise Exception("未找到登录表单")
                
                # 填写登录表单
                print("填写登录信息...")
                username_input.fill(username)
                password_input.fill(password)
                
                # 查找并点击登录按钮
                print("查找登录按钮...")
                submit_button = self.page.wait_for_selector('.lui_login_button_div_c.login_submit_btn')
                if not submit_button:
                    raise Exception("未找到登录按钮")
                
                print("点击登录按钮...")
                submit_button.click()
                
                # 等待登录成功（等待页面跳转）
                print("等待登录完成...")
                self.page.wait_for_url("**/sys/**", timeout=10000)
                
                # 获取 cookie
                cookies = self.context.cookies()
                session_cookie = next(
                    (cookie for cookie in cookies if cookie['name'] == 'SESSION'),
                    None
                )
                
                if session_cookie:
                    # 更新 headers 中的 cookie
                    self.headers['Cookie'] = f"SESSION={session_cookie['value']}"
                    print("登录成功，已获取 cookie")
                    return  # 成功后退出
                else:
                    raise Exception("未找到 SESSION cookie")
                
            except Exception as e:
                print(f"登录尝试 {retry_count + 1} 失败: {str(e)}")
                # 保存页面截图用于调试
                try:
                    self.page.screenshot(path=f'login_error_{retry_count + 1}.png')
                    with open(f'login_error_{retry_count + 1}.html', 'w', encoding='utf-8') as f:
                        f.write(self.page.content())
                except:
                    pass
                
                retry_count += 1
                if retry_count >= max_retries:
                    print("超过最大重试次数，登录失败")
                    import traceback
                    traceback.print_exc()
                    raise
                else:
                    print(f"等待 5 秒后重试...")
                    time.sleep(5)
                    continue

# 使用示例
if __name__ == "__main__":
    spider = MaterialSpider()
    spider.check_and_fetch_details()
