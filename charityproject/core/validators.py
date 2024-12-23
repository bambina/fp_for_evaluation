from django.core.validators import RegexValidator

from core.constants import *

# Regex-based validators
max_length_255_validator = RegexValidator(r"^.{1,255}$", MAX_LENGTH_255_INVALID_ERR)
