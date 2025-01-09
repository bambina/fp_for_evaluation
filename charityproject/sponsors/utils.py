from datetime import datetime, date


def calculate_age(birth_date) -> int:
    """
    Calculates the age based on the given birth date.
    """
    # Reference:
    # https://www.geeksforgeeks.org/python-program-to-calculate-age-in-year/
    # TODO: Test leap year
    today = date.today()
    age = (
        today.year
        - birth_date.year
        - ((today.month, today.day) < (birth_date.month, birth_date.day))
    )
    return age
