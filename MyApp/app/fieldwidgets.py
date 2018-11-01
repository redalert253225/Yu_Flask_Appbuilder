from wtforms.widgets import HTMLString, html_params


class DateTimePickerMinuteWidget(object):
    """
    Date Time picker from Eonasdan GitHub

    """
    data_template = ('<div class="input-group date appbuilder_datetime" id="datetimepicker">'
                    '<span class="input-group-addon"><i class="fa fa-calendar cursor-hand"></i>'
                    '</span>'
                    '<input class="form-control" data-format="yyyy-MM-dd hh:mm" %(text)s/>'
        '</div>'
        )

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        kwargs.setdefault('name', field.name)
        if not field.data:
            field.data = ""
        template = self.data_template

        return HTMLString(template % {'text': html_params(type='text',
                                        value=field.data,
                                        **kwargs)
                                })
