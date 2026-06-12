from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve
from django.conf import settings

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("", include("portal.urls")),
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.BASE_DIR / 'portal' / 'static'}),
]
