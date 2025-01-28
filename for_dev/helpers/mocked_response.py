from types import TracebackType
from typing import Any, Generator, Optional, Type, Union

from jj.expiration_policy import ExpirationPolicy
from jj.matchers import LogicalMatcher, RequestMatcher
from jj.mock import Mocked, RemoteHandler, RemoteResponseType, mocked
from rtry._types import AttemptValue, DelayCallable, DelayValue, LoggerCallable, TimeoutValue


__all__ = ("mocked_response",)


class MockedResponse(Mocked):
    """Класс для управления фиктивными ответами с возможностью ожидания определенного количества запросов.

    Args:
        handler (RemoteHandler): Обработчик, который будет использоваться для регистрации и дерегистрации.
        disposable (bool): Указывает, является ли ответ одноразовым. По умолчанию True.
        prefetch_history (bool): Позволяет предварительно загружать историю. По умолчанию True.
        wait_for_requests (int): Количество запросов, которые ждут. По умолчанию 1.
        wait_for_timeout (Union[float, int]): Время ожидания для запросов в секундах. По умолчанию 30 секунд.
    """
    def __init__(self, handler: RemoteHandler, *,
                 disposable: bool = True,
                 prefetch_history: bool = True,
                 wait_for_requests: int = 1,
                 wait_for_timeout: Union[float, int] = 30) -> None:
        super().__init__(handler, disposable=disposable, prefetch_history=prefetch_history)
        self._wait_for_requests = wait_for_requests
        self._wait_for_timeout = wait_for_timeout

    def __await__(self) -> Generator[Any, None, "MockedResponse"]:
        """Асинхронный метод для регистрации обработчика.

        Returns:
            Generator[Any, None, MockedResponse]: Генератор, возвращающий экземпляр MockedResponse.
        """
        yield from self._handler.register().__await__()
        return self

    async def __aexit__(self,
                        exc_type: Optional[Type[BaseException]],
                        exc_val: Optional[BaseException],
                        exc_tb: Optional[TracebackType]) -> None:
        """Асинхронный метод для выхода из контекста, дерегистрирующий обработчик.

        Если установлено предварительное получение истории, будет ожидать определенное количество запросов.

        Args:
            exc_type (Optional[Type[BaseException]]): Тип исключения.
            exc_val (Optional[BaseException]): Значение исключения.
            exc_tb (Optional[TracebackType]): Трассировка ошибки.
        """
        if self._prefetch_history:
            await self.wait_for_requests(self._wait_for_requests, timeout=self._wait_for_timeout)
        if self._disposable:
            await self._handler.deregister()

    async def wait_for_requests(self, count: int = 1, *, timeout: Optional[TimeoutValue] = None,
                                attempts: Optional[AttemptValue] = None,
                                delay: Optional[Union[DelayValue, DelayCallable]] = None,
                                logger: Optional[LoggerCallable] = None) -> None:
        """Асинхронный метод для ожидания прихода определенного количества запросов.

        Args:
            count (int): Количество ожидаемых запросов. По умолчанию 1.
            timeout (Optional[TimeoutValue]): Время ожидания в секундах.
            attempts (Optional[AttemptValue]): Указывает количество попыток для повторения. По умолчанию None.
            delay (Optional[Union[DelayValue, DelayCallable]]): Задержка между попытками.
            logger (Optional[LoggerCallable]): Функция логирования, используемая для информации о попытках.
        """
        if timeout is None:
            timeout = self._wait_for_timeout
        return await super().wait_for_requests(count, timeout=timeout, attempts=attempts, delay=delay, logger=logger)


def mocked_response(matcher: Union[RequestMatcher, LogicalMatcher],
                    response: RemoteResponseType,
                    expiration_policy: Optional[ExpirationPolicy] = None,
                    *,
                    disposable: Optional[bool] = None,
                    wait_for_requests: int = 1,
                    wait_for_timeout: Union[float, int] = 10.0
                    ) -> MockedResponse:


    m = mocked(matcher, response, expiration_policy, disposable=disposable)
    return MockedResponse(m._handler,
                          disposable=m._disposable,
                          prefetch_history=m._prefetch_history,
                          wait_for_requests=wait_for_requests,
                          wait_for_timeout=wait_for_timeout)
