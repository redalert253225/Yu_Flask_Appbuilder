from flask_appbuilder.widgets import ListWidget

class MonthlyCarTimeSlotWidget(ListWidget):
    template = 'widgets/MonthlyCarTimeSlotWidgets.html'

class YuTsaiLprCashJournalWidget(ListWidget):
    template = 'widgets/YuTsaiLprCashJournalWidgets.html'

class YuChartsWidgets(ListWidget):
    template = 'widgets/YuChartsWidgets.html'
