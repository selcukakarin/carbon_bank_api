from .models import BankAccount,  BankTransaction


from django.contrib import admin

# Register your models here.
admin.site.register(BankAccount)
admin.site.register(BankTransaction)