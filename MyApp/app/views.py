from app import appbuilder
from flask import render_template, redirect, url_for,flash
from flask_appbuilder import SimpleFormView,ModelView,MultipleView
from flask_appbuilder.baseviews import BaseModelView
from flask_appbuilder.charts.views import GroupByChartView,DirectByChartView
from flask_appbuilder.models.mongoengine.interface import MongoEngineInterface
from flask_babel import lazy_gettext as _
from flask_appbuilder import AppBuilder, BaseView, expose, has_access
from datetime import datetime,timedelta
from .forms import InvoiceNumberForm,SpeicalDayForm,MonthlyCarPlateTextForm,MonthlyCarTimeSlotForm,DayFinancialStatementsSearchForm,TrafficFlowForm
from .models import  InvoiceNumber,YuTsaiLprCashJournal,SpecialDayCollection,MonthlyCarPlateText,MonthlyCarTimeSlot
from flask_appbuilder.actions import action
import time
from xlwt import Workbook,XFStyle,Font
from flask import Response ,make_response,send_file
from werkzeug.datastructures import Headers
from flask_appbuilder.urltools import *
from .widgets import  YuTsaiLprCashJournalWidget,MonthlyCarTimeSlotWidget
from mongoengine.queryset.visitor import Q
from .yuView import YuChartsView


@appbuilder.app.errorhandler(404)  #Application wide 404 error handler
def page_not_found(e):
    return render_template('404.html', base_template=appbuilder.base_template, appbuilder=appbuilder), 404

