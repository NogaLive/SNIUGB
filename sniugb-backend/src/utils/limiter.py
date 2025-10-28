from slowapi import Limiter
from slowapi.util import get_remote_address

# Limiter único y reusable por toda la app
limiter = Limiter(key_func=get_remote_address, default_limits=[])
