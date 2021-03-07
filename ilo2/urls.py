from django.urls import path

from . import views

urlpatterns = [
    path('', views.IndexView.as_view(), name='home'),
    # System Status Pages
    path('systemStatus', views.SystemStatusView.as_view(), name='systemStatus'),
    path('systemStatus/summary', views.SystemStatusSummaryView.as_view(), name='systemStatusSummary'),
    path('systemStatus/health', views.SystemStatusHealthView.as_view(), name='systemStatusHealth'),
    path('systemStatus/ilolog', views.SystemStatusIloLogView.as_view(), name='systemStatusIloLog'),
    path('systemStatus/imllog', views.SystemStatusIMLLogView.as_view(), name='systemStatusIMLLog'),
    # TODO: These pages
    path('remoteConsole', views.IndexView.as_view(), name='remoteConsole'),
    path('virtualMedia', views.IndexView.as_view(), name='virtualMedia'),
    path('powerManagement', views.IndexView.as_view(), name='powerManagement'),
    path('administration', views.IndexView.as_view(), name='administration'),
]