class AddInvoiceNumberView(SimpleFormView):
    form =  InvoiceNumberForm
    form_title = _('Add_Invoice_Number')
    invoTuple=(   #順序很重要
        "營業人統編",
        "發票期別",
        "發票字軌名稱",
        "發票起號",
        "發票迄號")
    leInvonumber = 8
    leInvoiceWord = 2
    leBusinessNumber = 8
    allowFileName= set(['csv'])

    @has_access
    def form_post(self, form):
        try:
            self.checkFileName(form.file.data.filename)#確認檔名
            file= form.file.data.read()
            works= file.decode(encoding='Big5') #轉編碼  原檔為Big5
            works=self.cutStr(works)  #切割字串
            invoDict=self.checkKey(works)  #確認關鍵字 在第0行
            self.checkFile( works , invoDict , form.businessNumber.data , form.monthSlot.data )  #檢查內容
            self.upLoadInvoiceNumber( works , invoDict )   #寫入資料庫
        except Exception as e:
            flash(str(e))
            return redirect(url_for('AddInvoiceNumberView.this_form_get'))
        return redirect(url_for('InvoiceNumberView.list'))

    def checkFileName(self ,name): #確認副檔名
        get =name.rfind('.')
        if get > 0 :
            name =name[get+1:]
            if name  in self.allowFileName :
                return
        raise Exception(_('Fail File!%(name)s check it !',name=name))

    def upLoadInvoiceNumber( self , works , invoDict): #將發票號碼寫入資料庫
        for i in range( len(works)-1 ):  #第0不動作
            number = works[i+1][invoDict[ self.invoTuple[3] ]]
            nowTime = self.getTime()
            while True:
                john = InvoiceNumber(
                     monthSlot =  works[i+1][invoDict[ self.invoTuple[1] ]] ,
                     invoiceNumber  = works[i+1][invoDict[ self.invoTuple[2] ]]  + number,
                     status =  '0',
                     insertTime = nowTime)
                try:
                    john.save()
                except :
                    raise Exception(_('Can\'t update to DB! break in line%(line)s , %(number)s',lin=i,number=works[i+1][invoDict[ self.invoTuple[2] ]]  + number))
                if number == works[i+1][invoDict[ self.invoTuple[4] ]]:
                    break
                number = self.strAdd( number)

    def getTime(self):# 調整時間格式 與資料庫一致
        insertTime =  datetime.utcnow()
        insertTime = insertTime.isoformat()
        insertTime = insertTime[:-3]+'Z'
        return insertTime

    def checkFile(self , works , invoDict ,businessNumber, monthSlot ):#確認檔案內容格式
        for i in range( len(works)-1 ):  #第0不檢查
            self.checkBusinessNumber( works[i+1][ invoDict[ self.invoTuple[0] ]], businessNumber ,i+1) #確認營業人統編
            works[i+1][invoDict[self.invoTuple[1] ]]=self.checkMonthSlot(monthSlot ,works[i+1][invoDict[self.invoTuple[1] ] ],i+1  ) #調整期別格式,確認期別
            self.checkInvoiceWord( works[i+1][invoDict[self.invoTuple[2] ] ] , i+1) #確認字軌
            self.checkNumber(  #確認數字
                works[i+1][ invoDict[ self.invoTuple[3] ]],
                works[i+1][ invoDict[ self.invoTuple[4] ]], i+1 )
            self.checkRepeat( #確認重複
                works[i+1][ invoDict[ self.invoTuple[2] ]],
                works[i+1][ invoDict[ self.invoTuple[3] ]],
                works[i+1][ invoDict[ self.invoTuple[4] ]], i+1)

    def checkInvoiceWord(self , InvoiceWord , line ): #確認發票號碼字母 是否大寫,長度
        for i in InvoiceWord:
            if i<'A' or i>'Z':
                raise Exception(_('In line %(line)s,InvoiceWord Error!',line = line ))
        if len(InvoiceWord) != self.leInvoiceWord :
                raise Exception(_('In line %(line)s,InvoiceWord Error!',line = line ))

    def checkBusinessNumber(self, number ,businessNumber ,line):#確認營業人統編是否與輸入一致
        if number  != businessNumber:
            raise Exception(_('In line %(line)s, Business Number Don\'t Match!', line = line))
        if len(number) != self.leBusinessNumber:
            raise Exception(_('In line %(line)s, Length of Business Number  error', line = line ))

    def checkRepeat(self , header , startNumber , endNumber , line):#資料庫搜尋 確認有無重複
        number = startNumber
        while True:
            if InvoiceNumber.objects( invoiceNumber = header+number ).first() != None:
                raise Exception(_('In line %(line)s, Invoice Number Repetition!', line = line ))
            if number == endNumber:
                break
            number = self.strAdd( number )

    def strAdd( self ,number ): #字串加一
        num = len( number ) #after strTOint  not check char not 1-9
        for i in range( len( number) ):
            now = num - i -1
            if number[now] != '9' :
                temp = int(number[now] )+ 1
                number = number[:now] + str(temp)
                break
        if now == 0 : #99999
            raise Exception('strAdd overflow!')
        while len(number) != num:
            number += '0'
        return number

    def checkNumber( self , startNumber , endNumber , line):#確認發票號碼數字 ,長度
        if  len(startNumber ) != self.leInvonumber or len(endNumber ) != self.leInvonumber :
            raise Exception('In line {}, Length of Invonumber Number  error !'.format( line ))
        start = self.strTOint( startNumber )
        end = self.strTOint( endNumber )
        if start > end :
            raise Exception(_('In line %(line)s, Number sequential error !', line = line ))
        if (end-start+1)%50 :
            raise Exception(_('In line %(line)s , Not a multiple of fifty!',line = line ) )
        if start%100 != 0 and start%100 != 50 :   #判斷00 ,50 開頭
            raise Exception(_('In line %(line)s, Number does\'t start from zero !', line = line ))

    def strTOint(self , number):#避免 OxXXXXX
        count = 0
        for i in number:
            if i !='0':
                if i<'0' or i>'9':
                    raise Exception(_('String is not Number!'))
                break
            count+=1
        if number[count:] == "":
            return 0
        return int(float(number[count:]))

    def checkMonthSlot(self ,monthSlot , checkMonth,line):
        indexMonth=[]
        str =""
        jump = 0
        for i in checkMonth:#分割數字並儲存
            if i >='0' and  i <= '9':
                str+=i
                jump = 1
            elif jump==1:
                indexMonth.append(int(str))
                str=''
                jump = 0
        if str != '' :
            indexMonth.append(int(str))
        if len(indexMonth) != 4 or indexMonth[0] != indexMonth[2]:
            raise Exception(_('In line %(line)s,Format of data !  for example:107/09~107/10', line = line ))
        if indexMonth[1]%2 != 1 or indexMonth[1]+1 !=  indexMonth[3] or indexMonth[1] < 1 or indexMonth[1] > 11 :
            raise Exception(_('In line %(line)s,Month error!', line = line ))
        i = datetime.now()
        if indexMonth[3]  != 2 :
            if ( indexMonth[3] < i.month or indexMonth[3]-3 > i.month ) or ( i.year-1911) != indexMonth[0]:
                raise Exception(_('In line %(line)s,Expired!', line = line ))
        else :
            if  not( i.month in (11,12)  and ( i.year-1910 ) == indexMonth[0] ) and not( i.month in (1,2)  and ( i.year-1911 ) == indexMonth[0] ) :
                raise Exception(_('In line %(line)s,Expired!', line = line ))
        if indexMonth[1] != int(monthSlot[:2])   or indexMonth[3] != int(monthSlot[2:]) :
            raise Exception(_('In line %(line)s,Month Slot Don\'t Match!',line = line ))
        return monthSlot

    def checkKey(self, works):#檢查關鍵字
        invoDict={}
        try :
            for i in range(len(self.invoTuple)):
                invoDict[self.invoTuple[i]]=works[0].index(self.invoTuple[i])
        except :
            raise Exception(_('No found keywords!'))
        return invoDict

    def cutStr(self, word):#將資料分段
        editWord=[]
        part=""
        jump=0
        for i in range(len(word)):
            if word[i] != '\n' and word[i] != '\t' and word[i] != '\r':
                part = part+word[i]
                jump=0
            else:
                if jump == 0 :
                    editWord.append(part.split(','))
                    part=""
                    jump=1
        if part != "":
            editWord.append(part.split(','))
        for i in range(len(editWord)-1): #檢查每個段落的長度
            if len( editWord[ i ] ) != len( editWord[ i+1 ] ):
                raise Exception(_('There is a problem with the file content format!'))
        return editWord

