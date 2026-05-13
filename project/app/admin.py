from django.contrib import admin
from .models import Campaign,Fund,WithdrawalRequest
admin.site.register(Campaign)
admin.site.register(Fund)
admin.site.register(WithdrawalRequest)
# Register your models here.
