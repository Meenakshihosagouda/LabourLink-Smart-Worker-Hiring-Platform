import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from datetime import datetime, date

# Regex patterns
NAME_REGEX = r'^[a-zA-Z\s]+$'
PHONE_REGEX = r'^\d{10}$'
# At least 8 characters, any type
PASSWORD_REGEX = r'^.{8,}$'
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.(com|net|in|org|co\.in)$'

def validate_email_custom(value):
    if not re.match(EMAIL_REGEX, value):
        raise ValidationError(
            _("Enter a valid email address."),
            code='invalid_email'
        )

def validate_name(value):
    if not re.match(NAME_REGEX, value):
        raise ValidationError(
            _("Name should contain only alphabetic characters and spaces."),
            code='invalid_name'
        )

def validate_phone(value):
    if not re.match(PHONE_REGEX, value):
        raise ValidationError(
            _("Phone number must be exactly 10 digits."),
            code='invalid_phone'
        )

def validate_password(value):
    if not re.match(PASSWORD_REGEX, value):
        raise ValidationError(
            _("Password must be at least 8 characters."),
            code='invalid_password'
        )

def validate_booking_date(booking_date):
    if isinstance(booking_date, str):
        try:
            booking_date = datetime.strptime(booking_date, '%Y-%m-%d').date()
        except ValueError:
            raise ValidationError(_("Invalid date format. Use YYYY-MM-DD."))
    
    if booking_date < date.today():
        raise ValidationError(_("Booking date cannot be in the past."))

def validate_booking_time(booking_date, booking_time_str):
    """
    Validates that the booking time is not in the past if the date is today.
    booking_time_str should be something that can be compared or a slot name.
    If it's a slot name, we need to map it to a time.
    """
    if isinstance(booking_date, str):
        booking_date = datetime.strptime(booking_date, '%Y-%m-%d').date()
    
    if booking_date == date.today():
        from django.utils import timezone
        now = timezone.localtime(timezone.now())
        # Mapping slots to end times (the hour at which the slot is no longer bookable)
        slots = {
            '08-10': 10,
            '10-12': 12,
            '12-14': 14,
            '14-16': 16,
            '16-18': 18,
            '18-20': 20,
        }
        
        end_hour = slots.get(booking_time_str)
        if end_hour is not None and now.hour >= end_hour:
             raise ValidationError(_("Selected time slot has already passed for today."))
