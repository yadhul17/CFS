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




from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

def update_withdraw_status(request, pk):
    if request.method == "POST":
        withdraw_req = get_object_or_404(WithdrawalRequest, id=pk)
        action = request.POST.get('action')
        
        if action == 'approve':
            withdraw_req.status = 'approved'
            withdraw_req.save()

            # --- EMAIL LOGIC ---
            subject = f"Withdrawal Approved: {withdraw_req.campaign.title}"
            message = (
                f"Hello {withdraw_req.requested_by.username},\n\n"
                f"Your withdrawal request for the campaign '{withdraw_req.campaign.title}' has been approved.\n"
                f"Your amount will be paid through UPI shortly.\n\n"
                f"Thank you for using FundWave!"
            )
            recipient_list = [withdraw_req.requested_by.email]
            
            try:
                send_mail(subject, message, settings.EMAIL_HOST_USER, recipient_list)
                messages.success(request, "Request approved and email sent to conductor.")
            except Exception as e:
                messages.warning(request, "Status updated, but email failed to send.")
        
        elif action == 'reject':
            withdraw_req.status = 'rejected'
            withdraw_req.save()
            messages.info(request, "Withdrawal request rejected.")

    return redirect('admindashboard')


from django.shortcuts import render
from .models import Campaign

from django.db.models import Q, Sum
from .models import Campaign, WithdrawalRequest, Withdrawal # Import your models

def admindashboard(request):
    campains = Campaign.objects.all()
    
    # Existing stats
    total_count = campains.count()
    pending_count = Campaign.objects.filter(Q(status="pending") | Q(status="Rejected")).count()
    approved_count = Campaign.objects.filter(status="Approved").count()

    # Payout related data
    withdraw_requests = WithdrawalRequest.objects.all()
    pending_withdraw_count = WithdrawalRequest.objects.filter(status="pending").count()

    # ✅ NEW: Get all successfully completed payments
    completed_payouts = Withdrawal.objects.filter(status="completed").order_by('-created_at')
    
    # ✅ NEW: Calculate total money paid out
    total_payout_sum = completed_payouts.aggregate(Sum('amount'))['amount__sum'] or 0

    context = {
        'campains': campains,
        'withdraw_requests': withdraw_requests,
        'completed_payouts': completed_payouts, # Pass this to HTML
        'total_payout_sum': total_payout_sum,
        'total_count': total_count,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'pending_withdraw_count': pending_withdraw_count,
    }

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
from django.conf import settings
from .models import WithdrawalRequest, Withdrawal

def process_upi_payment(request, pk):
    # This view displays the checkout page based on the Request
    withdraw_req = get_object_or_404(WithdrawalRequest, id=pk)
    
    context = {
        'withdraw': withdraw_req,
        'conductor': withdraw_req.requested_by,
        'amount': withdraw_req.campaign.get_current_total(), # Added () if it's a method
        'razorpay_id': withdraw_req.campaign.razorpay_account_id,
        'RAZORPAY_KEY_ID': settings.RAZORPAY_KEY_ID,
    }
    return render(request, 'payment.html', context)

def payment_success_callback(request):
    payment_id = request.GET.get('payment_id')
    request_id = request.GET.get('request_id') # From our JS redirect
    
    # 1. Get the original request
    withdraw_req = get_object_or_404(WithdrawalRequest, id=request_id)
    
 

    # 3. Create the ACTUAL Withdrawal record (the payment log)
    new_payout = Withdrawal.objects.create(
        campaign=withdraw_req.campaign,
        amount=withdraw_req.campaign.get_current_total(),
        razorpay_payment_id=payment_id,
        status='completed'
    )
    
    return render(request, 'success_page.html', {'payment_id': payment_id})


from django.shortcuts import render, get_object_or_404
from .models import Campaign



# def update_withdraw_status(request, id):
#     withdraw = get_object_or_404(WithdrawalRequest, id=id)

#     if request.method == "POST":
#         action = request.POST.get("action")

#         if action == "approve":
#             withdraw.status = "approved"
#         elif action == "reject":
#             withdraw.status = "rejected"

#         withdraw.save()
#         messages.success(request, "Withdraw request updated.")

#     return redirect('admindashboard')

def withdraw(request, id):
    campaign = get_object_or_404(Campaign, id=id)

    # Security check (Only creator can request withdrawal)
    if campaign.creator != request.user:
        messages.error(request, "You are not allowed to withdraw this campaign.")
        return redirect('admindashboard')

    # Remove any existing pending requests (duplicates)
    duplicates = WithdrawalRequest.objects.filter(campaign=campaign, status='pending')
    if duplicates.exists():
        duplicates.delete()
        messages.info(request, "Existing pending request(s) removed.")

    # Create a new withdrawal request
    WithdrawalRequest.objects.create(
        campaign=campaign,
        requested_by=request.user,
        status='pending'
    )

    messages.success(request, "Withdrawal request sent to admin successfully.")
    return redirect('dashboard')



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

from django.shortcuts import render
from django.db.models import Sum, Prefetch
from .models import Campaign, Fund, Withdrawal

