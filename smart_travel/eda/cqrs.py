from abc import ABC, abstractmethod
from typing import TypedDict, Any


class CQRSCommand(ABC):
    @abstractmethod
    def execute(self, *args, **kwargs) -> bool: ...


class CQRSQueryResponse(TypedDict):
    status: bool
    data: Any


class CQRSQuery(ABC):
    @staticmethod
    @abstractmethod
    def execute(*args, **kwargs) -> CQRSQueryResponse: ...

    @staticmethod
    @abstractmethod
    def publish_event(*args, **kwargs): ...
