from asyncio.windows_events import NULL
from numpy import NaN
import win32com.client, sys, os
import pandas as pd 
import warnings
import requests
import time
from datetime import datetime

API_BASE_URL = "http://home.dandan.autos:8088"  # 替换为你的 API 地址
API_KEY = "your-api-key-here"  # 替换为你的 API 密钥

def main():
    try:
        # 连接 SAP
        SapGuiAuto = win32com.client.GetObject("SAPGUI")
        if not type(SapGuiAuto) == win32com.client.CDispatch:
            return 
        
        application = SapGuiAuto.GetScriptingEngine
        if not type(application) == win32com.client.CDispatch:
            SapGuiAuto = None
            return 
        
        connection = application.Children(0)
        if not type(connection) == win32com.client.CDispatch:
            application = None
            SapGuiAuto = None
            return
        
        session = connection.Children(0)
        if not type(session) == win32com.client.CDispatch:
            connection = None
            application = None
            SapGuiAuto = None
            return

        # 打开 MM01 事务码
        session.findById("wnd[0]").maximize()
        session.findById("wnd[0]/tbar[0]/okcd").text = "mm01"
        session.findById("wnd[0]").sendVKey(0)

        # 从 API 获取数据并处理
        response = requests.post(
            f"{API_BASE_URL}/api/materials/export",
            json={"api_key": API_KEY}
        )

        data = response.json()
        if data["status"] == "success":
            # 存储成功处理的物料 ID
            completed_materials = []
            
            for material in data["data"]:
                try:
                    # 处理单个物料
                    option(session, material)
                    
                    # 记录成功处理的物料
                    completed_materials.append(material['物料'])
                    print(f"成功处理物料: {material['物料']}")
                    time.sleep(1)  # 添加延时避免处理过快
                    
                except Exception as e:
                    print(f"处理物料 {material['物料']} 时出错: {str(e)}")
                    continue
            
            # 批量更新完成时间
            if completed_materials:
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/api/materials/complete",
                        json={
                            "api_key": API_KEY,
                            "material_ids": completed_materials,
                            "complete_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                    )
                    
                    if response.status_code == 200:
                        print(f"成功更新 {len(completed_materials)} 个物料的完成时间")
                    else:
                        print(f"更新完成时间失败: {response.text}")
                        
                except Exception as e:
                    print(f"更新完成时间时出错: {str(e)}")

    except Exception as e:
        print(f"发生错误: {str(e)}")
        print(sys.exc_info()[0])
    
    finally:
        session = None
        connection = None
        application = None
        SapGuiAuto = None

def option(session, data):
    # 处理 NA 值为空字符串
    def handle_na(value):
        if value == 'NA' or value == 'na' or value == 'N/A' or value == 'n/a':
            return ''
        return value

    # 使用 API 返回的数据替代 Excel 数据
    matnr = handle_na(data['物料'])
    werks = handle_na(data['工厂'])
    dismm = handle_na(data['MRP类型'])
    fxhor = handle_na(data['计划时间界'])
    dispo = handle_na(data['MRP控制者'])
    disls = handle_na(data['批量程序'])
    bstmi = handle_na(data['批量大小'])
    bstfe = handle_na(data['固定批量'])
    bstrf = handle_na(data['舍入值'])
    beskz = handle_na(data['采购类型'])
    kzech = handle_na(data['批量输入'])
    rgekz = handle_na(data['反冲'])
    dzeit = handle_na(data['自制生产时间'])
    plifz = handle_na(data['计划交货时间'])
    webaz = handle_na(data['收货处理时间'])
    strgr = handle_na(data['策略组'])
    vrmod = handle_na(data['消耗模式'])
    vint1 = handle_na(data['向后跨期期间'])
    vint2 = handle_na(data['向前消耗期间'] if '向前消耗期间' in data else data['向后跨期时间'])
    miskz = handle_na(data['综合MRP'])
    sbdkz = handle_na(data['独立集中'])
    fevor = handle_na(data['生产评估'])
    bklas = handle_na(data['评估分类'])
    price = handle_na(data['标准价格'])
    losgr = handle_na(data['成本核算批量'])
    eklas = handle_na(data['销售订单库存'])
    mmsta = handle_na(data['物料状态'])
    berad = handle_na(data['MRP区域'])

    first_digit = data['物料'][0]
    if first_digit == '1':
        mType = 'Z001'
    elif first_digit == '2':
        mType = 'Z002'
    elif first_digit == '4':
        mType = 'Z003'
    elif first_digit == '5':
        mType = 'Z004'
    else:
        mType = ''

    session.findById("wnd[0]").maximize()
    session.findById("wnd[0]/usr/ctxtRMMG1-MATNR").text = matnr
    session.findById("wnd[0]/usr/ctxtRMMG1-MATNR").caretPosition = 6
    session.findById("wnd[0]").sendVKey(0)
    session.findById("wnd[0]").sendVKey(0)
    session.findById("wnd[1]/tbar[0]/btn[19]").press()
    if dispo != 'NA' and dispo!= '' and dispo != None:
        session.findById("wnd[1]/usr/tblSAPLMGMMTC_VIEW").getAbsoluteRow(12).selected = -1
        session.findById("wnd[1]/usr/tblSAPLMGMMTC_VIEW").getAbsoluteRow(13).selected = -1
        session.findById("wnd[1]/usr/tblSAPLMGMMTC_VIEW").getAbsoluteRow(14).selected = -1
        session.findById("wnd[1]/usr/tblSAPLMGMMTC_VIEW").getAbsoluteRow(15).selected = -1
    session.findById("wnd[1]/usr/tblSAPLMGMMTC_VIEW/txtMSICHTAUSW-DYTXT[0,15]").setFocus()
    session.findById("wnd[1]/usr/tblSAPLMGMMTC_VIEW/txtMSICHTAUSW-DYTXT[0,15]").caretPosition = 0
    session.findById("wnd[1]/usr/tblSAPLMGMMTC_VIEW").verticalScrollbar.position = 3
    session.findById("wnd[1]/usr/tblSAPLMGMMTC_VIEW").verticalScrollbar.position = 6
    session.findById("wnd[1]/usr/tblSAPLMGMMTC_VIEW").verticalScrollbar.position = 9
    session.findById("wnd[1]/usr/tblSAPLMGMMTC_VIEW").verticalScrollbar.position = 12
    session.findById("wnd[1]/usr/tblSAPLMGMMTC_VIEW").getAbsoluteRow(23).selected = -1
    session.findById("wnd[1]/usr/tblSAPLMGMMTC_VIEW").getAbsoluteRow(24).selected = -1
    session.findById("wnd[1]/usr/tblSAPLMGMMTC_VIEW").getAbsoluteRow(25).selected = -1
    session.findById("wnd[1]/usr/tblSAPLMGMMTC_VIEW").getAbsoluteRow(26).selected = -1
    session.findById("wnd[1]/usr/tblSAPLMGMMTC_VIEW/txtMSICHTAUSW-DYTXT[0,15]").setFocus()
    session.findById("wnd[1]/usr/tblSAPLMGMMTC_VIEW/txtMSICHTAUSW-DYTXT[0,15]").caretPosition = 0
    session.findById("wnd[1]/tbar[0]/btn[0]").press()
    session.findById("wnd[1]/usr/ctxtRMMG1-WERKS").text = werks
    session.findById("wnd[1]/tbar[0]/btn[0]").press()

# MRP视图相关
    if dispo != 'NA' and dispo!= '' and dispo != None:
        session.findById("wnd[0]/usr/tabsTABSPR1/tabpSP13/ssubTABFRA1:SAPLMGMM:2000/subSUB3:SAPLMGD1:2482/ctxtMARC-DISMM").text = dismm
        session.findById("wnd[0]/usr/tabsTABSPR1/tabpSP13/ssubTABFRA1:SAPLMGMM:2000/subSUB3:SAPLMGD1:2482/txtMARC-FXHOR").text = fxhor
        session.findById("wnd[0]/usr/tabsTABSPR1/tabpSP13/ssubTABFRA1:SAPLMGMM:2000/subSUB3:SAPLMGD1:2482/ctxtMARC-DISPO").text = dispo
        session.findById("wnd[0]/usr/tabsTABSPR1/tabpSP13/ssubTABFRA1:SAPLMGMM:2000/subSUB4:SAPLMGD1:2483/ctxtMARC-DISLS").text = disls
    # 最小批量
        session.findById("wnd[0]/usr/tabsTABSPR1/tabpSP13/ssubTABFRA1:SAPLMGMM:2000/subSUB4:SAPLMGD1:2483/txtMARC-BSTMI").text = bstmi
    # 固定批量
        session.findById("wnd[0]/usr/tabsTABSPR1/tabpSP13/ssubTABFRA1:SAPLMGMM:2000/subSUB4:SAPLMGD1:2483/txtMARC-BSTFE").text = bstfe
    # 舍入值
        session.findById("wnd[0]/usr/tabsTABSPR1/tabpSP13/ssubTABFRA1:SAPLMGMM:2000/subSUB4:SAPLMGD1:2483/txtMARC-BSTRF").text = bstrf
        session.findById("wnd[0]/usr/tabsTABSPR1/tabpSP13/ssubTABFRA1:SAPLMGMM:2000/subSUB4:SAPLMGD1:2483/txtMARC-BSTRF").setFocus()
        session.findById("wnd[0]/usr/tabsTABSPR1/tabpSP13/ssubTABFRA1:SAPLMGMM:2000/subSUB4:SAPLMGD1:2483/txtMARC-BSTRF").caretPosition = 1
        session.findById("wnd[0]/usr/tabsTABSPR1/tabpSP13/ssubTABFRA1:SAPLMGMM:2000/subSUB5:SAPLMGD1:2480/btnMARC_DIBER_PUSH").press()

        session.findById("wnd[1]/usr/tblSAPLMD_MGD1TC_LOOPBERID/ctxtSMDMA-BERID[0,0]").text = berad
        session.findById("wnd[1]/usr/tblSAPLMD_MGD1TC_LOOPBERID/ctxtSMDMA-DISPR[2,0]").text = "NMRP"
        session.findById("wnd[1]/usr/tblSAPLMD_MGD1TC_LOOPBERID/ctxtSMDMA-DISPR[2,0]").setFocus()
        session.findById("wnd[1]/usr/tblSAPLMD_MGD1TC_LOOPBERID/ctxtSMDMA-DISPR[2,0]").caretPosition = 4
        session.findById("wnd[1]/tbar[0]/btn[7]").press()
        session.findById("wnd[0]/usr/tabsTABSPR1/tabpSP14").select()
    # 采购类型
        if session.findById("wnd[0]/usr/tabsTABSPR1/tabpSP14/ssubTABFRA1:SAPLMGMM:2000/subSUB2:SAPLMGD1:2484/ctxtMARC-BESKZ").changeable:
            session.findById("wnd[0]/usr/tabsTABSPR1/tabpSP14/ssubTABFRA1:SAPLMGMM:2000/subSUB2:SAPLMGD1:2484/ctxtMARC-BESKZ").text = beskz
    # 批量输入
        session.findById("wnd[0]/usr/tabsTABSPR1/tabpSP14/ssubTABFRA1:SAPLMGMM:2000/subSUB2:SAPLMGD1:2484/ctxtMARC-KZECH").text = kzech
    # 反冲
        session.findById("wnd[0]/usr/tabsTABSPR1/tabpSP14/ssubTABFRA1:SAPLMGMM:2000/subSUB2:SAPLMGD1:2484/ctxtMARC-RGEKZ").text = rgekz
    # 自制生产
        if dzeit != '' and dzeit != 'NA':
            session.findById("wnd[0]/usr/tabsTABSPR1/tabpSP14/ssubTABFRA1:SAPLMGMM:2000/subSUB3:SAPLMGD1:2485/txtMARC-DZEIT").text = dzeit
    # 计划交货时间
        session.findById("wnd[0]/usr/tabsTABSPR1/tabpSP14/ssubTABFRA1:SAPLMGMM:2000/subSUB3:SAPLMGD1:2485/txtMARC-PLIFZ").text = plifz
    # 收货处理时间
        session.findById("wnd[0]/usr/tabsTABSPR1/tabpSP14/ssubTABFRA1:SAPLMGMM:2000/subSUB3:SAPLMGD1:2485/txtMARC-WEBAZ").text = webaz
    # 计划边际码
        session.findById("wnd[0]/usr/tabsTABSPR1/tabpSP14/ssubTABFRA1:SAPLMGMM:2000/subSUB3:SAPLMGD1:2485/ctxtMARC-FHORI").text = "000"
        session.findById("wnd[0]/usr/tabsTABSPR1/tabpSP14/ssubTABFRA1:SAPLMGMM:2000/subSUB2:SAPLMGD1:2484/ctxtMARC-KZECH").setFocus()
        session.findById("wnd[0]/usr/tabsTABSPR1/tabpSP14/ssubTABFRA1:SAPLMGMM:2000/subSUB2:SAPLMGD1:2484/ctxtMARC-KZECH").caretPosition = 1
        session.findById("wnd[0]/usr/tabsTABSPR1/tabpSP15").select()
    # 可用性检查
        session.findById("wnd[0]/usr/tabsTABSPR1/tabpSP15/ssubTABFRA1:SAPLMGMM:2000/subSUB4:SAPLMGD1:2493/ctxtMARC-MTVFP").text = "02"
    # 策略组
        session.findById("wnd[0]/usr/tabsTABSPR1/tabpSP15/ssubTABFRA1:SAPLMGMM:2000/subSUB3:SAPLMGD1:2492/ctxtMARC-STRGR").text = strgr
    # 消耗模式
        session.findById("wnd[0]/usr/tabsTABSPR1/tabpSP15/ssubTABFRA1:SAPLMGMM:2000/subSUB3:SAPLMGD1:2492/ctxtMARC-VRMOD").text = vrmod
    # 逆向消耗期间
        session.findById("wnd[0]/usr/tabsTABSPR1/tabpSP15/ssubTABFRA1:SAPLMGMM:2000/subSUB3:SAPLMGD1:2492/txtMARC-VINT1").text = vint1
    # 向前消耗区间
        session.findById("wnd[0]/usr/tabsTABSPR1/tabpSP15/ssubTABFRA1:SAPLMGMM:2000/subSUB3:SAPLMGD1:2492/txtMARC-VINT2").text = vint2
    # 综合MRP
        session.findById("wnd[0]/usr/tabsTABSPR1/tabpSP15/ssubTABFRA1:SAPLMGMM:2000/subSUB3:SAPLMGD1:2492/ctxtMARC-MISKZ").text = miskz
        session.findById("wnd[0]/usr/tabsTABSPR1/tabpSP15/ssubTABFRA1:SAPLMGMM:2000/subSUB3:SAPLMGD1:2492/ctxtMARC-MISKZ").setFocus()
        session.findById("wnd[0]/usr/tabsTABSPR1/tabpSP15/ssubTABFRA1:SAPLMGMM:2000/subSUB3:SAPLMGD1:2492/ctxtMARC-MISKZ").caretPosition = 1
        session.findById("wnd[0]/usr/tabsTABSPR1/tabpSP16").select()
    # 独立集中
        session.findById("wnd[0]/usr/tabsTABSPR1/tabpSP16/ssubTABFRA1:SAPLMGMM:2000/subSUB2:SAPLMGD1:2495/ctxtMARC-SBDKZ").text = sbdkz

    # 工作计划
        if fevor != '': 
            session.findById("wnd[0]/usr/tabsTABSPR1/tabpSP20").select()
            session.findById("wnd[0]/usr/tabsTABSPR1/tabpSP20/ssubTABFRA1:SAPLMGMM:2000/subSUB2:SAPLMGD1:2601/ctxtMARC-FEVOR").text = fevor
            session.findById("wnd[0]/usr/tabsTABSPR1/tabpSP20/ssubTABFRA1:SAPLMGMM:2000/subSUB2:SAPLMGD1:2601/ctxtMARC-SFCPF").text = "ZJ01"
            session.findById("wnd[0]/usr/tabsTABSPR1/tabpSP20/ssubTABFRA1:SAPLMGMM:2000/subSUB2:SAPLMGD1:2601/ctxtMARC-SFCPF").setFocus()
            session.findById("wnd[0]/usr/tabsTABSPR1/tabpSP20/ssubTABFRA1:SAPLMGMM:2000/subSUB2:SAPLMGD1:2601/ctxtMARC-SFCPF").caretPosition = 4
        session.findById("wnd[0]").sendVKey(0)
# 财务相关
    
    session.findById("wnd[0]/usr/tabsTABSPR1/tabpSP27/ssubTABFRA1:SAPLMGMM:2000/subSUB2:SAPLMGD1:2800/subSUB1:SAPLCKMMAT:0010/tabsTABS/tabpPPLF/ssubSUBML:SAPLCKMMAT:0100/ctxtMBEW-BKLAS").text = bklas
    if mType == 'Z004':
        session.findById("wnd[0]/usr/tabsTABSPR1/tabpSP27/ssubTABFRA1:SAPLMGMM:2000/subSUB2:SAPLMGD1:2800/subSUB1:SAPLCKMMAT:0010/tabsTABS/tabpPPLF/ssubSUBML:SAPLCKMMAT:0100/ctxtMBEW-EKLAS").text = eklas
        session.findById("wnd[0]/usr/tabsTABSPR1/tabpSP27/ssubTABFRA1:SAPLMGMM:2000/subSUB2:SAPLMGD1:2800/subSUB1:SAPLCKMMAT:0010/tabsTABS/tabpPPLF/ssubSUBML:SAPLCKMMAT:0100/ctxtMBEW-EKLAS").setFocus()
        session.findById("wnd[0]/usr/tabsTABSPR1/tabpSP27/ssubTABFRA1:SAPLMGMM:2000/subSUB2:SAPLMGD1:2800/subSUB1:SAPLCKMMAT:0010/tabsTABS/tabpPPLF/ssubSUBML:SAPLCKMMAT:0100/ctxtMBEW-EKLAS").caretPosition = 4
        session.findById("wnd[0]").sendVKey(0)
        session.findById("wnd[0]").sendVKey(0)
    elif mType == 'Z003':
        session.findById("wnd[0]").sendVKey(0)
        session.findById("wnd[0]").sendVKey(0)
    else:
        session.findById("wnd[0]/usr/tabsTABSPR1/tabpSP27/ssubTABFRA1:SAPLMGMM:2000/subSUB2:SAPLMGD1:2800/subSUB1:SAPLCKMMAT:0010/tabsTABS/tabpPPLF/ssubSUBML:SAPLCKMMAT:0100/subSUBCURR:SAPLCKMMAT:0200/txtCKMMAT_DISPLAY-STPRS_1").text = price
        session.findById("wnd[0]/usr/tabsTABSPR1/tabpSP27/ssubTABFRA1:SAPLMGMM:2000/subSUB2:SAPLMGD1:2800/subSUB1:SAPLCKMMAT:0010/tabsTABS/tabpPPLF/ssubSUBML:SAPLCKMMAT:0100/subSUBCURR:SAPLCKMMAT:0200/txtCKMMAT_DISPLAY-STPRS_1").setFocus()
        session.findById("wnd[0]/usr/tabsTABSPR1/tabpSP27/ssubTABFRA1:SAPLMGMM:2000/subSUB2:SAPLMGD1:2800/subSUB1:SAPLCKMMAT:0010/tabsTABS/tabpPPLF/ssubSUBML:SAPLCKMMAT:0100/subSUBCURR:SAPLCKMMAT:0200/txtCKMMAT_DISPLAY-STPRS_1").caretPosition = 15
    session.findById("wnd[0]").sendVKey(0)
    session.findById("wnd[0]").sendVKey(0)
    session.findById("wnd[0]").sendVKey(0)
    if mType == 'Z004' or mType == 'Z003':
        session.findById("wnd[0]/usr/tabsTABSPR1/tabpSP29/ssubTABFRA1:SAPLMGMM:2000/subSUB2:SAPLMGD1:2904/ctxtMARC-MMSTA").text = mmsta
    session.findById("wnd[0]/usr/tabsTABSPR1/tabpSP29/ssubTABFRA1:SAPLMGMM:2000/subSUB2:SAPLMGD1:2904/chkMBEW-HKMAT").selected = -1
    session.findById("wnd[0]/usr/tabsTABSPR1/tabpSP29/ssubTABFRA1:SAPLMGMM:2000/subSUB3:SAPLMGD1:2903/txtMARC-LOSGR").text = losgr
    session.findById("wnd[0]/usr/tabsTABSPR1/tabpSP29/ssubTABFRA1:SAPLMGMM:2000/subSUB3:SAPLMGD1:2903/txtMARC-LOSGR").setFocus()
    session.findById("wnd[0]/usr/tabsTABSPR1/tabpSP29/ssubTABFRA1:SAPLMGMM:2000/subSUB3:SAPLMGD1:2903/txtMARC-LOSGR").caretPosition = 5
    session.findById("wnd[0]").sendVKey(0)
    session.findById("wnd[0]").sendVKey(0)
    session.findById("wnd[1]/usr/btnSPOP-OPTION1").press()

# # 保存        
#     session.findById("wnd[0]/tbar[0]/btn[11]").press()


if __name__ == "__main__":
    warnings.filterwarnings('ignore')
    main()

