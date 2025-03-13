<template>
  <div class="app-container" :style="bingWallpaperUrl ? { backgroundImage: `url(${bingWallpaperUrl})` } : {}">
    <!-- 登录部分 -->
    <div v-if="!isLoggedIn" class="login-container">
      <!-- 修改密码表单 -->
      <div v-if="showChangePassword" class="login-form">
        <h1>修改密码</h1>
        <h2>首次登录或密码重置后需要修改密码</h2>
        <input 
          type="password" 
          v-model="changePasswordForm.newPassword" 
          placeholder="新密码"
        >
        <input 
          type="password" 
          v-model="changePasswordForm.confirmPassword" 
          placeholder="确认新密码"
        >
        <button @click="handleChangePassword">确认修改</button>
      </div>
      
      <!-- 登录表单 -->
      <div v-else class="login-form">
        <h1>SAP数据收集系统</h1>
        <h2>用户登录</h2>
        <input v-model="loginForm.username" placeholder="用户名" type="text">
        <input v-model="loginForm.password" placeholder="密码" type="password">
        <div class="login-buttons">
          <button @click="handleLogin">登录</button>
          <button @click="showGuestDialog = true" class="guest-button">游客浏览</button>
        </div>
      </div>
    </div>

    <!-- 游客登录对话框 -->
    <div v-if="showGuestDialog" class="modal">
      <div class="modal-content guest-dialog">
        <h2>游客访问</h2>
        <div class="form-group">
          <label>申请人</label>
          <input 
            type="text" 
            v-model="guestForm.applicant" 
            placeholder="请输入申请人姓名"
            @keyup.enter="handleGuestLogin"
          >
        </div>
        <div class="modal-buttons">
          <button @click="handleGuestLogin">确认</button>
          <button @click="showGuestDialog = false">取消</button>
        </div>
      </div>
    </div>

    <!-- 主要内容 -->
    <div v-if="isLoggedIn" class="main-content">
      <div class="user-info">
        <div class="user-tag">
          <span class="username">{{ username }}</span>
          <span class="separator">:</span>
          <span class="department">{{ department }}</span>
        </div>
        <button v-if="!isGuest" @click="openSettings" class="settings-button">设置</button>
        <button v-if="!isGuest" @click="openEmailSettings">设置邮箱</button>
        <button v-if="!isGuest" @click="openChangePasswordModal">修改密码</button>
        <button v-if="department === '信息部'" @click="openUserManagement">用户管理</button>
        <button v-if="department === '信息部'" @click="openSystemSettings">系统设置</button>
        <button v-if="department === '信息部'" @click="sendStatusNotification">推送统计</button>
        <button @click="handleLogout">退出</button>
        <div class="right-buttons">
          <label v-if="canImport" class="file-input-label">
            <input type="file" @change="handleFileUpload" accept=".xlsx,.xls">
            <span>选择文件</span>
          </label>
          <button v-if="canExport && !isGuest" @click="exportToExcel">导出Excel</button>
        </div>
      </div>

      <div class="table-container">
        <!-- 添加搜索区域 -->
        <div class="search-area">
          <div class="search-item">
            <label>物料编号</label>
            <input 
              type="text" 
              v-model="searchForm.物料"
              placeholder="搜索物料编号"
              @input="handleSearch"
            >
          </div>
          <div class="search-item">
            <label>物料描述</label>
            <input 
              type="text" 
              v-model="searchForm.物料描述"
              placeholder="搜索物料描述"
              @input="handleSearch"
            >
          </div>
          <div class="search-item">
            <label>物料组</label>
            <input 
              type="text" 
              v-model="searchForm.物料组"
              placeholder="搜索物料组"
              @input="handleSearch"
            >
          </div>
          <div class="search-item">
            <label>工厂</label>
            <input 
              type="text" 
              v-model="searchForm.工厂"
              placeholder="搜索工厂"
              @input="handleSearch"
              :disabled="department === '制剂财务部' || department === '制药科技财务部'"
              :title="(department === '制剂财务部' || department === '制药科技财务部') ? '财务部门只能查看指定工厂的物料' : ''"
            >
          </div>
        </div>
        
        <div v-if="tableData.length" class="table-wrapper">
          <table border="1">
            <thead>
              <tr>
                <th v-for="header in headers" :key="header" :class="{ editable: isEditable(header) }">
                  {{ header }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, index) in tableData" :key="index">
                <td v-for="header in headers" :key="header">
                  <template v-if="isEditable(header)">
                    <select v-if="header === 'MRP控制者'"
                      v-model="row[header]"
                      @change="handleCellChange(index, header, $event)"
                      @blur="handleCellBlur(index, header, $event)">
                      <option value="">请选择</option>
                      <option v-for="option in mrpControllers" :key="option.value" :value="option.value">
                        {{ option.label }}
                      </option>
                    </select>
                    <input v-else
                      type="text" 
                      v-model="row[header]" 
                      @change="handleCellChange(index, header, $event)"
                      @blur="handleCellBlur(index, header, $event)"
                      @input="validateInput(index, header, $event)"
                      :placeholder="getPlaceholder(header)"
                    >
                  </template>
                  <template v-else>
                    <div v-if="header === '物料描述' || header === '生产厂商'" 
                         class="truncate-cell" 
                         :title="row[header]">
                      {{ row[header] }}
                    </div>
                    <template v-else-if="header === '财务状态'">
                      <span :style="getStatusStyle(getFinanceStatus(row))">
                        {{ getFinanceStatus(row) }}
                      </span>
                    </template>
                    <template v-else-if="header === 'MRP状态'">
                      <span :style="getStatusStyle(getMRPStatus(row))">
                        {{ getMRPStatus(row) }}
                      </span>
                    </template>
                    <template v-else-if="header === '完成状态'">
                      <span :style="getStatusStyle(getCompletionStatus(row))">
                        {{ getCompletionStatus(row) }}
                      </span>
                    </template>
                    <template v-else>
                      {{ row[header] }}
                    </template>
                  </template>
                </td>
              </tr>
            </tbody>
          </table>
          
          <!-- 添加分页组件 -->
          <div class="pagination">
            <button 
              :disabled="currentPage === 1"
              @click="handlePageChange(currentPage - 1)"
            >
              上一页
            </button>
            
            <span class="page-info">
              {{ currentPage }} / {{ totalPages }} 页
              (共 {{ totalItems }} 条)
            </span>
            
            <button 
              :disabled="currentPage === totalPages"
              @click="handlePageChange(currentPage + 1)"
            >
              下一页
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 设置对话框 -->
    <div v-if="showSettings" class="modal">
      <div class="modal-content settings-modal">
        <h2>设置</h2>
        <div class="form-group">
          <label class="checkbox-label">
            <input 
              type="checkbox" 
              v-model="showCompleted"
              @change="handleSettingsChange"
            >
            查看已完成物料
          </label>
        </div>
        <div class="form-group">
          <label class="checkbox-label">
            <input 
              type="checkbox" 
              v-model="emailPush"
              @change="handleSettingsChange"
            >
            接收邮件推送
          </label>
        </div>
        <div class="form-group">
          <label>显示行数</label>
          <input 
            type="number" 
            v-model="pageSize" 
            min="1" 
            max="100"
            @change="handleSettingsChange"
          >
        </div>
        <div class="modal-buttons">
          <button @click="closeSettings">关闭</button>
        </div>
      </div>
    </div>

    <!-- 用户管理对话框 -->
    <div v-if="showUserManagement" class="modal">
      <div class="modal-content">
        <h2>用户管理</h2>
        
        <!-- 添加用户表单 -->
        <div class="add-user-form">
          <h3>添加新用户</h3>
          <div class="form-group">
            <label>用户名</label>
            <input type="text" v-model="newUser.username" placeholder="输入用户名">
          </div>
          <div class="form-group">
            <label>部门</label>
            <select v-model="newUser.department">
              <option value="">请选择部门</option>
              <option value="运营管理部">运营管理部</option>
              <option value="采购部">采购部</option>
              <option value="信息部">信息部</option>
              <option value="QC检测室">QC检测室</option>
              <option value="制剂财务部">制剂财务部</option>
              <option value="制药科技财务部">制药科技财务部</option>
              <option value="制药科技制造部">制药科技制造部</option>
            </select>
          </div>
          <div class="form-group">
            <label>邮箱</label>
            <input type="email" v-model="newUser.email" placeholder="输入邮箱">
          </div>
          <button @click="addUser" class="add-button">添加用户</button>
        </div>

        <div class="divider"></div>

        <!-- 用户列表 -->
        <div class="user-list">
          <h3>现有用户</h3>
          <div v-for="user in users" :key="user.username" class="user-item">
            <div class="user-info">
              <span class="username">{{ user.username }}</span>
              <span class="department">({{ user.department }})</span>
            </div>
            <button @click="resetPassword(user.username)" class="reset-button">重置密码</button>
          </div>
        </div>
        
        <div class="modal-buttons">
          <button @click="showUserManagement = false">关闭</button>
        </div>
      </div>
    </div>

    <!-- 添加修改密码对话框 -->
    <div v-if="showChangePassword" class="modal">
      <div class="modal-content">
        <h2>修改密码</h2>
        <div class="form-group">
          <label>新密码</label>
          <input type="password" v-model="changePasswordForm.newPassword" placeholder="输入新密码">
        </div>
        <div class="form-group">
          <label>确认密码</label>
          <input type="password" v-model="changePasswordForm.confirmPassword" placeholder="确认新密码">
        </div>
        <div class="modal-buttons">
          <button @click="handleChangePassword">确认</button>
          <button @click="closeChangePasswordModal">取消</button>
        </div>
      </div>
    </div>

    <!-- 添加系统设置对话框 -->
    <div v-if="showSystemSettings" class="modal">
      <div class="modal-content">
        <h2>系统设置</h2>
        <div class="form-group">
          <label>钉钉机器人 Webhook URL</label>
          <input 
            type="text" 
            v-model="systemSettings.dingTalkUrl" 
            placeholder="请输入钉钉机器人 Webhook URL"
          >
        </div>
        <div class="form-group">
          <label>关键词（每行一个）</label>
          <textarea
            v-model="keywordsText"
            placeholder="请输入关键词，每行一个"
            rows="3"
          ></textarea>
        </div>
        <div class="form-group">
          <label>SMTP服务器地址</label>
          <input 
            type="text" 
            v-model="systemSettings.smtpServer" 
            placeholder="请输入SMTP服务器地址"
          >
        </div>
        <div class="form-group">
          <label>SMTP端口</label>
          <input 
            type="number" 
            v-model="systemSettings.smtpPort" 
            placeholder="请输入SMTP端口"
          >
        </div>
        <div class="form-group">
          <label>SMTP用户名</label>
          <input 
            type="text" 
            v-model="systemSettings.smtpUser" 
            placeholder="请输入SMTP用户名"
          >
        </div>
        <div class="form-group">
          <label>SMTP密码</label>
          <input 
            type="password" 
            v-model="systemSettings.smtpPassword" 
            placeholder="请输入SMTP密码"
          >
        </div>
        <!-- 在系统设置对话框中添加自动推送配置 -->
        <div class="form-group">
          <label class="checkbox-label">
            <input 
              type="checkbox" 
              v-model="systemSettings.pushEnabled"
            >
            启用每日自动推送（节假日不推送）
          </label>
        </div>

        <div class="form-group" v-if="systemSettings.pushEnabled">
          <label>推送时间</label>
          <input 
            type="time" 
            v-model="systemSettings.pushTime"
          >
        </div>
        <div class="settings-actions">
          <button @click="exportSettings" class="export-button">导出配置</button>
          <label class="import-button">
            导入配置
            <input 
              type="file" 
              accept=".toml"
              @change="importSettings"
              style="display: none"
            >
          </label>
        </div>
        <div class="modal-buttons">
          <button @click="saveSystemSettings">保存</button>
          <button @click="closeSystemSettings">取消</button>
        </div>
      </div>
    </div>

    <!-- 添加邮箱设置对话框 -->
    <div v-if="showEmailSettings" class="modal">
      <div class="modal-content">
        <h2>邮箱设置</h2>
        <div class="form-group">
          <label>邮箱地址</label>
          <input 
            type="email" 
            v-model="emailForm.email" 
            placeholder="请输入邮箱地址"
          >
        </div>
        <div class="modal-buttons">
          <button @click="saveEmailSettings">保存</button>
          <button @click="showEmailSettings = false">取消</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import * as XLSX from 'xlsx'
