from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError
from django.db.models import Case, When, Value, IntegerField, Sum
from django.http import JsonResponse
from datetime import date, datetime, timedelta
import json
import requests
import time

from .models import Service, Worker, Hire, Review, ContractorProfile, BulkRequest, BulkReview, ClientProfile
from .expert_system import predict_best_worker, predict_best_contractor
from .utils import calculate_distance
from .ai import detect_service, chatbot_response
from django.http import JsonResponse
import json

@login_required
def submit_review(request, bid):
    hire = get_object_or_404(Hire, id=bid, user=request.user)
    
    if hire.status != 'Completed':
        messages.error(request, "You can only rate completed jobs.")
        return redirect('user_dashboard')

    if request.method == "POST":
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        Review.objects.update_or_create(
            hire=hire,
            defaults={'rating': int(rating), 'comment': comment}
        )
        messages.success(request, "Thank you for your review!")
        return redirect('user_dashboard')

    return render(request, 'review_form.html', {'hire': hire})

@login_required
def submit_bulk_review(request, bid):
    bulk_request = get_object_or_404(BulkRequest, id=bid, user=request.user)
    
    if bulk_request.status != 'Completed':
        messages.error(request, "You can only rate completed projects.")
        return redirect('user_dashboard')

    if request.method == "POST":
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        BulkReview.objects.update_or_create(
            request=bulk_request,
            defaults={'rating': int(rating), 'comment': comment}
        )
        messages.success(request, "Thank you for your review!")
        return redirect('user_dashboard')

    return render(request, 'review_form.html', {'bulk_request': bulk_request})
from .ai import detect_service


# ---------- Home & Search ----------

def home(request):
    if request.user.is_authenticated:
        # worker → worker home
        if hasattr(request.user, 'worker'):
            return redirect('worker_home')

        # contractor → contractor home
        if hasattr(request.user, 'contractorprofile'):
            return redirect('contractor_home')

    # normal users only see home
    services = Service.objects.all()
    
    context = {
        'services': services,
        'workers_count': Worker.objects.count(),
        'services_count': Service.objects.count(),
    }


    return render(request, 'home.html', context)


@login_required
def worker_home(request):
    worker = get_object_or_404(Worker, user=request.user)
    # Home shows summary
    jobs = Hire.objects.filter(worker=worker).order_by('-date')[:3]
    reviews = Review.objects.filter(hire__worker=worker).order_by('-id')[:3]
    
    return render(request, 'worker_home.html', {
        'worker': worker,
        'jobs': jobs,
        'reviews': reviews,
        'total_hires': Hire.objects.filter(worker=worker).count(),
        'pending_count': Hire.objects.filter(worker=worker, status='Pending').count(),
    })


@login_required
def worker_dashboard(request):
    worker = get_object_or_404(Worker, user=request.user)
    
    pending_jobs = Hire.objects.filter(worker=worker, status='Pending').order_by('-id')
    accepted_jobs = Hire.objects.filter(worker=worker, status='Accepted').order_by('-id')
    completed_jobs = Hire.objects.filter(worker=worker, status='Completed').order_by('-id')
    reviews = Review.objects.filter(hire__worker=worker).order_by('-id')
    
    return render(request, 'worker_dashboard.html', {
        'worker': worker,
        'pending_jobs': pending_jobs,
        'accepted_jobs': accepted_jobs,
        'completed_jobs': completed_jobs,
        'reviews': reviews,
    })


@login_required
def contractor_home(request):
    contractor = get_object_or_404(ContractorProfile, user=request.user)
    # Home shows a summary/teaser of pending jobs
    pending_jobs = BulkRequest.objects.filter(contractor=contractor, status='Pending').order_by('-id')[:3]
    reviews = BulkReview.objects.filter(request__contractor=contractor).order_by('-id')[:3]
    
    return render(request, 'contractor_home.html', {
        'contractor': contractor,
        'pending_jobs': pending_jobs,
        'reviews': reviews,
        # Summary counts for cards
        'total_pending': BulkRequest.objects.filter(contractor=contractor, status='Pending').count(),
        'total_accepted': BulkRequest.objects.filter(contractor=contractor, status='Accepted').count(),
        'total_completed': BulkRequest.objects.filter(contractor=contractor, status='Completed').count(),
    })


