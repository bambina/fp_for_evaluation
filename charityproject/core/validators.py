from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from datetime import datetime, date
from core.constants import *

# Regex-based validators
max_length_255_validator = RegexValidator(r"^.{1,255}$", MAX_LENGTH_255_INVALID_ERR)
max_length_2048_validator = RegexValidator(r"^.{1,2048}$", MAX_LENGTH_2048_INVALID_ERR)
max_length_50_validator = RegexValidator(r"^.{1,50}$", MAX_LENGTH_50_INVALID_ERR)

alpha_2_code_validator = RegexValidator(
    regex=r"^[A-Z]{2}$",
    message=ALPHA_2_CODE_INVALID_ERR,
)

numeric_code_validator = RegexValidator(
    regex=r"^\d{3}$",
    message=NUMERIC_CODE_INVALID_ERR,
)


def validate_birth_date(value: str) -> date:
    """
    Validates and parses a date string in the format 'YYYY-MM-DD'.
    Ensures the date is not earlier than 2000-01-01.
    """
    try:
        # Convert the string to a date object
        parsed_date = datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise ValidationError(
            f"Invalid date format: '{value}'. Expected format: YYYY-MM-DD."
        )

    # Ensure the date is not earlier than 2000-01-01
    min_date = date(2000, 1, 1)
    if parsed_date < min_date:
        raise ValidationError(
            f"The date '{value}' cannot be earlier than {min_date.isoformat()}."
        )

    return parsed_date
