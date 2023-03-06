from django.urls import path, include
from rest_framework import routers

from .views import TransactionListAPIView, ActivateAccountView, AccountListAPIView, CreateDeposit, CreateTransfer, \
    CreateWithdraw

app_name = 'management'

router = routers.DefaultRouter()
# router.register('', views.BankAccountViewSet)
# router.register('withdraw', views.WithdrawViewSet)
# router.register('deposit', views.DepositViewSet, basename='deposit')
# router.register('transfer', views.TransferViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('transaction-list/<pk>', TransactionListAPIView.as_view(), name='transaction-list'),
    path('activate-account/<guid>', ActivateAccountView.as_view(), name='activate-account'),
    path('account-list/', AccountListAPIView.as_view(), name='account-list'),
    path('deposit/', CreateDeposit.as_view(), name='deposit'),
    path('transfer/', CreateTransfer.as_view(), name='transfer'),
    path('withdraw/', CreateWithdraw.as_view(), name='withdraw'),
]


