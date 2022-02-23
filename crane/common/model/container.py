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

"""Container Model.

Each container represents one process.

This file has two parts: user side and system side.

User side: user can choose the configuration.
- Request: container request made by user
    - Logical: resource wanted
    - Config: container configuration
        - Image: container image
        - Process: container process
        - Storage/MountMapping: container file system
        - Port: container port

SystemSide: this include configurations that cannot be chosen by user,
    or decided beforehand.
-

"""

from __future__ import annotations

from dataclasses import field, replace
from typing import Dict, List, Optional, Sequence

from crane.common.model import dataclass, resource, state
from crane.common.util.serialization import DataClassJSONSerializeMixin

################################################################
#            User Configuration classes
################################################################


@dataclass
class Image(DataClassJSONSerializeMixin):
    """Container image configuration given by user.

    Args:
        name (str): Name of the image

    """

    name: str

    # Copy from docker-py library
    # https://github.com/docker/docker-py/blob/96c12726fdb9b24e985b4de74d5c82145ccd8185/docker/utils/utils.py#L193
    def parse_repository_tag(self) -> tuple[str, str]:
        """Parse user given image name into repository and tag.

        Returns:
            tuple[str, str]: repository and tag, in sequence. Default tag is 'latest'

        Examples:
            >>> parse_respository_tag(Image("snuspl/crane:latest"))
                ("snuspl/crane", "latest")

        """
        if ":" in self.name:
            name, tag = self.name.rsplit(":", 1)
            return name, tag
        return self.name, "latest"


@dataclass(frozen=True)
class Process(DataClassJSONSerializeMixin):
    """Container process option.

    When command is not given, it falls back to command specified in image.
    Recommend explicitly specifying command.

    Args:
        cmd (Optional[str]): Command to run inside the container. Defaults to None.
        user (Optional[str]): Username inside container
        envs (Dict[str, str]): environment variables. Defaults to {}
        init (bool): enable the `init` container option

    """

    cmd: Optional[str] = None
    user: Optional[str] = None
    envs: Dict[str, str] = field(default_factory=dict)
    init: bool = True


@dataclass
class MountMapping(DataClassJSONSerializeMixin):
    """Mount mapping.

    Args:
        host_dir (str): Path on host machine.
        container_dir (str): Path on container.
        mode (str): File access mode (rw, readonly).

    """

    host_dir: str
    container_dir: str
    mode: str = field(default="rw")


@dataclass
class Storage(DataClassJSONSerializeMixin):
    """File system inside container option.

    Args:
        mounts (List[MountMapping]): Filesystem mount mapping. Defaults to [].

    """

    mounts: List[MountMapping] = field(default_factory=list)


@dataclass(frozen=True, eq=True)
class PortRequest(DataClassJSONSerializeMixin):
    """Port option.

    This is a request as you don't know what port will be available.

    Args:
        container_port (int): port inside container
        host_port (Optional[int]): host port. defaults to None
        expose_outside (bool): If true, port will be exposed publically

    """

    container_port: int
    host_port: Optional[int] = None
    expose_outside: bool = False


@dataclass
class Overlay(DataClassJSONSerializeMixin):
    """Overlay option.

    Args:
        name (str): Name of overlay network
        aliases (List[str]): Aliases of overlay network

    """

    name: str
    aliases: List[str] = field(default_factory=list)


@dataclass
class Network(DataClassJSONSerializeMixin):
    """Network Option.

    Args:
        rdma (bool): Whether to use rdma. Default as False.
        overlays (List[Overlay]): Overlay networks. Defaults to []
        ports (List[PortRequest]): Port mapping. Default as []

    """

    rdma: bool = False
    overlays: List[Overlay] = field(default_factory=list)
    ports: List[PortRequest] = field(default_factory=list)


@dataclass
class Host(DataClassJSONSerializeMixin):
    """Host Option.

    Args:
        shm_size (int): Shared memory (/dev/shm) size in bytes

    """

    shm_size: int = field(default=64 * 1024 * 1024)


