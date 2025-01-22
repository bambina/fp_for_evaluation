from core.validators import *
import pytest


class TestCoreValidators:
    def test_max_length_255_validator_valid(self):
        """Test max_length_255_validator with valid inputs"""
        valid_inputs = [
            "a" * 1,
            "a" * 255,
        ]
        for input_str in valid_inputs:
            max_length_255_validator(input_str)

    def test_max_length_255_validator_invalid(self):
        """Test max_length_255_validator with invalid inputs"""
        invalid_inputs = [
            "a" * 256,
            "",
        ]
        for input_str in invalid_inputs:
            with pytest.raises(ValidationError):
                max_length_255_validator(input_str)

    def test_alpha_2_code_validator_valid(self):
        """Test alpha_2_code_validator with valid inputs"""
        valid_codes = ["UK", "US", "GB"]
        for code in valid_codes:
            alpha_2_code_validator(code)

    def test_alpha_2_code_validator_invalid(self):
        """Test alpha_2_code_validator with invalid inputs"""
        invalid_codes = ["USA", "us", "1A"]
        for code in invalid_codes:
            with pytest.raises(ValidationError):
                alpha_2_code_validator(code)

    def test_numeric_code_validator_valid(self):
        """Test numeric_code_validator with valid inputs"""
        valid_codes = ["000", "123", "999"]
        for code in valid_codes:
            numeric_code_validator(code)

    def test_numeric_code_validator_invalid(self):
        """Test numeric_code_validator with invalid inputs"""
        invalid_codes = ["1234", "12", "abc"]
        for code in invalid_codes:
            with pytest.raises(ValidationError):
                numeric_code_validator(code)

    def test_validate_birth_date_valid(self):
        """Test validate_birth_date with valid inputs"""
        valid_dates = [
            ("2000-01-01", date(2000, 1, 1)),
            ("2000-01-02", date(2000, 1, 2)),
            ("2023-12-31", date(2023, 12, 31)),
            ("2024-02-29", date(2024, 2, 29)),
        ]
        for input_date, expected_date in valid_dates:
            result = validate_birth_date(input_date)
            assert result == expected_date

    def test_validate_birth_date_invalid(self):
        """Test validate_birth_date with invalid inputs"""
        invalid_dates = [
            "1999-12-31",  # Earlier than 2000-01-01
            "2000/01/01",  # Invalid separator
            "01-01-2000",  # Invalid format
            "2001-02-29",  # Not a leap year
            "2023-04-31",  # Invalid day for April
            "2024-12-31 00:00:00",  # Invalid format
        ]
        for input_date in invalid_dates:
            with pytest.raises(ValidationError):
                validate_birth_date(input_date)
