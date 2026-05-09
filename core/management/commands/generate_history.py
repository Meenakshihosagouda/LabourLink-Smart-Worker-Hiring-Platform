import random
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from core.models import (
    Worker, Booking, Review,
    ContractorProfile, BulkRequest, BulkReview,
    Service, ClientProfile
)

# ─── Realistic seed data ────────────────────────────────────────────────────

WORKER_PROBLEMS = [
    "Pipe leaking under kitchen sink",
    "Ceiling fan not working, needs rewiring",
    "Bathroom tile cracked and needs replacing",
    "Water heater stopped heating",
    "Electrical short in living room",
    "AC unit making loud noise",
    "Fridge not cooling properly",
    "Washing machine leaking from bottom",
    "Door lock broken, need replacement",
    "Roof gutter blocked and overflowing",
    "Gas stove burner not igniting",
    "Toilet flush mechanism broken",
    "Garden tap dripping continuously",
    "Bedroom light switch not working",
    "Outdoor socket needs weatherproofing",
    "Drainage pipe blocked in bathroom",
    "Solar panel connection came loose",
    "Intercom system not functioning",
    "Paint peeling off exterior wall",
    "Window frame warped and won't close",
    "Damp patch appearing on living room wall",
    "Kitchen exhaust fan making grinding noise",
    "Garage door opener motor seized",
    "CCTV camera offline, needs reconnecting",
    "Geyser thermostat needs replacement",
]

WORKER_COMMENTS = [
    "Very professional, arrived on time and fixed everything quickly.",
    "Did a great job, highly recommend!",
    "Good work but took a bit longer than expected.",
    "Excellent service, very thorough and tidy.",
    "Solved the problem efficiently, fair price.",
    "Friendly and knowledgeable, would hire again.",
    "Fixed the issue but left a slight mess.",
    "Outstanding! Went above and beyond.",
    "Decent work, job done as requested.",
    "A little late but overall satisfied with the result.",
    "Very skilled, explained everything clearly.",
    "Quick response and high-quality repair.",
    "Reasonable price, satisfied with the outcome.",
    "Did not clean up properly after the job.",
    "Super fast and reliable, will use again.",
]

BULK_DESCRIPTIONS = [
    "Need workers for full office renovation including painting and flooring.",
    "Warehouse construction project requiring electrical and plumbing teams.",
    "Residential apartment complex needs 3 weeks of maintenance work.",
    "Shopping mall exterior and interior deep cleaning project.",
    "Factory floor safety upgrades and equipment installation.",
    "Multi-storey car park lighting and electrical overhaul.",
    "New school campus internal finishing and furniture assembly.",
    "Hospital ward refurbishment including ceiling, flooring and electrics.",
    "Hotel lobby and pool area renovation project.",
    "Government office block annual maintenance and repairs.",
    "Large housing estate communal areas painting project.",
    "Corporate headquarters fit-out and partition installation.",
    "Stadium seating replacement and structural inspection work.",
    "Industrial chimney inspection and repair.",
    "Airport terminal retail space renovation.",
    "Railway station platform and signage upgrade.",
    "University hostel deep cleaning and minor repairs.",
    "Supermarket refrigeration and HVAC servicing.",
    "Agricultural warehouse roofing and gutter replacement.",
    "Marina dock and electrical systems annual maintenance.",
]

BULK_STRATEGIC_NOTES = [
    "Prefer early morning start to avoid disruption.",
    "Site access requires security clearance — coordinate in advance.",
    "Materials will be provided on-site, no need to bring own.",
    "Weekend work only, no weekday access permitted.",
    "Parking available on-site for teams.",
    "Strict safety PPE compliance required at all times.",
    "Night shift work preferred to avoid foot traffic.",
    "",
    "Client will be present during initial day, please be punctual.",
    "Follow-up inspection by client after completion.",
]

BULK_AREAS = [
    "Hyderabad", "Mumbai", "Bangalore", "Chennai",
    "Delhi", "Pune", "Kolkata", "Ahmedabad",
    "Jaipur", "Lucknow",
]

DURATIONS = ["1 week", "2 weeks", "3 weeks", "1 month", "2 months", "3 days", "5 days"]

TIME_SLOTS = ["Morning", "Afternoon", "Evening"]

RATING_WEIGHTS = [5, 5, 4, 4, 4, 3, 3, 2, 1]   # skew toward higher ratings


