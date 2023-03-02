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
from .paginations import CustomerPagination
from .permissions import IsOwner
from .serializers import CustomerSerializer


class CustomerViewSet(mixins.CreateModelMixin,
                      mixins.ListModelMixin,
                      viewsets.GenericViewSet):
    queryset = Customer.objects.filter(is_deleted=False).order_by('-created_date')
    serializer_class = CustomerSerializer
    permission_classes = [IsCustomer]
    pagination_class = CustomerPagination

    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return super(CustomerViewSet, self).get_permissions()

    def list(self, request, *args, **kwargs):
        customer = request.user.customer
        serializer = self.get_serializer(instance=customer)

        return Response(serializer.data)


class CustomerCreateAPIView(CreateAPIView):
    queryset = Customer.objects.filter(is_deleted=False).order_by('-created_date')
    serializer_class = CustomerSerializer
    permission_classes = [IsAdminUser]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CustomerListAPIView(ListAPIView):
    serializer_class = CustomerSerializer
    pagination_class = CustomerPagination
    queryset = Customer.objects.filter(is_deleted=False).order_by('-created_date')


class GetBalanceAPIView(RetrieveAPIView):
    queryset = BankAccount.objects.filter(is_deleted=False)
    serializer_class = AccountSerializer
    lookup_field = 'owner'
    permission_classes = [IsAdminUser | IsOwner, ]

    def get_queryset(self):
        return BankAccount.objects.filter(Q(owner=self.kwargs["owner"]))