def search(request):
    q = request.GET.get('q', '').strip()
    is_ajax = request.GET.get('ajax') == '1'

    if not q:
        if is_ajax:
            return JsonResponse({'error': 'No query provided'})
        return redirect('home')
        
    service_name = detect_service(q)

    if service_name != "unknown":
        try:
            # Fetch the actual service object to get its correct slug
            service = Service.objects.get(name=service_name)
            url = reverse('service', kwargs={'slug': service.slug})
            if is_ajax:
                return JsonResponse({'url': url})
            return redirect(url)
        except Service.DoesNotExist:
            # Fallback for case mismatch or missing DB entry
            from django.utils.text import slugify
            url = reverse('service', kwargs={'slug': slugify(service_name)})
            if is_ajax:
                return JsonResponse({'url': url})
            return redirect(url)

    if is_ajax:
        return JsonResponse({'error': 'No results found'})

    return render(request, 'search.html', {
        'q': q,
        'msg': 'Could not detect service. Try describing your problem clearly.'
    })


def services_page(request):
    if request.user.is_authenticated and (hasattr(request.user, 'worker') or hasattr(request.user, 'contractorprofile')):
        return redirect('home')

    services = Service.objects.all()

    data = []
    for s in services:
        workers_count = Worker.objects.filter(service=s, is_available=True).count()
        contractors_count = ContractorProfile.objects.filter(service=s).count()

        data.append({
            'service': s,
            'workers': workers_count,
            'contractors': contractors_count,
        })

    return render(request, 'services.html', {'data': data})


