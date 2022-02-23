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

"""Crane lib exceptions.

Connection error is raised by httpx or grpclib.

BaseCraneAPIException
|-BadResponseError
|   |-HTTPBadResponseError
|-InvalidConfigurationError
|   |-InvalidJobConfigError
|   |   |-InvalidResourceConfigError
|   |   |-InvalidENVConfigError
|   |   |-InvalidMountConfigError
|   |   |-InvalidSMConfigError
|-DevDeployError
"""


class BaseCraneAPIException(Exception):
    """Base exception class for all Crane API exceptions."""


class BadResponseError(BaseCraneAPIException):
    """Connection successful but got not expected response.

    Due to bad parameters or invalid authentication.
    """


class InvalidConfigurationError(BaseCraneAPIException):
    """Raised when given configuration is badly formed."""


class DevDeployError(BaseCraneAPIException):
    """Raised when dev deployment fails."""


class HTTPBadResponseError(BadResponseError):
    """Raised when received a http response with error status code."""

    def __init__(self, status_code: int, msg: str) -> None:
        """Initialize."""
        self.status_code = status_code
        self.msg = msg

        super().__init__(f"[{status_code}] {msg}")


class InvalidJobConfigError(InvalidConfigurationError):
    """Given job configuration is invalid."""


class InvalidResourceConfigError(InvalidJobConfigError):
    """Given resource configuration is invalid."""


class InvalidENVConfigError(InvalidJobConfigError):
    """Given environment variable configuration is invalid."""


class InvalidMountConfigError(InvalidJobConfigError):
    """Given storage mount configuration is invalid."""


class InvalidSMConfigError(InvalidJobConfigError):
    """Given shared memory configuration is invalid."""


class InvalidWorkspaceConfigError(InvalidConfigurationError):
    """Given workspace configuration is invalid."""
