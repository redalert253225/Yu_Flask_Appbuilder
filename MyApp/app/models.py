from mongoengine import Document,EmbeddedDocument
from mongoengine import DateTimeField, StringField, ReferenceField, ListField,IntField
from mongoengine import DictField,EmbeddedDocumentField,EmbeddedDocumentListField
from datetime import datetime
from flask_appbuilder.models.decorators import renders
from flask_babel import lazy_gettext as _

class InvoiceNumber(Document):
    monthSlot =  StringField( required=True )
    invoiceNumber =  StringField( required=True )
    status =  StringField( required=True ,default= '0')
    insertTime =  StringField( required=True ,default=datetime.utcnow )
    meta = {
        "collection" : "invoiceNumber",
        "max_size" : 40000000
    }

    def saveT(self):
        self.insertTime =  self.insertTime.isoformat()
        self.insertTime = self.insertTime [:-3]+'Z'
        self.save()

class YuTsaiLprCashJournal(Document):
    plateText = StringField( default= "" )
    inTime = StringField( default= "" )
    outTime =  StringField( default= "" )
    payTime = ListField(StringField(default= ""  ))
    payTimeLatest = StringField( default= "" )
    machineId =  DictField( default= {'type':"",'number':""})
    inCarJpg = StringField( default= "" )
    outCarJpg = StringField( default= "" )
    inCameraSource = StringField( default= "" )
    outCameraSource = StringField( default= "" )
    sIdNumber = StringField( default= "" )
    receivable = StringField( default= "" )
    discount = StringField( default= "" )
    cash = StringField( default= "" )
    disType =  ListField(DictField(default= {'chungyo':"",'store':""}))
    chungyoNumber = StringField( default= "" )
    rateType =StringField( default= "" )
    customerCompanyId =StringField( default= "" )
    invoiceNumber = StringField( default= "" )
    invoicePrintTime = StringField( default= "" )
    invoiceVehicleNumber = StringField( default= "" )
    invoiceDonationNumber = StringField( default= "" )
    status = StringField( default= "" )
    carType = StringField( default= "" )
    feeType = StringField( default= "" )
    monthlyCarPlateText = StringField( default= "" )
    discountArray = ListField(StringField(default= "" ))
    randomNumber = StringField( default= "" )
    meta = {
        "collection" : "yuTsaiLprCashJournal"
    }

    def chungyoDisType(self):
        if self.disType != []:
            return self.disType[0]['chungyo']
        return ""

    def storeDisType(self):
        if self.disType != []:
            return self.disType[1]['store']
        return ""

    def getInTimeDate(self):
        return self.inTime[:10]

class SpecialDayCollection(Document):
    day = StringField( required=True )
    feeRate = StringField( required=True )
    meta = {
        "collection" : "specialDayCollection"
    }

    def sFeeRate(self):
        if self.feeRate == '8':
            return _('Holiday')
        elif self.feeRate == '9':
            return _('Weekday')
        return "Error"

class MonthlyCarPlateText(Document):
    plateText = StringField( required=True )
    startDateTime = StringField( required=True )
    endDateTime = StringField( required=True )
    monthlyCarType = StringField( required=True )
    meta = {
        "collection" : "monthlyCarPlateText"
    }

    def carFeeRate(self):
        if self.monthlyCarType == '0':
            return _('weekday only')
        return "Error"

class DictCarFeeRate(EmbeddedDocument):
    startTime = StringField( default= "" )
    endTime = StringField(default= ""  )
    timeSlotFee = StringField(default= ""  )
    executeRow = StringField(default= ""  )
    feeRateTable = StringField(default= ""  )
    ps = StringField(default= ""  )

class MonthlyCarTimeSlot(Document):
    monthlyCarTimeSlotArr = ListField(DictField())
    meta = {
        "collection" : "monthlyCarTimeSlot"
    }

    def startTime(self):
        data = []
        for item in self.monthlyCarTimeSlotArr :
            data.append(item['startTime'])
        return data

    def endTime(self):
        data = []
        for item in self.monthlyCarTimeSlotArr :
            data.append(item['endTime'])
        return data

    def timeSlotFee(self):
        data = []
        for item in self.monthlyCarTimeSlotArr :
            data.append(item['timeSlotFee'])
        return data

    def executeRow(self):
        data = []
        for item in self.monthlyCarTimeSlotArr :
            data.append(item['executeRow'])
        return data

    def feeRateTable(self):
        data = []
        for item in self.monthlyCarTimeSlotArr :
            data.append(item['feeRateTable'])
        return data

    def ps(self):
        data = []
        for item in self.monthlyCarTimeSlotArr :
            data.append(item['ps'])
        return data
