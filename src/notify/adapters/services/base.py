from abc import ABC


class ServiceError(Exception):
    def __init__(self, message):
        self.message = message


class BaseService(ABC):
    @classmethod
    async def create_service(cls, *args, **kwargs):
        """Service factory method"""
        instance = cls()
        return instance
