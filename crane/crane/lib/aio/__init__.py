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

"""Crane library, Python APIs that interact with crane cluster.

Note that crane library only supports unix.

crane.lib.aio.app: crane library for application managers
crane.lib.aio.user: crane library for users
crane.lib.aio.admin: crane library for cluster admins

"""

from crane.lib.aio.user import AsyncUserClient

__all__ = ["AsyncUserClient"]
