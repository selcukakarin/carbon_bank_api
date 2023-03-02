from django.urls import path, include
from rest_framework import routers

from . import views
from .views import TransactionListAPIView

app_name = 'management'

router = routers.SimpleRouter()
router.register('', views.BankAccountViewSet)
router.register('withdraw', views.WithdrawViewSet)
router.register('deposit', views.DepositViewSet)
router.register('transfer', views.TransferViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('list/<pk>', TransactionListAPIView.as_view(), name='list'),
]