@dataclass(frozen=True)
class Config(DataClassJSONSerializeMixin):
    """Container configuration given by user.

    This is a logical specification of a container.

    Args:
        image (Image): Container image config
        resource_spec (resource.Logical): Container resource config
        process (Process): Container process config. Defaults to No config
        storage (Storage): Container storage config. Defaults to No config
        network (Network): Container network config. Defaults to No config
        host (Host): Container host config. Defaults to No config

    """

    image: Image
    resource_spec: resource.Logical
    process: Process = field(default_factory=Process)
    storage: Storage = field(default_factory=Storage)
    network: Network = field(default_factory=Network)
    host: Host = field(default_factory=Host)

    def add_overlay(self, overlay_name: str, alias: str) -> Config:
        """Add overlay network configuration to this container."""
        overlays = [*self.network.overlays, Overlay(overlay_name, [alias])]
        network = replace(self.network, overlays=overlays)
        return replace(self, network=network)


@dataclass(frozen=True)
class Metadata(DataClassJSONSerializeMixin):
    """Container metadata.

    Information is given to containers as file at tmp/name

    Args:
        log (bool): If this is true, container stdout/stderr is logged

    """

    log: bool = False


@dataclass(frozen=True, eq=True)
class PortMapping(DataClassJSONSerializeMixin):
    """Port mapping.

    Args:
        container_port (int): Container side port
        host_port (int): Host side port
        host_ip (str): Host side ip address
        transport (str): Transport protocol (tcp / udp)

    """

    container_port: int
    host_port: int
    host_ip: str
    transport: str = "tcp"


@dataclass
class KillOption(DataClassJSONSerializeMixin):
    """Kill container options.

    Args:
        force (bool): if true, send sigkill, else sigterm
        grace_period (float): grace period given after sigint

    """

    force: bool
    grace_period: float = 10

    # todo: add authority (Literal[scheduler, user])


class State(state.State):
    """Physical Container state.

    State is always updated by node manager.
    Cluster manager reads state

    DOWN: Container is down, not yet read by NM
    READY: Container is launching (protected)
    INVALID: Container configuration is invalid
    RUNNING: Container is running
    DONE: Container exited successfully
    ERROR: Container exited unsuccessfully
    """

    DOWN = state.auto()
    READY = state.auto()
    RUNNING = state.auto()

    DONE = state.auto()
    ERROR = state.auto()
    INVALID = state.auto()

    FAILURE = INVALID | ERROR
    TERMINATED = FAILURE | DONE

    @staticmethod
    def __transitions__() -> list[tuple[State, State]]:
        """Container state transitions."""
        return [
            (State.DOWN, State.READY | State.ERROR),
            (State.READY, State.RUNNING | State.FAILURE),
            (State.RUNNING, State.DONE | State.ERROR),
        ]

    @staticmethod
    def __init_state__() -> State:
        """Containers start from DOWN state."""
        return State.DOWN


@dataclass(frozen=True)
class StateHistory(state.StateHistory[State]):
    """Container state history."""

    states: Sequence[State]


################################################################
#            Crane Configuration classes
################################################################


@dataclass
class CreateInfo(DataClassJSONSerializeMixin):
    """Container creation information.

    This is created after container creation in container runtimes.
    """

    port_mapping_list: List[PortMapping] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class ExitInfo(DataClassJSONSerializeMixin):
    """Container exit information.

    Created after container exits successfully.
    if exit_code is -1, it means the container never ran.
    """

    exit_code: int
    err_msg: str = ""  # container runtime err msg


@dataclass
class ErrInfo(DataClassJSONSerializeMixin):
    """Container error information."""

    err_msg: str


@dataclass
class Allocation(DataClassJSONSerializeMixin):
    """Container allocation information."""

    node_name: str
    resource_spec: resource.Physical

    def build_gpu_string(self) -> str:
        """Return string representation of gpu indices.

        For use with cuda_string(visible devices).

        Returns:
            str: cuda_visible_devices string

        """
        if not self.resource_spec.gpu_indices:
            return ""
        return ",".join(map(str, self.resource_spec.gpu_indices))

    def to_physical_cluster(self) -> resource.PhysicalCluster:
        """Change this object into physical resource group."""
        if not self.resource_spec:
            return resource.PhysicalCluster.empty()

        return resource.PhysicalCluster({self.node_name: self.resource_spec})


@dataclass(frozen=True)
class Container:
    """Represents a physical container.

    Args:
        id (str): container ID
        config (Config): Container config
        allocation (Allocation): allocated resources
        metadata (Metadata): Container metadata

    """

    id: str  # pylint: disable=invalid-name
    config: Config
    allocation: Allocation
    metadata: Metadata = field(default_factory=Metadata)
