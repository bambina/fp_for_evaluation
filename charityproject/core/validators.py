from django.core.validators import RegexValidator

from core.constants import *

# Regex-based validators
max_length_255_validator = RegexValidator(r"^.{1,255}$", MAX_LENGTH_255_INVALID_ERR)

alpha_2_code_validator = RegexValidator(
    regex=r"^[A-Z]{2}$",
    message=ALPHA_2_CODE_INVALID_ERR,
)

numeric_code_validator = RegexValidator(
    regex=r"^\d{3}$",
    message=NUMERIC_CODE_INVALID_ERR,
)
