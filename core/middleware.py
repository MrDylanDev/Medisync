from threading import local

_request_local = local()


def get_current_user():
    """Get the current request user from thread-local storage."""
    return getattr(_request_local, 'user', None)


class RequestUserMiddleware:
    """
    Middleware that stores the current request user in thread-local storage.
    
    This enables models like BaseModel to auto-set the created_by field
    without needing to pass the user explicitly through every code path.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _request_local.user = getattr(request, 'user', None)
        response = self.get_response(request)
        _request_local.user = None
        return response