def service_page(request, slug):
    if request.user.is_authenticated and (hasattr(request.user, 'worker') or hasattr(request.user, 'contractorprofile')):
        return redirect('home')

    service = get_object_or_404(Service, slug=slug)
    area = request.GET.get('area', '').strip()

    # Only GET params trigger results — session is for map pre-fill only
    lat = request.GET.get('lat')
    lon = request.GET.get('lon')

    # Save to session when user explicitly submits location
    if lat and lon:
        request.session['user_lat'] = lat
        request.session['user_lon'] = lon

    # Map pre-fill: restore previous pin without triggering results
    map_lat = lat or request.session.get('user_lat')
    map_lon = lon or request.session.get('user_lon')

    workers = Worker.objects.filter(service=service, is_available=True)

    recommended_worker = None

    # Expert System Recommendation — only when user explicitly submitted lat/lon
    if lat and lon:
        best_score = -1
        for w in workers:
            dist = calculate_distance(lat, lon, w.latitude, w.longitude)
            score = predict_best_worker(
                w.rating,
                dist,
                w.success_rate,
                w.jobs_completed
            )
            w.ml_score = score
            w.distance = dist
            if score > best_score:
                best_score = score
                recommended_worker = w

    if area:
        workers = workers.annotate(
            is_local=Case(
                When(area__icontains=area, then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            )
        ).order_by('-is_local', 'user__username')
    else:
        if lat and lon:
            workers = sorted(workers, key=lambda x: getattr(x, 'ml_score', 0), reverse=True)
        else:
            workers = workers.order_by('user__username')

    # Fetch user's phone for auto-fill
    user_phone = ''
    if request.user.is_authenticated:
        if hasattr(request.user, 'clientprofile'):
            user_phone = request.user.clientprofile.phone
        elif hasattr(request.user, 'worker'):
            user_phone = request.user.worker.phone
        elif hasattr(request.user, 'contractorprofile'):
            user_phone = request.user.contractorprofile.phone

    return render(request, 'service_detail.html', {
        'service': service,
        'workers': workers,
        'search_area': area,
        'recommended_worker': recommended_worker,
        'user_lat': lat,
        'user_lon': lon,
        'map_lat': map_lat,
        'map_lon': map_lon,
        'user_phone': user_phone,
    })


# ---------- Auth ----------


def login_view(request):
    if request.method == 'POST':
        u = request.POST['username']
        p = request.POST['password']
        user = authenticate(request, username=u, password=p)

        if user:
            login(request, user)

            # 👷 worker login
            if hasattr(user, 'worker'):
                return redirect('worker_home')

            # 🏢 contractor login
            elif hasattr(user, 'contractorprofile'):
                return redirect('contractor_home')

            # 👤 normal user
            else:
                return redirect('home')

        return render(request, 'login.html', {'error': 'Invalid credentials'})

    return render(request, 'login.html')







def logout_view(request):
    logout(request)
    messages.get_messages(request).used = True
    return redirect('home')




def register_user(request):
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        f = request.POST.get('first_name')
        e = request.POST.get('email')
        ph = request.POST.get('phone')

        if not all([u, p, f, e, ph]):
            messages.error(request, "All fields are required")
            return render(request, 'register_user.html')

        if User.objects.filter(username=u).exists():
            messages.error(request, "Username already exists")
            return render(request, 'register_user.html')

        user = User.objects.create_user(
            username=u, 
            password=p,
            first_name=f,
            email=e
        )
        
        ClientProfile.objects.create(user=user, phone=ph)

        messages.success(request, "Account created successfully! Please sign in.")
        return redirect('login')
    return render(request, 'register_user.html')




def register_worker(request):
    services = Service.objects.all()

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        service = request.POST.get('service')
        phone = request.POST.get('phone')
        area = request.POST.get('area')

        # 1️⃣ basic validation
        if not all([username, password, service, phone, area]):
            messages.error(request, "All fields are required")
            return render(request, 'register_worker.html', {'services': services})

        # 2️⃣ username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return render(request, 'register_worker.html', {'services': services})

        try:
            user = User.objects.create_user(
                username=username,
                password=password
            )

            Worker.objects.create(
                user=user,
                service_id=service,
                phone=phone,
                area=area
            )

        except IntegrityError:
            messages.error(request, "This worker account already exists")
            return render(request, 'register_worker.html', {'services': services})

        messages.success(request, "Worker registered successfully")
        return redirect('login')

    return render(request, 'register_worker.html', {'services': services})



# ---------- Dashboards ----------

@login_required
def dashboard(request):
    try:
        Worker.objects.get(user=request.user)
        return redirect('worker_dashboard')
    except Worker.DoesNotExist:
        return redirect('user_dashboard')


@login_required
def user_dashboard(request):
    hires = Hire.objects.filter(user=request.user)

    # Workers (for map / list)
    workers = Worker.objects.filter(is_available=True)

    # Services
    services = Service.objects.all()

    # Bulk hire requests by this user
    bulk_requests = BulkRequest.objects.filter(user=request.user)

    return render(request, 'user_dashboard.html', {
        'hires': hires,
        'workers': workers,
        'services': services,
        'bulk_requests': bulk_requests,
    })




@login_required
def worker_hires(request):
    worker = get_object_or_404(Worker, user=request.user)
    pending_jobs = Hire.objects.filter(worker=worker, status='Pending').order_by('-id')
    accepted_jobs = Hire.objects.filter(worker=worker, status='Accepted').order_by('-id')
    completed_jobs = Hire.objects.filter(worker=worker, status='Completed').order_by('-id')
    reviews = Review.objects.filter(hire__worker=worker).order_by('-id')
    
    return render(request, 'worker/bookings.html', {
        'worker': worker,
        'pending_jobs': pending_jobs,
        'accepted_jobs': accepted_jobs,
        'completed_jobs': completed_jobs,
        'reviews': reviews,
    })

@login_required
def worker_area(request):
    worker = get_object_or_404(Worker, user=request.user)
    return render(request, 'worker/area.html', {
        'worker': worker,
    })

@login_required
def worker_availability(request):
    worker = get_object_or_404(Worker, user=request.user)
    
    return render(request, 'worker/availability.html', {
        'worker': worker,
        'total_hires': Hire.objects.filter(worker=worker).count(),
        'pending_count': Hire.objects.filter(worker=worker, status='Pending').count(),
    })


# ---------- Hire ----------

@login_required
def hire_worker(request, wid):
    worker = get_object_or_404(Worker, id=wid)

    if request.method != "POST":
        return redirect('service', slug=worker.service.slug)

    name = request.POST.get('name')
    phone = request.POST.get('phone')
    email = request.POST.get('email')
    address = request.POST.get('address')
    problem = request.POST.get('problem')
    date_str = request.POST.get('date')
    time_slot = request.POST.get('time_slot')
    lat = request.POST.get('latitude')
    lon = request.POST.get('longitude')

    # 1️⃣ Validate inputs
    if not problem or not date_str or not address or not phone:
        messages.error(request, "Please fill required fields (Phone, Address, Problem, Date).")
        return redirect('service', slug=worker.service.slug)

    # 1.5️⃣ Date validation (No same-day booking for workers)
    try:
        booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, "Invalid date format.")
        return redirect('service', slug=worker.service.slug)

    if booking_date <= date.today():
        messages.error(request, "Bookings for individual professionals must be scheduled for tomorrow onwards.")
        return redirect('service', slug=worker.service.slug)

    # 2️⃣ Check worker availability
    if not worker.is_available:
        messages.error(request, "Worker is currently not available.")
        return redirect('service', slug=worker.service.slug)

    # 3️⃣ Check date conflict
    conflict = Hire.objects.filter(
        worker=worker,
        date=booking_date,
        status__in=["Pending", "Accepted"]
    ).exists()

    if conflict:
        messages.error(request, "Worker is already hired for this date.")
        return redirect('service', slug=worker.service.slug)

    # 4️⃣ Create hire
    Hire.objects.create(
        user=request.user,
        worker=worker,
        name=name or request.user.get_full_name() or request.user.username,
        phone=phone,
        email=email or request.user.email,
        address=address,
        problem=problem,
        date=booking_date,
        time_slot=time_slot or 'Morning',
        latitude=float(lat) if lat else None,
        longitude=float(lon) if lon else None,
        status="Pending"
    )

    messages.success(request, "Hire request sent successfully!")
    return redirect('user_dashboard')