import axios from 'axios'
import { debounce } from 'lodash-es'  // 导入debounce

interface MaterialRow {
  '工厂': string;
  '物料': string;
  '物料描述': string;
  '物料组': string;
  '市场': string;
  '备注1': string;
  '备注2': string;
  '生产厂商': string;
  '检测周期': string;
  '最小批量大小': string;
  '舍入值': string;
  '计划交货时间': string;
  'MRP控制者': string;
  'MRP类型': string;
  '批量程序': string;
  '固定批量': string;
  '再订货点': string;
  '安全库存': string;
  '批量大小': string;
  '采购类型': string;
  '收货处理时间': string;
  'MRP区域': string;
  '反冲': string;
  '批量输入': string;
  '自制生产时间': string;
  '策略组': string;
  '综合MRP': string;
  '消耗模式': string;
  '向后跨期期间': string;
  '向后跨期时间': string;
  '独立/集中': string;
  '计划时间界': string;
  '生产评估': string;
  '生产计划': string;
  '新建时间': string;
  '完成时间': string;
  '评估分类': string;
  '销售订单库存': string;
  '价格确定': string;
  '价格控制': string;
  '标准价格': string;
  '价格单位': string;
  '用QS的成本核算': string;
  '物料来源': string;
  '差异码': string;
  '物料状态': string;
  '成本核算批量': string;
  '基本计量单位': string;
  [key: string]: string;
}

interface SearchParams {
  page: number;
  page_size: number;
  物料?: string;
  物料描述?: string;
  物料组?: string;
  工厂?: string;
  show_completed: boolean;
  游客姓名?: string;
}

// 分页相关的状态
const currentPage = ref(1)
const pageSize = ref(15)  // 恢复这个定义
const totalPages = ref(0)
const totalItems = ref(0)
const tableData = ref<MaterialRow[]>([])
const headers = computed(() => {
  const baseHeaders = [
    '工厂', '物料', '物料描述', '物料组', '市场', '备注1', '备注2', '生产厂商', '基本计量单位'
  ]
  
  const financeHeaders = [
    '评估分类', '销售订单库存', '价格确定', '价格控制', '标准价格', '价格单位',
    '用QS的成本核算', '物料来源', '差异码', '物料状态', '成本核算批量'
  ]
  
  const timeHeaders = ['新建时间', '完成时间']
  
  const otherHeaders = [
    '检测时间QC', '最小批量大小PUR', '舍入值PUR', '计划交货时间PUR',
    'MRP控制者', 'MRP类型', '批量程序', '固定批量', '再订货点', 
    '安全库存', '批量大小', '舍入值', '采购类型', '收货处理时间', 
    '计划交货时间', 'MRP区域', '反冲', '批量输入', '自制生产时间', 
    '策略组', '综合MRP', '消耗模式', '向后跨期期间', '向后跨期时间', 
    '独立集中', '计划时间界', '生产评估', '生产计划'
  ]

  // 游客视图列
  const guestHeaders = [
    ...baseHeaders,
    '财务完成状态',
    'MRP完成状态',
    '完成状态'
  ]
  
  // 根据部门返回不同的列
  if (department.value === '游客') {
    return guestHeaders
  } else if (department.value === '信息部') {
    return [...baseHeaders, ...financeHeaders, ...otherHeaders, ...timeHeaders]
  } else if (department.value === '制剂财务部' || department.value === '制药科技财务部') {
    return [...baseHeaders, ...financeHeaders, ...timeHeaders]
  }
  return [...baseHeaders, ...otherHeaders, ...timeHeaders]
})