class InvoiceNumberView(ModelView):
    datamodel = MongoEngineInterface(InvoiceNumber)
    label_columns = {'monthSlot':_('monthSlot'),'invoiceNumber':_('invoiceNumber'),'status':_('status'),'insertTime':_('insertTime')}
    list_columns = ['monthSlot','invoiceNumber','status','insertTime']
    list_title = _('Search_Invoice_Number')

    @action("muldelete", "Delete", "Delete all Really?", "fa-rocket", single=False)
    def muldelete(self, items):
        myTime =datetime.utcnow()
        count =0
        if isinstance(items, list):
            for item in items:
                if item.status == '0':
                    item=self.changeDel( item , myTime ,count)
                    self.datamodel.edit(item)
                    self.update_redirect()
                count += 1
        else:
            items=self.changeDel( items , myTime, count)
            self.datamodel.edit(items)
        #time.sleep(1)#一秒只能刪一次避免時間一樣
        return redirect(self.get_redirect())

    def changeDel(self , item ,myTime ,count ): #發票號碼更改為('MM'+'DD' + char(時) + char(分) + char(秒) + count(3位數)
        item.status='2'
        item.invoiceNumber = myTime.strftime("%m%d") + chr(myTime.hour +48) + chr(myTime.minute+48) + chr(myTime.second+48) +str( count  ).zfill(3)
        return item

