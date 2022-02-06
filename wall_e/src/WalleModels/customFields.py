from django.db import models


class GeneratedIdentityField(models.AutoField):

    description = "An Integer column which uses `GENERATED {ALWAYS | BY DEFAULT} AS IDENITY`. \
                  A modern alternative to `BIGSERIAL` from the SQL standard."

    def __init__(self, always=False, *args, **kwargs):
        self.always = always
        super(GeneratedIdentityField, self).__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs['always'] = self.always
        return name, path, args, kwargs

    def db_type(self, connection):
        return f"INTEGER GENERATED {'ALWAYS' if self.always else 'BY DEFAULT'} AS IDENTITY"