@login_required
def my_hires(request):
    hires = Hire.objects.filter(user=request.user)
    bulk_requests = BulkRequest.objects.filter(user=request.user)
    
    context = {
        'pending_hires': hires.filter(status='Pending'),
        'accepted_hires': hires.filter(status='Accepted'),
        'completed_hires': hires.filter(status='Completed'),
        
        'pending_bulk': bulk_requests.filter(status='Pending'),
        'accepted_bulk': bulk_requests.filter(status='Accepted'),
        'completed_bulk': bulk_requests.filter(status='Completed'),
    }
    
    return render(request, 'my_bookings.html', context)


@login_required
def update_hire_status(request, bid, status):
    hire = get_object_or_404(Hire, id=bid)
    
    # Professional (Worker) updates status
    if hasattr(request.user, 'worker') and hire.worker.user == request.user:
        hire.status = status
        hire.save()
        
        # Trigger stat updates
        if status in ['Completed', 'Cancelled']:
            hire.worker.update_stats(status)
            
        messages.success(request, f"Hire status updated to {status}")
        return redirect('worker_hires')
    
    # Customer (User) marks as Completed
    elif hire.user == request.user and status == 'Completed':
        hire.status = 'Completed'
        hire.save()
        
        # Trigger ML stat updates
        hire.worker.update_stats('Completed')
        
        messages.success(request, "Job marked as completed. Please share your feedback!")
        return redirect('submit_review', bid=hire.id)

    return redirect('home')

def post_job(request):
    return render(request, 'post_job.html')

