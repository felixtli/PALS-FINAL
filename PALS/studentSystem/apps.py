from django.apps import AppConfig

class StudentsystemConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "studentSystem"

    def ready(self):
        import studentSystem.signals  # ensure signals are registered
