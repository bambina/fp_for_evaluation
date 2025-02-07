# Constants used in the application

# Logger names
PROJECT_LOGGER_NAME = "charityproject"

# Error messages
MAX_LENGTH_255_INVALID_ERR = "Must be 255 characters or fewer"
MAX_LENGTH_2048_INVALID_ERR = "Must be 2048 characters or fewer"
MAX_LENGTH_50_INVALID_ERR = "Must be 50 characters or fewer"
ALPHA_2_CODE_INVALID_ERR = (
    "This field must contain exactly 2 uppercase alphabetic characters."
)
NUMERIC_CODE_INVALID_ERR = "This field must contain exactly 3 numeric digits."

# Field length constraints for relational and vector databases
MAX_QUESTION_LEN = 255
MAX_ANSWER_LEN = 2048
MAX_CHILD_NAME_LEN = 255
MAX_CHILD_PROFILE_LEN = 2048