class YuTsaiLprCashJournalView(ModelView):
    datamodel = MongoEngineInterface(YuTsaiLprCashJournal)
    excel_col0=[ '發票異動別','公司編號','發票公司編號','發票類型','發票號碼','發票日期','發票開立時間','客戶編號',
        '客戶名稱','客戶統一編號','稅別','零稅率註記(0/1)','外銷方式','證明文件名稱','證明文件編號','出口報關類別',
        '出口報關號碼','發票抬頭','發票地址','貨品金額','稅額','總金額','是否列印','隨機碼',
        '勾選 愛心碼','愛心碼','勾選 載具類別','載具類別碼','載具號碼','原發票號碼','產品序號','產品編號1',
        '產品名稱1','基本單位數量','基本單位','單價1','單品稅額','小計','廠商編號','訂單單號',
        '驗收號碼','發票作廢日期','發票作廢時間','發票作廢理由','發票月份:起月','發票月份:迄月','條款備註']
    label_columns = {'sIdNumber':_('sIdNumber'),'plateText':_('plateText'),'inTime':_('inTime'),'outTime':_('outTime'),
        'chungyoNumber':_('chungyoNumber'),'receivable':_('receivable'),'discount':_('discount'),'cash':_('cash'),
        'storeDisType':_('storeDisType'),'chungyoDisType':_('chungyoDisType'),'rateType':_('rateType'),'invoiceNumber':_('invoiceNumber'),
        'customerCompanyId':_('customerCompanyId'),'carType':_('carType')}
    search_columns = ['sIdNumber','plateText','inTime','outTime' ,'chungyoNumber','receivable','discount','cash','rateType','invoiceNumber','customerCompanyId','carType']
    list_columns = ['sIdNumber','plateText','inTime','outTime' ,'chungyoNumber','receivable','discount','cash','storeDisType','chungyoDisType','rateType','invoiceNumber','customerCompanyId','carType']
    extra_args = {'cashTatol': 0,'receivableTatol': 0,'discountTatol': 0 }
    list_title = _('Cash_Journal')
    base_permissions = ['can_show','can_list']
    list_widget = YuTsaiLprCashJournalWidget
    list_template = 'YuTsaiLprCashJournal.html'
    nowListData = None

    @expose('/list/')
    @has_access
    def list(self):
        widgets = self._list()
        filters=self._filters
        joined_filters = filters.get_joined_filters(self._base_filters)
        count, self.nowListData = self.datamodel.query(joined_filters)
        self.getMoney()
        return self.render_template(self.list_template,
                                    title=self.list_title,
                                    widgets=widgets)

    def getMoney(self): #統計金額
        self.extra_args['cashTatol'] = 0
        self.extra_args['receivableTatol'] = 0
        self.extra_args['discountTatol'] = 0
        for item in  self.nowListData :
            if item['cash'] != "":
                 self.extra_args['cashTatol'] +=  int(item['cash'])
            if item['receivable'] != "" :
                self.extra_args['receivableTatol'] +=  int(item['receivable'])
            if item['discount'] != "" :
                self.extra_args['discountTatol'] +=  int(item['discount'])

    @expose('/downloadExcel/')
    def downloadExcel(self):
        myExcel = Workbook() #建立Excel檔
        myStyle = self.setFont(name = "微軟正黑體") #建立字形
        sheet1 = myExcel.add_sheet(u'Sheet 1',cell_overwrite_ok=True) #建立分頁
        for index ,content in enumerate( self.excel_col0 ) :
            sheet1.write(0, index, content,myStyle)
        line = 1
        for item in  self.nowListData :
            if item.invoiceNumber !="":
                sheet1.write(line, 0, '1',myStyle)
                sheet1.write(line, 1, '7',myStyle)
                sheet1.write(line, 2, '001',myStyle)
                sheet1.write(line, 3, '3',myStyle)
                sheet1.write(line, 4,  item.invoiceNumber ,myStyle)
                strTime=self.getNumber(item.invoicePrintTime)
                sheet1.write(line, 5,  strTime[:8] ,myStyle)
                sheet1.write(line, 6,  strTime[8:] ,myStyle)
                sheet1.write(line, 10,  '1' ,myStyle)
                sheet1.write(line, 18,  '依個資法不公布' ,myStyle)
                money = self.countTax( item.cash)
                sheet1.write(line, 19,  money['priceOfGoods'] ,myStyle)
                sheet1.write(line, 20,  money['tax'] ,myStyle)
                sheet1.write(line, 21,  money['cash'] ,myStyle)
                sheet1.write(line, 22,  '0' ,myStyle)
                sheet1.write(line, 23,   item.randomNumber, myStyle)
                sheet1.write(line, 30,  '1', myStyle)
                sheet1.write(line, 31,  '001', myStyle)
                sheet1.write(line, 32,  '停車費', myStyle)
                sheet1.write(line, 33,  '1', myStyle)
                sheet1.write(line, 34,  '式', myStyle)
                sheet1.write(line, 35,  money['priceOfGoods'] , myStyle)
                sheet1.write(line, 36,  money['tax'] , myStyle)
                sheet1.write(line, 37,  money['cash'] , myStyle)
                invoiceMonth=self.checkMonth(strTime[:6] )
                sheet1.write(line, 44,  invoiceMonth[0] , myStyle)
                sheet1.write(line, 45,   invoiceMonth[1] , myStyle)
                if  item.customerCompanyId !="":
                    sheet1.write(line, 7,   'B002', myStyle)
                    sheet1.write(line, 8,   'B2B消費者', myStyle)
                    sheet1.write(line, 9,  item.customerCompanyId , myStyle)
                    sheet1.write(line, 17,  item.customerCompanyId ,myStyle)
                else :
                    sheet1.write(line, 7,   'B001', myStyle)
                    sheet1.write(line, 8,   'B2C消費者', myStyle)
                    sheet1.write(line, 9,   '0000000000', myStyle)
                    sheet1.write(line, 17,  '0000000000' ,myStyle)
                line +=1
        myExcel.save("app/"+'test.xls')
        response = make_response(send_file("CashJournal.xls"))
        response.headers["Content-Disposition"] = "attachment; filename=test.xls;"
        return response

    def checkMonth(self,month): #確認是哪個期別(年+月)
        invoiceMonth = []
        if int(month[-1]) % 2 != 0 :
            invoiceMonth.append(month)
            invoiceMonth.append(self.monthAdd(month,1))
        else :
            invoiceMonth.append(self.monthAdd(month,-1))
            invoiceMonth.append(month)
        return invoiceMonth

    def monthAdd(self , month , i):#期別(年+月)加減(對月份加減)
        number = int(month[4:])+ i
        if number < 10:
            return month[:4]+'0'+str(number)
        return month[:4]+str(number)

    def countTax(self , cash):#計算稅額
        cash = int(cash)
        dictMoney={}
        dictMoney['priceOfGoods'] = self.myRound( cash/1.05)
        dictMoney['tax'] = cash - dictMoney['priceOfGoods']
        dictMoney['cash']= cash
        return dictMoney

    def myRound(self , number):#四捨五入到小數第二位
        if (number *1000 %10) >= 5 :
            return round((number*1000+10)/1000,2)
        return round(number,2)

    def getNumber(self , str):# 取出字串裡的數字  如果非數字會剔除
        number =''
        for i in str:
            if i >= '0' and i <= '9':
                number += i
        return number

    def setFont(self , name, height = 220 ,color_index = 4, bold = False ):
        style = XFStyle()  # 初始化样式
        font = Font()  # 为样式创建字体
        font.name = name # 'Times New Roman'
        font.bold = bold #加粗
        font.color_index = color_index
        font.height = height
        style.font = font
        return style

