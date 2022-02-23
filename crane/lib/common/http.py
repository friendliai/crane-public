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

"""HTTP protocol related utilities."""

from __future__ import annotations

from typing import Iterable

from httpx import Response

from crane.common.util.conversion import as_collection
from crane.lib.common.exception import HTTPBadResponseError


def assert_response(
    res: Response,
    expected_status_code: int | Iterable[int] = 200,
):
    """Assert response to have expected status code.

    More sophisticated then res.raise_for_status() which only checks for 2xx status.

    Args:
        res (Response): response object
        expected_status_code (int | Iterable[int]): expected status code(s).
            Defaults to 200.

    Raises:
        HTTPBadResponseError: if status code is not expected

    """
    expected_status_codes = as_collection(expected_status_code)
    if res.status_code in expected_status_codes:
        return

    decoded = _decode_response(res)
    raise HTTPBadResponseError(res.status_code, decoded)


def _decode_response(res: Response) -> str:
    """Decode response and get error message."""
    try:
        content_type = res.headers["content-type"]
        media_type, *media_params = content_type.split(";")
    except (KeyError, ValueError):
        return "Unknown"

    # take care of OWS
    media_type = media_type.strip()

    if content_type == "application/json":
        try:
            data: dict = res.json()
            return data.get("detail") or data.get("message") or str(data)
        except ValueError:
            return "Json decode failed"

    if content_type == "text/plain":
        media_param = media_params[0].strip() if media_params else "charset=utf-8"
        _, encoding = media_param.split("=")
        return str(res.content, encoding, errors="replace")

    return res.text
