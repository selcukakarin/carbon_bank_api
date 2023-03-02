from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate

from customers.models import Customer
from .models import BankAccount, BankTransaction
from management.api.views import BankAccountViewSet, DepositViewSet, TransferViewSet, WithdrawViewSet


class BankAccountViewSetAPITest(APITestCase):

    @classmethod
    def register_customer(cls, email, identity_id):
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

    def setUp(self):
        self.factory = APIRequestFactory()

    def test_retrieve_account_list(self):
        self.register_customer('selcuk@gmail.com', '123456')
        customer = Customer.objects.get(user__username='selcuk@gmail.com')

        url = reverse('management:bankaccount-list')
        request = self.factory.get(path=url)
        force_authenticate(request, customer.user)
        view = BankAccountViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_account_activation_another_customer(self):
        self.register_customer('selcuk1@gmail.com', '123456')
        customer1 = Customer.objects.get(user__username='selcuk1@gmail.com')
        bank_customer1 = customer1.bankaccount

        self.register_customer('selcuk2@gmail.com', '123457')
        customer2 = Customer.objects.get(user__username='selcuk2@gmail.com')

        url = reverse('management:bankaccount-activate', args=[bank_customer1.guid])
        request = self.factory.put(path=url)
        force_authenticate(request, customer2.user)
        view = BankAccountViewSet.as_view({'put': 'activate'})
        response = view(request, guid=bank_customer1.guid)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_account_activation(self):
        self.register_customer('selcuk@gmail.com', '123456')
        customer = Customer.objects.get(user__username='selcuk@gmail.com')
        bank_account = customer.bankaccount

        url = reverse('management:bankaccount-activate', args=[bank_account.guid])
        request = self.factory.put(path=url)
        force_authenticate(request, customer.user)
        view = BankAccountViewSet.as_view({'put': 'activate'})
        response = view(request, guid=bank_account.guid)
        bank_account.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(bank_account.is_active)

    def test_block_account(self):
        self.register_customer('selcuk@gmail.com', '123456')
        customer = Customer.objects.get(user__username='selcuk@gmail.com')
        bank_account = customer.bankaccount
        bank_account.is_active = True
        bank_account.save()

        url = reverse('management:bankaccount-deactivate', args=[bank_account.guid])
        request = self.factory.put(path=url)
        force_authenticate(request, customer.user)
        view = BankAccountViewSet.as_view({'put': 'deactivate'})
        response = view(request, guid=bank_account.guid)
        bank_account.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(bank_account.is_active)

    def test_unblock_account(self):
        self.register_customer('selcuk@gmail.com', '123456')
        customer = Customer.objects.get(user__username='selcuk@gmail.com')
        bank_account = customer.bankaccount
        bank_account.is_active = False
        bank_account.save()

        url = reverse('management:bankaccount-activate', args=[bank_account.guid])
        request = self.factory.put(path=url)
        force_authenticate(request, customer.user)
        view = BankAccountViewSet.as_view({'put': 'activate'})
        response = view(request, guid=bank_account.guid)
        bank_account.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(bank_account.is_active)

    def test_deposit_account(self):
        self.register_customer('selcuk@gmail.com', '123456')
        customer = Customer.objects.get(user__username='selcuk@gmail.com')
        assertEqual = customer.bankaccount
        assertEqual.is_active = True
        assertEqual.save()

        url = reverse('management:deposit')
        data = {'amount': 20000}
        request = self.factory.post(path=url, data=data)
        force_authenticate(request, customer.user)
        view = DepositViewSet.as_view({'post': 'create'})
        response = view(request)
        assertEqual.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(assertEqual.total_balance, 20000)
        mutation = assertEqual.mutations.first()
        self.assertEqual(mutation.description, 'Amount deposit')

    def test_deposit_inactive_account(self):
        self.register_customer('selcuk@gmail.com', '123456')
        customer = Customer.objects.get(user__username='selcuk@gmail.com')

        url = reverse('management:deposit')
        data = {'amount': 20000}
        request = self.factory.post(path=url, data=data)
        force_authenticate(request, customer.user)
        view = DepositViewSet.as_view({'post': 'create'})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(response.data['sender'][0]), 'Bank account is not active.')

    def test_withdraw_account(self):
        self.register_customer('selcuk1@gmail.com', '12345')
        customer = Customer.objects.get(user__email='selcuk1@gmail.com')
        bank_account = customer.bankaccount
        bank_account.is_active = True
        bank_account.save()
        self.create_deposit(bank_account, 100)

        data = {
            'sender': customer.pk,
            'amount': 10,
        }
        url = reverse('management:withdraw')
        request = self.factory.post(path=url, data=data)
        force_authenticate(request, customer.user)
        view = WithdrawViewSet.as_view({'post': 'create'})
        response = view(request)
        bank_account.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(bank_account.total_balance, 90)
        mutation = bank_account.mutations.latest('pk')
        self.assertEqual(mutation.description, 'Amount withdrawn')

    def test_withdraw_from_inactive_account(self):
        self.register_customer('selcuk1@gmail.com', '12345')
        customer = Customer.objects.get(user__email='selcuk1@gmail.com')
        bank_account = customer.bankaccount
        bank_account.is_active = False
        bank_account.save()
        self.create_deposit(bank_account, 100)

        data = {
            'sender': customer.pk,
            'amount': 10,
        }
        url = reverse('management:withdraw')
        request = self.factory.post(path=url, data=data)
        force_authenticate(request, customer.user)
        view = WithdrawViewSet.as_view({'post': 'create'})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(response.data['sender'][0]), 'Bank account is not active.')

    def test_withdraw_account_with_amount_exceeded(self):
        self.register_customer('selcuk1@gmail.com', '12345')
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
        request = self.factory.post(path=url, data=data)
        force_authenticate(request, customer.user)
        view = WithdrawViewSet.as_view({'post': 'create'})
        response = view(request)
        bank_account.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(response.data['amount']), 'Insufficient balance.')

    def test_bank_transfer(self):
        self.register_customer('selcuk1@gmail.com', '12345')
        customer1 = Customer.objects.get(user__email='selcuk1@gmail.com')
        bank_customer1 = customer1.bankaccount
        bank_customer1.is_active = True
        bank_customer1.save()
        self.create_deposit(bank_customer1, 130000)

        self.register_customer('customer2@gmail.com', '54321')
        customer2 = Customer.objects.get(user__email='customer2@gmail.com')
        bank_customer2 = customer2.bankaccount
        bank_customer2.is_active = True
        bank_customer2.save()

        data = {
            'destination_account_number': bank_customer2.account_number,
            'amount': 30000
        }
        url = reverse('management:transfer')
        request = self.factory.post(path=url, data=data)
        force_authenticate(request, customer1.user)
        view = TransferViewSet.as_view({'post': 'create'})
        response = view(request)
        bank_customer1.refresh_from_db()
        bank_customer2.refresh_from_db()
        mutation_customer1 = bank_customer1.mutations.latest('pk')
        mutation_customer2 = bank_customer2.mutations.latest('pk')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(bank_customer1.total_balance, 100000)
        self.assertEqual(bank_customer2.total_balance, 30000)
        self.assertEqual(mutation_customer1.description, 'Amount transferred')
        self.assertEqual(mutation_customer2.description, 'Amount received')

    def test_bank_transfer_with_amount_exceeded(self):
        self.register_customer('selcuk1@gmail.com', '12345')
        customer1 = Customer.objects.get(user__email='selcuk1@gmail.com')
        bank_customer1 = customer1.bankaccount
        bank_customer1.is_active = True
        bank_customer1.save()
        self.create_deposit(bank_customer1, 1000)

        self.register_customer('selcuk2@gmail.com', '54321')
        customer2 = Customer.objects.get(user__email='selcuk2@gmail.com')
        bank_customer2 = customer2.bankaccount
        bank_customer2.is_active = True
        bank_customer2.save()

        data = {
            'destination_account_number': bank_customer2.account_number,
            'amount': 5000,
        }
        url = reverse('management:transfer')
        request = self.factory.post(path=url, data=data)
        force_authenticate(request, customer1.user)
        view = TransferViewSet.as_view({'post': 'create'})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(response.data['amount']), 'Insufficient balance.')

    def test_bank_transfer_using_inactive_account(self):
        self.register_customer('selcuk1@gmail.com', '12345')
        customer1 = Customer.objects.get(user__email='selcuk1@gmail.com')
        bank_customer1 = customer1.bankaccount
        bank_customer1.is_active = False
        bank_customer1.save()
        self.create_deposit(bank_customer1, 1000)

        self.register_customer('selcuk2@gmail.com', '54321')
        customer2 = Customer.objects.get(user__email='selcuk2@gmail.com')
        bank_customer2 = customer2.bankaccount
        bank_customer2.is_active = True
        bank_customer2.save()

        data = {
            'destination_account_number': bank_customer2.account_number,
            'amount': 5000,
        }
        url = reverse('management:transfer')
        request = self.factory.post(path=url, data=data)
        force_authenticate(request, customer1.user)
        view = TransferViewSet.as_view({'post': 'create'})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(response.data['sender']), 'Bank account is not active.')

    def test_bank_transfer_to_inactive_account(self):
        self.register_customer('selcuk1@gmail.com', '12345')
        customer1 = Customer.objects.get(user__email='selcuk1@gmail.com')
        bank_customer1 = customer1.bankaccount
        bank_customer1.is_active = True
        bank_customer1.save()
        self.create_deposit(bank_customer1, 1000)

        self.register_customer('selcuk2@gmail.com', '54321')
        customer2 = Customer.objects.get(user__email='selcuk2@gmail.com')
        bank_customer2 = customer2.bankaccount
        bank_customer2.is_active = False
        bank_customer2.save()

        data = {
            'destination_account_number': bank_customer2.account_number,
            'amount': 1000,
        }
        url = reverse('management:transfer')
        request = self.factory.post(path=url, data=data)
        force_authenticate(request, customer1.user)
        view = TransferViewSet.as_view({'post': 'create'})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(response.data['receiver']), 'Bank account is not active.')

    def test_bank_transfer_to_invalid_account(self):
        self.register_customer('selcuk1@gmail.com', '12345')
        customer1 = Customer.objects.get(user__email='selcuk1@gmail.com')
        bank_customer1 = customer1.bankaccount
        bank_customer1.is_active = True
        bank_customer1.save()
        self.create_deposit(bank_customer1, 1000)

        self.register_customer('selcuk2@gmail.com', '54321')
        customer2 = Customer.objects.get(user__email='selcuk2@gmail.com')
        bank_customer2 = customer2.bankaccount
        bank_customer2.is_active = True
        bank_customer2.save()

        data = {
            'destination_account_number': '555555555',
            'amount': 1000,
        }
        url = reverse('management:transfer')
        request = self.factory.post(path=url, data=data)
        force_authenticate(request, customer1.user)
        view = TransferViewSet.as_view({'post': 'create'})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(response.data['destination_account_number']), 'Invalid account number.')

    def test_retrieve_account_mutations(self):
        self.register_customer('selcuk1@gmail.com', '12345')
        customer = Customer.objects.get(user__email='selcuk1@gmail.com')
        bank_account = customer.bankaccount
        bank_account.is_active = True
        bank_account.save()
        self.create_deposit(bank_account, 1000)

        url = reverse(
            'management:bankaccount-mutations',
            args=[bank_account.guid.hex],
        )
        request = self.factory.get(path=url)
        force_authenticate(request, customer.user)
        view = BankAccountViewSet.as_view({'get': 'mutations'})
        response = view(request, guid=bank_account.guid)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