class SpecailDayView(ModelView):
    datamodel = MongoEngineInterface(SpecialDayCollection)
    label_columns = {'day':_('day'),'sFeeRate':_('feeRate')}
    search_columns = ['day']
    list_columns = ['day','sFeeRate']
    add_form = SpeicalDayForm
    base_permissions = ['can_show','can_list','can_delete','can_add']
    list_title = _('Specail  Day')

    def _add(self):
        is_valid_form = True
        get_filter_args(self._filters)
        exclude_cols = self._filters.get_relation_cols()
        form = self.add_form.refresh()
        if request.method == 'POST':
            self._fill_form_exclude_cols(exclude_cols, form)
            if form.validate():
                if SpecialDayCollection.objects( day = form.data['day'] ).first() != None:
                    flash(_('Repeated Date') )
                    return None
                self.process_form(form, True)
                item = self.datamodel.obj()
                form.populate_obj(item)
                try:
                    self.pre_add(item)
                except Exception as e:
                    flash(str(e), "danger")
                else:
                    if self.datamodel.add(item):
                        self.post_add(item)
                    flash(*self.datamodel.message)
                finally:
                    return None
            else:
                is_valid_form = False
        if is_valid_form:
            self.update_redirect()
        return self._get_add_widget(form=form, exclude_cols=exclude_cols)

