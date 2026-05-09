from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

# 10-digit phone validator
phone_validator = RegexValidator(
    regex=r'^\d{10}$',
    message="Phone number must be exactly 10 digits."
)

class Service(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=2, default='S')
    desc = models.CharField(max_length=120)

    def __str__(self):
        return self.name


class Worker(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    phone = models.CharField(max_length=10, validators=[phone_validator])
    area = models.CharField(max_length=100)
    is_available = models.BooleanField(default=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    # ML Recommendation Fields
    rating = models.FloatField(default=0.0)
    jobs_completed = models.IntegerField(default=0)
    total_jobs = models.IntegerField(default=0)
    success_rate = models.FloatField(default=100.0)

    @property
    def calc_average_rating(self):
        reviews = Review.objects.filter(hire__worker=self)
        if reviews.exists():
            total = sum(r.rating for r in reviews)
            count = reviews.count()
            return float(f"{total / count:.1f}")
        return 0.0

    @property
    def calc_success_rate(self):
        total = Hire.objects.filter(worker=self, status__in=['Accepted', 'Completed', 'Cancelled']).count()
        if total == 0:
            return 100.0
        completed = Hire.objects.filter(worker=self, status='Completed').count()
        return float(f"{completed / total * 100:.1f}")

    def update_stats(self, new_status):
        """Update persistent ML fields based on new hire status."""
        if new_status == 'Completed':
            self.jobs_completed += 1
            self.total_jobs += 1
        elif new_status == 'Cancelled':
            self.total_jobs += 1
        if self.total_jobs > 0:
            self.success_rate = float(f"{self.jobs_completed / self.total_jobs * 100:.1f}")
        else:
            self.success_rate = 100.0
        self.save()

    def __str__(self):
        return f"{self.user.username} - {self.service.name}"

class ContractorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=10, validators=[phone_validator])
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    area = models.CharField(max_length=100)

    total_workers = models.IntegerField()
    available_workers = models.IntegerField()
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    # ML Recommendation Fields
    rating = models.FloatField(default=0.0)
    total_projects = models.IntegerField(default=0)
    projects_completed = models.IntegerField(default=0)
    success_rate = models.FloatField(default=100.0)

    @property
    def calc_average_rating(self):
        reviews = BulkReview.objects.filter(request__contractor=self)
        if reviews.exists():
            total = sum(r.rating for r in reviews)
            count = reviews.count()
            return float(f"{total / count:.1f}")
        return 0.0

    @property
    def calc_success_rate(self):
        total = BulkRequest.objects.filter(contractor=self, status__in=['Accepted', 'Completed', 'Cancelled']).count()
        if total == 0:
            return 100.0
        completed = BulkRequest.objects.filter(contractor=self, status='Completed').count()
        return float(f"{completed / total * 100:.1f}")

    def update_stats(self, action):
        """Update persistent ML fields based on bulk request action."""
        if action == 'complete':
            self.projects_completed += 1
            self.total_projects += 1
        elif action == 'cancel':
            self.total_projects += 1
        if self.total_projects > 0:
            self.success_rate = float(f"{self.projects_completed / self.total_projects * 100:.1f}")
        else:
            self.success_rate = 100.0
        self.save()

    def __str__(self):
        return self.company_name


class ClientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=10, validators=[phone_validator])

    def __str__(self):
        return self.user.username




class Hire(models.Model):
    STATUS = (
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    )

    TIME_SLOTS = (
        ('Morning', 'Morning (9 AM - 12 PM)'),
        ('Afternoon', 'Afternoon (12 PM - 4 PM)'),
        ('Evening', 'Evening (4 PM - 8 PM)'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE)
    
    # Contact & Job Details
    name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=10, blank=True, validators=[phone_validator])
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    
    # Precise Location
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    
    problem = models.TextField()
    date = models.DateField()
    time_slot = models.CharField(max_length=20, choices=TIME_SLOTS, default='Morning')
    
    status = models.CharField(max_length=20, choices=STATUS, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} → {self.worker.user.username}"


class Review(models.Model):
    hire = models.OneToOneField(Hire, on_delete=models.CASCADE)
    rating = models.IntegerField(default=5)
    comment = models.TextField(blank=True)

    def __str__(self):
        return f"{self.hire.worker.user.username} - {self.rating}★"


class BulkRequest(models.Model):
    STATUS = (
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Completed', 'Completed'),
        ('Rejected', 'Rejected'),
        ('Cancelled', 'Cancelled'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    contractor = models.ForeignKey(
        ContractorProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    
    # Contact Details
    name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=10, blank=True, validators=[phone_validator])
    email = models.EmailField(blank=True)

    workers_needed = models.IntegerField()
    area = models.CharField(max_length=120)
    duration = models.CharField(max_length=50)
    description = models.TextField()
    strategic_notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='Pending')
    start_date = models.DateField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class BulkReview(models.Model):
    request = models.OneToOneField(BulkRequest, on_delete=models.CASCADE)
    rating = models.IntegerField(default=5)
    comment = models.TextField(blank=True)
