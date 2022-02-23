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

"""Minicluster subcommands for crane user client."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, AsyncIterator

import crane.common.constant as C
from crane.common.api_model import MCCreateRequest, MCCreateResponse, MCInspectResponse
from crane.common.model import container
from crane.common.model import log as log_model
from crane.common.model import mini_cluster
from crane.common.model.resource import Logical as LogicalResource
from crane.lib.aio.client import ClientCommandCollection
from crane.lib.aio.user.typing import UserLibConfig
from crane.lib.common.exception import (
    InvalidENVConfigError,
    InvalidMountConfigError,
    InvalidResourceConfigError,
    InvalidSMConfigError,
)
from crane.lib.common.http import assert_response

logger = logging.getLogger(__name__)


class MiniClusterCommandCollection(ClientCommandCollection[UserLibConfig]):
    """Job subcommands."""

    async def filter(
        self,
        id_or_name: str,
        tags: list[str] | None = None,
        state: list[str] | None = None,
    ) -> list[str]:
        """Filter jobs by id, name or tags."""
        params = dict(id_or_name=id_or_name, tags=tags or [], state=state or [])
        res = await self._session.get(
            f"/gateway{C.Gateway.URL.MINI_CLUSTER_LIST}", params=params
        )
        assert_response(res)

        job_list = res.json()

        return job_list

    async def inspect(self, job_id: str) -> MCInspectResponse:
        """Inspect a job by its id."""
        url = f"/gateway{C.Gateway.URL.MINI_CLUSTER_DETAIL.format(mc_id=job_id)}"
        res = await self._session.get(url)
        assert_response(res)
        return MCInspectResponse.from_json(res.text)

    async def kill(self, mc_id: str, force: bool) -> None:
        """Kill a mini-cluster by its id."""
        params = {"force": "true" if force else "false"}
        url = f"/gateway{C.Gateway.URL.MINI_CLUSTER_KILL.format(mc_id=mc_id)}"
        res = await self._session.post(url, params=params)
        assert_response(res)

    async def delete(self, mc_id: str) -> None:
        """Remove a mini-cluster by its id."""
        url = f"/gateway{C.Gateway.URL.MINI_CLUSTER_DETAIL.format(mc_id=mc_id)}"
        res = await self._session.delete(url)
        assert_response(res)

    # pylint: disable=too-many-arguments, too-many-locals
    async def add(
        self,
        image: str,
        resource: str,
        command: str | None = None,
        envs: list[str] | None = None,
        mounts: list[str] | None = None,
        ports: list[int] | None = None,
        public_ports: list[int] | None = None,
        rdma: bool = False,
        overlay: bool = False,
        shm_size: str = "64m",
        name: str | None = None,
        tags: list[str] | None = None,
        init: bool = False,
        workspace_id: str | None = None,
    ) -> MCCreateResponse:
        """Add a new job to cluster."""
        envs = envs or []
        mounts = mounts or []
        ports = ports or []
        public_ports = public_ports or []

        # build config
        resource_spec = _build_resource(resource)

        app_image = container.Image(name=image)
        app_process = container.Process(cmd=command, envs=_build_envs(envs), init=init)
        app_storage = container.Storage(mounts=_build_mounts(mounts))
        app_network = container.Network(
            rdma=rdma, ports=_build_ports(ports, public_ports)
        )
        app_host = container.Host(shm_size=_build_shm_size(shm_size))
        app_config = container.Config(
            image=app_image,
            resource_spec=resource_spec.am_resource,
            process=app_process,
            storage=app_storage,
            network=app_network,
            host=app_host,
        )

        mini_cluster_setting = mini_cluster.MiniClusterSetting(overlay=overlay)
        job_config = mini_cluster.Config(
            app_manager=app_config,
            resource_spec=resource_spec,
            mini_cluster_setting=mini_cluster_setting,
        )
        job_request = MCCreateRequest(
            config=job_config, name=name, workspace_id=workspace_id, tags=tags or []
        )

        res = await self._session.post(
            f"/gateway{C.Gateway.URL.MINI_CLUSTER_LIST}", json=job_request.to_dict()
        )
        assert_response(res, 201)
        job_info = MCCreateResponse.from_dict(res.json())
        return job_info

    async def log(
        self,
        mc_id: str,
        follow: bool = False,
        filter_: log_model.LogFilter = log_model.LogFilter(),
    ) -> AsyncIterator[log_model.Log]:
        """Iterate through a log."""
        params: dict[str, Any] = dict(follow=follow)
        body = filter_.to_dict()

        url = f"/gateway{C.Gateway.URL.JOB_LOG.format(mc_id=mc_id)}"

        with self._session.stream("GET", url, params=params, json=body) as res:
            assert_response(res)
            async for line in res.aiter_lines():
                # Filter keep-alive
                if line:
                    yield log_model.Log.from_json(line)


def _build_resource(resource_: str) -> mini_cluster.ResourceSpec:
    """Return resource request given resource string.

    Args:
        resource_ (str): resource string

    Returns:
        mini_cluster.ResourceSpec: resource request

    Raises:
        InvalidResourceConfigError: if resource string is invalid.

    """
    resource_list = resource_.split(":")
    resource_list = [r for r in resource_list if r]
    if not resource_list or len(resource_list) > 3:
        raise InvalidResourceConfigError("Invalid resource format.")

    try:
        if len(resource_list) == 1:
            app_gpu = int(resource_list[0])
            min_gpu = app_gpu
            max_gpu = app_gpu
        elif len(resource_list) == 2:
            app_gpu = int(resource_list[0])
            min_gpu = int(resource_list[1])
            max_gpu = min_gpu
        else:
            app_gpu = int(resource_list[0])
            min_gpu = int(resource_list[1])
            max_gpu = int(resource_list[2])
    except ValueError:
        raise InvalidResourceConfigError("Invalid resource format.") from None

    if not app_gpu <= min_gpu <= max_gpu:
        raise InvalidResourceConfigError("Resource value out of range.")

    am_resource = LogicalResource(num_gpu=app_gpu)
    min_resource = LogicalResource(num_gpu=min_gpu)
    max_resource = LogicalResource(num_gpu=max_gpu)
    resource_spec = mini_cluster.ResourceSpec(
        am_resource=am_resource, min_resource=min_resource, max_resource=max_resource
    )

    return resource_spec


def _build_envs(envs: list[str]) -> dict[str, str]:
    """Return env dict given env string.

    Args:
        envs (list[str]): env string

    Returns:
        dict[str, str]: env request

    Raises:
        InvalidENVConfigError: if env string is invalid.

    """
    try:
        env_dict = {}
        for env in envs:
            key, value = env.split("=")
            env_dict[key] = value
        return env_dict
    except ValueError:
        raise InvalidENVConfigError(
            "Wrong environment setting detected\n\tUsage: -e [key]=[value]"
        ) from None


def _build_mounts(mounts: list[str]) -> list[container.MountMapping]:
    """Return mount mapping given env string.

    Args:
        mounts (list[str]): mount string

    Returns:
        list[container.MountMapping]: mount mapping

    Raises:
        InvalidMountConfigError: if mount string is invalid.

    """
    try:
        mount_configs = []
        for mount in mounts:
            host_dir, container_dir, mode = mount.split(":")
            mount_configs.append(
                container.MountMapping(
                    host_dir=str(Path(host_dir).resolve()),
                    container_dir=container_dir,
                    mode=mode,
                )
            )
        return mount_configs
    except ValueError:
        raise InvalidMountConfigError(
            "Wrong mount setting detected\n"
            "\tUsage: -m [host_dir]:[container_dir]:[option]"
        ) from None


def _build_ports(
    ports: list[int], public_ports: list[int]
) -> list[container.PortRequest]:
    """Return port requests."""
    port_requests = []
    for port in ports:
        port_requests.append(
            container.PortRequest(container_port=port, expose_outside=False)
        )
    for port in public_ports:
        port_requests.append(
            container.PortRequest(container_port=port, expose_outside=True)
        )

    return port_requests


def _build_shm_size(shm_size: str) -> int:
    """Return shared memory config given shared memory size.

    Args:
        shm_size (str): shared memory size in human readable form

    Returns:
        int: shared memory size in bytes

    Raises:
        InvalidSMConfigError: if given size is invalid.

    """
    match = re.fullmatch(r"(?=.)(\d*(\.\d+)?)([bkmgBKMG]?)", shm_size)
    if match is None:
        raise InvalidSMConfigError(
            f"Wrong shared memory option: {shm_size}\n"
            f"\tInput as format <float>.<unit>, "
            "where <unit> is one of 'b', 'k', 'm', 'g'.\n"
            "\t<unit> is defaulted to 'b' if omitted. "
        )
    mantissa = float(match.group(1))
    exponent = ["b", "k", "m", "g"].index(match.group(3).lower())
    return int(mantissa * 1024 ** exponent)
