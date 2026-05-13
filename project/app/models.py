from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum
from decimal import Decimal

class Campaign(models.Model):
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='campaigns')
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    goal = models.DecimalField(max_digits=12, decimal_places=2)
    file=models.FileField(upload_to='campaign_files/',null=True,blank=True,default=None)
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
        ('completed','Completed')
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.status}"

    def get_current_total(self):
        # We sum the 'cash' field for all entries linked to this campaign where is_paid is True
        result = self.project.filter(is_paid=True).aggregate(total=Sum('cash'))
        return result['total'] or 0

    
    def update_status(self):
        current_total = self.get_current_total() # Assuming this sums up successful Funds
        if current_total >= self.goal:
            self.status = 'completed'
        elif self.status == 'completed' and current_total < self.goal:
            # Optional: revert if a payment was refunded/deleted
            self.status = 'approved' 
        self.save() 
    


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



class WithdrawalRequest(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='payout_requests') # Unique name
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE)
    requested_at = models.DateTimeField(auto_now_add=True)

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"Request: {self.campaign.title} - {self.status}"


class Withdrawal(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('processing', 'Processing Payment'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    # Unique related_name: 'actual_withdrawals'
    campaign = models.ForeignKey('Campaign', on_delete=models.CASCADE, related_name='actual_withdrawals') 
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment: {self.campaign.title} - ₹{self.amount}"
