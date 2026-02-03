from django.shortcuts import render,get_object_or_404,redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .models import *
from django.db.models import Q
from django.contrib.auth.decorators import login_required


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


from django.shortcuts import render
from .models import Campaign

def admindashboard(request):
    campains = Campaign.objects.all()
    
    total_count = campains.count()
    
   
    pending_count = Campaign.objects.filter(
        Q(status="pending") | Q(status="Rejected")
    ).count()  
    print(pending_count)  
    # 4. Get Approved Count (optional but useful for dashboards)
    approved_count = Campaign.objects.filter(status="Approved").count()

    context = {
        'campains': campains,
        'total_count': total_count,
        'pending_count': pending_count,
        'approved_count': approved_count,
    }

    print(f"Total: {total_count}, Pending: {pending_count}")

    
    return render(request, 'admindashboard.html', context)


def get_users(request):
    users = User.objects.filter(~Q(is_staff=True))
    print(users)
    return render(request,'users.html',{'users':users})
def update_campaign_status(request, id):
    if request.method == 'POST':
        value = request.POST.get('action')
        
      
        print(f"Action received: {value}")
        print(f"Campaign ID: {id}")

      
        campaign = get_object_or_404(Campaign, id=id)
        
        if value == 'approve':
            campaign.status = 'Approved'
        elif value == 'reject':
            campaign.status = 'Rejected'
        
        
        campaign.save()

   
    return redirect('admindashboard')



from django.shortcuts import render, get_object_or_404
from .models import Campaign

def campainview(request, id):
    # Fetch the campaign or return 404
    campaign = get_object_or_404(Campaign, id=id)

    # In your model, you don't have a 'raised' field yet. 
    # I'll set it to 0 for now, but you should add it to your model later!
    raised_amount = 0 
    
    # Calculate progress
    progress = 0
    if campaign.goal > 0:
        progress = (raised_amount / float(campaign.goal)) * 100

    # Formatting for the template
    context = {
        'campaign': campaign,
        'progress': progress,
        'raised_str': "{:,.2f}".format(raised_amount),
        'goal_str': "{:,.2f}".format(campaign.goal),
    }

    return render(request, 'campainview.html', context)

def home(request):
    campaigns = Campaign.objects.filter(status="Approved")[:3]
    
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





@login_required
def userdashboard(request):
    user = request.user  # 'user' now holds the logged-in User object
    print(user)      
       # This will print the username to your terminal
    print(user.id)
    campaigns=Campaign.objects.filter(creator=user.id)
    print(campaigns)
    return render(request, 'userdashboard.html',{'campaigns':campaigns})

def explore(request):
    query = request.GET.get('q')
    
    if query:
        # Filter: title contains query OR description contains query
        campains = Campaign.objects.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query) |
            Q(category__icontains=query)
        ).distinct()
    else:
        # If no query, show all
        
        campains=Campaign.objects.all()

    return render (request,'explore.html',{'campains':campains})

def donate(request,id):
    campaign=Campaign.objects.get(id=id)
    print(campaign)
    if request.method == 'POST':
        amount=request.POST.get('cash')
        print(amount)
    return render(request,'donate.html',{'campaign':campaign})


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
        
        # NEW: Collect Razorpay Account ID from the form
        razorpay_id = request.POST.get('razorpay_account_id')

        # 3. Collect File Data
        image = request.FILES.get('image')

        # 4. Create and Save the Model Instance
        try:
            new_campaign = Campaign.objects.create(
                creator=request.user,
                title=title,
                category=category,
                goal=goal,
                description=description,
                conductor_name=conductor_name,
                conductor_contact=conductor_contact,
                conductor_bio=conductor_bio,
                image=image,
                # Link the razorpay ID here
                razorpay_account_id=razorpay_id, 
                status='pending'
            )
            # No need for new_campaign.save() after .objects.create() 
            # as create() saves it to the DB automatically.
            
            messages.success(request, "Campaign submitted successfully! Waiting for admin approval.")
            return redirect('dashboard')
            
        except Exception as e:
            messages.error(request, f"Error creating campaign: {e}")

    return render(request, 'campain.html')
@login_required
def deletecampaign(request, id):
    # 1. Fetch the specific campaign instance
    campaign = get_object_or_404(Campaign, id=id)

    # 2. Security Check: Only the creator (or a staff member) can delete it
    if campaign.creator != request.user and not request.user.is_staff:
        messages.error(request, "You do not have permission to delete this campaign.")
        return redirect('dashboard')

    # 3. Execution: Use the instance 'campaign' in lowercase
    try:
        campaign.delete()
        messages.success(request, f"Campaign '{campaign.title}' deleted successfully.")
    except Exception as e:
        messages.error(request, f"Error deleting campaign: {e}")

    # 4. Redirect based on who deleted it
    if request.user.is_staff:
        return redirect('admindashboard')
    return redirect('dashboard')
    