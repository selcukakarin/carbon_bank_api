from django.db.models import Q
from rest_framework import mixins, viewsets
from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from cores.permissions import IsCustomer
from customers.models import Customer
from management.api.serializers import AccountSerializer
from management.models import BankAccount
from .permissions import IsOwner
from .serializers import CustomerListSerializer, CustomerCreateSerializer


class CustomerCreateAPIView(CreateAPIView):
    """
        Create User Fonksiyon. You should be admin user.
    """
    queryset = Customer.objects.filter(is_deleted=False).order_by('-created_date')
    serializer_class = CustomerCreateSerializer
    permission_classes = [IsAdminUser]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CustomerListAPIView(ListAPIView):
    """
        List all customer information. You should be admin user.
    """
    permission_classes = [IsAdminUser]
    serializer_class = CustomerListSerializer
    queryset = Customer.objects.filter(is_deleted=False).order_by('-created_date')


class GetBalanceAPIView(RetrieveAPIView):
    """
        Get balance for a specific bank account. You should be admin user. owner parameter = customer id
    """
    queryset = BankAccount.objects.filter(is_deleted=False)
    serializer_class = AccountSerializer
    lookup_field = 'owner'
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return BankAccount.objects.filter(Q(owner=self.kwargs["owner"]))
