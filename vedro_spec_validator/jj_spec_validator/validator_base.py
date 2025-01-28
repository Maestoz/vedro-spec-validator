from abc import ABC, abstractmethod
from typing import Any


class BaseValidator(ABC):
    @abstractmethod
    def validate(self, mocked: Any) -> None:
        pass

    @abstractmethod
    def prepare_data(self) -> dict:
        pass

    @abstractmethod
    def output(self, e: Exception, text: str = None) -> None:
        pass

    @property
    @abstractmethod
    def func_name(self) -> str:
        pass

    @property
    @abstractmethod
    def spec_link(self) -> str | None:
        pass

    @property
    @abstractmethod
    def skip_if_failed_to_get_spec(self) -> bool:
        pass