<template>
  <div class="app-container" :style="bingWallpaperUrl ? { backgroundImage: `url(${bingWallpaperUrl})` } : {}">
    <!-- 登录部分 -->
    <div v-if="!isLoggedIn" class="login-container">
      <div class="login-form">
        <h1>SAP数据收集系统</h1>
        <h2>用户登录</h2>
        <input v-model="loginForm.username" placeholder="用户名" type="text">
        <input v-model="loginForm.password" placeholder="密码" type="password">
        <button @click="handleLogin">登录</button>
      </div>
    </div>

    <!-- 主要内容 -->
    <div v-else class="main-content">
      <div class="user-info">
        <span>用户: {{ username }}</span>
        <span>部门: {{ department }}</span>
        <button @click="handleLogout">退出</button>
      </div>

      <div class="table-container">
        <div class="actions">
          <input v-if="canImport" type="file" @change="handleFileUpload" accept=".xlsx,.xls">
          <button v-if="canExport" @click="exportToExcel">导出Excel</button>
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
                      @change="handleCellChange(index, header, $event)">
                      <option value="">请选择</option>
                      <option v-for="option in mrpControllers" :key="option.value" :value="option.value">
                        {{ option.label }}
                      </option>
                    </select>
                    <input v-else
                      type="text" 
                      v-model="row[header]" 
                      @change="handleCellChange(index, header, $event)"
                      @input="validateInput(index, header, $event)"
                      :placeholder="getPlaceholder(header)"
                    >
                  </template>
                  <template v-else>
                    {{ row[header] }}
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
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import * as XLSX from 'xlsx'
import axios from 'axios'

interface MaterialRow {
  '物料': string;
  '物料描述': string;
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
  [key: string]: string;
}

// 分页相关的状态
const currentPage = ref(1)
const pageSize = ref(15)
const totalPages = ref(0)
const totalItems = ref(0)
const tableData = ref<MaterialRow[]>([])
const headers = [
  '物料', '物料描述', '市场', '备注1', '备注2', '生产厂商', 
  '检测时间QC', '最小批量大小PUR', '舍入值PUR', '计划交货时间PUR', 
  'MRP控制者', 'MRP类型', '批量程序', '固定批量', '再订货点', 
  '安全库存', '批量大小', '舍入值', '采购类型', '收货处理时间', 
  '计划交货时间', 'MRP区域', '反冲', '批量输入', '自制生产时间', 
  '策略组', '综合MRP', '消耗模式', '向后跨期期间', '向后跨期时间', 
  '独立集中', '计划时间界', '生产评估', '生产计划', '新建时间', '完成时间'
]

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

// 登录相关
const isLoggedIn = ref(false)
const username = ref('')
const department = ref('')
const loginForm = ref({
  username: '',
  password: ''
})

// API基础URL
const API_BASE_URL = 'http://localhost:8000'

// 权限控制
const canImport = computed(() => department.value === '信息部')
const canExport = computed(() => department.value === '信息部')

const getEditableColumns = computed(() => {
  switch (department.value) {
    case '运营管理部':
      return ['MRP控制者']
    case '采购部':
      return ['最小批量大小PUR', '舍入值PUR', '计划交货时间PUR']
    case 'QC检测室':
      return ['检测时间QC']
    default:
      return []
  }
})

// 登录处理
const handleLogin = async () => {
  try {
    const response = await axios.post(`${API_BASE_URL}/login`, loginForm.value)
    localStorage.setItem('token', response.data.token)
    username.value = loginForm.value.username
    department.value = response.data.department
    isLoggedIn.value = true
    // 登录成功后加载数据(只需要一次)
    await loadMaterials()
  } catch (error) {
    alert('登录失败')
  }
}

// 退出登录
const handleLogout = () => {
  localStorage.removeItem('token')
  isLoggedIn.value = false
  username.value = ''
  department.value = ''
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
        市场: row.市场?.trim() || null,
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
        完成时间: null
      }))

    if (processedData.length === 0) {
      alert('没有有效的数据需要导入')
      return
    }
    
    try {
      const response = await axios.post(`${API_BASE_URL}/materials`, processedData, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      })
      await loadMaterials() // 重新加载数据以显示最新结果
      alert(response.data.message) // 显示成功导入的数量
    } catch (error: any) {
      if (error.response?.data?.detail?.duplicates) {
        const duplicates = error.response.data.detail.duplicates
        alert(`以下物料编号已存在：\n${duplicates.join('\n')}`)
      } else {
        console.error('保存数据失败:', error)
        alert('保存数据失败')
      }
    }
  }
  reader.readAsBinaryString(file)
}

// 加载物料数据
const loadMaterials = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/materials`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
      params: {
        page: currentPage.value,
        page_size: pageSize.value
      }
    })
    
    tableData.value = response.data.items
    totalItems.value = response.data.total
    totalPages.value = response.data.total_pages
    currentPage.value = response.data.page
  } catch (error) {
    alert('加载数据失败')
  }
}

// 导出Excel
const exportToExcel = async () => {
  if (!canExport.value) {
    alert('没有权限导出数据')
    return
  }

  try {
    // 获取符合条件的数据
    const response = await axios.get(`${API_BASE_URL}/materials/export`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
    })

    if (!response.data || response.data.length === 0) {
      alert('没有可导出的数据')
      return
    }

    // 导出Excel
    const ws = XLSX.utils.json_to_sheet(response.data)
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, 'Materials')
    XLSX.writeFile(wb, 'materials.xlsx')

    // 重新加载数据以更新显示
    await loadMaterials()
    
    alert(`成功导出 ${response.data.length} 条数据`)
  } catch (error: any) {
    console.error('导出失败:', error)
    alert(error.response?.data?.detail || '导出失败')
  }
}

// 单元格数据变更处理
const handleCellChange = async (rowIndex: number, header: string, event: Event) => {
  if (!isEditable(header)) return
  
  const value = header === 'MRP控制者' 
    ? (event.target as HTMLSelectElement).value 
    : (event.target as HTMLInputElement).value
  
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
    
    alert(error.response?.data?.detail || '保存失败')
  }
}

// 页码改变处理函数
const handlePageChange = async (page: number) => {
  currentPage.value = page
  await loadMaterials()
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
      const response = await axios.get(`${API_BASE_URL}/materials`, {
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
      
      // 加载数据
      await loadMaterials()
    } catch (error) {
      // token 无效，清除本地存储
      localStorage.removeItem('token')
      isLoggedIn.value = false
      username.value = ''
      department.value = ''
    }
  }
}

// 修改 onMounted
onMounted(() => {
  getBingWallpaper()
  checkLoginStatus() // 添加登录状态检查
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
  const firstChar = row.物料?.[0]
  
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
  row.安全库存 = ['4', '5'].includes(firstChar) ? 'NA' : ''

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

  // MRP区域计算
  row.MRP区域 = row.物料 ? '5000-1' : ''

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
}

.actions {
  margin-bottom: 20px;
  display: flex;
  gap: 10px;
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
}

table {
  border-collapse: collapse;
  width: 100%;
}

th, td {
  padding: 8px;
  text-align: left;
  border: 1px solid #ddd;
  white-space: nowrap;
  min-width: 120px;
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

/* 可编辑单元格的样式 */
td:has(input), td:has(select) {
  background-color: rgba(76, 175, 80, 0.05);
}

/* 输入错误提示 */
input:invalid {
  border-color: #ff5252;
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
  font-size: 18px;
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
</style>
