class BusinessError(Exception):
    """Base exception for all kitchen business errors."""
    pass


class NotFoundError(BusinessError):
    """Raised when an entity is not found or does not belong to the restaurant."""
    pass


class AlreadyExistsError(BusinessError):
    """Raised when an entity already exists."""
    pass


class InvalidStateTransitionError(BusinessError):
    """Raised when an invalid status transition is requested."""
    pass


class KitchenValidationError(BusinessError):
    """Raised when validation fails."""
    pass

