import ipdb
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate

from management.models import BankAccount
from .api.views import CustomerCreateAPIView
from .models import Customer


class CustomerAPITest(APITestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_superuser(
            email='tes111t@test.com',
            password='test123',
            username="test_user"
        )
        self.client.force_authenticate(user=self.user)

    @classmethod
    def create_customer(cls, email, identity_id):
        user = User.objects.create_user(
            username=email,
            email=email,
            password='test123',
            first_name='selcuk',
            last_name='akarın',
        )

        customer = Customer.objects.create(
            identity_number=identity_id,
            address='istanbul',
            sex=Customer.MALE,
            user=user,
        )

        BankAccount.objects.create(
            account_number=BankAccount.generate_account_number(),
            owner=customer,
        )

    def test_create_customer(self):
        payload = {
            'first_name': 'selcuk',
            'last_name': 'akarın',
            'address': 'ümraniye istanbul',
            'sex': Customer.MALE,
            'identity_number': '9876543210',
            'email': 'selcuk@gmail.com',
            'password': 'Selcuk123',
        }
        url = reverse('customers:create')
        response = self.client.post(url, payload)
        customer = Customer.objects.get(user__username='selcuk@gmail.com')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(customer.bankaccount.is_active)

    def test_create_customer_with_email_exists(self):
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

        url = reverse('customers:create')
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {
            'username': ['This username is already exists.'],
        })

    def test_retrieve_customer_account(self):
        self.create_customer('selcuk1@gmail.com', '123456')
        self.create_customer('selcuk2@gmail.com', '1234561')
        # customer1 = Customer.objects.get(user__username='selcuk1@gmail.com')
        url = reverse('customers:list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            response.data["count"] == Customer.objects.all().count())
