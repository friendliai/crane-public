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

"""Sequence generators."""

from __future__ import annotations

import random
from itertools import repeat
from typing import Iterator

from typing_extensions import Literal

SequenceType = Literal["constant", "exponential", "fibonacci"]


def generate_sequence(
    seq_type: SequenceType,
    *,
    jitter: bool = False,
    init: float = 0.0,
    upper: float | None = None,
) -> Iterator[float]:
    """Generates a sequence.

    Args:
        seq_type (SequenceType): sequence type
        jitter (bool): if true, jitter values. Defaults to False.
        init (float): sequence initial value. Defaults to zero.
        upper (float | None): sequence values upper bound. Defaults to None.

    """
    sequence = _sequence(seq_type, init)

    if jitter:
        sequence = jitter_seq(sequence)
    if upper is not None:
        sequence = bound_seq(sequence, upper)

    yield from sequence


def _sequence(seq_type: SequenceType, init: float) -> Iterator[float]:
    if seq_type == "constant":
        yield from constant_seq(init)

    elif seq_type == "exponential":
        yield from exponential_seq(init)

    elif seq_type == "fibonacci":
        yield from fibonacci_seq(init)

    else:
        raise NotImplementedError(seq_type)


def bound_seq(seq: Iterator[float], upper: float) -> Iterator[float]:
    """Bound given sequence."""
    for val in seq:
        yield min(val, upper)


def jitter_seq(seq: Iterator[float]) -> Iterator[float]:
    """Jitter values by uniform sampling from zero to current value."""
    for val in seq:
        yield random.uniform(0, val)


def constant_seq(init: float) -> Iterator[float]:
    """Generates a sequence of constant values."""
    yield from repeat(init)


def exponential_seq(init: float) -> Iterator[float]:
    """Generates a sequence of exponential values."""
    while True:
        yield init
        init *= 2


def fibonacci_seq(init: float) -> Iterator[float]:
    """Generates a sequence of fibonacci values."""
    v = init

    while True:
        yield init
        init, v = v, init + v
