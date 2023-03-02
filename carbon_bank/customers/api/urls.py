from django.urls import path

from . import views
from .views import CustomerCreateAPIView, CustomerListAPIView, GetBalanceAPIView

app_name = "customers"
urlpatterns = [
    path('create/', CustomerCreateAPIView.as_view(), name='create'),
    path('list/', CustomerListAPIView.as_view(), name='list'),
    path('customer-list', views.CustomerViewSet, name='customer-list'),
    path('get-balance/<owner>', GetBalanceAPIView.as_view(), name='get-balance'),
]
