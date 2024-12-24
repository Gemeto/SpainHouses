from django.urls import path
from . import views

urlpatterns = [
    path("announcements/", views.AnnouncementListView.as_view(), name="announcements"),
    path('announcement/<int:pk>', views.AnnouncementDetailView.as_view(), name='announcement-detail'),
]