from typing import Any, Dict, Union

from aiohttp.web_urldispatcher import DynamicResource
from jj.matchers import AllMatcher as JJAllMatcher
from jj.matchers import AnyMatcher as JJAnyMatcher
from jj.matchers import EqualMatcher as JJEqualMatcher
from jj.matchers import MethodMatcher as JJMethodMatcher
from jj.matchers import PathMatcher as JJPathMatcher
from jj.matchers import ResolvableMatcher
from jj.matchers.attribute_matchers import RouteMatcher as JJRouteMatcher

from ._common import destroy_prefix, normalize_path

__all__ = ('create_openapi_matcher', )


class BaseMatcher:
    def match(self, spec_unit: tuple[str, str]) -> bool:
        raise NotImplementedError()


class MethodMatcher(BaseMatcher):
    def __init__(self, mocked_method: Any) -> None:
        self._mocked_method = mocked_method

    def match(self, spec_unit: tuple[str, str]) -> bool:
        return bool(self._mocked_method == spec_unit[0])

    def __repr__(self) -> str:
        """
        Return a string representation of the MethodMatcher instance.

        :return: A string describing the class and matcher.
        """
        return f"{self.__class__.__qualname__}({self._mocked_method!r})"


class _Resource(DynamicResource):
    def match(self, path: str) -> Union[Dict[str, str], None]:
        return self._match(path)


class RouteMatcher(BaseMatcher):
    def __init__(self, mocked_path: str) -> None:
        self._mocked_path = mocked_path

    def match(self, spec_unit: tuple[str, str]) -> bool:
        mock = self._mocked_path
        spec = spec_unit[1]

        if "{" in mock:
            return normalize_path(mock) == normalize_path(spec)
        else:
            self._resource_spec = _Resource(spec)
            return self._resource_spec.match(mock) is not None

    def __repr__(self) -> str:
        """
        Return a string representation of the RouteMatcher instance.

        :return: A string describing the class and matcher.
        """
        return f"{self.__class__.__qualname__}({self._mocked_path!r})"


class AnyMatcher(BaseMatcher):
    def __init__(self, matchers: list[BaseMatcher]) -> None:
        assert len(matchers) > 0
        self._matchers = matchers

    def match(self, spec_unit: tuple[str, str]) -> bool:
        for matcher in self._matchers:
            if matcher.match(spec_unit):
                return True
        return False

    def __repr__(self) -> str:
        """
        Return a string representation of the AnyMatcher instance.

        :return: A string describing the class and matchers.
        """
        return (f"{self.__class__.__qualname__}"
                f"({self._matchers!r}")


class AllMatcher(BaseMatcher):
    def __init__(self, matchers: list[BaseMatcher]) -> None:
        assert len(matchers) > 0
        self._matchers = matchers

    def match(self, spec_unit: tuple[str, str]) -> bool:
        for matcher in self._matchers:
            if not matcher.match(spec_unit):
                return False
        return True

    def __repr__(self) -> str:
        """
        Return a string representation of the AllMatcher instance.

        :return: A string describing the class and matchers.
        """
        return (f"{self.__class__.__qualname__}"
                f"({self._matchers!r})")


def create_openapi_matcher(matcher: ResolvableMatcher, prefix: str | None = None) -> BaseMatcher | None:
    spec_matcher: BaseMatcher

    if isinstance(matcher, JJMethodMatcher):
        submatcher = matcher.sub_matcher
        if isinstance(submatcher, JJEqualMatcher):
            spec_matcher = MethodMatcher(mocked_method=submatcher.expected)
            return spec_matcher
        else:
            return None

    elif isinstance(matcher, JJPathMatcher):
        submatcher = matcher.sub_matcher
        if isinstance(submatcher, JJRouteMatcher):
            mocked_path = submatcher.path
            if prefix:
                mocked_path = destroy_prefix(submatcher.path, prefix)
            spec_matcher = RouteMatcher(mocked_path=mocked_path)
            return spec_matcher
        else:
            return None

    elif isinstance(matcher, JJAllMatcher):
        submatchers = matcher.sub_matchers
        matchers = [create_openapi_matcher(submatcher, prefix=prefix) for submatcher in submatchers if create_openapi_matcher(submatcher, prefix=prefix) is not None]
        spec_matcher = AllMatcher(matchers=matchers)
        return spec_matcher

    elif isinstance(matcher, JJAnyMatcher):
        submatchers = matcher.sub_matchers
        matchers = [create_openapi_matcher(submatcher, prefix=prefix) for submatcher in submatchers if create_openapi_matcher(submatcher, prefix=prefix) is not None]
        spec_matcher = AnyMatcher(matchers=matchers)
        return spec_matcher
    else:
        return None
