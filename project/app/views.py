from django.shortcuts import render,get_object_or_404,redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .models import *
from django.db.models import Q
from django.contrib.auth.decorators import login_required
import razorpay
from django.conf import settings
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt

razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


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
    print(campaign.id)
    
    

    
  # 1. Get the latest 'snapshot' of the total raised from the Fund model
    last_fund_record = Fund.objects.filter(
        campain=campaign, 
        is_paid=True
    ).last()

    # 2. Extract the amount or default to 0 if no payments exist yet
    current_total = last_fund_record.total_raised if last_fund_record else 0

    # 3. Calculate Balance (Amount left to reach goal)
    balance = max(campaign.goal - current_total, 0)

    # 4. Calculate Progress Percentage
    if campaign.goal > 0:
        # Formula: (Current / Goal) * 100
        progress_percent = (current_total / campaign.goal) * 100
        # Cap at 100% so the progress bar doesn't break the UI
        progress_percent = min(progress_percent, 100)
    else:
        progress_percent = 0

    context = {
        'campaign': campaign,
        'current_state': current_total,      # Total money collected
        'balance': balance,                # Money still needed
        'progress': progress_percent,       # 0 to 100 for the bar
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





from django.db.models import Sum

@login_required
def userdashboard(request):
    user = request.user
    campaigns = Campaign.objects.filter(creator=user)
    
    # Get all paid funds for this user's campaigns
    funds = Fund.objects.filter(campain__creator=user, is_paid=True).order_by('-id')
    
    # Calculate the grand total raised across all campaigns
    total_raised_all = funds.aggregate(Sum('cash'))['cash__sum'] or 0
    
    context = {
        'campaigns': campaigns,
        'funds': funds,
        'total_raised_all': total_raised_all,
    }
    return render(request, 'userdashboard.html', context)
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



def donate(request, id):
    campaign = get_object_or_404(Campaign, id=id)
    
    # --- 1. CALCULATE LIVE DATA (For the Progress Bar) ---
    # Get the last successful fund record to find the total_raised snapshot
    last_fund_record = Fund.objects.filter(
        campain=campaign, 
        is_paid=True
    ).last()

    current_total = last_fund_record.total_raised if last_fund_record else 0
    balance = max(campaign.goal - current_total, 0)
    
    if campaign.goal > 0:
        progress_percent = min((current_total / campaign.goal) * 100, 100)
    else:
        progress_percent = 0

    # --- 2. HANDLE FORM SUBMISSION (POST) ---
    if request.method == "POST":
        amount_str = request.POST.get('cash')
        name = request.POST.get('name')
        phoneno = request.POST.get('phoneno')

        if amount_str:
            amount = int(amount_str)
            
            # Create Razorpay Order
            razorpay_order = razorpay_client.order.create({
                "amount": amount * 100,  # paise
                "currency": "INR",
                "payment_capture": "1"
            })
            
            order_id = razorpay_order['id']
            
            # Create local Fund record (Not paid yet)
            Fund.objects.create(
                campain=campaign,
                cash=amount,
                name=name,
                phoneno=phoneno,
                razorpay_order_id=order_id
            )
            
            return render(request, 'payment_checkout.html', {
                'order_id': order_id,
                'amount': amount,
                'campaign': campaign,
                'razorpay_key': settings.RAZORPAY_KEY_ID
            })

    # --- 3. RENDER THE DONATE PAGE (GET) ---
    context = {
        'campaign': campaign,
        'current_state': current_total,      # Used for the "Raised" text
        'balance': balance,                # Used for "Needed" text
        'progress': progress_percent,       # Used for bar width
        'goal_str': "{:,.2f}".format(campaign.goal),
    }

    return render(request, 'donate.html', context)

@csrf_exempt
def payment_success(request):
    if request.method == "POST":
        payment_id = request.POST.get('razorpay_payment_id')
        order_id = request.POST.get('razorpay_order_id')
        signature = request.POST.get('razorpay_signature')

        # 1. Validation: Ensure we actually got the data
        if not all([payment_id, order_id, signature]):
            return render(request, 'failure.html', {'error': "Missing payment details from Razorpay."})

        params_dict = {
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }

        try:
            # 2. Verify Signature
            razorpay_client.utility.verify_payment_signature(params_dict)

            with transaction.atomic():
                # 3. Fetch the fund record
                fund = Fund.objects.select_for_update().filter(razorpay_order_id=order_id).first()
                
                if not fund:
                    return render(request, 'failure.html', {'error': "Order not found."})

                # Only process if not already paid (prevents issues on page refresh)
                if not fund.is_paid:
                    fund.is_paid = True
                    fund.razorpay_payment_id = payment_id
                    fund.save() # Mark as paid first

                    # 4. Calculate total (Now that is_paid=True, the aggregate will include this fund)
                    campaign = fund.campain
                    total_data = Fund.objects.filter(
                        campain=campaign, 
                        is_paid=True
                    ).aggregate(Sum('cash'))
                    
                    actual_total_raised = total_data['cash__sum'] or 0
                    
                    # 5. Update the snapshot
                    fund.total_raised = actual_total_raised
                    fund.save()

            remain = max(campaign.goal - actual_total_raised, 0)
    
            progress_percentage = 0
            if campaign.goal > 0:
                progress_percentage = min((actual_total_raised / campaign.goal) * 100, 100)

            context = {
                'fund': fund,
                'campaign': campaign,
                'amount': fund.cash if fund else 0,
                'remain': remain,
                'actual_total_raised': actual_total_raised,
                'progress_percentage': progress_percentage,
                'goal': campaign.goal,
            }
            return render(request, 'success.html', context)
                
                # If already paid, just show success
               

        except razorpay.errors.SignatureVerificationError:
            return render(request, 'failure.html', {'error': "Signature mismatch. Authenticity could not be verified."})
        except Exception as e:
            # This will catch things like spelling errors (e.g., if 'campain' is wrong)
            print(f"CRITICAL ERROR: {str(e)}") 
            return render(request, 'failure.html', {'error': "An internal error occurred."})

    return redirect('home')
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
    
def working(request):
    return render(request,'working.html')


