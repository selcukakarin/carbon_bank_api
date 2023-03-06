from django.db.models import Q
from rest_framework import viewsets, mixins, status
from rest_framework.generics import ListAPIView, RetrieveUpdateAPIView, CreateAPIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from cores.permissions import IsCustomer
from customers.models import Customer
from management.models import BankAccount, BankTransaction
from .serializers import (AccountSerializer, DepositTransactionSerializer,
                          TransferTransactionSerializer, WithdrawSerializer,
                          TransactionSerializer, AccountActivateSerializer)


class CreateDeposit(CreateAPIView):
    queryset = BankTransaction.objects.filter(is_deleted=False)
    serializer_class = DepositTransactionSerializer
    permission_classes = [IsCustomer]

    def perform_create(self, serializer):
        data = self.request.data.copy()
        if not self.request.user.is_superuser:
            data['sender'] = Customer.objects.get(user=self.request.user).pk
        serializer = self.get_serializer(data=data, context={'request': self.request})
        if serializer.is_valid():
            response = serializer.save()
            return Response(response, status.HTTP_201_CREATED)
        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)


class CreateTransfer(CreateAPIView):
    queryset = BankTransaction.objects.filter(is_deleted=False)
    serializer_class = TransferTransactionSerializer
    permission_classes = [IsAdminUser | IsCustomer, ]

    def perform_create(self, serializer):
        data = self.request.data.copy()
        if not self.request.user.is_superuser:
            data['sender'] = self.request.user.customer.pk
        serializer = self.get_serializer(data=data, context={'request': self.request})
        if serializer.is_valid():
            response = serializer.save()
            return Response(response, status.HTTP_201_CREATED)
        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)


class CreateWithdraw(CreateAPIView):
    queryset = BankTransaction.objects.filter(is_deleted=False)
    serializer_class = WithdrawSerializer
    permission_classes = [IsCustomer]

    def perform_create(self, serializer):
        data = self.request.data.copy()
        if not self.request.user.is_superuser:
            data['sender'] = self.request.user.customer.pk
        serializer = self.get_serializer(data=data, context={'request': self.request})
        if serializer.is_valid():
            response = serializer.save()
            return Response(response, status.HTTP_201_CREATED)
        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)


class AccountListAPIView(ListAPIView):
    serializer_class = AccountSerializer
    queryset = BankAccount.objects.filter(is_deleted=False)
    permission_classes = [IsAdminUser | IsCustomer]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return BankAccount.objects.filter(is_deleted=False)
        return BankAccount.objects.filter(owner=self.request.user.customer)


class ActivateAccountView(RetrieveUpdateAPIView):
    serializer_class = AccountActivateSerializer
    queryset = BankAccount.objects.filter(is_deleted=False)
    lookup_field = 'guid'
    # permission_classes = [IsAdminUser]


class TransactionListAPIView(ListAPIView):
    """
        List all transaction for a specific user. you should be admin. pk = Customer id
    """
    serializer_class = TransactionSerializer
    queryset = BankTransaction.objects.filter(is_deleted=False)
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return BankTransaction.objects.filter(Q(sender=Customer.objects.get(pk=self.kwargs["pk"])) | Q(
            receiver=Customer.objects.get(pk=self.kwargs["pk"])))
