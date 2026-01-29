from django.db import models
from django.contrib.auth.models import User

class Campaign(models.Model):
    # Link to the user who created it
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='campaigns')
    
    # Project Basics
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    goal = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField()
    
    # Conductor Information
    conductor_name = models.CharField(max_length=255)
    conductor_contact = models.CharField(max_length=255, blank=True, null=True)
    conductor_bio = models.TextField(blank=True, null=True)
    
    # Media
    image = models.ImageField(upload_to='campaign_banners/')
    
    # Moderation Logic
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.status}"
    

class Fund(models.Model):
    name=models.CharField(max_length=20,null=True)
    phoneno=models.CharField(max_length=10,null=True)
    campain=models.ForeignKey(Campaign,on_delete=models.CASCADE,related_name='project')
    cash=models.IntegerField()
    
    donated_at = models.DateTimeField(auto_now_add=True,null=True)
    def __str__(self):
        return f"{self.title} - {self.status}"
    def progress_percentage(self):
        if self.goal_amount <= 0:
            return 0
        return int((self.raised_amount / self.goal_amount) * 100)