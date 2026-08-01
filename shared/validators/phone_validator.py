import re

from django.core.exceptions import ValidationError


def validate_phone(value):

    pattern = r"^\+?[0-9]{10,15}$"

    if not re.match(pattern, value):

        raise ValidationError(
            "Invalid phone number."
        )