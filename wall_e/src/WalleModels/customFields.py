from django.db import models
import django_db_orm_settings


class GeneratedIdentityField(models.AutoField):
    description = "An Integer column which uses `GENERATED {ALWAYS | BY DEFAULT} AS IDENTITY`. \
                  A modern alternative to `BIGSERIAL` from the SQL standard."

    def __init__(self, *args, **kwargs):

        # this is necessary because of the `always` that was used in the fourth migration
        kwargs.pop('always', None)

        # have to do it like this cause otherwise loaddata will not work when loading datat from PROD,
        # you wind up with the error
        # DETAIL:  Column "ban_id" is an identity column defined as GENERATED ALWAYS.
        # HINT:  Use OVERRIDING SYSTEM VALUE to override.
        self.always = django_db_orm_settings.environment == "PRODUCTION"

        super(GeneratedIdentityField, self).__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs['always'] = self.always
        return name, path, args, kwargs

    def db_type(self, connection):
        return f"INTEGER GENERATED {'ALWAYS' if self.always else 'BY DEFAULT'} AS IDENTITY"