@login_required
def bulk_hire(request):
    services = Service.objects.all()
    contractors = []

    # Fetch user phone for auto-fill
    user_phone = ''
    if request.user.is_authenticated:
        if hasattr(request.user, 'clientprofile'):
            user_phone = request.user.clientprofile.phone
        elif hasattr(request.user, 'worker'):
            user_phone = request.user.worker.phone
        elif hasattr(request.user, 'contractorprofile'):
            user_phone = request.user.contractorprofile.phone

    if request.method == 'POST':
        service_id = request.POST.get('service')
        workers_needed = request.POST.get('workers_needed')
        area = request.POST.get('area', '').strip()

        # Defensive check
        if not service_id or not workers_needed:
            messages.error(request, "Please fill all required fields")
            return render(request, 'bulk_hire.html', {
                'services': services,
                'contractors': [],
                'user_phone': user_phone,
                'selected_service': Service.objects.get(id=service_id).slug if service_id else None
            })

        workers_needed = int(workers_needed)
        search_date = datetime.strptime(request.POST.get('start_date'), '%Y-%m-%d').date()

        # Get lat/lon from request or session
        user_lat = request.POST.get('latitude') or request.session.get('user_lat')
        user_lon = request.POST.get('longitude') or request.session.get('user_lon')

        # Save to session for persistence
        if request.POST.get('latitude') and request.POST.get('longitude'):
            request.session['user_lat'] = request.POST.get('latitude')
            request.session['user_lon'] = request.POST.get('longitude')

        # STEP 1: user is searching for contractors
        if not request.POST.get('contractor'):
            # Fetch all contractors for the service
            contractors_qs = ContractorProfile.objects.filter(service_id=service_id)
            
            # We'll filter in Python because we need to calculate complex availability for each
            contractors = []
            for c in contractors_qs:
                # Calculate reserved workers for this date (Accepted jobs starting on or before search date)
                reserved = BulkRequest.objects.filter(
                    contractor=c,
                    status='Accepted',
                    start_date__lte=search_date
                ).aggregate(Sum('workers_needed'))['workers_needed__sum'] or 0
                
                effective_available = c.total_workers - reserved
                
                if effective_available >= workers_needed:
                    # Add dynamic attribute for template display
                    c.dynamic_available = effective_available
                    
                    # Manual local match calculation
                    c.is_local = area.lower() in c.area.lower()

                    # Calculate Expert System recommendation score
                    dist = 999.0 # fallback
                    if user_lat and user_lon:
                        dist = calculate_distance(user_lat, user_lon, c.latitude, c.longitude)
                    
                    c.distance = dist
                    c.ml_score = predict_best_contractor(
                        c.rating,
                        c.success_rate,
                        effective_available,
                        c.total_projects,
                        dist
                    )
                    
                    contractors.append(c)

            # Identify recommended contractor
            recommended_contractor = None
            if contractors:
                # Sort by ml_score descending
                contractors.sort(key=lambda x: getattr(x, 'ml_score', 0), reverse=True)
                recommended_contractor = contractors[0]

            return render(request, 'bulk_hire.html', {
                'services': services,
                'contractors': contractors,
                'recommended_contractor': recommended_contractor,
                'selected_service': Service.objects.get(id=service_id).slug if service_id else None,
                'search_area': area,
                'user_lat': user_lat,
                'user_lon': user_lon,
                'user_phone': user_phone,
                # Pass contact details for persistence in hidden inputs
                'client_name': request.POST.get('name'),
                'client_phone': request.POST.get('phone'),
                'client_email': request.POST.get('email'),
                'strategic_notes': request.POST.get('strategic_notes')
            })

        # STEP 2: user selected a contractor
        contractor = get_object_or_404(
            ContractorProfile,
            id=request.POST.get('contractor')
        )
        
        # Re-calculate availability for the selected date
        reserved = BulkRequest.objects.filter(
            contractor=contractor,
            status='Accepted',
            start_date__lte=search_date
        ).aggregate(Sum('workers_needed'))['workers_needed__sum'] or 0
        
        effective_available = contractor.total_workers - reserved

        if effective_available < workers_needed:
            messages.error(request, f"Contractor only has {effective_available} workers available for that date.")
            return redirect('bulk_hire')

        BulkRequest.objects.create(
            user=request.user,
            contractor=contractor,
            service_id=service_id,
            name=request.POST.get('name'),
            phone=request.POST.get('phone'),
            email=request.POST.get('email'),
            workers_needed=int(request.POST['workers_needed']),
            description=request.POST.get('description'),
            strategic_notes=request.POST.get('strategic_notes'),
            area=request.POST.get('area'),
            duration=request.POST.get('duration'),
            start_date=request.POST.get('start_date'),
            latitude=float(user_lat) if user_lat else None,
            longitude=float(user_lon) if user_lon else None,
            status='Pending'
        )

        messages.success(request, "Bulk hire request sent successfully")
        return redirect('user_dashboard')

    # GET request
    selected_service = request.GET.get('service')
    return render(request, 'bulk_hire.html', {
        'services': services,
        'contractors': None,
        'selected_service': selected_service,
        'user_phone': user_phone,
    })


