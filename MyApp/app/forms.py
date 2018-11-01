from wtforms import Form, StringField , SubmitField,DateField,SelectField
from wtforms.validators import DataRequired , Length
from flask_appbuilder.forms import DynamicForm
from flask_wtf.file import FileField
from flask_babel import lazy_gettext as _
from flask_appbuilder.fieldwidgets import BS3TextFieldWidget,DatePickerWidget
from .fieldwidgets import DateTimePickerMinuteWidget

class InvoiceNumberForm(DynamicForm):
    monthSlot  = StringField(_('MonthSlot'),
        description=_('For example ,January and February : 0102'),
        validators = [DataRequired(),Length(min=4,max=4)],
        widget=BS3TextFieldWidget())
    businessNumber = StringField(_('BusinessNumber'),
        description=_('Key In Business Number!'),
        validators = [DataRequired(),Length(min=8,max=8)],
        widget=BS3TextFieldWidget())
    file = FileField(_('Chose Invoice Field'),
        validators=[DataRequired()],
        description=_('only CSV!'))

class myTest(DynamicForm):                                        #設定 Login 框架
    submit = SubmitField('change')

class SpeicalDayForm(DynamicForm):
    day = StringField(_('Date'),
        description=_('For example ,2018-01-01'),
        validators = [DataRequired(),Length(min=10,max=10)],
        widget=DatePickerWidget())
    feeRate = SelectField(_('Fee Rate'),
        choices=[('8',_('Holiday') ), ('9',_('Weekday'))])

class MonthlyCarPlateTextForm(DynamicForm):
    plateText = StringField(  _('plateText'),
        validators = [DataRequired()],
        widget=BS3TextFieldWidget())
    startDateTime = StringField( _('start time'),
        description=_('For example ,2018-01-01 12:00'),
        validators = [DataRequired()],
        widget=DateTimePickerMinuteWidget())
    endDateTime = StringField( _('end time'),
        description=_('For example ,2018-01-31 12:00'),
        validators = [DataRequired()],
        widget= DateTimePickerMinuteWidget())
    monthlyCarType = SelectField(_('Car Fee Rate'),
        choices=[('0',_('only weekday') )])

class MonthlyCarTimeSlotForm(DynamicForm):
    starTime = StringField( _('Star Time '),
        validators = [DataRequired()],
        widget=BS3TextFieldWidget())
    endTime = StringField( _('End Time'),
        validators = [DataRequired()],
        widget=BS3TextFieldWidget())
    timeSlotFee = StringField( _('timeSlotFee'),
        validators = [DataRequired()],
        widget=BS3TextFieldWidget())
    executeRow = StringField( _('executeRow'),
        widget=BS3TextFieldWidget())
    feeRateTable = StringField( _('feeRateTable'),
        widget=BS3TextFieldWidget())
    ps = StringField( _('ps '),
        widget=BS3TextFieldWidget())

class DayFinancialStatementsSearchForm(DynamicForm):
    day = StringField(_('Date'),
        validators = [DataRequired(),Length(min=10,max=10)],
        widget=DatePickerWidget())