class MonthlyCarPlateTextView(ModelView):
    datamodel = MongoEngineInterface(MonthlyCarPlateText)
    label_columns = {'plateText':_('plateText'),'startDateTime':_('startDateTime'),'endDateTime':_('endDateTime'),'carFeeRate':_('carFeeRate')}
    search_columns = ['plateText']
    list_columns = ['plateText','startDateTime','endDateTime','carFeeRate']
    add_form = MonthlyCarPlateTextForm
    edit_form = MonthlyCarPlateTextForm
    list_title = _('Monthly  Car')
    base_permissions = ['can_show','can_list','can_add','can_delete']

    def _add(self):
        is_valid_form = True
        get_filter_args(self._filters)
        exclude_cols = self._filters.get_relation_cols()
        form = self.add_form.refresh()
        if request.method == 'POST':
            self._fill_form_exclude_cols(exclude_cols, form)
            if form.validate():
                if MonthlyCarPlateText.objects( plateText = form.data['plateText'] ).first() != None:
                    flash(_('Repeated PlateText') )
                    return None
                self.process_form(form, True)
                item = self.datamodel.obj()
                form.populate_obj(item)
                if not self.checkItemTime(item):
                    flash(_('Time Error') )
                    return None
                try:
                    self.pre_add(item)
                except Exception as e:
                    flash(str(e), "danger")
                else:
                    if self.datamodel.add(item):
                        self.post_add(item)
                    flash(*self.datamodel.message)
                finally:
                    return None
            else:
                is_valid_form = False
        if is_valid_form:
            self.update_redirect()
        return self._get_add_widget(form=form, exclude_cols=exclude_cols)

    def checkItemTime(self , item):
        if len( item.startDateTime) == 16 and len( item.endDateTime)  == 16 :
            if  item.startDateTime[10] ==" " and  item.endDateTime[10] == " ":
                item.startDateTime = item.startDateTime[:10] +'T'+item.startDateTime[11:]
                item.endDateTime= item.endDateTime[:10]+'T'+item.endDateTime[11:]
                return True
        return False

class MonthlyCarTimeSlotView(ModelView):
    datamodel = MongoEngineInterface(MonthlyCarTimeSlot)
    label_columns = {'startTime':_('startTime'),'endTime':_('endTime'), 'timeSlotFee':_('timeSlotFee' ) ,'executeRow':_('executeRow'), 'feeRateTable':_('feeRateTable') , 'ps':_('ps') }
    list_columns = ['startTime','endTime', 'timeSlotFee' ,'executeRow', 'feeRateTable' , 'ps' ]
    list_title = _('Monthly Car Time')
    list_widget = MonthlyCarTimeSlotWidget
    base_permissions = ['can_show','can_list','can_delete','can_add']

    @expose('/add', methods=['GET', 'POST'])
    def add(self):
        return redirect(url_for('AddMonthlyCarTimeSlotView.this_form_get'))

class AddMonthlyCarTimeSlotView(SimpleFormView):
    form =  MonthlyCarTimeSlotForm
    form_title = _('Add  Monthly  Car  Time  Slot')

    @has_access
    def form_post(self, form):
        if  form.data['endTime'] > form.data['starTime'] :
            john = MonthlyCarTimeSlot( monthlyCarTimeSlotArr =[{
                'startTime' : form.data['starTime'],
                'endTime' : form.data['endTime'],
                'timeSlotFee' : form.data['timeSlotFee'],
                'executeRow' : form.data['executeRow'],
                'feeRateTable' : form.data['feeRateTable'],
                'ps' : form.data['ps']},])
            john.save()
        else :
            flash((_('Date Error') ))
        return redirect(url_for('MonthlyCarTimeSlotView.list'))

class DayFinancialStatementsView(YuChartsView):
    form = DayFinancialStatementsSearchForm
    form_title = _('Day Financial Statements')
    form_template  = 'DayFinancialStatements.html'
    chart_title = 'Day Financial Statements'
    extra_args = {'cashTatol': 0,'receivableTatol': 0,'discountTatol': 0 ,'carsTatol': 0,'day':'0','invoiceNumber':[0,0]}
    label_columns ={'day':'day','cashTatol': 'cashTatol','receivableTatol':'receivableTatol ','discountTatol':'discountTatol '}
    definitions = [
    {
        'label': 'Day',
        'group': 'day',
        'series': ['receivableTatol','discountTatol','cashTatol']
    }]

    def updateData(self):
        self.statistics(self.extra_args['day'])
        self.charData=[]
        self.charData.append([ #順序要等於definitions['series']
            self.extra_args['day'] ,
            self.extra_args['receivableTatol'],
            self.extra_args['discountTatol'],
            self.extra_args['cashTatol']
        ])

    def form_get(self, form):
        if self.extra_args['day'] == '0':
            today = datetime.utcnow().date()
            self.extra_args['day'] = (today+timedelta(days = -1)).strftime("%Y-%m-%d")
        self.updateData()

    def form_post(self, form):
        if len(form.data['day']) == 10:
            self.extra_args['day'] = form.data['day']
        self.updateData()

    def searchDateTime(self , day):
        endTime =  (datetime.strptime(day, '%Y-%m-%d')+timedelta(days = 1)).strftime("%Y-%m-%d")+'T09:00:00'
        startTime = day+'T09:00:00'
        return startTime, endTime

    def statistics(self , day):
        startTime ,endTime = self.searchDateTime( day)
        self.extra_args['cashTatol'] = 0
        self.extra_args['receivableTatol'] = 0
        self.extra_args['discountTatol'] = 0
        self.extra_args['carsTatol'] = 0
        self.extra_args['invoiceNumber']=[0,0]
        firstInvoice = 0
        lastInvoice =0
        data = YuTsaiLprCashJournal.objects( Q(outTime__lte = endTime) & Q(outTime__gt = startTime) ).all()
        if data :
            firstInvoice = lastInvoice = data[0]['invoicePrintTime']
            self.extra_args['invoiceNumber'][0] = data[0]['invoiceNumber']
            self.extra_args['invoiceNumber'][1] = data[0]['invoiceNumber']
            for item in data :
                if item['invoicePrintTime'] < firstInvoice:
                    firstInvoice = item['invoicePrintTime']
                    self.extra_args['invoiceNumber'][0] = item['invoiceNumber']
                if item['invoicePrintTime'] > lastInvoice:
                    lastInvoice = item['invoicePrintTime']
                    self.extra_args['invoiceNumber'][1] = item['invoiceNumber']
                self.extra_args['carsTatol'] += 1
                self.extra_args['cashTatol'] += int(item['cash'])
                self.extra_args['receivableTatol'] += int(item['receivable'])
                self.extra_args['discountTatol'] += int(item['discount'])

