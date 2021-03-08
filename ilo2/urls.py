from django.urls import path
from . import systemStatusViews
from . import virtualMediaViews

urlpatterns = [
    path('',
          systemStatusViews.IndexView.as_view(),
          name='home'),
    # System Status Pages
    path('systemStatus',
          systemStatusViews.SystemStatusView.as_view(),
          name='systemStatus'),
    path('systemStatus/summary',
          systemStatusViews.SystemStatusSummaryView.as_view(),
          name='systemStatusSummary'),
    path('systemStatus/health',
          systemStatusViews.SystemStatusHealthView.as_view(),
          name='systemStatusHealth'),
    path('systemStatus/ilolog',
          systemStatusViews.SystemStatusIloLogView.as_view(),
          name='systemStatusIloLog'),
    path('systemStatus/imllog',
          systemStatusViews.SystemStatusIMLLogView.as_view(),
          name='systemStatusIMLLog'),
    # Virtual Media Pages
    path('virtualMedia',
          virtualMediaViews.VirtualMediaView.as_view(),
          name='virtualMedia'),
    path('virtualMedia/summary',
          virtualMediaViews.VirtualMediaSummaryView.as_view(),
          name='virtualMediaSummary'),
    # TODO: These pages
    path('remoteConsole',
          systemStatusViews.IndexView.as_view(),
          name='remoteConsole'),
    path('powerManagement',
          systemStatusViews.IndexView.as_view(),
          name='powerManagement'),
    path('administration',
          systemStatusViews.IndexView.as_view(),
          name='administration'),
]
