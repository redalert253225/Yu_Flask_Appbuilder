from flask_appbuilder import AppBuilder, BaseView, expose, has_access
from flask_appbuilder.charts.widgets import DirectChartWidget
from flask_appbuilder.models.group import DirectProcessData
from .widgets import  YuChartsWidgets
from flask_appbuilder import SimpleFormView

class YuChartsView(SimpleFormView):
    #define your form
    edit_widget = YuChartsWidgets
    form_template  = 'YuCharts.html'
    chart_title = ''
    chart_3d = 'true'
    height = '400px'
    chart_type = 'ColumnChart'
    chart_widget = DirectChartWidget
    ProcessClass = DirectProcessData
    charData = []

    @expose("/form", methods=['GET'])
    @has_access
    def this_form_get(self):
        self._init_vars()
        form = self.form.refresh()
        self.form_get(form)
        widgets = self._get_edit_widget(form=form)
        widgets = self._get_chart_widget( widgets= widgets )
        self.update_redirect()
        return self.render_template(self.form_template,
                                    title=self.form_title,
                                    widgets=widgets,
                                    appbuilder=self.appbuilder
        )

    @expose("/form", methods=['POST'])
    @has_access
    def this_form_post(self):
        self._init_vars()
        form = self.form.refresh()

        if form.validate_on_submit():
            response = self.form_post(form)
            if not response:
                return redirect(self.get_redirect())
            return response
        else:
            widgets = self._get_edit_widget(form=form)
            widgets = self._get_chart_widget( widgets= widgets )
            return self.render_template(
                self.form_template,
                title=self.form_title,
                widgets=widgets,
                appbuilder=self.appbuilder
            )

    def get_group_by_class(self, definition):
        group_by = definition['group']
        series = definition['series']
        formatter = {}
        return self.ProcessClass([group_by], series, formatter)

    def _get_chart_widget(self, widgets=None):
        widgets = widgets or dict()
        definition = self.definitions[0]
        group = self.get_group_by_class(definition)
        value_columns = group.to_json(self.charData, self.label_columns)
        widgets['chart'] = self.chart_widget(route_base=self.route_base,
                                             chart_title=self.chart_title,
                                             chart_type=self.chart_type,
                                             chart_3d=self.chart_3d,
                                             height=self.height,
                                             value_columns=value_columns,
                                             modelview_name=self.__class__.__name__)
        return widgets