class TrafficFlowView(YuChartsView):
    form = TrafficFlowForm
    form_title = _('Traffic Flow')
    form_template  = 'TrafficFlow.html'
    extra_args = {'countCar': 0 }
    label_columns ={'hour':'hour','cars': 'In Car'}
    definitions = [{
        'label': 'Day',
        'group': 'hour',
        'series': ['cars']
    }]
    inTatolCar = [
        ['00:00',0],['01:00',0],['02:00',0],['03:00',0],['04:00',0],['05:00',0],
        ['06:00',0],['07:00',0],['08:00',0],['09:00',0],['10:00',0],['11:00',0],
        ['12:00',0],['13:00',0],['14:00',0],['15:00',0],['16:00',0],['17:00',0],
        ['18:00',0],['19:00',0],['20:00',0],['21:00',0],['22:00',0],['23:00',0]
    ]
    outTatolCar = [
        ['00:00',0],['01:00',0],['02:00',0],['03:00',0],['04:00',0],['05:00',0],
        ['06:00',0],['07:00',0],['08:00',0],['09:00',0],['10:00',0],['11:00',0],
        ['12:00',0],['13:00',0],['14:00',0],['15:00',0],['16:00',0],['17:00',0],
        ['18:00',0],['19:00',0],['20:00',0],['21:00',0],['22:00',0],['23:00',0]
    ]
    choseChart = 'IN'
    chart_title = 'Traffic Flow'
    startDay = ''
    endDay = ''

    def updateData(self):
        self.initTatolCar()
        self.statistics()
        if self.choseChart == 'IN':
            self.charData=self.inTatolCar
            self.label_columns['cars'] = 'In Car'
        elif self.choseChart == 'OUT':
            self.charData=self.outTatolCar
            self.label_columns['cars'] = 'Out Car'
        self.chart_title = self.startDay+'  ~  '+self.endDay

    def form_get(self, form):
        if self.startDay == '':
            today = datetime.utcnow().date()
            day = (today+timedelta(days = -1)).strftime("%Y-%m-%d")
            self.startDay = day
            self.endDay = day
        self.updateData()

    @expose('/checkChoseChart/<chose>' )
    def checkChoseChart(self ,chose):
        if chose ==  'IN':
            self.choseChart = 'IN'
        elif chose == 'OUT':
            self.choseChart = 'OUT'
        return redirect(url_for('TrafficFlowView.this_form_get'))

    def initTatolCar(self):
        self.extra_args['countCar'] =  0
        for i in range(24) :
            self.inTatolCar[i][1]=0
            self.outTatolCar[i][1]=0

    def form_post(self, form):
        if len(form.data['startDay']) == 10 and  len(form.data['endDay']) == 10 and form.data['startDay'] <= form.data['endDay']:
            self.startDay = form.data['startDay']
            self.endDay = form.data['endDay']
        self.updateData()

    def statistics(self ):
        endTime =  self.endDay +'T23:59:59'
        startTime = self.startDay +'T00:00:00'
        data = YuTsaiLprCashJournal.objects( Q(outTime__lte = endTime) & Q(outTime__gt = startTime) ).all()
        if data :
            for item in data :
                self.extra_args['countCar'] += 1
                try:# 排除 沒有值的狀況
                    self.inTatolCar[ int(item.inTime[11:13]) ][1]+=1
                    self.outTatolCar[ int(item.outTime[11:13]) ][1]+=1
                except:
                    continue

