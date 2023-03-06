from django.db import transaction
from rest_framework import serializers

from customers.models import Customer
from management.models import BankAccount, BankTransaction


class AccountSerializer(serializers.ModelSerializer):
    owner = serializers.CharField(source='owner.user.get_full_name')
    balance = serializers.DecimalField(
        source='total_balance',
        decimal_places=2,
        max_digits=12,
    )

    class Meta:
        model = BankAccount
        fields = [
            'id', 'guid', 'account_number', 'owner', 'is_active', 'balance'
        ]


class AccountActivateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = [
            'is_active'
        ]


class TransactionSerializer(serializers.ModelSerializer):
    bank_account = serializers.CharField(source='bank_account.account_number')
    sender = serializers.CharField(source='sender.user.email')
    receiver = serializers.CharField(source='receiver.user.email')

    class Meta:
        model = BankTransaction
        fields = [
            'id', 'bank_account', 'sender', 'receiver', 'amount', 'is_debit',
        ]


class DepositTransactionSerializer(serializers.Serializer):
    # sender = serializers.PrimaryKeyRelatedField(
    #     queryset=Customer.objects.filter(is_deleted=False),
    #     write_only=True
    # )
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)

    def validate(self, attrs):
        # sender = attrs.get('sender')
        sender = Customer.objects.get(user=self.context["request"].user)
        if not sender.bankaccount.is_active:
            raise serializers.ValidationError({
                'sender': 'Bank account is not active.'
            })
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        sender = Customer.objects.get(user=self.context["request"].user)
        deposit_amount = validated_data.get('amount')
        deposit_tran = BankTransaction()
        deposit_tran.bank_account = sender.bankaccount
        deposit_tran.sender = sender
        deposit_tran.receiver = sender
        deposit_tran.amount = deposit_amount
        deposit_tran.is_debit = False
        deposit_tran.description = 'Amount deposit'
        deposit_tran.save()

        serializer = TransactionSerializer(instance=deposit_tran)
        return serializer.data


class WithdrawSerializer(DepositTransactionSerializer):

    @transaction.atomic
    def create(self, validated_data):
        sender = Customer.objects.get(user=self.context["request"].user)
        deposit_amount = validated_data.get('amount')
        sender_bank = BankAccount.objects.select_for_update().get(
            pk=sender.bankaccount.pk,
        )
        if sender_bank.total_balance < deposit_amount:
            raise serializers.ValidationError({
                'amount': 'Insufficient balance.'
            })
        withdraw_tran = BankTransaction()
        withdraw_tran.bank_account = sender.bankaccount
        withdraw_tran.sender = sender
        withdraw_tran.receiver = sender
        withdraw_tran.amount = deposit_amount
        withdraw_tran.is_debit = True
        withdraw_tran.description = 'Amount withdrawn'
        withdraw_tran.save()

        serializer = TransactionSerializer(instance=withdraw_tran)
        return serializer.data


class TransferTransactionSerializer(serializers.Serializer):
    sender = serializers.PrimaryKeyRelatedField(
        queryset=Customer.objects.filter(is_deleted=False),
    )
    destination_account_number = serializers.CharField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)

    @transaction.atomic
    def create(self, validated_data):
        sender = validated_data.get('sender')
        amount = validated_data.get('amount')
        account_number = validated_data.get('destination_account_number')

        try:
            receiver_bank = BankAccount.objects.select_for_update().get(
                account_number=account_number,
            )
        except BankAccount.DoesNotExist:
            raise serializers.ValidationError({
                'destination_account_number': 'Invalid account number.'
            })

        if not receiver_bank.is_active:
            raise serializers.ValidationError({
                'receiver': 'Bank account is not active.'
            })

        if not sender.bankaccount.is_active:
            raise serializers.ValidationError({
                'sender': 'Bank account is not active.'
            })

        # Be sure sender bank has sufficient balance!
        sender_bank = BankAccount.objects.select_for_update().get(
            pk=sender.bankaccount.pk,
        )
        if sender_bank.total_balance < amount:
            raise serializers.ValidationError({
                'amount': 'Insufficient balance.'
            })

        # Bank transaction for sender.
        transaction_sender = BankTransaction()
        transaction_sender.bank_account = sender.bankaccount
        transaction_sender.sender = sender
        transaction_sender.receiver = receiver_bank.owner
        transaction_sender.amount = amount
        transaction_sender.is_debit = True
        transaction_sender.description = 'Amount transferred'
        transaction_sender.save()

        # Bank transaction for receiver.
        transaction_receiver = BankTransaction()
        transaction_receiver.bank_account = receiver_bank
        transaction_receiver.sender = sender
        transaction_receiver.receiver = receiver_bank.owner
        transaction_receiver.amount = amount
        transaction_receiver.is_debit = False
        transaction_receiver.description = 'Amount received'
        transaction_receiver.save()

        serializer = TransactionSerializer(instance=transaction_sender)
        return serializer.data
