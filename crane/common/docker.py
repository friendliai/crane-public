# pylint: disable=consider-using-ternary
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

"""Utilities for creating docker options."""

from __future__ import annotations

import shlex
from contextlib import contextmanager
from typing import Iterator, Optional, TypeVar

from pydantic import BaseModel
from typing_extensions import Literal

from crane.common.model import container
from crane.vendor import async_docker as ad

T = TypeVar("T", bound=BaseModel)


def add_crane_label(obj: T, role: str | None = None) -> T:
    """Add crane specific label to docker option."""
    labels = dict(crane="true")
    if role:
        labels["role"] = role
    return add_label(obj, labels)


def add_label(obj: T, labels: dict[str, str]) -> T:
    """Add label to docker option."""
    return obj.copy(update={"labels": labels})


def local_volume(
    name: str, opts: Optional[dict[str, str]] = None
) -> ad.VolumesCreatePostRequest:
    """Create a local volume option."""
    return ad.VolumesCreatePostRequest(
        name=name, driver="local", driver_opts=opts or {}
    )


def overlay(name: str) -> ad.NetworksCreatePostRequest:
    """Create overlay network option.

    Args:
        name (str): name of the overlay network

    """
    return ad.NetworksCreatePostRequest(
        name=name,
        driver="overlay",
        check_duplicate=True,
        internal=False,
        attachable=True,
    )


def network_attach_option(alias_config: dict[str, list[str]]) -> ad.NetworkingConfig:
    """Create networking configuration from network name to aliases mapping."""
    endpoints_config = {
        name: ad.EndpointsConfig(__root__=ad.EndpointSettings(aliases=aliases))
        for name, aliases in alias_config.items()
    }
    return ad.NetworkingConfig(endpoints_config=endpoints_config)


@contextmanager
def suppress_no_docker_entity() -> Iterator[None]:
    """A context manager for ignoring docker errors that correspond to 404."""
    try:
        yield
    except ad.DockerHTTPError as e:
        if e.status_code != 404:
            raise


