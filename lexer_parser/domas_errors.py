class ReservedWordError(Exception):
    def __init__(self, keyword):
        message = f'Reserved word {keyword} cannot be used in this context.'
        super().__init__(message)


class RedefinitionError(Exception):
    def __init__(self, id):
        message = f'ERROR: Redefinition of {id}'
        super().__init__(message)


class UndeclaredIdError(Exception):
    def __init__(self, id):
        message = f'ERROR: Use of undeclared identifier {id}'
        super().__init__(message)


class CompilationError(Exception):
    pass