// MRP控制者选项
const mrpControllers = [
  { value: 'Y01', label: 'Y01 研发试制物料' },
  { value: 'Z01', label: 'Z01 美国市场成品&半成品' },
  { value: 'Z02', label: 'Z02 美国市场原辅料' },
  { value: 'Z03', label: 'Z03 美国市场包材' },
  { value: 'Z04', label: 'Z04 中国市场成品&半成品' },
  { value: 'Z05', label: 'Z05 中国市场原辅料' },
  { value: 'Z06', label: 'Z06 中国市场包材' },
  { value: 'Z07', label: 'Z07 欧洲市场成品&半成品' },
  { value: 'Z08', label: 'Z08 欧洲市场原辅料' },
  { value: 'Z09', label: 'Z09 欧洲市场包材' },
  { value: 'Z10', label: 'Z10 大客户成品&半成品' },
  { value: 'Z11', label: 'Z11 大客户原辅料' },
  { value: 'Z12', label: 'Z12 大客户包材' },
  { value: 'Z13', label: 'Z13 劳保用品' }
]

// 登录相关状态
const isLoggedIn = ref(false)
const username = ref('')
const department = ref('')
const isGuest = ref(false)  // 添加游客标识
const loginForm = ref({
  username: '',
  password: ''
})

// 游客相关状态
const showGuestDialog = ref(false)
const guestForm = ref({
  applicant: ''
})

// 修改密码相关状态
const showChangePassword = ref(false)
const changePasswordForm = ref({
  newPassword: '',
  confirmPassword: ''
})
const tempToken = ref('') // 存储临时token

// 修改 API_BASE_URL 的定义
const API_BASE_URL = import.meta.env.MODE === 'development' 
  ? 'http://localhost:8000'  // 开发环境
  : ''  // 生产环境使用相对路径

// 权限控制
const canImport = computed(() => department.value === '信息部')
const canExport = computed(() => true)  // 所有用户都可以导出
 
const getEditableColumns = computed(() => {
  switch (department.value) {
    case '运营管理部':
      return ['MRP控制者', '最小批量大小PUR', '舍入值PUR', '计划交货时间PUR', '检测时间QC']  // 添加采购部的字段
    case '采购部':
      return ['最小批量大小PUR', '舍入值PUR', '计划交货时间PUR']
    case 'QC检测室':
      return ['检测时间QC']
    case '制剂财务部':
    case '制药科技财务部':
      return ['评估分类', '销售订单库存', '价格确定', '价格控制', '标准价格', 
              '价格单位', '用QS的成本核算', '物料来源', '差异码', '物料状态', '成本核算批量']
    default:
      return []
  }
})

// 在其他 ref 定义附近添加
const emailPush = ref(false)

// 登录处理
const handleLogin = async () => {
  try {
    console.log('登录前 - isGuest:', isGuest.value)
    
    const response = await axios.post(`${API_BASE_URL}/login`, loginForm.value)
    
    // 保存 token
    localStorage.setItem('token', response.data.token)
    
    // 设置用户信息
    isLoggedIn.value = true
    isGuest.value = false  // 确保设置为false
    department.value = response.data.department
    username.value = loginForm.value.username
    
    console.log('登录后 - isGuest:', isGuest.value, 'department:', department.value)
    
    // 设置工厂筛选
    if (department.value === '制剂财务部') {
      searchForm.value.工厂 = '5000'
    } else if (department.value === '制药科技财务部' || department.value === '制药科技制造部') {
      searchForm.value.工厂 = '5300'
    } else {
      searchForm.value.工厂 = ''
    }
    
    // 设置用户配置
    if (response.data.settings) {
      showCompleted.value = response.data.settings.show_completed
      pageSize.value = response.data.settings.page_size
      if ('email_push' in response.data.settings) {
        emailPush.value = response.data.settings.email_push
      }
    }
    
    // 检查是否需要修改密码
    if (response.data.need_change_password) {
      showChangePassword.value = true
    }
    
    // 加载表格数据
    await loadTableData()
    
  } catch (error: any) {
    alert(error.response?.data?.detail || '登录失败')
  }
}

// 处理修改密码
const handleChangePassword = async () => {
  if (!changePasswordForm.value.newPassword || 
      changePasswordForm.value.newPassword !== changePasswordForm.value.confirmPassword) {
    alert('两次输入的密码不一致')
    return
  }

  try {
    // 如果是首次登录修改密码，直接使用临时 token
    const token = tempToken.value || localStorage.getItem('token')
    
    await axios.put(`${API_BASE_URL}/user/password`, {
      newPassword: changePasswordForm.value.newPassword
    }, {
      headers: { 
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })
    
    // 使用新密码自动重新登录
    loginForm.value.password = changePasswordForm.value.newPassword
    showChangePassword.value = false
    
    try {
      const response = await axios.post(`${API_BASE_URL}/login`, {
        username: username.value,
        password: changePasswordForm.value.newPassword
      })
      
      // 更新 token 和登录状态
      localStorage.setItem('token', response.data.token)
      isLoggedIn.value = true
      isGuest.value = false  // 确保设置为false
      department.value = response.data.department
      tempToken.value = ''  // 清除临时 token
      
      // 清空修改密码表单
      changePasswordForm.value.newPassword = ''
      changePasswordForm.value.confirmPassword = ''
      
      alert('密码修改成功')
      
      // 重新加载数据
      await loadTableData()
      
    } catch (error) {
      alert('自动重新登录失败，请手动登录')
      handleLogout()
    }
    
  } catch (error: any) {
    console.error('修改密码失败:', error)
    alert('修改密码失败')
  }
}

// 退出登录
const handleLogout = () => {
  isLoggedIn.value = false
  isGuest.value = false  // 重置游客状态
  username.value = ''
  department.value = ''
  localStorage.removeItem('token')
  
  // 重置分页相关状态
  currentPage.value = 1
  totalPages.value = 0
  totalItems.value = 0
  tableData.value = []
}

// 获取输入框提示文本
const getPlaceholder = (header: string) => {
  switch (header) {
    case '检测周期':
      return '请输入整数'
    case '计划交货时间':
      return '请输入整数'
    case '最小批量大小':
      return '请输入数字'
    case '舍入值':
      return '请输入数字'
    default:
      return ''
  }
}

// 验证输入
const validateInput = (rowIndex: number, header: string, event: Event) => {
  const input = event.target as HTMLInputElement
  const value = input.value
  let isValid = true

  switch (header) {
    case '检测周期':
    case '计划交货时间':
      // 只允许整数
      if (!/^\d*$/.test(value)) {
        input.value = value.replace(/[^\d]/g, '')
        isValid = false
      }
      break
    case '最小批量大小':
    case '舍入值':
      // 允许数字和小数点
      if (!/^\d*\.?\d*$/.test(value)) {
        input.value = value.replace(/[^\d.]/g, '')
        isValid = false
      }
      // 确保只有一个小数点
      if ((value.match(/\./g) || []).length > 1) {
        input.value = value.substring(0, value.lastIndexOf('.'))
        isValid = false
      }
      break
  }

  // 如果输入有效且值已改变，则触发保存
  if (isValid && value !== tableData.value[rowIndex][header]) {
    handleCellChange(rowIndex, header, event)
  }
}

// 判断列是否可编辑
const isEditable = (header: string) => {
  return getEditableColumns.value.includes(header)
}

// 文件上传处理
const handleFileUpload = async (event: Event) => {
  if (!canImport.value) {
    alert('没有权限导入数据')
    return
  }

  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return

  const reader = new FileReader()
  reader.onload = async (e) => {
    const data = e.target?.result
    const workbook = XLSX.read(data, { type: 'binary' })
    const firstSheetName = workbook.SheetNames[0]
    const worksheet = workbook.Sheets[firstSheetName]
    
    const jsonData = XLSX.utils.sheet_to_json<MaterialRow>(worksheet)
    
    // 过滤掉物料为空的数据并处理所有字段
    const processedData = jsonData
      .filter(row => row.物料?.trim())
      .map(row => ({
        物料: row.物料?.trim() || '',
        物料描述: row.物料描述?.trim() || '',
        物料组: row.物料组?.trim() || null,
        市场: row.市场?.trim() || null,
        基本计量单位: row.基本计量单位?.trim() || null,  // 直接使用 Excel 中的值
        备注1: row.备注1?.trim() || null,
        备注2: row.备注2?.trim() || null,
        生产厂商: row.生产厂商?.trim() || null,
        检测时间QC: row.检测周期?.trim() || null,
        最小批量大小PUR: row.最小批量大小?.trim() || null,
        舍入值PUR: row.舍入值?.trim() || null,
        计划交货时间PUR: row.计划交货时间?.trim() || null,
        MRP控制者: row.MRP控制者?.trim() || null,
        MRP类型: row.MRP类型?.trim() || null,
        批量程序: row.批量程序?.trim() || null,
        固定批量: row.固定批量?.trim() || null,
        再订货点: row.再订货点?.trim() || null,
        安全库存: row.安全库存?.trim() || null,
        批量大小: row.批量大小?.trim() || null,
        舍入值: row.舍入值?.trim() || null,
        采购类型: row.采购类型?.trim() || null,
        收货处理时间: row.收货处理时间?.trim() || null,
        计划交货时间: row.计划交货时间?.trim() || null,
        MRP区域: row.MRP区域?.trim() || null,
        反冲: row.反冲?.trim() || null,
        批量输入: row.批量输入?.trim() || null,
        自制生产时间: row.自制生产时间?.trim() || null,
        策略组: row.策略组?.trim() || null,
        综合MRP: row.综合MRP?.trim() || null,
        消耗模式: row.消耗模式?.trim() || null,
        向后跨期期间: row.向后跨期期间?.trim() || null,
        向后跨期时间: row.向后跨期时间?.trim() || null,
        独立集中: row.独立集中?.trim() || null,
        计划时间界: row.计划时间界?.trim() || null,
        生产评估: row.生产评估?.trim() || null,
        生产计划: row.生产计划?.trim() || null,
        新建时间: null,
        完成时间: null,
        评估分类: row.评估分类?.trim() || null,
        销售订单库存: row.销售订单库存?.trim() || null,
        价格确定: row.价格确定?.trim() || null,
        价格控制: row.价格控制?.trim() || null,
        标准价格: row.标准价格?.trim() || null,
        价格单位: row.价格单位?.trim() || null,
        用QS的成本核算: row.用QS的成本核算?.trim() || null,
        物料来源: row.物料来源?.trim() || null,
        差异码: row.差异码?.trim() || null,
        物料状态: row.物料状态?.trim() || null,
        成本核算批量: row.成本核算批量?.trim() || null,
        工厂: row.工厂?.trim() || null,
      }))

    if (processedData.length === 0) {
      alert('没有有效的数据需要导入')
      return
    }
    
    try {
      const response = await axios.post(`${API_BASE_URL}/materials`, processedData, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      })
      await loadTableData() // 重新加载数据以显示最新结果
      
      // 显示导入结果，包括成功和跳过的信息
      const successMessage = response.data.message
      const skippedMaterials = response.data.skipped
      
      let message = successMessage
      if (skippedMaterials.length > 0) {
        message += `\n\n以下物料已存在，已跳过：\n${skippedMaterials.join('\n')}`
      }
      
      alert(message)
      
    } catch (error: any) {
      console.error('保存数据失败:', error)
      alert('保存数据失败')
    }
  }
  reader.readAsBinaryString(file)
}

