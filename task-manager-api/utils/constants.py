# Constantes de domínio — eliminam magic strings/numbers espalhados (RP-12 / AP-13).
VALID_STATUSES = ['pending', 'in_progress', 'done', 'cancelled']
CLOSED_STATUSES = ('done', 'cancelled')
VALID_ROLES = ['user', 'admin', 'manager']

MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200
MIN_PASSWORD_LENGTH = 4
MIN_PRIORITY = 1
MAX_PRIORITY = 5
DEFAULT_PRIORITY = 3
DEFAULT_COLOR = '#000000'

EMAIL_REGEX = r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$'
