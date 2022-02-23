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

"""Crane user client resource commands."""

from __future__ import annotations

import crane.common.constant as C
from crane.common.model import resource
from crane.lib.aio.client import ClientCommandCollection
from crane.lib.aio.user.typing import UserLibConfig
from crane.lib.common.http import assert_response


class ResourceCommandCollection(ClientCommandCollection[UserLibConfig]):
    """Commands for resource."""

    async def cluster_resource(self) -> resource.PhysicalAllocationCluster:
        """Query resource state.

        Returns:
            resource.PhysicalAllocationCluster: cluster resource state

        Raises:
            HTTPBadResponseError: if status code is not expected
            HTTPConnectionError: if connection fails

        """
        res = await self._session.get(f"/gateway{C.Gateway.URL.CLUSTER_RESOURCE}")
        assert_response(res)
        return resource.PhysicalAllocationCluster.from_dict(res.json())