// 加载物料数据
const loadTableData = async () => {
  try {
    console.log('loadTableData - isGuest:', isGuest.value, 'department:', department.value)
    
    const params: SearchParams = {
      page: currentPage.value,
      page_size: pageSize.value,
      show_completed: showCompleted.value,
      物料: searchForm.value.物料 || undefined,
      物料描述: searchForm.value.物料描述 || undefined,
      物料组: searchForm.value.物料组 || undefined,
      工厂: searchForm.value.工厂 || undefined
    }
    
    // 如果是游客，添加游客姓名参数
    if (isGuest.value) {
      params.游客姓名 = username.value
      console.log('添加游客参数:', username.value)
    }
    
    console.log('请求参数:', params)
    console.log('请求头:', isGuest.value ? '无token' : '有token')
    
    const response = await axios.get(`${API_BASE_URL}/materials`, {
      params: params,
      headers: isGuest.value ? {} : {
        Authorization: `Bearer ${localStorage.getItem('token')}`
      }
    })
    
    console.log('响应状态:', response.status)
    console.log('响应数据条数:', response.data.items.length)
    
    tableData.value = response.data.items
    totalItems.value = response.data.total
    totalPages.value = response.data.total_pages
    
  } catch (error) {
    console.error('加载数据失败:', error)
    alert('加载数据失败')
  }
}

// 导出Excel
const exportToExcel = async () => {
  try {
    // 根据部门获取可见字段  
    const visibleFields = computed(() => {
      const baseFields = ['工厂', '物料', '物料描述', '物料组', '市场', '备注1', '备注2', '生产厂商', '基本计量单位']
      const financeFields = [
        '评估分类', '销售订单库存', '价格确定', '价格控制', '标准价格', '价格单位',
        '用QS的成本核算', '物料来源', '差异码', '物料状态', '成本核算批量'
      ]
      const otherFields = [
        '检测时间QC', '最小批量大小PUR', '舍入值PUR', '计划交货时间PUR',
        'MRP控制者', 'MRP类型', '批量程序', '固定批量', '再订货点', 
        '安全库存', '批量大小', '舍入值', '采购类型', '收货处理时间', 
        '计划交货时间', 'MRP区域', '反冲', '批量输入', '自制生产时间', 
        '策略组', '综合MRP', '消耗模式', '向后跨期期间', '向后跨期时间', 
        '独立集中', '计划时间界', '生产评估', '生产计划'
      ]

      switch (department.value) {
        case '信息部':
          return [...baseFields, ...financeFields, ...otherFields]
        case '制剂财务部':
        case '制药科技财务部':
          return [...baseFields, ...financeFields]
        case '采购部':
          return [...baseFields, '最小批量大小PUR', '舍入值PUR', '计划交货时间PUR']
        case 'QC检测室':
          return [...baseFields, '检测时间QC']
        case '运营管理部':
          return [...baseFields, ...otherFields]
        default:
          return baseFields
      }
    })

    // 获取未完成的数据
    const response = await axios.get(`${API_BASE_URL}/materials`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
      params: {
        page: 1,
        page_size: 999999,  // 获取所有数据
        show_completed: false  // 只获取未完成的
      }
    })

    // 过滤字段
    const filteredData = response.data.items.map((item: any) => {
      const filtered: any = {}
      visibleFields.value.forEach(field => {
        filtered[field] = item[field]
      })
      return filtered
    })

    // 创建工作表
    const ws = XLSX.utils.json_to_sheet(filteredData)
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, 'Materials')

    // 导出文件
    XLSX.writeFile(wb, `物料数据_${department.value}_${new Date().toISOString().split('T')[0]}.xlsx`)

  } catch (error) {
    console.error('导出失败:', error)
    alert('导出失败，请重试')
  }
}

