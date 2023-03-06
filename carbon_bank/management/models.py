import random
import uuid
from django.db import models
from django.db.models import Sum
from cores.models import CustomBaseClass


class BankAccount(CustomBaseClass):
    guid = models.UUIDField(unique=True, editable=False, default=uuid.uuid4)
    account_number = models.CharField(max_length=15, unique=True)
    owner = models.OneToOneField('customers.Customer', on_delete=models.CASCADE)
    is_active = models.BooleanField(default=False)

    @property
    def total_balance(self):
        aggregate_credit = BankTransaction.objects.filter(
            bank_account__pk=self.pk,
            is_debit=False,
        ).aggregate(total=Sum('amount'))

        aggregate_debit = BankTransaction.objects.filter(
            bank_account__pk=self.pk,
            is_debit=True,
        ).aggregate(total=Sum('amount'))

        credit = aggregate_credit.get('total')
        credit = credit if credit is not None else 0

        debit = aggregate_debit.get('total')
        debit = debit if debit is not None else 0

        return credit - debit

    @classmethod
    def generate_account_number(cls):
        return ''.join(random.choice('0123456789ABCDEFGHIKLMNOPRS') for _ in range(13))

    def __str__(self):
        return f'Account number: {self.account_number}     Balance: {self.total_balance}      Owner: {self.owner.fullname}' \
               f'Guid: {self.owner.guid}'


class BankTransaction(CustomBaseClass):
    bank_account = models.ForeignKey(
        BankAccount,
        related_name='mutations',
        on_delete=models.CASCADE,
    )
    sender = models.ForeignKey(
        'customers.Customer',
        related_name='sender',
        on_delete=models.CASCADE,
    )
    receiver = models.ForeignKey(
        'customers.Customer',
        related_name='receiver',
        on_delete=models.CASCADE,
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    is_debit = models.BooleanField(default=False)
    description = models.TextField()

    def __str__(self):
        return (f'Owner: {self.bank_account.owner.user.get_full_name()} '
                f'{"Debit: " if self.is_debit else "Credit: "} {self.amount}'
                f' MODIFIED DATE: {self.modified_date}')