@login_required
def edit_profile(request):
    user = request.user
    worker = getattr(user, 'worker', None)
    contractor = getattr(user, 'contractorprofile', None)
    client = getattr(user, 'clientprofile', None)

    if request.method == "POST":
        # General User Fields
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.save()

        phone = request.POST.get('phone')

        # Role Specific Fields
        if worker:
            worker.phone = phone
            worker.area = request.POST.get('area', worker.area)
            worker.save()
        elif contractor:
            contractor.company_name = request.POST.get('company_name', contractor.company_name)
            contractor.phone = phone
            contractor.area = request.POST.get('area', contractor.area)
            contractor.save()
        elif client:
            client.phone = phone
            client.save()
        else:
            # Create or update ClientProfile for standard users
            from core.models import ClientProfile
            client_profile, created = ClientProfile.objects.get_or_create(user=user)
            client_profile.phone = phone
            client_profile.save()

        messages.success(request, "Profile updated successfully!")
        
        # Redirect based on role
        if worker:
            return redirect('worker_dashboard')
        elif contractor:
            return redirect('contractor_dashboard')
        return redirect('user_dashboard')

    return render(request, 'edit_profile.html', {
        'worker': worker,
        'contractor': contractor,
        'client': client,
    })


@login_required
def edit_worker_profile(request):
    return redirect('edit_profile')


@login_required
def edit_contractor_profile(request):
    return redirect('edit_profile')

@login_required
def toggle_worker_availability(request):
    worker = Worker.objects.get(user=request.user)
    worker.is_available = not worker.is_available
    worker.save()
    return redirect('worker_availability')



def register_contractor(request):
    services = Service.objects.all()   # ← REQUIRED

    if request.method == 'POST':
        user = User.objects.create_user(
            username=request.POST['username'],
            password=request.POST['password']
        )

        total = int(request.POST['total_workers'])

        ContractorProfile.objects.create(
            user=user,
            company_name=request.POST['company_name'],
            phone=request.POST['phone'],
            area=request.POST['area'],
            service_id=request.POST['service'],
            total_workers=total,
            available_workers=total
        )

        messages.success(request, "Contractor registered successfully")
        return redirect('login')

    return render(request, 'register_contractor.html', {
        'services': services   # ← MUST BE PASSED
    })


@login_required
def contractor_dashboard(request):
    contractor = request.user.contractorprofile

    pending_jobs = BulkRequest.objects.filter(contractor=contractor, status='Pending').order_by('-id')
    accepted_jobs = BulkRequest.objects.filter(contractor=contractor, status='Accepted').order_by('-id')
    completed_jobs = BulkRequest.objects.filter(contractor=contractor, status='Completed').order_by('-id')
    reviews = BulkReview.objects.filter(request__contractor=contractor).order_by('-id')

    if request.method == 'POST':
        total = int(request.POST['total_workers'])
        avail = int(request.POST['available_workers'])
        
        if avail > total:
            messages.error(request, "Available workers cannot exceed total workforce count.")
        else:
            contractor.total_workers = total
            contractor.available_workers = avail
            contractor.save()
            messages.success(request, "Workforce updated successfully!")

    return render(request, 'contractor_dashboard.html', {
        'contractor': contractor,
        'pending_jobs': pending_jobs,
        'accepted_jobs': accepted_jobs,
        'completed_jobs': completed_jobs,
        'reviews': reviews,
    })



