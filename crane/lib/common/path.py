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

"""Utilities for path."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Iterable

import crane.common.constant as C


def walk_with_deny_list(root: Path, patterns: list[str]) -> Iterable[Path]:
    """Return file, directory paths that does not match the patterns.

    All paths are relative to the root.
    Each pattern should be a glob pattern.

    """
    pattern_matcher = PatternMatcher(patterns)
    for file in pattern_matcher.walk(root):
        yield file


class PatternMatcher:
    """Filter the files that match the `patterns`."""

    INCLUDE_PROMPT = "!"
    REMOVE_PROMPT_LIST = ("./", "/")

    def __init__(self, patterns: list[str]):  # pylint: disable=super-init-not-called
        """Add patterns. Note .craneignore is included as default."""
        self.patterns = [*patterns, C.Workspace.CONTEXT_DIR]

    def walk(self, root: Path) -> Iterable[Path]:
        """Iterate through files and yield paths according to ignore syntax.

        First, recursively iterate all files that match the ignore pattern.
        Then, recursively iterate all files and yield if not in exclude list.

        """
        # TODO: do not search a directory if it is excluded (early terminate)

        files = set(root.rglob("*"))

        for pattern in self.patterns:
            include = pattern.startswith(PatternMatcher.INCLUDE_PROMPT)
            if include:
                pattern = pattern[len(PatternMatcher.INCLUDE_PROMPT) :]

            # dockerignore specific. not gitignore
            for prompt in PatternMatcher.REMOVE_PROMPT_LIST:
                if pattern.startswith(prompt):
                    pattern = pattern[len(prompt) :]

            # normalize path according to dockerignore's rule
            pattern = re.sub(r"^(\.\.\/)+", "", pattern)
            pattern = os.path.normpath(pattern)

            update_func = _include_path if include else _exclude_path
            files = update_func(root, files, pattern)

        yield from files


def _exclude_path(root: Path, files: set[Path], pattern: str) -> set[Path]:
    matches = set(root.glob(pattern))

    def _exclude(f: Path) -> bool:
        for match in matches:
            if match == f or match in f.parents:
                return True
        return False

    files = {f for f in files if not _exclude(f)}
    if pattern.endswith("/**"):
        files |= set(root.glob(pattern[: -len("/**")]))
    return files


def _include_path(root: Path, files: set[Path], pattern: str) -> set[Path]:
    matches = set(root.rglob(pattern))

    add_files: set[Path] = set()
    for match in matches:
        add_files.add(match)
        if match.is_dir():
            add_files |= set(match.rglob("*"))

    return files | add_files
