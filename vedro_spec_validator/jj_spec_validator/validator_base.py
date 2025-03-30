from abc import ABC, abstractmethod
from typing import Any


class BaseValidator(ABC):

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