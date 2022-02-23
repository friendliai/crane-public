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

"""Implement common decorators."""

from __future__ import annotations

import asyncio
import logging
import operator
import re
import sys
import time
from collections import ChainMap
from functools import wraps
from itertools import islice
from typing import Iterable

from crane.common.util.conversion import as_collection
from crane.common.util.sequence import SequenceType, generate_sequence

logger = logging.getLogger(__name__)


def prefix_docstring(prefix: str):
    """Prefix a function's docstring.

    >>> func.__doc__
    [prefix] <function's original docstring>

    Args:
        prefix (str): The prefix to add before the function's docstring

    """

    def _prefix_decorator(f):
        @wraps(f)
        def _wrapper(*args, **kwargs):
            return f(*args, **kwargs)

        new_docstring = f"[{prefix}] {_wrapper.__doc__}"
        _wrapper.__doc__ = new_docstring

        return _wrapper

    return _prefix_decorator


def make_method_timer(logger_module):
    """Time the wrapped coroutine method and print with logger.

    Calling this method returns a timer decorator.
    When decorated with @timer, the decorator tries to take advantage
    of the instance's 'name' attribute, along with the method's name.
    When decorated with @timer(name), directly uses the name argument.

    """

    def outer_decorator(arg):
        # decorated with @timer
        if callable(arg):  # pylint: disable=no-else-return

            @wraps(arg)
            async def _wrapper(self, *args, **kwargs):
                if hasattr(self, "name"):
                    subject = f"{arg.__name__} of {self.name}"
                else:
                    subject = arg.__name__
                logger_module.info("Start %s", subject)
                start_time = time.time()
                ret = await arg(self, *args, **kwargs)
                duration = time.time() - start_time
                logger_module.info("Finish %s in %lf seconds", subject, duration)
                return ret

            return _wrapper

        # decorated with @timer(name)
        else:

            def decorator(f):
                @wraps(f)
                async def _wrapper(*args, **kwargs):
                    subject = arg
                    logger_module.info("Start %s", subject)
                    start_time = time.time()
                    ret = await f(*args, **kwargs)
                    duration = time.time() - start_time
                    logger_module.info("Finish %s in %lf seconds", subject, duration)
                    return ret

                return _wrapper

            return decorator

    return outer_decorator


# TODO: move to partial
def async_partial(async_func, *args, **kwargs):
    """Functools partial, but async."""

    @wraps(async_func)
    async def _wrapper(*func_args, **func_kwargs):
        return await async_func(*args, *func_args, **ChainMap(func_kwargs, kwargs))

    return _wrapper


BackoffType = SequenceType


def async_retry_on_exception(
    exc: type[Exception] | Iterable[type[Exception]],
    retry_num: int,
    grace_period: float | tuple[float, float],
    backoff: BackoffType = "constant",
    log: bool = False,
    jitter: bool = False,
):
    """A decorator that calls the function again whenever an expected exception occurs.

    Args:
        exc (type[Exception] | Iterable[type[Exception]]): excepted exceptions
        retry_num (int): number of times to retry. -1 means infinite.
        grace_period (float | tuple[float, float]): initial grace period between retries
            set maximum grace period if given as tuple ([initial, maximum])
        backoff (BackoffType): backoff policy
            defaults to constant.
        log (bool): if true, log every exception
        jitter (bool): if true, add jitter to waiting time, use full jitter
            (aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/)

    Raises:
        Exception: raises the last occurred exception when failed more than expected.

    """
    exception_list: tuple[type[Exception], ...] = tuple(as_collection(exc))

    stop = retry_num + 1 or None  # stop is None, if retry_num is -1

    max_period: float | None
    if isinstance(grace_period, tuple):
        init_period, max_period = grace_period
    else:
        init_period, max_period = grace_period, None

    def _decorator(f):
        @wraps(f)
        async def _wrapper(*args, **kwargs):
            total_period = 0.0
            err: Exception | None = None

            seq = generate_sequence(
                backoff, jitter=jitter, init=init_period, upper=max_period
            )
            for idx, period in enumerate(islice(seq, stop)):
                try:
                    return await f(*args, **kwargs)
                except exception_list as e:  # pylint: disable=catching-non-exception
                    err = e

                    if idx + 1 != stop:
                        await asyncio.sleep(period)
                        total_period += period

                    if log:
                        logger.warning(
                            "%d retry(%lf) at %s: %s",
                            idx,
                            total_period,
                            f.__name__,
                            repr(err),
                        )

            assert err is not None
            raise err  # pylint: disable=raising-non-exception,raising-bad-type

        return _wrapper

    return _decorator


_PYTHON_VER_REGEX = re.compile(r"(\d)\.(\d+)(\+?)")


def assert_python_version(python_ver: str):
    """Assert runtime python version at function call.

    >>> @assert_python_version("3.6")
        def hi(): ...
    >>> # current version should be 3.6
    >>>
    >>> @assert_python_version("3.6+")
    >>> # current version should be 3.6 and above

    """
    # parse version
    match = re.fullmatch(_PYTHON_VER_REGEX, python_ver)
    if match is None:
        raise RuntimeError(f"Python version should be {python_ver}")

    expected_ver = (int(match[1]), int(match[2]))
    cmp_func = operator.ge if match[3] == "+" else operator.eq

    curr_ver = (sys.version_info.major, sys.version_info.minor)
    match_python_ver = cmp_func(curr_ver, expected_ver)

    if not match_python_ver:
        raise RuntimeError(f"Python version {python_ver} does not match expected")

    def _wrapper(func):
        return func

    return _wrapper
