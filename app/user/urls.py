"""
URLs fro the user API.
"""
from django.urls import path
from user import views


app_name = "tenant"

urlpatterns = [
    path("create/", views.CreateTenantView.as_view(), name="create"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("mine/", views.ManageTenantView.as_view(), name="manage"),
    path(
        "token/refresh/", views.CustomTokenRefreshView.as_view(), name="token_refresh"
    ),
    path("api-keys/", views.APIKeyListCreateView.as_view(), name="api_keys"),
    path(
        "api-keys/<uuid:id>/", views.APIKeyDetailView.as_view(), name="api_key_detail"
    ),
]
