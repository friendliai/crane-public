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


"""Handling sync function asynchronously."""

from __future__ import annotations

import os
import tarfile

from crane.common.util.asynclib import sync_to_async


@sync_to_async
def compress(dst_file: str, src_dir: str) -> None:
    """Asynchronously compress tarball."""
    with tarfile.open(dst_file, "w:gz") as tar:
        tar.add(src_dir, arcname=os.path.basename(src_dir))


@sync_to_async
def extract(dst_dir: str, src_file: str) -> None:
    """Asynchronously extract tarball."""
    with tarfile.open(src_file) as tar:
        tar.extractall(path=dst_dir)