// 添加处理失去焦点的函数
const handleCellBlur = async (rowIndex: number, header: string, event: Event) => {
  if (!isEditable(header)) return
  
  let value = header === 'MRP控制者' 
    ? (event.target as HTMLSelectElement).value 
    : (event.target as HTMLInputElement).value
  
  // 如果值为空，设置默认值并触发保存
  if (!value.trim() && header !== 'MRP控制者') {
    value = header === '标准价格' ? '0' : 'NA'
    
    // 更新输入框的值
    if (header === 'MRP控制者') {
      (event.target as HTMLSelectElement).value = value
    } else {
      (event.target as HTMLInputElement).value = value
    }
    
    // 直接更新本地数据，避免重复请求
    tableData.value[rowIndex][header] = value
    
    // 触发保存到后端
    try {
      await axios.put(
        `${API_BASE_URL}/materials/${encodeURIComponent(tableData.value[rowIndex].物料)}`,
        {
          field: header,
          value: value
        },
        {
          headers: { 
            Authorization: `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json'
          }
        }
      )
      
      // 检查是否需要触发计算
      checkAndCalculate(tableData.value[rowIndex])
      
    } catch (error) {
      console.error('保存默认值失败:', error)
    }
  }
}

// 修改原有的 handleCellChange 函数
const handleCellChange = async (rowIndex: number, header: string, event: Event) => {
  if (!isEditable(header)) return
  
  let value = header === 'MRP控制者' 
    ? (event.target as HTMLSelectElement).value 
    : (event.target as HTMLInputElement).value
  
  // 处理空值的默认值（除了 MRP控制者）
  if (!value.trim() && header !== 'MRP控制者') {
    value = header === '标准价格' ? '0' : 'NA'
  }
  
  const material = tableData.value[rowIndex]
  
  try {
    await axios.put(
      `${API_BASE_URL}/materials/${encodeURIComponent(material.物料)}`,
      {
        field: header,
        value: value
      },
      {
        headers: { 
          Authorization: `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      }
    )
    
    // 更新本地数据
    tableData.value[rowIndex][header] = value
    
    // 检查是否需要触发计算
    checkAndCalculate(tableData.value[rowIndex])
    
  } catch (error: any) {
    // 恢复原值
    if (header === 'MRP控制者') {
      (event.target as HTMLSelectElement).value = material[header]
    } else {
      (event.target as HTMLInputElement).value = material[header]
    }
    
    // 只在非空值时显示错误
    if (value.trim()) {
      alert(error.response?.data?.detail || '保存失败')
    }
  }
}

// 处理分页变化
const handlePageChange = async (newPage: number) => {
  console.log('分页变化 - isGuest:', isGuest.value, 'newPage:', newPage)
  
  currentPage.value = newPage
  
  try {
    const params: SearchParams = {
      page: currentPage.value,
      page_size: pageSize.value,
      show_completed: showCompleted.value,
      物料: searchForm.value.物料 || undefined,
      物料描述: searchForm.value.物料描述 || undefined,
      物料组: searchForm.value.物料组 || undefined,
      工厂: searchForm.value.工厂 || undefined
    }
    
    // 如果是游客，添加游客姓名参数
    if (isGuest.value) {
      params.游客姓名 = username.value
      console.log('分页添加游客参数:', username.value)
    }
    
    console.log('分页请求参数:', params)
    
    const response = await axios.get(`${API_BASE_URL}/materials`, {
      params: params,
      headers: isGuest.value ? {} : {
        Authorization: `Bearer ${localStorage.getItem('token')}`
      }
    })
    
    tableData.value = response.data.items
    totalItems.value = response.data.total
    totalPages.value = response.data.total_pages
    
  } catch (error) {
    console.error('加载分页数据失败:', error)
    alert('加载分页数据失败')
  }
}

// 在现有的 import 语句下添加
const bingWallpaperUrl = ref('')

// 在现有的代码中添加获取壁纸的函数
const getBingWallpaper = async () => {
  try {
    const response = await axios.get('https://bing.biturl.top/')
    bingWallpaperUrl.value = response.data.url
  } catch (error) {
    console.error('获取壁纸失败:', error)
    // 设置默认背景色作为后备方案
    bingWallpaperUrl.value = ''
  }
}

// 在 script setup 部分添加以下代码
const checkLoginStatus = async () => {
  const token = localStorage.getItem('token')
  if (token) {
    try {
      // 验证 token 有效性
      await axios.get(`${API_BASE_URL}/materials`, {
        headers: { Authorization: `Bearer ${token}` },
        params: {
          page: 1,
          page_size: pageSize.value
        }
      })
      
      // 从 token 中解析用户信息
      const tokenData = JSON.parse(atob(token.split('.')[1]))
      username.value = tokenData.username
      department.value = tokenData.department
      isLoggedIn.value = true
      
      // 设置工厂筛选
      if (department.value === '制剂财务部') {
        searchForm.value.工厂 = '5000'
      } else if (department.value === '制药科技财务部' || department.value === '制药科技制造部') {
        searchForm.value.工厂 = '5300'
      } else {
        searchForm.value.工厂 = ''
      }
      
      // 移除这里的 loadTableData 调用
    } catch (error) {
      localStorage.removeItem('token')
      isLoggedIn.value = false
      username.value = ''
      department.value = ''
    }
  }
}

// 修改 onMounted
onMounted(async () => {
  getBingWallpaper()
  
  // 如果已经登录，加载用户设置和数据
  const token = localStorage.getItem('token')
  if (token) {
    try {
      // 解析 token 获取用户信息
      const tokenData = JSON.parse(atob(token.split('.')[1]))
      username.value = tokenData.username
      department.value = tokenData.department
      isLoggedIn.value = true
      
      // 设置工厂筛选
      if (department.value === '制剂财务部') {
        searchForm.value.工厂 = '5000'
      } else if (department.value === '制药科技财务部' || department.value === '制药科技制造部') {
        searchForm.value.工厂 = '5300'
      } else {
        searchForm.value.工厂 = ''
      }
      
      // 从后端获取最新的用户设置
      const response = await axios.get(`${API_BASE_URL}/user/settings`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      
      // 更新设置状态
      if (response.data) {
        showCompleted.value = response.data.show_completed
        pageSize.value = response.data.page_size
        emailPush.value = response.data.email_push || false
      }
      
      // 只在这里加载一次数据
      await loadTableData()
    } catch (error) {
      console.error('加载用户设置失败:', error)
      handleLogout()
    }
  }
})

// 检查是否需要触发计算
const checkAndCalculate = (row: MaterialRow) => {
  // 检查7,8,9,10,11列是否都有值
  const requiredFields = [
    row.检测时间QC,
    row.最小批量大小PUR,
    row.舍入值PUR,
    row.计划交货时间PUR,
    row.MRP控制者
  ]
  
  if (requiredFields.every(field => field?.trim())) {
    calculateFields(row)
  }
}

// 计算字段值
const calculateFields = (row: MaterialRow) => {
  // 确保row.物料存在
  if (!row.物料) {
    return
  }
  
  const firstChar = row.物料[0]
  
  // MRP区域计算
  if (row.工厂 === '5000') {
    row.MRP区域 = '5000-1'
  } else if (row.工厂 === '5300') {
    row.MRP区域 = '5300-1'
  } else {
    row.MRP区域 = ''
  }

  // MRP类型计算
  if (firstChar === '4' && row.市场 === '中国') {
    row.MRP类型 = 'ND'
  } else if (firstChar === '5' && row.市场 === '中国') {
    row.MRP类型 = 'ND'
  } else if (firstChar === '5' && row.市场 !== '中国') {
    row.MRP类型 = 'M2'
  } else if (row.物料) {
    row.MRP类型 = 'PD'
  }

  // 批量程序计算
  if (firstChar === '1') {
    row.批量程序 = 'MB'
  } else if (['2', '3'].includes(firstChar)) {
    row.批量程序 = 'WB'
  } else if (firstChar === '4' && row.市场 !== '中国' && row.MRP控制者 !== 'Y01') {
    row.批量程序 = 'FX'
  } else if (row.物料) {
    row.批量程序 = 'EX'
  }

  // 固定批量计算
  row.固定批量 = (row.批量程序 !== 'FX' && row.批量程序 !== '') ? 'NA' : ''

  // 再订货点计算
  row.再订货点 = row.物料 ? 'NA' : ''

  // 安全库存计算
  row.安全库存 = ['4', '5'].includes(firstChar) ? 'NA' : '0'

  // 采购类型计算
  if (row.物料) {
    row.采购类型 = ['1', '2', '3'].includes(firstChar) ? 'F' : 'E'
  }

  // 收货处理时间计算
  const 检测时间 = parseInt(row.检测时间QC || '0')
  if (firstChar === '5') {
    row.收货处理时间 = (检测时间 + 2).toString()
  } else if (firstChar === '4') {
    row.收货处理时间 = '0'
  } else if (firstChar === '1' && row.MRP控制者 !== 'Y01') {
    row.收货处理时间 = (检测时间 + 24).toString()
  } else if (row.物料) {
    row.收货处理时间 = (检测时间 + 4).toString()
  }

  // 计划交货时间计算
  row.计划交货时间 = ['4', '5'].includes(firstChar) ? 'NA' : row.计划交货时间PUR

  // 反冲计算
  if (firstChar === '1') {
    row.反冲 = '2'
  } else if (['2', '4'].includes(firstChar)) {
    row.反冲 = '1'
  } else if (row.物料) {
    row.反冲 = 'NA'
  }

  // 批量输入计算
  row.批量输入 = firstChar === '4' ? '1' : 'NA'

  // 自制生产时间计算
  if (firstChar === '4') {
    row.自制生产时间 = '25'
  } else if (firstChar === '5') {
    row.自制生产时间 = '10'
  } else {
    row.自制生产时间 = 'NA'
  }

  // 策略组计算
  if (firstChar === '4') {
    row.策略组 = '10'
  } else if (firstChar === '5' && row.市场 === '中国') {
    row.策略组 = '11'
  } else if (firstChar === '5') {
    row.策略组 = '50'
  } else {
    row.策略组 = 'NA'
  }

  // 综合MRP计算
  row.综合MRP = (firstChar === '5' && row.市场 === '中国') ? '2' : 'NA'

  // 消耗模式计算
  if (firstChar === '5' && row.市场 === '中国') {
    row.消耗模式 = '2'
  } else if (firstChar === '5') {
    row.消耗模式 = '1'
  } else {
    row.消耗模式 = 'NA'
  }

  // 向前/向后消耗期间计算
  if (firstChar === '5' && row.市场 === '中国') {
    row.向后跨期期间 = '30'
    row.向后跨期时间 = '30'
  } else if (firstChar === '5') {
    row.向后跨期期间 = '999'
    row.向后跨期时间 = '999'
  } else {
    row.向后跨期期间 = 'NA'
    row.向后跨期时间 = 'NA'
  }

  // 独立/集中计算
  row.独立集中 = firstChar === '5' ? 'NA' : '2'

  // 计划时间界计算
  if (firstChar === '5' && row.市场 === '中国') {
    row.计划时间界 = '1'
  } else if (firstChar === '5') {
    row.计划时间界 = '60'
  } else {
    row.计划时间界 = 'NA'
  }

  // 生产调度员计算
  row.生产评估 = ['4', '5'].includes(firstChar) ? row.MRP控制者 : 'NA'

  // 生产计划参数文件计算
  row.生产计划 = ['4', '5'].includes(firstChar) ? 'ZJ01' : 'NA'

  // 批量大小和舍入值计算
  row.批量大小 = row.最小批量大小PUR
  row.舍入值 = row.舍入值PUR

  // 更新数据库
  updateCalculatedFields(row)
}

// 更新数据库中的计算字段
const updateCalculatedFields = async (row: MaterialRow) => {
  try {
    const calculatedFields = {
      MRP类型: row.MRP类型,
      批量程序: row.批量程序,
      固定批量: row.固定批量,
      再订货点: row.再订货点,
      安全库存: row.安全库存,
      采购类型: row.采购类型,
      收货处理时间: row.收货处理时间,
      计划交货时间: row.计划交货时间,
      MRP区域: row.MRP区域,
      反冲: row.反冲,
      批量输入: row.批量输入,
      自制生产时间: row.自制生产时间,
      策略组: row.策略组,
      综合MRP: row.综合MRP,
      消耗模式: row.消耗模式,
      向后跨期期间: row.向后跨期期间,
      向后跨期时间: row.向后跨期时间,
      独立集中: row.独立集中,
      计划时间界: row.计划时间界,
      生产评估: row.生产评估,
      生产计划: row.生产计划,
      批量大小: row.批量大小,
      舍入值: row.舍入值
    }

    await axios.put(
      `${API_BASE_URL}/materials/${encodeURIComponent(row.物料)}/calculated-fields`,
      calculatedFields,
      {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      }
    )
  } catch (error) {
    console.error('更新计算字段失败:', error)
    alert('更新计算字段失败')
  }
}

// 设置相关的状态
const showSettings = ref(false)
const showCompleted = ref(false)

// 用户管理相关的状态
const showUserManagement = ref(false)
const users = ref<Array<{username: string, department: string}>>([])

// 打开设置对话框
const openSettings = () => {
  showSettings.value = true
}

// 加载用户设置
const loadUserSettings = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/user/settings`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
    })
    showCompleted.value = response.data.show_completed
    pageSize.value = response.data.page_size
    emailPush.value = response.data.email_push || false
  } catch (error) {
    console.error('加载用户设置失败:', error)
  }
}

// 修改保存设置函数
const handleSettingsChange = async () => {
  try {
    // 保存设置到服务器
    await axios.post(`${API_BASE_URL}/user/settings`, {
      show_completed: showCompleted.value,
      page_size: pageSize.value,
      email_push: emailPush.value
    }, {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
    })
    
    // 重新加载数据
    currentPage.value = 1
    
    // 确保工厂筛选不会被重置
    if (department.value === '制剂财务部') {
      searchForm.value.工厂 = '5000'
    } else if (department.value === '制药科技财务部' || department.value === '制药科技制造部') {
      searchForm.value.工厂 = '5300'
    }
    
    await loadTableData()
  } catch (error) {
    console.error('保存设置失败:', error)
    alert('保存设置失败')
  }
}

// 修改设置对话框，添加关闭按钮的处理
const closeSettings = () => {
  showSettings.value = false
}

// 打开用户管理
const openUserManagement = async () => {
  showUserManagement.value = true
  await loadUsers()
}

// 加载用户列表
const loadUsers = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/users`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
    })
    users.value = response.data
  } catch (error) {
    console.error('加载用户列表失败:', error)
  }
}

