from django.apps import AppConfig


class DicPickConfig(AppConfig):
  """An app config that sets up our signals."""
  default_auto_field = "django.db.models.BigAutoField"
  name = "dicpick"

  def ready(self):
    import dicpick.signals
