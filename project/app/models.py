from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum
from decimal import Decimal

class Campaign(models.Model):
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='campaigns')
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    goal = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField()
    
    conductor_name = models.CharField(max_length=255)
    conductor_contact = models.CharField(max_length=255, blank=True, null=True)
    conductor_bio = models.TextField(blank=True, null=True)
    razorpay_account_id = models.CharField(max_length=100, blank=True, null=True)
    
    image = models.ImageField(upload_to='campaign_banners/')
    
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.status}"

    


class Fund(models.Model):
    name = models.CharField(max_length=20, null=True)
    phoneno = models.CharField(max_length=10, null=True)
    campain = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='project')
    cash = models.IntegerField()
    total_raised=models.IntegerField(default=0)
    is_paid = models.BooleanField(default=False)
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    donated_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f"Donation by {self.name} to {self.campain.title}"