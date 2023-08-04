"""
URL configuration for main project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf.urls import include
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.staticfiles.storage import staticfiles_storage
from django.views.generic import RedirectView, TemplateView

from dicpick import urls as dicpick_urls
# from dicpick.monkeypatch import auth_with_email

urlpatterns = [
  path('admin/', admin.site.urls),
  # path('accounts/login/', auth_views.login),
  path('accounts/', include('django.contrib.auth.urls')),

  path('faq/', TemplateView.as_view(template_name='dicpick/faq.html'), name='faq'),
  path('contact_us/', TemplateView.as_view(template_name='dicpick/contact_us.html'), name='contact_us'),
  path('privacy/', TemplateView.as_view(template_name='dicpick/privacy.html'), name='privacy'),
  path('terms/', TemplateView.as_view(template_name='dicpick/terms.html'), name='terms'),
  path('favicon.ico', RedirectView.as_view(url=staticfiles_storage.url('favicon.ico'), permanent=False)),

  path("__debug__/", include("debug_toolbar.urls")),
  path('', include(dicpick_urls, namespace='dicpick')),
]


# Monkeypatching goes here because this file is guaranteed to execute before any requests are handled.
# auth_with_email.patch()
