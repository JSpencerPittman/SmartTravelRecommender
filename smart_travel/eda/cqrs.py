from abc import ABC, abstractmethod
from typing import TypedDict


class CQRSCommand(ABC):
    @abstractmethod
    def execute(self, *args, **kwargs) -> bool: ...


class CQRSQueryResponse(TypedDict):
    status: bool


class CQRSQuery(ABC):
    @staticmethod
    @abstractmethod
    def execute(*args, **kwargs) -> CQRSQueryResponse: ...
