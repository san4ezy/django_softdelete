from django.apps import AppConfig

class DjangoSoftDeleteConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'django_softdelete'
    verbose_name = 'Django Soft Delete'
