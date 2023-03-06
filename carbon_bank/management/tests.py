from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate

from customers.models import Customer
from .api.serializers import AccountActivateSerializer
from .models import BankAccount, BankTransaction


class BankAccountViewSetAPITest(APITestCase):

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

    @classmethod
    def create_deposit(cls, bank, amount):
        deposit = BankTransaction()
        deposit.bank_account = bank
        deposit.sender = bank.owner
        deposit.receiver = bank.owner
        deposit.amount = amount
        deposit.is_debit = False
        deposit.description = 'Amount deposit'
        deposit.save()

    def create_and_authenticate_su(self):
        self.user = User.objects.create_superuser(
            email='tes111t@test.com',
            password='test123',
            username="test_user"
        )
        self.client.force_authenticate(user=self.user)

    def setUp(self):
        self.factory = APIRequestFactory()

    def test_retrieve_account_list(self):
        self.create_and_authenticate_su()
        self.create_customer('selcuk@gmail.com', '123456')
        self.create_customer('selcuk2@gmail.com', '1234562')
        url = reverse('management:account-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            response.data["count"] == BankAccount.objects.all().count())

    def test_activate_deactivate_bank_account(self):
        self.create_and_authenticate_su()
        self.create_customer('selcuk1@gmail.com', '123456')
        customer1 = Customer.objects.get(user__username='selcuk1@gmail.com')
        bank_customer1 = customer1.bankaccount

        url = reverse('management:activate-account', args=[bank_customer1.guid])
        data = {}
        # activate bank account
        data['is_active'] = "True"
        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["is_active"], True)

        # deactivate bank account
        data['is_active'] = "False"
        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["is_active"], False)

    def test_deposit_account(self):
        self.create_customer('selcuk@gmail.com', '123456')
        customer = Customer.objects.get(user__username='selcuk@gmail.com')
        bankaccount = customer.bankaccount
        bankaccount.is_active = True
        bankaccount.save()
        self.client.force_authenticate(user=customer.user)

        # deposit with active account
        url = reverse('management:deposit')
        data = {'amount': 20000, 'sender': customer.pk}
        response = self.client.post(url, data)
        bankaccount.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(bankaccount.total_balance, 20000)

        # deposit with inactive account
        bankaccount.is_active = False
        bankaccount.save()
        bankaccount.refresh_from_db()
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(response.data['sender'][0]), 'Bank account is not active.')

    def test_withdraw_account(self):
        self.create_customer('selcuk1@gmail.com', '12345')
        customer = Customer.objects.get(user__email='selcuk1@gmail.com')
        bank_account = customer.bankaccount
        bank_account.is_active = True
        bank_account.save()
        self.create_deposit(bank_account, 100)

        # withdraw with active account
        data = {
            'sender': customer.pk,
            'amount': 10,
        }
        url = reverse('management:withdraw')
        self.client.force_authenticate(user=customer.user)
        response = self.client.post(url, data)
        bank_account.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(bank_account.total_balance, 90)

        # withdraw with inactive account
        bank_account.is_active = False
        bank_account.save()
        bank_account.refresh_from_db()
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(response.data['sender'][0]), 'Bank account is not active.')


    def test_withdraw_account_with_amount_exceeded(self):
        self.create_customer('selcuk1@gmail.com', '12345')
        customer = Customer.objects.get(user__email='selcuk1@gmail.com')
        bank_account = customer.bankaccount
        bank_account.is_active = True
        bank_account.save()
        self.create_deposit(bank_account, 100)

        data = {
            'sender': customer.pk,
            'amount': 500,
        }
        url = reverse('management:withdraw')
        self.client.force_authenticate(user=customer.user)
        response = self.client.post(url, data)
        bank_account.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(response.data['amount']), 'Insufficient balance.')

    def test_bank_transfer(self):
        self.create_customer('selcuk1@gmail.com', '12345')
        customer1 = Customer.objects.get(user__email='selcuk1@gmail.com')
        bank_customer1 = customer1.bankaccount
        bank_customer1.is_active = True
        bank_customer1.save()
        self.create_deposit(bank_customer1, 130000)

        self.create_customer('customer2@gmail.com', '54321')
        customer2 = Customer.objects.get(user__email='customer2@gmail.com')
        bank_customer2 = customer2.bankaccount
        bank_customer2.is_active = True
        bank_customer2.save()

        data = {
            'sender': customer1.pk,
            'destination_account_number': bank_customer2.account_number,
            'amount': 30000
        }
        url = reverse('management:transfer')
        self.client.force_authenticate(user=customer1.user)
        response = self.client.post(url, data)
        bank_customer1.refresh_from_db()
        bank_customer2.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(bank_customer1.total_balance, 100000)
        self.assertEqual(bank_customer2.total_balance, 30000)

    def test_bank_transfer_with_amount_exceeded(self):
        self.create_customer('selcuk1@gmail.com', '12345')
        customer1 = Customer.objects.get(user__email='selcuk1@gmail.com')
        bank_customer1 = customer1.bankaccount
        bank_customer1.is_active = True
        bank_customer1.save()
        self.create_deposit(bank_customer1, 1000)

        self.create_customer('selcuk2@gmail.com', '54321')
        customer2 = Customer.objects.get(user__email='selcuk2@gmail.com')
        bank_customer2 = customer2.bankaccount
        bank_customer2.is_active = True
        bank_customer2.save()

        data = {
            'sender': customer1.pk,
            'destination_account_number': bank_customer2.account_number,
            'amount': 5000,
        }
        url = reverse('management:transfer')
        self.client.force_authenticate(user=customer1.user)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(response.data['amount']), 'Insufficient balance.')

    def test_bank_transfer_using_inactive_account(self):
        self.create_customer('selcuk1@gmail.com', '12345')
        customer1 = Customer.objects.get(user__email='selcuk1@gmail.com')
        bank_customer1 = customer1.bankaccount
        bank_customer1.is_active = False
        bank_customer1.save()
        self.create_deposit(bank_customer1, 1000)

        self.create_customer('selcuk2@gmail.com', '54321')
        customer2 = Customer.objects.get(user__email='selcuk2@gmail.com')
        bank_customer2 = customer2.bankaccount
        bank_customer2.is_active = True
        bank_customer2.save()

        data = {
            'sender': customer1.pk,
            'destination_account_number': bank_customer2.account_number,
            'amount': 5000,
        }
        url = reverse('management:transfer')
        self.client.force_authenticate(user=customer1.user)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(response.data['sender']), 'Bank account is not active.')

    def test_bank_transfer_to_inactive_account(self):
        self.create_customer('selcuk1@gmail.com', '12345')
        customer1 = Customer.objects.get(user__email='selcuk1@gmail.com')
        bank_customer1 = customer1.bankaccount
        bank_customer1.is_active = True
        bank_customer1.save()
        self.create_deposit(bank_customer1, 1000)

        self.create_customer('selcuk2@gmail.com', '54321')
        customer2 = Customer.objects.get(user__email='selcuk2@gmail.com')
        bank_customer2 = customer2.bankaccount
        bank_customer2.is_active = False
        bank_customer2.save()

        data = {
            'sender': customer1.pk,
            'destination_account_number': bank_customer2.account_number,
            'amount': 1000,
        }
        url = reverse('management:transfer')
        self.client.force_authenticate(user=customer1.user)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(response.data['receiver']), 'Bank account is not active.')

    def test_bank_transfer_to_invalid_account(self):
        self.create_customer('selcuk1@gmail.com', '12345')
        customer1 = Customer.objects.get(user__email='selcuk1@gmail.com')
        bank_customer1 = customer1.bankaccount
        bank_customer1.is_active = True
        bank_customer1.save()
        self.create_deposit(bank_customer1, 1000)

        self.create_customer('selcuk2@gmail.com', '54321')
        customer2 = Customer.objects.get(user__email='selcuk2@gmail.com')
        bank_customer2 = customer2.bankaccount
        bank_customer2.is_active = True
        bank_customer2.save()

        data = {
            'sender': customer1.pk,
            'destination_account_number': '555555555',
            'amount': 1000,
        }
        url = reverse('management:transfer')
        self.client.force_authenticate(user=customer1.user)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(response.data['destination_account_number']), 'Invalid account number.')
