import logging
from django.apps import AppConfig, apps as django_apps

logger = logging.getLogger(__name__)


class CommonConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'common'

    def ready(self):
        from .views import register_trash_model
        from .models import BaseModel

        for model in django_apps.get_models():
            try:
                if issubclass(model, BaseModel) and not model._meta.abstract:
                    if getattr(model, 'include_in_trash', True):
                        register_trash_model(model)
            except Exception as e:
                logger.debug(f"No se registró {model} en la papelera: {e}")