@login_required
def userdashboard(request):
    user = request.user
    
    # Prefetch the latest withdrawal for each campaign
    # We use 'actual_withdrawals' because that is your related_name
    latest_withdrawal = Withdrawal.objects.order_by('-created_at')
    
    campaigns = Campaign.objects.filter(creator=user).prefetch_related(
        Prefetch('actual_withdrawals', queryset=latest_withdrawal, to_attr='latest_withdrawal_list')
    )
    
    # Logic to attach the single latest withdrawal object to each campaign
    for campaign in campaigns:
        campaign.last_withdrawal = campaign.latest_withdrawal_list[0] if campaign.latest_withdrawal_list else None

    funds = Fund.objects.filter(campain__creator=user, is_paid=True).order_by('-id')
    total_raised_all = funds.aggregate(Sum('cash'))['cash__sum'] or 0
    
    context = {
        'campaigns': campaigns,
        'funds': funds,
        'total_raised_all': total_raised_all,
    }
    return render(request, 'userdashboard.html', context)
    
def explore(request):
    # 1. Get parameters
    query = request.GET.get('q')
    category_filter = request.GET.get('cat')
    
    # 2. INITIALIZE the variable FIRST (This prevents the UnboundLocalError)
    campaigns_qs = Campaign.objects.all().prefetch_related('project')
    
    # 3. Apply Search Filter
    if query:
        campaigns_qs = campaigns_qs.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query)
        ).distinct()

    # 4. Apply Category Filter
    if category_filter:
        campaigns_qs = campaigns_qs.filter(category__iexact=category_filter)

    # 5. Process math (Now 'campaigns_qs' is guaranteed to exist)
    for campaign in campaigns_qs:
        current_total = campaign.get_current_total()
        goal = campaign.goal
        campaign.current_total_val = current_total
        campaign.balance = max(goal - Decimal(current_total), 0)
        
        if goal > 0:
            campaign.progress_percent = min((Decimal(current_total) / goal) * 100, 100)
        else:
            campaign.progress_percent = 0

    context = {
        'campains': campaigns_qs,
        'active_category': category_filter,
    }
    
    return render(request, 'explore.html', context)



from decimal import Decimal

def donate(request, id):
    # Fetch the campaign
    campaign = get_object_or_404(Campaign, id=id)
    
    # 1. TRIGGER THE DB UPDATE
    # This calls the method you wrote in models.py which checks live Sum and saves to DB
    campaign.update_status()
    
    # Refresh the object from DB to make sure we have the latest 'status' and 'total'
    campaign.refresh_from_db()

    # 2. CALCULATE LIVE DATA FOR UI
    # Use your model method instead of last_fund_record to ensure 100% accuracy
    current_total = campaign.get_current_total()
    goal = campaign.goal
    balance = max(goal - Decimal(current_total), 0)
    
    if goal > 0:
        progress_percent = min((Decimal(current_total) / goal) * 100, 100)
    else:
        progress_percent = 0

    # 3. HANDLE FORM SUBMISSION (POST)
    if request.method == "POST":
        # Check if campaign is already completed to prevent over-funding
        if campaign.status == 'completed':
            # Redirect or show error if goal is already met
            return redirect('allprojects')

        amount_str = request.POST.get('cash')
        name = request.POST.get('name')
        phoneno = request.POST.get('phoneno')

        if amount_str:
            amount = int(amount_str)
            
            # Razorpay Order Logic
            razorpay_order = razorpay_client.order.create({
                "amount": amount * 100,  # paise
                "currency": "INR",
                "payment_capture": "1"
            })
            
            order_id = razorpay_order['id']
            
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

    # 4. RENDER CONTEXT
    context = {
        'campaign': campaign,
        'current_state': current_total,
        'balance': balance,
        'progress': float(progress_percent),
        'goal_str': "{:,.2f}".format(campaign.goal),
    }

    return render(request, 'donate.html', context)
@csrf_exempt
def payment_success(request):
    if request.method == "POST":
        payment_id = request.POST.get('razorpay_payment_id')
        order_id = request.POST.get('razorpay_order_id')
        signature = request.POST.get('razorpay_signature')

        if not all([payment_id, order_id, signature]):
            return render(request, 'failure.html', {'error': "Missing payment details from Razorpay."})

        params_dict = {
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }

        try:
            razorpay_client.utility.verify_payment_signature(params_dict)

            # Use atomic transaction to ensure data consistency
            with transaction.atomic():
                fund = Fund.objects.select_for_update().filter(razorpay_order_id=order_id).first()
                
                if not fund:
                    return render(request, 'failure.html', {'error': "Order not found."})

                campaign = fund.campain # Accessing the campaign object

                if not fund.is_paid:
                    fund.is_paid = True
                    fund.razorpay_payment_id = payment_id
                    fund.save() 

                    # ✅ TRIGGER STATUS UPDATE HERE
                    # This calls your model method which calculates the total 
                    # and flips status to 'completed' if the goal is met.
                    campaign.update_status()

                    # Re-fetch/refresh total for the success page UI
                    actual_total_raised = campaign.get_current_total()
                    
                    # Update snapshot on the fund record
                    fund.total_raised = actual_total_raised
                    fund.save()
                else:
                    # If already paid (page refresh), just get the current total
                    actual_total_raised = campaign.get_current_total()

            # Logic for UI Progress Bar
            remain = max(campaign.goal - actual_total_raised, 0)
            print(remain)
            if remain==0:
                campaign.status = 'completed'
                campaign.save()

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

        except razorpay.errors.SignatureVerificationError:
            return render(request, 'failure.html', {'error': "Signature mismatch. Authenticity could not be verified."})
        except Exception as e:
            print(f"CRITICAL ERROR: {str(e)}") 
            return render(request, 'failure.html', {'error': f"An internal error occurred: {str(e)}"})

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
        campaign_file = request.FILES.get('file') 

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
                file=campaign_file,

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


