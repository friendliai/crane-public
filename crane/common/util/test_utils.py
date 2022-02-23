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

"""Crane testing utilities."""

from __future__ import annotations

import asyncio
import sys
from dataclasses import dataclass

SYNC_FUNC_TEMPLATE = """\
@pytest.fixture
def {fixture_name}({args}):
    fixture_obj = {datacls}({args})
    if hasattr(fixture_obj, "__fixture__"):
        fixture_obj.__fixture__()
    return fixture_obj
"""

ASYNC_FUNC_TEMPLATE = """\
@pytest.fixture
async def {fixture_name}({args}):
    fixture_obj = {datacls}({args})
    if hasattr(fixture_obj, "__fixture__"):
        await fixture_obj.__fixture__()
    return fixture_obj
"""


def make_fixture_group(fixture_name: str):
    """Return a class decorator that creates a pytest fixture.

    Args:
        fixture_name (str): The name of the created fixture

    """

    def _wrapper(cls):
        datacls = dataclass(cls)
        args = ", ".join(getattr(datacls, "__dataclass_fields__"))

        template = SYNC_FUNC_TEMPLATE
        if hasattr(cls, "__fixture__") and asyncio.iscoroutinefunction(cls.__fixture__):
            template = ASYNC_FUNC_TEMPLATE

        func_code = template.format(
            fixture_name=fixture_name, datacls=datacls.__name__, args=args
        )
        global_ns = sys.modules[cls.__module__].__dict__
        exec(func_code, global_ns)  # pylint: disable=exec-used

        return cls

    return _wrapper
