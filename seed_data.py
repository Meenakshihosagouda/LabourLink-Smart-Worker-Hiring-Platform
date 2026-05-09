import os
import django
import random

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'findmy.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import Service, Worker, ContractorProfile, Booking, BulkRequest, Review, BulkReview

def seed_data():
    # 1. Clear existing sample data
    print("Cleaning up old sample data...")
    # Keep superusers
    User.objects.filter(is_superuser=False).delete()
    
    services = Service.objects.all()
    if not services.exists():
        print("No services found. Please run migrations first.")
        return

    # Expanded Pools for Unique Names
    first_names = [
        "Aarav", "Arjun", "Aditya", "Vihaan", "Vivaan", "Sai", "Ishaan", "Ayaan", "Krishna", "Aryan",
        "Rohan", "Siddharth", "Varun", "Kabir", "Reyansh", "Atharv", "Advait", "Shaurya", "Ishani",
        "Ananya", "Diya", "Aarya", "Saanvi", "Sanya", "Riya", "Kavya", "Aditi", "Ira", "Myra",
        "Rahul", "Amit", "Suresh", "Ramesh", "Vijay", "Anil", "Sunil", "Pankaj", "Deepak", "Manoj",
        "Rajesh", "Sanjay", "Alok", "Vikas", "Ashok", "Gopal", "Harish", "Kailash", "Lokesh", "Mohit",
        "Naveen", "Pradeep", "Sameer", "Tarun", "Umesh", "Vinod", "Yash", "Zeeshan", "Abhishek", "Bhavin",
        "Chirag", "Dinesh", "Eknath", "Farhan", "Gaurav", "Hemant", "Inder", "Jatin", "Kunal", "Lalit",
        "Mahesh", "Nitin", "Pranav", "Rishi", "Sohan", "Tushar", "Utkarsh", "Vivek", "Yuvraj", "Zubair",
        "Amar", "Bharat", "Chetan", "Dev", "Eshwar", "Fateh", "Gagan", "Hardik", "Imran", "Jagat",
        "Karan", "Lucky", "Manish", "Naman", "Om", "Pari", "Pooja", "Preeti", "Radha", "Sita",
        "Kiran", "Meera", "Asha", "Lata", "Usha", "Sneha", "Neha", "Priya", "Swati", "Anjali"
    ]
    
    last_names = [
        "Sharma", "Verma", "Gupta", "Malhotra", "Kapoor", "Khanna", "Mehra", "Joshi", "Patel", "Shah",
        "Reddy", "Nair", "Iyer", "Iyengar", "Menon", "Pillai", "Goud", "Yadav", "Singh", "Chauhan",
        "Pandey", "Mishra", "Trivedi", "Pathak", "Dubey", "Rao", "Hegde", "Shetty", "Bhat", "Kulkarni",
        "Deshpande", "Patil", "Deshmukh", "Chavan", "Pawar", "Shinde", "Bose", "Das", "Chatterjee", "Banerjee",
        "Mukherjee", "Sarkar", "Sen", "Roy", "Khan", "Ahmed", "Sheikh", "Sayyed", "Ansari", "Qureshi"
    ]

    worker_pool = []
    for f in first_names:
        for l in last_names:
            worker_pool.append(f"{f} {l}")
    
    random.shuffle(worker_pool)

    # Bangalore Locations
    bangalore_locations = [
        ("Koramangala", 12.9352, 77.6245),
        ("Indiranagar", 12.9719, 77.6412),
        ("HSR Layout", 12.9105, 77.6450),
        ("Whitefield", 12.9698, 77.7500),
        ("Jayanagar", 12.9308, 77.5838),
        ("MG Road", 12.9738, 77.6119),
        ("Malleshwaram", 12.9982, 77.5691),
        ("Banashankari", 12.9254, 77.5468),
        ("Hebbal", 13.0354, 77.5988),
        ("Sarjapur", 12.8680, 77.7809),
        ("Bannerghatta", 12.8364, 77.5925),
        ("Marathahalli", 12.9569, 77.7011),
        ("Rajajinagar", 12.9902, 77.5533),
        ("Basavanagudi", 12.9406, 77.5738),
        ("Ulsoor", 12.9817, 77.6285),
        ("Bellandur", 12.9304, 77.6784),
        ("Electronic City", 12.8452, 77.6632),
        ("Vijayanagar", 12.9712, 77.5361),
        ("Kalyan Nagar", 13.0232, 77.6425),
        ("Yeshwanthpur", 13.0235, 77.5564),
        ("JP Nagar", 12.9063, 77.5857),
        ("BTM Layout", 12.9165, 77.6101),
        ("Frazer Town", 12.9972, 77.6144),
        ("RT Nagar", 13.0177, 77.5944),
        ("Hennur", 13.0339, 77.6378)
    ]

    # Professional Business Naming Pool
    biz_adjectives = ["Premier", "Elite", "Pro", "Master", "Reliable", "Quality", "Swift", "City", "Modern", "Advanced"]
    biz_middle = ["Support", "Care", "Maintenance", "Engineering", "Builders", "Concepts", "Systems", "Design"]
    biz_endings = ["Pvt Ltd", "Corporation", "Group", "Services", "Industries", "Solutions", "Infrastructure"]

    print(f"Starting seeding for {services.count()} services...")

    worker_idx = 0
    generated_usernames = set()

    def get_unique_username(base):
        name = base.lower().replace(" ", "_")
        final_name = name
        counter = 1
        while final_name in generated_usernames or User.objects.filter(username=final_name).exists():
            final_name = f"{name}_{counter}"
            counter += 1
        generated_usernames.add(final_name)
        return final_name

    for service in services:
        print(f"Seeding {service.name} professionals...")
        
        # 10 Workers per service
        for i in range(10):
            fullname = worker_pool[worker_idx]
            username = get_unique_username(fullname)
            worker_idx += 1
            
            user = User.objects.create_user(username=username, password="1234")
            user.first_name = fullname.split(" ")[0]
            user.last_name = fullname.split(" ")[1] if len(fullname.split(" ")) > 1 else ""
            user.save()
            
            loc_name, lat, lon = random.choice(bangalore_locations)
            lat += random.uniform(-0.005, 0.005)
            lon += random.uniform(-0.005, 0.005)
            
            Worker.objects.create(
                user=user,
                service=service,
                phone=f"{random.randint(6, 9)}{random.randint(100000000, 999999999)}",
                area=loc_name,
                latitude=lat,
                longitude=lon,
                rating=0.0,
                jobs_completed=0,
                total_jobs=0,
                success_rate=100.0,
                is_available=True
            )

        # 10 Contractors per service
        for i in range(10):
            company_name = f"{random.choice(biz_adjectives)} {service.name} {random.choice(biz_middle)} {random.choice(biz_endings)}"
            username = get_unique_username(company_name.split(" ")[0] + "_" + str(random.randint(1000, 9999)))
            
            user = User.objects.create_user(username=username, password="1234")
            
            loc_name, lat, lon = random.choice(bangalore_locations)
            lat += random.uniform(-0.005, 0.005)
            lon += random.uniform(-0.005, 0.005)
            
            total_workers = random.randint(15, 60)
            
            ContractorProfile.objects.create(
                user=user,
                company_name=company_name,
                phone=f"{random.randint(6, 9)}{random.randint(100000000, 999999999)}",
                service=service,
                area=loc_name,
                total_workers=total_workers,
                available_workers=total_workers,
                latitude=lat,
                longitude=lon,
                rating=0.0,
                total_projects=0,
                projects_completed=0,
                success_rate=100.0
            )

    print("Refined seeding completed successfully!")

if __name__ == "__main__":
    seed_data()
