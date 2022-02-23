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

"""CLI Argument utilities."""

from __future__ import annotations


class ArgumentBuilder:
    """Builder pattern for creating command line arguments.

    Args:
        arg_sep (str): separator between arguments
        arg_value_sep (str): separator between argument and its value

    """

    def __init__(self, *, arg_sep: str = " ", arg_value_sep: str = " "):
        """Initialize."""
        self.arg_sep = arg_sep
        self.arg_value_sep = arg_value_sep

        self._args: list[str] = []

    def add(self, value: str) -> ArgumentBuilder:
        """Add a positional argument."""
        self._args.append(value)
        return self

    def set(self, arg: str, value: str) -> ArgumentBuilder:
        """Add a keyword argument."""
        self._args.append(f"--{arg}{self.arg_value_sep}{value}")
        return self

    def build(self) -> str:
        """Joint arguments into a single string."""
        return self.arg_sep.join(self._args)
