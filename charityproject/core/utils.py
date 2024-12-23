# Description: Utility functions for the core app.


def write_success(stdout, style, msg):
    """
    Utility function to write a success message to stdout with SUCCESS styling.
    """
    stdout.write(style.SUCCESS(msg))


def write_error(stdout, style, msg):
    """
    Utility function to write an error message to stdout with ERROR styling.
    """
    stdout.write(style.ERROR(msg))