// 重置用户密码
const resetPassword = async (username: string) => {  // 添加 username 参数
  
  try {
    await axios.post(`${API_BASE_URL}/users/${username}/reset-password`, {}, {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
    })
    alert('密码重置成功')
  } catch (error: any) {
    console.error('重置密码失败:', error)
    alert('重置密码失败')
  }
}

// 添加用户状态
const user = ref<{
  username: string;
  department: string;
  need_change_password: boolean;
} | null>(null)

// 添加搜索表单状态
const searchForm = ref({
  物料: '',
  物料描述: '',
  物料组: '',
  工厂: ''  // 添加工厂字段
})

// 添加防抖函数
const _debounce = (fn: Function, delay: number) => {
  let timer: number | null = null
  return (...args: any[]) => {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => {
      fn(...args)
      timer = null
    }, delay)
  }
}

// 搜索处理函数
const handleSearch = debounce(async () => {
  try {
    console.log('handleSearch - isGuest:', isGuest.value, 'department:', department.value)
    
    // 重置到第一页
    currentPage.value = 1
    
    // 构建搜索参数
    const params: SearchParams = {
      page: currentPage.value,
      page_size: pageSize.value,
      物料: searchForm.value.物料 || undefined,
      物料描述: searchForm.value.物料描述 || undefined,
      物料组: searchForm.value.物料组 || undefined,
      工厂: searchForm.value.工厂 || undefined,
      show_completed: showCompleted.value
    }
    
    // 如果是游客，添加游客姓名参数
    if (isGuest.value) {
      params.游客姓名 = username.value
      console.log('添加游客参数:', username.value)
    }
    
    console.log('搜索请求参数:', params)
    console.log('搜索请求头:', isGuest.value ? '无token' : '有token')
    
    // 发送请求
    const response = await axios.get(`${API_BASE_URL}/materials`, {
      params: params,
      headers: isGuest.value ? {} : {
        Authorization: `Bearer ${localStorage.getItem('token')}`
      }
    })
    
    console.log('搜索响应状态:', response.status)
    console.log('搜索响应数据条数:', response.data.items.length)
    console.log('后端返回的is_guest:', response.data.is_guest)
    
    // 更新表格数据
    tableData.value = response.data.items
    totalItems.value = response.data.total
    totalPages.value = response.data.total_pages
    
  } catch (error) {
    console.error('搜索失败:', error)
    alert('搜索失败，请重试')
  }
}, 300)  // 300ms的防抖延迟