class ContainerOption(ad.ContainersCreatePostRequest):
    """Container configuration."""

    def set_image(self, image: str) -> ContainerOption:
        """Configure container image option.

        Args:
            image (str): container image

        Returns:
            ContainerOption: self

        """
        return self.copy(update={"image": image})

    def set_process(
        self, cmd: str | None, user: str | None = None, init: bool = False
    ) -> ContainerOption:
        """Configure container process option.

        Args:
            cmd (str | None): container command. If none, use command set in image.
            user (str | None): User inside container that runs command.
            init (bool): enable tini as init process. Defaults to False

        Returns:
            ContainerOption: self

        """
        host_config = self.host_config or ad.HostConfig()
        host_config = host_config.copy(update={"init": init})

        update: dict[str, object] = {"host_config": host_config}
        if cmd:
            update["cmd"] = shlex.split(cmd)

        if user:
            update["user"] = user

        return self.copy(update=update)

    def set_envs(self, envs: dict[str, str]) -> ContainerOption:
        """Configure container environment variables.

        Args:
            envs (dict[str, str]): environment variables.

        Returns:
            ContainerOption: self

        """
        env = [f"{k}={v}" for k, v in envs.items()] + (self.env or [])
        return self.copy(update={"env": env})

    def set_storage(self, *mounts: container.MountMapping) -> ContainerOption:
        """Configure container file_system option.

        Args:
            mounts (list[container.MountMapping]): container mount list

        Returns:
            ContainerOption: self

        """
        host_config = self.host_config or ad.HostConfig()

        binds = [f"{m.host_dir}:{m.container_dir}:{m.mode}" for m in mounts]
        binds += host_config.binds or []
        host_config = host_config.copy(update={"binds": binds})

        return self.copy(update={"host_config": host_config})

    def set_ports(self, *ports: container.PortMapping) -> ContainerOption:
        """Configure container port forwarding.

        Args:
            ports (list[container.PortMapping]): container ports

        Returns:
            ContainerOption: self

        """
        host_config = self.host_config or ad.HostConfig()

        exposed_ports = dict(self.exposed_ports or {})
        port_bindings = dict(host_config.port_bindings or {})
        for p in ports:
            container_port = f"{p.container_port}/{p.transport}"
            host_info = dict(HostPort=str(p.host_port), HostIp=p.host_ip)

            exposed_ports[container_port] = ad.ExposedPorts()

            if container_port not in port_bindings:
                port_bindings[container_port] = []

            port_bindings[container_port].append(host_info)

        host_config = host_config.copy(update={"port_bindings": port_bindings})

        return self.copy(
            update={"host_config": host_config, "exposed_ports": exposed_ports}
        )

    def set_network(
        self,
        networks: ad.NetworkingConfig | None = None,
        hostname: str | None = None,
        rdma: bool = False,
    ) -> ContainerOption:
        """Configure container network option.

        Args:
            networks (ad.NetworkingConfig | None): container aliases
            hostname (str | None): hostname of container
            rdma (bool): if supported by rdma

        Returns:
            ContainerOption: self

        """
        endpoints_config = (
            self.networking_config and self.networking_config.endpoints_config or {}
        )
        if networks:
            endpoints_config.update(networks.endpoints_config or {})
            # todo: docker engine only allow one endpoint config at startup.
            #       networks other than one should be attached via network connect
        networking_config = ad.NetworkingConfig(endpoints_config=endpoints_config)

        updates: dict[str, object] = {"networking_config": networking_config}

        if hostname:
            updates["hostname"] = hostname

        host_config = self.host_config or ad.HostConfig()

        if rdma:
            cap_add = host_config.cap_add or []
            cap_add = cap_add + ["IPC_LOCK", "SYS_NICE"]

            devices = host_config.devices or []
            devices = devices + [
                ad.DeviceMapping(
                    path_on_host="/dev/infiniband/uverbs0",
                    path_in_container="/dev/infiniband/uverbs0",
                    cgroup_permissions="rwm",
                ),
                ad.DeviceMapping(
                    path_on_host="/dev/infiniband/uverbs1",
                    path_in_container="/dev/infiniband/uverbs1",
                    cgroup_permissions="rwm",
                ),
            ]
            host_config = host_config.copy(
                update={"cap_add": cap_add, "devices": devices}
            )
            updates["host_config"] = host_config
        return self.copy(update=updates)

    def set_cap(self, *capabilities: str) -> ContainerOption:
        """Add capabilities."""
        host_config = self.host_config or ad.HostConfig()
        cap_add = host_config.cap_add or []
        cap_add.extend(capabilities)

        host_config = host_config.copy(update={"cap_add": cap_add})
        return self.copy(update={"host_config": host_config})

    def set_host(self, shm_size: int) -> ContainerOption:
        """Configure container host option.

        Args:
            shm_size (int): Shared memory (/dev/shm) size in bytes

        Returns:
            ContainerOption: self

        """
        host_config = self.host_config or ad.HostConfig()
        host_config = host_config.copy(update={"shm_size": shm_size})
        return self.copy(update={"host_config": host_config})

    def set_runtime(
        self, pid_host: bool, health_cmd: str | None, log_url: str | None
    ) -> ContainerOption:
        """Configure container runtime option.

        Args:
            pid_host (bool): If expose pid with host.
            health_cmd (str): Health Check command
            log_url (str | None): Fluentd log server URL

        Returns:
            ContainerOption: self

        """
        host_config = self.host_config or ad.HostConfig()
        host_updates: dict[str, object] = {}

        if pid_host:
            host_updates["pid_host"] = "host"

        if log_url:
            host_updates["log_config"] = ad.LogConfig(
                type="fluentd",
                config={
                    "fluentd-address": log_url,
                    "fluentd-sub-second-precision": "true",
                },
            )

        host_config = host_config.copy(update=host_updates)
        update: dict[str, object] = {"host_config": host_config}

        if health_cmd is not None:
            health_config = ad.HealthConfig(
                test=shlex.split(health_cmd),
                start_period=5_000_000_000,
                interval=3_000_000_000,
                timeout=10_000_000_000,
                retries=15,
            )
            update["healthcheck"] = health_config

        return self.copy(update=update)

    def set_exit(
        self,
        *,
        auto_remove: bool = False,
        restart_policy: Literal["", "always", "unless-stopped", "on-failure"] = "",
        maximum_retry: int | None = None,
    ) -> ContainerOption:
        """Configure container removal option.

        Args:
            auto_remove (bool): If remove container automatically if finishes.
            restart_policy (str): One of "", "always", "unless-stopped", "on-failure"
            maximum_retry (int | None): Has effect only if policy is "on-failure"

        Returns:
            ContainerOption: self

        """
        if restart_policy != "on-failure" and maximum_retry is not None:
            raise ValueError(
                f"maximum_retry is not supported for restart policy {restart_policy}"
            )

        host_config = self.host_config or ad.HostConfig()

        policy = host_config.restart_policy or ad.RestartPolicy()
        if restart_policy:
            policy = policy.copy(update={"name": restart_policy})

        if maximum_retry:
            policy = policy.copy(update={"maximum_retry_count": maximum_retry})

        host_updates: dict[str, object] = {"restart_policy": policy}

        if auto_remove:
            host_updates["auto_remove"] = True

        host_config = host_config.copy(update=host_updates)
        return self.copy(update={"host_config": host_config})
