class RepoError(Exception):
    def __init__(self, message):
        self.message = message


class RepoObjectNotFound(RepoError):
    pass