// 新用户表单状态
const newUser = ref({
  username: '',
  department: '',
  email: ''
})

// 添加用户函数
const addUser = async () => {
  // 表单验证
  if (!newUser.value.username || !newUser.value.department) {
    alert('请填写用户名和部门')
    return
  }

  try {
    await axios.post(
      `${API_BASE_URL}/users`, 
      newUser.value,
      {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      }
    )
    
    // 清空表单
    newUser.value = {
      username: '',
      department: '',
      email: ''
    }
    
    // 重新加载用户列表
    await loadUsers()
    alert('添加用户成功')
  } catch (error: any) {
    if (error.response?.status === 409) {
      alert('用户名已存在')
    } else {
      alert('添加用户失败')
    }
  }
}

// 打开修改密码对话框
const openChangePasswordModal = () => {
  showChangePassword.value = true
  changePasswordForm.value = {
    newPassword: '',
    confirmPassword: ''
  }
}

// 关闭修改密码对话框
const closeChangePasswordModal = () => {
  showChangePassword.value = false
}

// 系统设置相关状态
const showSystemSettings = ref(false)
const systemSettings = ref({
  dingTalkUrl: '',
  keywords: [],
  smtpServer: '',   // 添加这些 SMTP 相关字段
  smtpPort: 25,
  smtpUser: '',
  smtpPassword: '',
  pushEnabled: true,
  pushTime: '09:00'
})

// 添加关键词相关状态
const keywordsText = ref('')

// 修改打开系统设置对话框函数
const openSystemSettings = async () => {
  try {
    // 获取当前设置
    const response = await axios.get(`${API_BASE_URL}/system/settings`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
    })
    
    // 更新所有设置字段
    systemSettings.value = {
      dingTalkUrl: response.data.dingTalkUrl || '',
      keywords: response.data.keywords || [],
      smtpServer: response.data.smtpServer || '',
      smtpPort: response.data.smtpPort || 25,
      smtpUser: response.data.smtpUser || '',
      smtpPassword: response.data.smtpPassword || '',
      pushEnabled: response.data.pushEnabled ?? true,
      pushTime: response.data.pushTime || '09:00'
    }
    
    keywordsText.value = response.data.keywords.join('\n')
    showSystemSettings.value = true
  } catch (error) {
    console.error('获取系统设置失败:', error)
    alert('获取系统设置失败')
  }
}

// 修改保存系统设置函数
const saveSystemSettings = async () => {
  try {
    const keywords = keywordsText.value
      .split('\n')
      .map(k => k.trim())
      .filter(k => k)
    
    await axios.post(
      `${API_BASE_URL}/system/settings`,
      {
        dingTalkUrl: systemSettings.value.dingTalkUrl,
        keywords: keywords,
        smtpServer: systemSettings.value.smtpServer,
        smtpPort: systemSettings.value.smtpPort,
        smtpUser: systemSettings.value.smtpUser,
        smtpPassword: systemSettings.value.smtpPassword,
        pushEnabled: systemSettings.value.pushEnabled,
        pushTime: systemSettings.value.pushTime
      },
      {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      }
    )
    alert('系统设置保存成功')
    showSystemSettings.value = false
  } catch (error) {
    console.error('保存系统设置失败:', error)
    alert('保存系统设置失败')
  }
}

// 发送物料状态统计通知
const sendStatusNotification = async () => {
  try {
    // 获取物料状态统计
    const response = await axios.get(
      `${API_BASE_URL}/materials/status`,
      {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      }
    )
    
    // 发送钉钉通知
    const notifyResponse = await axios.post(
      `${API_BASE_URL}/notify/status`,
      response.data,
      {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      }
    )
    
    if (notifyResponse.data.message) {
      alert('推送成功')
    }
  } catch (error) {
    console.error('推送失败:', error)
    alert('推送失败，请检查钉钉机器人配置')
  }
}

// 关闭系统设置对话框
const closeSystemSettings = () => {
  showSystemSettings.value = false
}

// 添加邮箱设置相关状态
const showEmailSettings = ref(false)
const emailForm = ref({
  email: ''
})

// 打开邮箱设置对话框
const openEmailSettings = async () => {
  try {
    // 获取当前用户邮箱
    const response = await axios.get(`${API_BASE_URL}/user/email`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
    })
    emailForm.value.email = response.data.email || ''
    showEmailSettings.value = true
  } catch (error) {
    console.error('获取邮箱设置失败:', error)
    alert('获取邮箱设置失败')
  }
}

// 保存邮箱设置
const saveEmailSettings = async () => {
  try {
    await axios.put(
      `${API_BASE_URL}/user/email`,
      { email: emailForm.value.email },
      { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } }
    )
    showEmailSettings.value = false
    alert('邮箱设置已保存')
  } catch (error) {
    console.error('保存邮箱设置失败:', error)
    alert('保存邮箱设置失败')
  }
}

