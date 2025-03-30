from datetime import date


def calculate_age(birth_date) -> int:
    """
    Calculates the age based on the given birth date.

    This implementation is based on the example from:
    https://www.geeksforgeeks.org/python-program-to-calculate-age-in-year/
    """
    today = date.today()
    age = (
        today.year
        - birth_date.year
        - ((today.month, today.day) < (birth_date.month, birth_date.day))
    )
    return age
