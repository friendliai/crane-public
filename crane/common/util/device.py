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

"""Utilities for gpu."""

import pathlib
import re
from typing import AbstractSet


def parse_gpu_indices(gpus: str) -> AbstractSet[int]:
    """Parse a CUDA_VISIBLE_DEVICE-like gpu string."""
    if gpus == "all":
        return get_available_gpus()
    if not gpus:
        return frozenset()

    if re.fullmatch(r"\d+(,\d+)*", gpus) is None:
        raise TypeError(gpus)

    return frozenset(map(int, gpus.split(",")))


def get_available_gpus() -> AbstractSet[int]:
    """Return available gpu index numbers.

    Returns:
        AbstractSet[int]: index numbers of available GPUs

    """
    try:
        p = pathlib.Path("/proc/driver/nvidia/gpus")
        gpu_count = len(list(p.iterdir()))
    except FileNotFoundError:
        return frozenset()

    return frozenset(range(gpu_count))


def check_rdma() -> bool:
    """Check if rdma is possible in this node.

    Returns:
        bool: true if rdma possible

    """
    try:
        p = pathlib.Path("/dev/infiniband")
        verb_file_list = [x for x in p.iterdir() if "uverb" in p.name]
    except FileNotFoundError:
        return False

    use_rdma = len(verb_file_list) == 2
    return use_rdma