// 导出配置
const exportSettings = async () => {
  try {
    const response = await axios.get(
      `${API_BASE_URL}/system/settings/export`,
      {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
        responseType: 'blob'
      }
    )
    
    // 从响应头获取文件名
    const filename = response.headers['content-disposition']?.split('filename=')[1]?.replace(/"/g, '') || 'system_settings.toml'
    
    // 创建下载链接
    const blob = new Blob([response.data], { type: 'application/toml' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('导出配置失败:', error)
    alert('导出配置失败')
  }
}

// 导入配置
const importSettings = async (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  
  // 检查文件类型
  if (!file.name.endsWith('.toml')) {
    alert('请选择 .toml 格式的配置文件')
    input.value = ''
    return
  }
  
  try {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await axios.post(
      `${API_BASE_URL}/system/settings/import`,
      formData,
      {
        headers: { 
          Authorization: `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'multipart/form-data'
        }
      }
    )
    
    alert('配置导入成功')
    // 重新加载系统设置
    await openSystemSettings()
  } catch (error: any) {
    console.error('导入配置失败:', error)
    if (error.response?.data?.detail) {
      alert(`导入失败: ${error.response.data.detail}`)
    } else {
      alert('导入配置失败，请检查文件格式')
    }
  }
  
  // 清空文件输入
  input.value = ''
}

// 添加工厂筛选逻辑
const getFactoryFilter = computed(() => {
  switch (department.value) {
    case '制剂财务部':
      return '5000'
    case '制药科技财务部':
    case '制药科技制造部':
      return '5300'
    default:
      return ''
  }
})

// 处理游客登录
const handleGuestLogin = async () => {
  if (!guestForm.value.applicant) {
    alert('请输入申请人姓名')
    return
  }
  
  try {
    console.log('游客登录前 - isGuest:', isGuest.value)
    
    // 设置游客默认显示15条记录
    pageSize.value = 15
    currentPage.value = 1
    
    const response = await axios.get(`${API_BASE_URL}/materials`, {
      params: {
        游客姓名: guestForm.value.applicant,
        page: currentPage.value,
        page_size: pageSize.value
      }
    })
    
    console.log('游客登录响应:', response.data)
    
    if (response.data.items.length > 0) {
      // 先设置游客标识，再设置其他状态
      isGuest.value = true
      isLoggedIn.value = true
      username.value = guestForm.value.applicant
      department.value = '游客'
      showGuestDialog.value = false
      
      console.log('游客登录后 - isGuest:', isGuest.value, 'department:', department.value)
      
      // 更新表格数据，直接使用后端返回的数据
      tableData.value = response.data.items
      totalItems.value = response.data.total
      totalPages.value = response.data.total_pages
    } else {
      alert('没有找到相关物料信息')
    }
  } catch (error) {
    console.error('游客登录失败:', error)
    alert('游客登录失败')
  }
}

// 计算财务状态
const getFinanceStatus = (row: MaterialRow) => {
  return row.标准价格 ? '已完成' : '未完成'
}

// 计算MRP状态
const getMRPStatus = (row: MaterialRow) => {
  const requiredFields = [
    row.MRP控制者,
    row.最小批量大小PUR,
    row.舍入值PUR,
    row.计划交货时间PUR,
    row.检测时间QC
  ]
  return requiredFields.every(field => field?.trim()) ? '已完成' : '未完成'
}

// 计算完成状态
const getCompletionStatus = (row: MaterialRow) => {
  return row.完成时间 ? '已完成' : '未完成'
}

// 获取状态单元格的样式
const getStatusStyle = (status: string) => {
  return {
    color: status === '已完成' ? '#4CAF50' : '#FF5722',
    fontWeight: 'bold'
  }
}

// 添加游客视图的计算状态
const calculateGuestStatus = (row: MaterialRow) => {
  return {
    财务完成状态: row.标准价格 ? '已完成' : '未完成',
    MRP完成状态: (row.MRP控制者 && row.最小批量大小PUR && row.舍入值PUR && 
                row.计划交货时间PUR && row.检测时间QC) ? '已完成' : '未完成',
    完成状态: row.完成时间 ? '已完成' : '未完成'
  }
}
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  background-attachment: fixed;
  padding: 20px;
}

.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: rgba(0, 0, 0, 0.4); /* 添加半透明遮罩 */
}

.login-form {
  background: rgba(255, 255, 255, 0.95); /* 增加表单背景透明度 */
  padding: 30px;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px); /* 添加毛玻璃效果 */
  width: 320px;
}

.login-form input {
  display: block;
  width: 100%;
  margin: 10px 0;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.user-info {
  margin-bottom: 20px;
  display: flex;
  gap: 20px;
  align-items: center;
  background-color: rgba(255, 255, 255, 0.9);
  padding: 10px 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.user-info button {
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
  background-color: #4CAF50;
  color: white;
}

.user-info button:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

.user-info button:active {
  transform: translateY(1px);
}

/* 添加导出按钮特殊样式 */
.user-info button:last-child {
  background-color: #2196F3;
}

.actions {
  display: none;
}

button {
  padding: 8px 16px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

button:hover {
  background-color: #45a049;
}

.table-container {
  overflow-x: auto;
  max-width: 100%;
}

.table-wrapper {
  margin-top: 20px;
  overflow-x: auto;  /* 允许表格横向滚动 */
}

table {
  border-collapse: collapse;
  width: max-content;  /* 表格宽度根据内容自动调整 */
  min-width: 100%;    /* 但不小于容器宽度 */
}

th, td {
  padding: 8px;
  text-align: left;
  border: 1px solid #ddd;
  white-space: nowrap;  /* 防止内容换行 */
  width: 1px;          /* 让列宽自动适应内容 */
}

th {
  background-color: #f4f4f4;
  font-weight: bold;
  position: sticky;
  top: 0;
  z-index: 1;
}

th.editable {
  background-color: #e8f5e9;  /* 可编辑列的表头背景色 */
}

tr:nth-child(even) {
  background-color: #f9f9f9;
}

tr:hover {
  background-color: #f5f5f5;
}

/* 输入框样式 */
input {
  width: 100%;
  padding: 4px;
  border: none;
  background: transparent;
}

input:focus {
  outline: 2px solid #4CAF50;
  background: white;
}

/* 添加下拉框样式 */
select {
  width: 100%;
  padding: 4px;
  border: none;
  background: transparent;
  cursor: pointer;
}

select:focus {
  outline: 2px solid #4CAF50;
  background: white;
}

/* 可编辑单元格的样式 */
td:has(input), td:has(select) {
  background-color: rgba(76, 175, 80, 0.05);
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 20px;
  gap: 20px;
}

.page-info {
  font-size: 14px;
  color: #666;
}

.pagination button {
  padding: 6px 12px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.pagination button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.pagination button:hover:not(:disabled) {
  background-color: #45a049;
}

.login-form h1 {
  text-align: center;
  color: #333;
  margin-bottom: 20px;
  font-size: 24px;
}

.login-form h2 {
  text-align: center;
  color: #666;
  margin-bottom: 20px;
  font-size: 16px;
  line-height: 1.4;
}

.main-content {
  background-color: rgba(255, 255, 255, 0.95);
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
  margin: 20px auto;
  max-width: 95%;
}

/* 截断单元格样式 */
.truncate-cell {
  max-width: 300px;  /* 约20个中文字符的宽度 */
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 确保其他单元格样式不变 */
th, td {
  padding: 8px;
  text-align: left;
  border: 1px solid #ddd;
  white-space: nowrap;
  width: 1px;
}

.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 20px;
  border-radius: 8px;
  min-width: 400px;
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
}

.form-group input {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.modal-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}

.user-list {
  max-height: 400px;
  overflow-y: auto;
}

.user-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  border-bottom: 1px solid #eee;
}

.user-item button {
  padding: 4px 8px;
  font-size: 12px;
}

.add-user-form {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 4px;
}

.add-user-form h3 {
  margin-top: 0;
  margin-bottom: 15px;
  color: #2c3e50;
}

.divider {
  height: 1px;
  background-color: #ddd;
  margin: 20px 0;
}

.user-list h3 {
  margin-top: 0;
  margin-bottom: 15px;
  color: #2c3e50;
}

.user-info {
  display: flex;
  gap: 10px;
  align-items: center;
}

.user-tag {
  display: flex;
  align-items: center;
  background: linear-gradient(to right, #e3f2fd, #bbdefb);
  padding: 6px 12px;
  border-radius: 20px;
  box-shadow: 0 2px 4px rgba(33, 150, 243, 0.1);
  border: 1px solid #90caf9;
}

.username {
  font-weight: 600;
  color: #1976d2;
}

.separator {
  margin: 0 6px;
  color: #1976d2;
  font-weight: 600;
}

.department {
  color: #2196f3;
}

.right-buttons {
  margin-left: auto;
  display: flex;
  gap: 10px;
  align-items: center;
}

.file-input-label {
  display: inline-block;
  padding: 6px 12px;
  background-color: #2196F3;
  color: white;
  border-radius: 4px;
  cursor: pointer;
  transition: opacity 0.2s;
}

.file-input-label:hover {
  opacity: 0.9;
}

.file-input-label input[type="file"] {
  display: none;
}

/* 添加搜索区域样式 */
.search-area {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
  background-color: #f5f5f5;
  padding: 15px;
  border-radius: 4px;
}

.search-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.search-item label {
  font-size: 12px;
  color: #666;
}

.search-item input {
  padding: 6px 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  width: 200px;
}

.search-item input:focus {
  outline: none;
  border-color: #4CAF50;
  box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2);
}

.settings-button {
  padding: 6px 12px;
  background-color: #607d8b;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: opacity 0.2s;
}

.settings-button:hover {
  opacity: 0.9;
}

.settings-modal {
  max-width: 400px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  width: auto;
  margin: 0;
}

.form-group input[type="number"] {
  width: 80px;
  padding: 4px 8px;
}

.settings-actions {
  display: flex;
  gap: 10px;
  margin: 20px 0;
}

.export-button, .import-button {
  padding: 8px 16px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.import-button {
  background-color: #2196F3;
}

.export-button:hover, .import-button:hover {
  opacity: 0.9;
}

.login-buttons {
  display: flex;
  gap: 10px;
  justify-content: center;
  margin-top: 20px;
}

.guest-button {
  background-color: #607d8b;
}

.guest-button:hover {
  background-color: #546e7a;
}

.guest-dialog {
  max-width: 400px;
}

/* 添加状态列的样式 */
td[class*="完成状态"] {
  font-weight: bold;
}

td[class*="完成状态"]:contains("已完成") {
  color: #4caf50;
}

td[class*="完成状态"]:contains("未完成") {
  color: #f44336;
}
</style>

