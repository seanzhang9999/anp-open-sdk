import fnmatch

from anp_foundation.config import get_global_config

config = get_global_config()
EXEMPT_PATHS = config.auth_middleware.exempt_paths


def is_exempt(path):
    """
       Check if a path is exempt from authentication.

       Args:
           path: The URL path to check

       Returns:
           bool: True if the path is exempt, False otherwise
       """
    # Check if path is in the exempt paths list
    for exempt_path in EXEMPT_PATHS:
        # Exact match for root path
        if exempt_path == "/" and path == "/":
            return True
        # Exact match for other paths
        elif path == exempt_path:
            return True
        # Path starts with exempt path that ends with a slash (directory match)
        elif exempt_path != '/' and exempt_path.endswith('/') and path.startswith(exempt_path):
            return True
        else:
            return any(fnmatch.fnmatch(path, pattern) for pattern in EXEMPT_PATHS)
    return False
