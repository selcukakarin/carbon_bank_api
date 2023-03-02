from django.db.models import Q
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from cores.permissions import IsBankAdmin, IsCustomer
from customers.models import Customer
from management.models import BankAccount, BankTransaction
from .paginations import GeneralPagination
from .serializers import (AccountSerializer, DepositTransactionSerializer,
                          TransferTransactionSerializer, WithdrawSerializer,
                          MutationSerializer, TransactionSerializer)


class BankAccountViewSet(mixins.ListModelMixin,
                         viewsets.GenericViewSet):
    serializer_class = AccountSerializer
    permission_classes = [IsBankAdmin]
    queryset = BankAccount.objects.filter(is_deleted=False)
    lookup_field = 'guid'
    pagination_class = GeneralPagination

    def get_serializer_class(self):
        if self.action == 'mutations':
            return MutationSerializer
        return super(BankAccountViewSet, self).get_serializer_class()

    def get_queryset(self):
        queryet = super(BankAccountViewSet, self).get_queryset()
        return queryet.filter(owner=self.request.user.customer)

    def list(self, request, *args, **kwargs):
        customer = request.user.customer
        bank_account = customer.bankaccount
        data = self.get_serializer(instance=bank_account).data

        return Response(data)

    @action(methods=['put'], detail=True, permission_classes=[IsBankAdmin])
    def activate(self, request, **kwargs):
        bank_account = self.get_object()
        bank_account.is_active = True
        bank_account.save()

        return Response(status=status.HTTP_200_OK)

    @action(methods=['put'], detail=True, permission_classes=[IsBankAdmin])
    def deactivate(self, request, **kwargs):
        bank_account = self.get_object()
        bank_account.is_active = False
        bank_account.save()

        return Response(status=status.HTTP_200_OK)

    @action(methods=['get'], detail=True, permission_classes=[IsBankAdmin])
    def mutations(self, request, **kwargs):
        bank_account = self.get_object()
        mutations = bank_account.mutations.filter(is_deleted=False).order_by('-created_date')
        mutations = self.paginate_queryset(mutations)
        serializer = self.get_serializer(instance=mutations, many=True)

        return self.get_paginated_response(serializer.data)


class DepositViewSet(mixins.CreateModelMixin,
                     viewsets.GenericViewSet):
    serializer_class = DepositTransactionSerializer
    permission_classes = [IsCustomer]
    queryset = BankTransaction.objects.filter(is_deleted=False)

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        if not request.user.is_superuser:
            data['sender'] = request.user.customer.pk
        serializer = self.get_serializer(data=data, context={'request': request})
        if serializer.is_valid():
            response = serializer.save()
            return Response(response, status.HTTP_201_CREATED)
        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)


class TransferViewSet(mixins.CreateModelMixin,
                      viewsets.GenericViewSet):
    serializer_class = TransferTransactionSerializer
    permission_classes = [IsAdminUser|IsCustomer,]
    queryset = BankTransaction.objects.filter(is_deleted=False)

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        if not request.user.is_superuser:
            data['sender'] = request.user.customer.pk
        serializer = self.get_serializer(data=data, context={'request': request})
        if serializer.is_valid():
            response = serializer.save()
            return Response(response, status.HTTP_201_CREATED)
        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)


class WithdrawViewSet(mixins.CreateModelMixin,
                      viewsets.GenericViewSet):
    serializer_class = WithdrawSerializer
    permission_classes = [IsCustomer]
    queryset = BankTransaction.objects.filter(is_deleted=False)

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        if not request.user.is_superuser:
            data['sender'] = request.user.customer.pk
        serializer = self.get_serializer(data=data, context={'request': request})
        if serializer.is_valid():
            response = serializer.save()
            return Response(response, status.HTTP_201_CREATED)
        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)



class TransactionListAPIView(ListAPIView):
    serializer_class = TransactionSerializer
    pagination_class = GeneralPagination
    queryset = BankTransaction.objects.filter(is_deleted=False)
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return BankTransaction.objects.filter(Q(sender=Customer.objects.get(pk=self.kwargs["pk"])) | Q(
            receiver=Customer.objects.get(pk=self.kwargs["pk"])))
