class ServiceError(Exception):
    """Base class for all service exceptions."""
    pass


class NotFoundError(ServiceError):
    """Raised when a resource cannot be found."""
    pass


class ValidationError(ServiceError):
    """Raised when business validation fails."""
    pass


class ConflictError(ServiceError):
    """Raised when a resource already exists."""
    pass



class RestaurantNotFoundError(NotFoundError):
    pass


class CategoryNotFoundError(NotFoundError):
    pass


class MenuItemNotFoundError(NotFoundError):
    pass


class MenuItemAlreadyExistsError(ConflictError):
    pass

class CategoryAlreadyExistsError(ConflictError):
    pass