@login_required
def bulk_action(request, bid, action):
    contractor = request.user.contractorprofile

    bulk = get_object_or_404(
        BulkRequest,
        id=bid,
        contractor=contractor
    )

    # ACCEPT
    if action == 'accept':
        # Dynamic check for that specific start date
        reserved = BulkRequest.objects.filter(
            contractor=contractor,
            status='Accepted',
            start_date__lte=bulk.start_date
        ).aggregate(Sum('workers_needed'))['workers_needed__sum'] or 0
        
        effective_available = contractor.total_workers - reserved

        if effective_available < bulk.workers_needed:
            messages.error(request, f"Not enough capacity for {bulk.start_date}. Available: {effective_available}")
            return redirect('contractor_dashboard')

        bulk.status = 'Accepted'
        bulk.save()

        # Update current snapshot ONLY if the job has already started
        if bulk.start_date <= date.today():
            contractor.available_workers -= bulk.workers_needed
            contractor.save()

        messages.success(request, "Job accepted")

    # REJECT
    elif action == 'reject':
        bulk.status = 'Rejected'
        bulk.save()
        messages.info(request, "Job rejected")

    # COMPLETE
    elif action == 'complete':
        # Contractor completes
        if hasattr(request.user, 'contractorprofile') and bulk.contractor == request.user.contractorprofile:
            if bulk.status != 'Accepted':
                messages.error(request, "Accept job first")
                return redirect('contractor_dashboard')

            bulk.status = 'Completed'
            bulk.save()

            # Trigger ML stat updates
            contractor.update_stats('complete')

            # return workers back ONLY if they were subtracted (job started)
            if bulk.start_date <= date.today():
                request.user.contractorprofile.available_workers += bulk.workers_needed
                request.user.contractorprofile.save()

            messages.success(request, "Job completed & workers returned")
            return redirect('contractor_dashboard')

        # Customer completes
        elif bulk.user == request.user:
            bulk.status = 'Completed'
            bulk.save()
            
            # Trigger stat updates
            if bulk.contractor:
                bulk.contractor.update_stats('complete')

            # Return workers if contractor was assigned and job had started
            if bulk.contractor and bulk.start_date <= date.today():
                bulk.contractor.available_workers += bulk.workers_needed
                bulk.contractor.save()
                
            messages.success(request, "Project marked as finished. Please rate the service!")
            return redirect('submit_bulk_review', bid=bulk.id)

    # CANCEL
    elif action == 'cancel':
        if bulk.status in ['Pending', 'Accepted']:
            bulk.status = 'Cancelled'
            bulk.save()
            
            # Trigger stat updates
            if bulk.contractor:
                bulk.contractor.update_stats('cancel')
                
                # If was accepted and started, return workers
                if bulk.status == 'Accepted' and bulk.start_date <= date.today():
                    bulk.contractor.available_workers += bulk.workers_needed
                    bulk.contractor.save()
            
            messages.warning(request, "Project cancelled.")
        else:
            messages.error(request, "Cannot cancel this project now.")
        return redirect('contractor_dashboard')

    return redirect('contractor_dashboard')




@csrf_exempt
@login_required
def save_contractor_location(request):
    if request.method == "POST":
        contractor = request.user.contractorprofile
        data = json.loads(request.body)
        lat = data.get("latitude")
        lon = data.get("longitude")

        contractor.latitude = lat
        contractor.longitude = lon

        # ⛔ VERY IMPORTANT → prevent block
        time.sleep(1)

        headers = {
            "User-Agent": "findmyworker-app"
        }

        try:
            url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}"
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                res = response.json()

                area = res.get("address", {}).get("city") or \
                       res.get("address", {}).get("town") or \
                       res.get("address", {}).get("village") or \
                       res.get("address", {}).get("suburb")

                if area:
                    contractor.area = area

        except:
            pass

        contractor.save()
        return JsonResponse({"status": "ok"})
    return JsonResponse({"status": "error"})


@csrf_exempt
@login_required
def save_worker_location(request):
    if request.method == "POST":
        worker = request.user.worker
        data = json.loads(request.body)
        lat = data.get("latitude")
        lon = data.get("longitude")

        worker.latitude = lat
        worker.longitude = lon

        time.sleep(1)
        headers = {"User-Agent": "findmyworker-app"}

        try:
            url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}"
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                res = response.json()
                area = res.get("address", {}).get("city") or \
                       res.get("address", {}).get("town") or \
                       res.get("address", {}).get("village") or \
                       res.get("address", {}).get("suburb")
                if area:
                    worker.area = area
        except:
            pass

        worker.save()
        return JsonResponse({"status": "ok"})
    return JsonResponse({"status": "error"})


def landing_page(request):
    """
    Renders the modern premium homepage.
    """
    return render(request, 'core/landing.html')


def chatbot_reply(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_message = data.get("message", "")
            reply = chatbot_response(user_message)
            return JsonResponse({"reply": reply})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Invalid request method"}, status=405)
