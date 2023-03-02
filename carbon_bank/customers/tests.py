from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate

from customers.api.views import CustomerViewSet
from .models import Customer


class CustomerAPITest(APITestCase):

    def setUp(self):
        self.factory = APIRequestFactory()

    def test_register_customer(self):
        payload = {
            'first_name': 'selcuk',
            'last_name': 'akarın',
            'address': 'ümraniye istanbul',
            'sex': Customer.MALE,
            'identity_number': '9876543210',
            'email': 'selcuk@gmail.com',
            'password': 'Selcuk123',
        }

        url = reverse('customers:customer-list')
        request = self.factory.post(path=url, data=payload)
        view = CustomerViewSet.as_view({'post': 'create'})
        response = view(request)
        customer = Customer.objects.get(user__username='selcuk@gmail.com')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(customer.bankaccount.is_active)

    def test_register_customer_with_email_exists(self):
        user = User.objects.create_user(
            username='selcuk51@carbonbank.com',
            email='selcuk51@carbonbank.com',
            password='test123',
            first_name='selcuk',
            last_name='akarın',
        )
        Customer.objects.create(
            identity_number='7777',
            address='atatürk mah. halitbey sokak',
            sex=Customer.MALE,
            user=user,
        )

        payload = {
            'first_name': 'ali',
            'last_name': 'veli',
            'sex': Customer.MALE,
            'identity_number': '0123456789',
            'email': 'selcuk51@carbonbank.com',
            'password': 'test123',
            'address': 'halkalı istanbul',
        }

        url = reverse('customers:customer-list')
        request = self.factory.post(path=url, data=payload)
        view = CustomerViewSet.as_view({'post': 'create'})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {
            'username': ['This username is already exists.'],
        })

    def test_retrieve_customer_account(self):
        self.test_register_customer()
        customer = Customer.objects.get(user__username='selcuk@gmail.com')

        url = reverse('customers:customer-list')
        request = self.factory.get(path=url)
        force_authenticate(request, customer.user)
        view = CustomerViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
