"""
Resume Views URL Configuration
"""
from django.urls import path
from .views import ResumeDetailView, ResumeListCreateView

app_name = "resume"
urlpatterns = [
    path("", ResumeListCreateView.as_view(), name="resume_list_create"),
    path("<uuid:pk>/", ResumeDetailView.as_view(), name="resume_detail"),
]