class Command(BaseCommand):
    help = "Generate 20 random historical work records for every worker and contractor."

    def handle(self, *args, **options):
        self._generate_workers()
        self._generate_contractors()
        self.stdout.write(self.style.SUCCESS("\nDone! History generated for all workers and contractors."))

    # ─── WORKERS ────────────────────────────────────────────────────────────

    def _generate_workers(self):
        # Get or create a generic client user used as the "customer" for history
        client_user = self._get_or_create_client()

        workers = Worker.objects.all()
        if not workers.exists():
            self.stdout.write(self.style.WARNING("No workers found — skipping worker history."))
            return

        self.stdout.write(f"Generating history for {workers.count()} worker(s)...")

        for worker in workers:
            # Reset stats before regenerating to avoid double-counting
            worker.jobs_completed = 0
            worker.total_jobs = 0
            worker.success_rate = 100.0
            worker.rating = 0.0
            worker.save()

            completed_count = 0
            cancelled_count = 0

            for i in range(20):
                # Spread dates over the past 18 months
                days_ago = random.randint(10, 540)
                booking_date = date.today() - timedelta(days=days_ago)

                # Randomise status: mostly Completed, some Cancelled
                status = random.choices(
                    ["Completed", "Cancelled"],
                    weights=[80, 20]
                )[0]

                booking = Booking.objects.create(
                    user=client_user,
                    worker=worker,
                    name=client_user.get_full_name() or "Historic Client",
                    phone="9000000000",
                    email=client_user.email or "history@example.com",
                    address=f"{random.randint(1, 200)}, Heritage Lane",
                    problem=random.choice(WORKER_PROBLEMS),
                    date=booking_date,
                    time_slot=random.choice(TIME_SLOTS),
                    status=status,
                )

                # Add a review for every Completed booking
                if status == "Completed":
                    completed_count += 1
                    rating = random.choice(RATING_WEIGHTS)
                    Review.objects.create(
                        booking=booking,
                        rating=rating,
                        comment=random.choice(WORKER_COMMENTS),
                    )
                else:
                    cancelled_count += 1

            # Recompute and save stats
            total = completed_count + cancelled_count
            worker.jobs_completed = completed_count
            worker.total_jobs = total
            worker.success_rate = round((completed_count / total) * 100, 1) if total else 100.0

            # Compute average rating from the new reviews
            reviews = Review.objects.filter(booking__worker=worker)
            if reviews.exists():
                worker.rating = round(sum(r.rating for r in reviews) / reviews.count(), 1)

            worker.save()

            self.stdout.write(
                f"  Worker '{worker.user.username}': "
                f"{completed_count} completed, {cancelled_count} cancelled | "
                f"Rating: {worker.rating} | Success: {worker.success_rate}%"
            )

    # ─── CONTRACTORS ────────────────────────────────────────────────────────

    def _generate_contractors(self):
        client_user = self._get_or_create_client()

        contractors = ContractorProfile.objects.all()
        if not contractors.exists():
            self.stdout.write(self.style.WARNING("No contractors found — skipping contractor history."))
            return

        self.stdout.write(f"\nGenerating history for {contractors.count()} contractor(s)...")

        for contractor in contractors:
            # Reset stats
            contractor.projects_completed = 0
            contractor.total_projects = 0
            contractor.success_rate = 100.0
            contractor.rating = 0.0
            contractor.save()

            completed_count = 0
            cancelled_count = 0

            for i in range(20):
                days_ago = random.randint(10, 540)
                start_date = date.today() - timedelta(days=days_ago)

                status = random.choices(
                    ["Completed", "Cancelled"],
                    weights=[80, 20]
                )[0]

                workers_used = random.randint(2, min(contractor.total_workers, 30))

                bulk = BulkRequest.objects.create(
                    user=client_user,
                    contractor=contractor,
                    service=contractor.service,
                    name=client_user.get_full_name() or "Historic Client",
                    phone="9000000000",
                    email=client_user.email or "history@example.com",
                    workers_needed=workers_used,
                    area=random.choice(BULK_AREAS),
                    duration=random.choice(DURATIONS),
                    description=random.choice(BULK_DESCRIPTIONS),
                    strategic_notes=random.choice(BULK_STRATEGIC_NOTES),
                    start_date=start_date,
                    status=status,
                )

                if status == "Completed":
                    completed_count += 1
                    rating = random.choice(RATING_WEIGHTS)
                    BulkReview.objects.create(
                        request=bulk,
                        rating=rating,
                        comment=random.choice(WORKER_COMMENTS),
                    )
                else:
                    cancelled_count += 1

            # Recompute stats
            total = completed_count + cancelled_count
            contractor.projects_completed = completed_count
            contractor.total_projects = total
            contractor.success_rate = round((completed_count / total) * 100, 1) if total else 100.0

            reviews = BulkReview.objects.filter(request__contractor=contractor)
            if reviews.exists():
                contractor.rating = round(sum(r.rating for r in reviews) / reviews.count(), 1)

            contractor.save()

            self.stdout.write(
                f"  Contractor '{contractor.company_name}': "
                f"{completed_count} completed, {cancelled_count} cancelled | "
                f"Rating: {contractor.rating} | Success: {contractor.success_rate}%"
            )

    # ─── HELPERS ────────────────────────────────────────────────────────────

    def _get_or_create_client(self):
        """Return (or create) a dedicated client user for historical records."""
        user, created = User.objects.get_or_create(
            username="history_client",
            defaults={
                "first_name": "Historic",
                "last_name": "Client",
                "email": "history@example.com",
            }
        )
        if created:
            user.set_password("historyclient123")
            user.save()
            ClientProfile.objects.create(user=user, phone="9000000000")
            self.stdout.write("  Created 'history_client' user for historic records.")
        return user
