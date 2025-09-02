from asyncio.windows_events import NULL
from numpy import NaN
import win32com.client, sys, os
import pandas as pd 

excelName = '物料主数据新增清单20240806(2).XLSX'
def main():

    try:
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
        session.findById("wnd[0]").maximize()
        session.findById("wnd[0]/tbar[0]/okcd").text = "mm01"
        session.findById("wnd[0]").sendVKey(0)
        data = pd.read_excel(excelName, keep_default_na=False)

        for num in data.index:
            option(session, data, num)
            
    except:
        print("error")
        print(sys.exc_info()[0])
 
    finally:
        session = None
        connection = None
        application = None
        SapGuiAuto = None

def option(session, data, num):
    matnr = data['物料'][num]
    werks = data['工厂'][num]
    bklas = data['评估分类'][num]
    if data['标准价格'][num] != '':
        price = round(data['标准价格'][num],2)
    if data['成本核算批量'][num] != NULL and data['成本核算批量'][num] != '':
        losgr = data['成本核算批量'][num]
        print(losgr)
    else:
        losgr = 1
    mType = data['MTyp'][num]
    eklas = data['销售订单库存'][num]
    mmsta = data['物料状态'][num]
    session.findById("wnd[0]/usr/ctxtRMMG1-MATNR").text = matnr
    session.findById("wnd[0]/usr/ctxtRMMG1-MATNR").caretPosition = 6
    session.findById("wnd[0]").sendVKey(0)
    # if mType != 'Z002':
    session.findById("wnd[0]").sendVKey(0)
    session.findById("wnd[1]/tbar[0]/btn[19]").press()
    session.findById("wnd[1]/usr/tblSAPLMGMMTC_VIEW").verticalScrollbar.position = 18
    session.findById("wnd[1]/usr/tblSAPLMGMMTC_VIEW").getAbsoluteRow(23).selected = -1
    session.findById("wnd[1]/usr/tblSAPLMGMMTC_VIEW").getAbsoluteRow(24).selected = -1
    session.findById("wnd[1]/usr/tblSAPLMGMMTC_VIEW").getAbsoluteRow(25).selected = -1
    session.findById("wnd[1]/usr/tblSAPLMGMMTC_VIEW").getAbsoluteRow(26).selected = -1
    session.findById("wnd[1]/usr/tblSAPLMGMMTC_VIEW/txtMSICHTAUSW-DYTXT[0,8]").setFocus()
    session.findById("wnd[1]/usr/tblSAPLMGMMTC_VIEW/txtMSICHTAUSW-DYTXT[0,8]").caretPosition = 0
    session.findById("wnd[1]/tbar[0]/btn[0]").press()
    session.findById("wnd[1]/usr/ctxtRMMG1-WERKS").text = werks
    session.findById("wnd[1]/tbar[0]/btn[0]").press()
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
    

if __name__ == "__main__":
    main()
