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


"""Constants for crane."""

import inspect
from typing import Iterator


class _MetaConst(type):
    def __setattr__(cls, key: str, value: object) -> None:
        """Raise error if tries to update constants."""
        raise TypeError

    def __iter__(cls) -> Iterator[object]:
        """Cannot modify constants."""
        for name, obj in inspect.getmembers(cls):
            if name.startswith("_"):
                continue
            yield obj


class Const(metaclass=_MetaConst):
    """Constant base class."""

    def __setattr__(self, key: str, value: object) -> None:
        """Raise error if tries to update constants."""
        raise TypeError
