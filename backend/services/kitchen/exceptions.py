class BusinessError(Exception):
    pass


class AlreadyExistsError(BusinessError):
    pass

class MissingStuff(Exception):
    pass

