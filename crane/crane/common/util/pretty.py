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

"""Utilities for pretty printing."""

from __future__ import annotations

from dataclasses import astuple, is_dataclass
from enum import Enum
from typing import _GenericAlias  # type: ignore
from typing import Any, Callable, Sequence, TypeVar

from tabulate import tabulate


def tabulate_dataclass(dataclass_list: list[Any]) -> str:
    """Format a dataclass object list into a table."""
    # assert all member is dataclass
    if any(not is_dataclass(obj) for obj in dataclass_list):
        raise ValueError("This method supports only dataclasses")

    # assert all member has same fields
    classes = list(set(obj.__class__ for obj in dataclass_list))
    if len(classes) > 1:
        raise ValueError("Different dataclasses detected")

    rows = [astuple(obj) for obj in dataclass_list]
    columns = [(name, f.type) for name, f in classes[0].__dataclass_fields__.items()]

    return tabulate_rows(rows, columns)


T = TypeVar("T", bound=Sequence[Any])


def tabulate_rows(rows: list[T], columns: list[tuple[str, type]]) -> str:
    """Format a list of rows into a table."""
    col_names, col_types = list(zip(*columns))

    formatters = [_format_factory(t) for t in col_types]

    data = [_format_row(row, formatters) for row in rows]
    table = tabulate(data, headers=col_names)
    return table


def _format_row(row: T, formatters: list[Callable[[Any], str]]) -> list[str]:
    """Format a dataclass object into a row."""
    formatted_row: list[str] = []

    f: Callable[[Any], str]
    cell: Any
    for f, cell in zip(formatters, row):
        formatted_row.append(f(cell))

    return formatted_row


def _format_factory(type_: type | _GenericAlias) -> Callable[[Any], str]:
    if isinstance(type_, _GenericAlias):
        type_ = type_.__origin__

    if issubclass(type_, (list, tuple)):
        return _format_sequence
    if issubclass(type_, Enum):
        return _format_enum
    if issubclass(type_, bytes):
        return _format_bytes

    return _format_identity


def _format_identity(o: Any) -> str:
    return str(o)


def _format_sequence(o: Sequence[Any]) -> str:
    item_print_limit = 3

    contract_list = len(o) > item_print_limit
    o = list(o)[:item_print_limit]

    fmt_list = ", ".join(map(str, o))
    if contract_list:
        fmt_list += " ..."
    return fmt_list


def _format_enum(o: Enum) -> str:
    return o.value


def _format_bytes(o: bytes) -> str:
    return repr(o)
