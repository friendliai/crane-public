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

"""Log models."""

from dataclasses import field
from datetime import datetime
from enum import Enum
from typing import Optional

from crane.common.model import dataclass
from crane.common.util.serialization import DataClassJSONMixin


class LogSource(str, Enum):
    """Source of log.

    STDERR: stderr log
    STDOUT: stdout log

    """

    STDERR = "stderr"
    STDOUT = "stdout"


@dataclass
class Log(DataClassJSONMixin):
    """Log model.

    Args:
        container_id (str): container ID
        source (LogSource): Source of log
        log (str): actual log content
        timestamp (datetime.datetime): Timestamp

    """

    container_id: str
    source: LogSource
    log: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True, eq=True)
class LogFilter(DataClassJSONMixin):
    """Log filter rules.

    Args:
        source (Optional[LogSource]): filter only stdout/stderr. defaults to None.
        since (Optional[datetime]): filter logs after this time. defaults to None.

    """

    source: Optional[LogSource] = None
    since: Optional[datetime] = None
