from django.db.models.signals import ModelSignal

post_soft_delete = ModelSignal(use_caching=True)
post_hard_delete = ModelSignal(use_caching=True)
post_restore = ModelSignal(use_caching=True)