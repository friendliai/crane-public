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


"""Implement assertion helper functions for async."""

import asyncio


async def assert_complete_in_time(coroutine, time=0.01):
    """Assert that a coroutine is completed in time.

    Raises:
        AssertionError: if the coroutine is not completed

    """
    try:
        return await asyncio.wait_for(coroutine, timeout=time)
    except asyncio.TimeoutError:
        raise AssertionError from None


async def assert_not_complete(coroutine, time=0.01):
    """Assert that a coroutine is not completed in time.

    Raises:
        AssertionError: if the coroutine is completed

    """
    try:
        await asyncio.wait_for(coroutine, timeout=time)
        raise AssertionError
    except asyncio.TimeoutError:
        pass
