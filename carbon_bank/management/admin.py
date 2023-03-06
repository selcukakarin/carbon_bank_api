from .models import BankAccount, BankTransaction

from django.contrib import admin


class BankAccountAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'guid', 'account_number', 'owner', 'is_active', 'total_balance'
    ]
    list_display_links = ['id', 'is_active', 'total_balance']
    search_fields = ['guid', 'owner', 'account_number']
    list_filter = ['is_active']


admin.site.register(BankAccount, BankAccountAdmin)

#
# # Register your models here.
# admin.site.register(BankAccount)
admin.site.register(BankTransaction)
