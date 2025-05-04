from django.apps import AppConfig


class BaseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'base'
<<<<<<< HEAD
=======
    
>>>>>>> 40265fa96d43daf7e52e876c31df26ca56378ddb
    def ready(self):
        import base.signals

