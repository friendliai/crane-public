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

"""Workspace related utilities."""

from __future__ import annotations

import hashlib
import os
import struct
import tarfile
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable

import crane.common.constant as C
from crane.lib.common.exception import InvalidWorkspaceConfigError
from crane.lib.common.path import walk_with_deny_list


# TODO: implement asyncio version
def zip_workspace(base_path: Path) -> Path:
    """Zip again the bundle of zipfile and craneconfig.

    TODO: The tarfile should be free from race conditions.
    TODO: If the tarfile has the same hash value from the previous one,
          do not send the tarfile and reuse the one in the worspace server.

    """
    config_path = base_path / C.Workspace.CONTEXT_DIR / C.Workspace.CONFIG_PATH

    if not config_path.exists():
        raise InvalidWorkspaceConfigError(f"Cannot find config file at {config_path}")

    current_hash = _get_md5_hexdigest(base_path)
    wrapper_tarball_path = base_path / C.Workspace.CONTEXT_DIR / f"{current_hash}.tar"

    # If the tarfile with the hash value exists, skip creating tarfile.
    if wrapper_tarball_path.exists():
        return wrapper_tarball_path

    with zip_workspace_content(base_path) as contents_zip_path:
        with tarfile.open(wrapper_tarball_path, "w") as tar:
            tar.add(contents_zip_path, arcname=C.Workspace.CONTENT_TAR_FILE)
            tar.add(config_path, arcname=C.Workspace.CONFIG_PATH)

    return wrapper_tarball_path


@contextmanager
def zip_workspace_content(base_path: Path):
    """Zip the given directory and save the tar file in a temp directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        ws_fname = tmp_path / C.Workspace.CONTENT_TAR_FILE

        with tarfile.open(ws_fname, "w:gz") as tar:
            for file in _walk_files_to_include(base_path):
                tar.add(file, arcname=file.relative_to(base_path))
        yield ws_fname


def _get_md5_hexdigest(file_path: Path) -> str:
    """Get MD5 hash value of the files including the last modified time."""
    ws_hash = hashlib.md5()
    for file in _walk_files_to_include(file_path):
        if not os.path.isfile(file_path / file):
            continue

        # Update hash using file content
        with open(file_path / file, "rb") as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                ws_hash.update(chunk)

        # Update hash using the latest modified time
        modified_time = os.stat(file_path / file).st_ctime
        ws_hash.update(struct.pack("d", modified_time))

    return ws_hash.hexdigest()


def _walk_files_to_include(base_path: Path) -> Iterable[Path]:
    """Parse .craneignore files and returns files to include.

    TODO: recursive craneignore files.

    """
    try:
        craneignore_file = (
            base_path / C.Workspace.CONTEXT_DIR / C.Workspace.CRANEIGNORE_PATH
        )
        with open(craneignore_file, "r", encoding="utf-8") as f:
            patterns = [
                line.strip() for line in f if line.strip() and not line.startswith("#")
            ]
    except OSError:
        patterns = []

    return walk_with_deny_list(base_path, patterns)
