from django.conf import settings
from django.conf.urls import include, url
from django.urls import path
from django.views import defaults as default_views
from django.views.generic import TemplateView

urlpatterns = [
    url(r'^$', TemplateView.as_view(template_name='index.html'), name="home"),
    path('ilo2/', include('ilo2.urls')),
]

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        url(r'^400/$', default_views.bad_request, kwargs={'exception': Exception("Bad Request!")}),
        url(r'^403/$', default_views.permission_denied,
                       kwargs={'exception': Exception("Permission Denied")}),
        url(r'^404/$', default_views.page_not_found,
                       kwargs={'exception': Exception("Page not Found")}),
        url(r'^500/$', default_views.server_error),
    ]
