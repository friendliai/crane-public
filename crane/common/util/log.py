# Copyright (C) 2018-2021 Seoul National University
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

"""Logging utilities."""

from __future__ import annotations

import logging
from asyncio import iscoroutinefunction
from functools import wraps
from time import monotonic as time_
from typing import Any, Callable, TypeVar, overload

from termcolor import colored

from crane.common.util.descriptor import LazyAttribute

F = TypeVar("F", bound=Callable)
logger = logging.getLogger(__name__)


@overload
def log_func(
    func: None = None,
    *,
    logger_: logging.Logger = logger,
    log_level: int = logging.DEBUG,
    template: str = "",
    func_input: bool = True,
    func_output: bool = True,
    func_exception: bool = True,
    time: bool = True,
) -> Callable[[F], F]:
    ...


@overload
def log_func(func: F) -> F:
    ...


def log_func(
    func: F | None = None,
    *,
    logger_: logging.Logger = logger,
    log_level: int = logging.DEBUG,
    template: str = "",  # pylint: disable=unused-argument
    func_input: bool = True,
    func_output: bool = True,
    func_exception: bool = True,
    time: bool = True,
) -> F | Callable[[F], F]:
    """Log a function for its input and output."""

    def _inner_decorator(func: F) -> F:
        nonlocal template
        template = template or func.__name__

        ctx = _LogContext(
            logger_, log_level, template, func_input, func_output, func_exception, time
        )

        async def _async_wrapper(*args, **kwargs):
            ctx.input_args = (args, kwargs)
            with ctx:
                ctx.ret = await func(*args, **kwargs)
                return ctx.ret

        def _sync_wrapper(*args, **kwargs):
            ctx.input_args = (args, kwargs)
            with ctx:
                ctx.ret = func(*args, **kwargs)
                return ctx.ret

        if iscoroutinefunction(func):
            return wraps(func)(_async_wrapper)  # type: ignore
        return wraps(func)(_sync_wrapper)  # type: ignore

    if func is not None:
        return _inner_decorator(func)

    return _inner_decorator


# pylint: disable=too-many-instance-attributes
class _LogContext:

    input_args: LazyAttribute[Any] = LazyAttribute()
    ret: LazyAttribute[Any] = LazyAttribute()

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        logger_: logging.Logger = logger,
        log_level: int = logging.DEBUG,
        template: str = "",
        func_input: bool = True,
        func_output: bool = True,
        func_exception: bool = True,
        time: bool = True,
    ) -> None:
        """Initialize."""
        self.logger_ = logger_
        self.log_level = log_level
        self.template = template
        self.func_input = func_input
        self.func_output = func_output
        self.func_exception = func_exception
        self.time = time

        self.start_time = 0.0

    def __enter__(self) -> _LogContext:
        input_str = str(self.input_args)
        self._log_on_condition(self.func_input, "called with", "%s %r", input_str)
        self.start_time = time_()
        return self

    def __exit__(self, exc_type: Any, *_) -> None:
        self._log_on_condition(
            self.time, "took", "%s %f seconds", time_() - self.start_time
        )
        if exc_type is None:
            self._log_on_condition(self.func_output, "returned with", "%s %r", self.ret)
            return

        self._log_on_condition(self.func_exception, "raised error", "%s", exc_info=True)

    def _log_on_condition(
        self, cond: bool, detail: str, log_msg: str, *args: Any, **kw: Any
    ) -> None:
        if cond:
            header = colored(f"[{self.template}] {detail}", "yellow")
            self.logger_.log(self.log_level, log_msg, header, *args, **kw)
