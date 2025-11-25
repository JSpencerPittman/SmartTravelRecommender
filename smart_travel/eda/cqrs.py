from abc import ABC, abstractmethod
from typing import TypedDict


class CQRSCommand(ABC):
    @abstractmethod
    def execute(self, *args, **kwargs) -> bool: ...

    @staticmethod
    @abstractmethod
    def publish_event(*args, **kwargs): ...


class CQRSQueryResponse(TypedDict):
    status: bool


class CQRSQuery(ABC):
    @staticmethod
    @abstractmethod
    def execute(*args, **kwargs) -> CQRSQueryResponse: ...

    @staticmethod
    @abstractmethod
    def publish_event(*args, **kwargs): ...