'''
class tryDirectByChartView(DirectByChartView):
    datamodel = MongoEngineInterface(YuTsaiLprCashJournal)
    chart_title = 'Direct Data Example'

    definitions = [
    {
        'label': 'Unemployment',
        'group': 'getInTimeDate',
        'series': ['cash',
                   'receivable']
    }]

    def _get_chart_widget(self, filters=None,
                          order_column='',
                          order_direction='',
                          widgets=None,
                          direct=None,
                          height=None,
                          definition='',
                          **args):

        height = height or self.height
        widgets = widgets or dict()
        joined_filters = filters.get_joined_filters(self._base_filters)
        # check if order_column may be database ordered
        if not self.datamodel.get_order_columns_list([order_column]):
            order_column = ''
            order_direction = ''
        count, lst = self.datamodel.query(filters=joined_filters,
                                          order_column=order_column,
                                          order_direction=order_direction)
        if not definition:
            definition = self.definitions[0]
        group = self.get_group_by_class(definition)
        group1 = self.myAdd(group.apply(lst, sort=order_column == '') )

        value_columns = group.to_json(group1, self.label_columns)
        widgets['chart'] = self.chart_widget(route_base=self.route_base,
                                             chart_title=self.chart_title,
                                             chart_type=self.chart_type,
                                             chart_3d=self.chart_3d,
                                             height=height,
                                             value_columns=value_columns,
                                             modelview_name=self.__class__.__name__,
                                             **args)
        return widgets

    def myAdd(self , group):
        base =[]
        for item in group:
            item[1]=int(item[1])
            item[2]=int(item[2])
            for item1 in base :
                if item1[0] == item[0]:
                    item1[1]+= item[1]
                    item1[2]+= item[2]
                    break
            else:
                base.append(item)
        return base

class TestView(BaseView):
    default_view = 'test'
    @expose('/test/?<show0>' )
    @has_access
    def test(self ,show0):
        return self.render_template('test.html', show0 = show0)
'''
#appbuilder.add_view_no_menu(TestView)
appbuilder.add_view_no_menu(AddMonthlyCarTimeSlotView)
appbuilder.add_view(AddInvoiceNumberView, "Add Invoice Number", icon="fa-hand-o-up", label=_("Add_Invoice_Number"),category="MyForms", category_icon="fa-cloud-upload",category_label=_("Forms"))
appbuilder.add_view(InvoiceNumberView, "Invoice Number", icon="fa-th-list", label=_("Invoice_Number"), category="MyDataBase", category_icon="fa-database",category_label=_("Database"))
appbuilder.add_view(YuTsaiLprCashJournalView, "Yu Tsai Lpr Cash Journal", icon="fa-th-list", label=_("Cash Journal"),category="MyDataBase")
appbuilder.add_view(SpecailDayView, "Specail Day", icon="fa-th-list", label=_("SpecailDay"),category="MyDataBase")
appbuilder.add_view(MonthlyCarPlateTextView, "Monthly Car Plate Text ", icon="fa-th-list", label=_("Monthly Car"),category="MyDataBase")
appbuilder.add_view(MonthlyCarTimeSlotView, "Monthly Car Time Slot", icon="fa-th-list", label=_("Monthly Car Time Slot"),category="MyDataBase")
appbuilder.add_view(DayFinancialStatementsView, "Day Financial Statements", icon="fa-th-list", label=_("Day Financial Statements"),category="MyDataBase")
appbuilder.add_view(TrafficFlowView, "Traffic Flow", icon="fa-th-list", label=_("Traffic Flow"),category="MyDataBase")
#appbuilder.add_view(tryDirectByChartView, "try  Direct  By  Chart", icon="fa-th-list", label=_(" Direct  By  Chart"),category="MyDataBase")
appbuilder.security_cleanup() #清除被廢棄的列表名稱
