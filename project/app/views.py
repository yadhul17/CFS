from django.shortcuts import render,get_object_or_404,redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .models import *

# Create your views here.

def adminlogin(request):
    if request.method=='POST':
        username=request.POST.get('username')
        password=request.POST.get('password')
        
        print(username,password)
        admin=authenticate(username=username,password=password)
        if admin is not None:
            if admin.is_staff:
                login(request, admin)
                return redirect('admindashboard')
            else:
                messages.error(request, "Access denied: Staff only.")
        else:
            messages.error(request, "Invalid username or password.")

        

    return render(request,'adminlogin.html')


def admindashboard(request):
    campains=Campaign.objects.all()
    print(campains)
    


    return render(request,'admindashboard.html',{'campains':campains})
def update_campaign_status(request, id):
    if request.method == 'POST':
        value = request.POST.get('action')
        
        # This will now show in your terminal!
        print(f"Action received: {value}")
        print(f"Campaign ID: {id}")

        # --- Actual Database Update ---
        # 1. Get the object
        campaign = get_object_or_404(Campaign, id=id)
        
        if value == 'approve':
            campaign.status = 'Approved'
        elif value == 'reject':
            campaign.status = 'Rejected'
        
        
        campaign.save()

   
    return redirect('admindashboard')

def home(request):
    campaigns = Campaign.objects.filter(status="Approved")
    
    print("Printing approved campaigns to server console:")
    print(campaigns)

    
    return render(request, 'home.html', {'campaigns': campaigns})


def userregister(request):
    if request.method=='POST':
        fullname=request.POST.get('fullname')
        email=request.POST.get('email')
        password=request.POST.get('password')
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return render(request, 'userregister.html')

        user = User.objects.create_user(
            username=email, 
            email=email, 
            password=password,
            first_name=fullname
        )

        if user:
            user.save()
            return redirect('login')
        

    return render(request,'userregister.html')


def userlogin(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
       
        user = authenticate(username=email, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back to FundWave, {user.username}!")
            return redirect('dashboard') 
        else:
            messages.error(request, "Invalid email or password. Please try again.")
           
            return render(request, 'userlogin.html')
            
    return render(request, 'userlogin.html')


def userdashboard(requset):
    return render(requset,'userdashboard.html')


def createcampain(request):
    if request.method == 'POST':
        # 1. Collect Text Data
        title = request.POST.get('title')
        category = request.POST.get('category')
        goal = request.POST.get('goal')
        description = request.POST.get('description')
        
        # 2. Collect Conductor Data
        conductor_name = request.POST.get('conductor_name')
        conductor_contact = request.POST.get('conductor_contact')
        conductor_bio = request.POST.get('conductor_bio')
        
        # 3. Collect File Data (Crucial for ImageField)
        image = request.FILES.get('image')

        # 4. Create and Save the Model Instance
        try:
            new_campaign = Campaign.objects.create(
                creator=request.user,  # Links the campaign to the logged-in intern/user
                title=title,
                category=category,
                goal=goal,
                description=description,
                conductor_name=conductor_name,
                conductor_contact=conductor_contact,
                conductor_bio=conductor_bio,
                image=image,
                status='pending'  # It starts as pending for admin approval
            )
            new_campaign.save()
            messages.success(request, "Campaign submitted successfully! Waiting for admin approval.")
            return redirect('dashboard')
            
        except Exception as e:
            messages.error(request, f"Error creating campaign: {e}")

    return render(request, 'campain.html')