# pylint: disable=used-before-assignment
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

"""Admin related models."""

from __future__ import annotations

import datetime
from typing import List, Optional

from crane.common.api_model import user
from crane.common.model import dataclass, resource
from crane.common.util.serialization import DataClassJSONMixin, DataClassYAMLMixin


@dataclass
class NodeStatus(DataClassJSONMixin):
    """Crane node status.

    Args:
        node_id (str): Node ID
        node_name (str): Node HostName
        node_ip (str): Node IP address
        create_time (datetime.datetime): node create time (init/join) time
        role (Literal["manager", "worker"]): node role in cluster

    """

    node_id: str
    node_name: str
    node_ip: str
    create_time: datetime.datetime
    role: str


@dataclass
class SwarmToken(DataClassJSONMixin):
    """Token from docker swarm.

    Args:
        manager (str): manager token
        worker (str): worker token

    """

    manager: str
    worker: str


@dataclass
class ClusterStatus(DataClassJSONMixin, DataClassYAMLMixin):
    """Cluster status.

    Args:
        nodes (List[NodeStatus]): status for each node in the cluster
        token (SwarmToken): token to join the cluster

    """

    nodes: List[NodeStatus]
    token: SwarmToken


@dataclass
class DevConfig(DataClassJSONMixin):
    """Configuration used only in development.

    Args:
        auth (bool): whether to set authentication on/off
        debug (bool): if true, set debugging mode for some components
        local_crane_path (Optional[str]): if set,
            will override crane core components to use local implementation

    """

    auth: bool = True
    debug: bool = False
    local_crane_path: Optional[str] = None


@dataclass
class NodeConfig(DataClassJSONMixin):
    """Configuration for each node.

    Args:
        gpu (resource.Physical): GPU resource this node will use
        host_ip (str): cluster IP address of the host
        use_rdma (bool): Whether this node can use rdma
        log_port (int): Fluentd logging port

    """

    gpu: resource.Physical
    host_ip: str
    use_rdma: bool
    log_port: int = 54321


@dataclass
class SkipConfig(DataClassJSONMixin):
    """Flag for skipping components."""

    monitor: bool = False
    logging: bool = False
    billing: bool = True
    proxy: bool = True
    workspace: bool = False


# pylint: disable=too-many-instance-attributes
@dataclass
class InitCluster(DataClassJSONMixin):
    """Configuration set to initialize cluster."""

    node: NodeConfig
    dev: DevConfig
    skip: SkipConfig
    root: user.Credential

    keycloak_port: int = 8080
    gateway_port: int = 8000
    ws_server_port: int = 8001
    grafana_port: int = 4000
    kibana_port: int = 4001


@dataclass
class JoinCluster(DataClassJSONMixin):
    """Configuration to join a cluster."""

    remote_addrs: List[str]
    swarm_token: str

    node: NodeConfig
    dev: DevConfig
    skip: SkipConfig = SkipConfig()

    gateway_port: int = 8000


@dataclass
class InstallConfig(DataClassJSONMixin):
    """Configuration to install crane.

    Args:
        version (str): version of crane to install.

    """

    version: str


@dataclass
class LeaveConfig(DataClassJSONMixin):
    """Configuration to leave the cluster.

    Args:
        force (bool): leader nodes need to force-leave for safety.
        persist (bool): with the persist option, containers and
            volumes are not removed.

    """

    force: bool
    persist: bool


@dataclass
class NodeUpdateConfig(DataClassJSONMixin):
    """Configuration for node promote and demote.

    Args:
        node_id (Optional[str]): Prefix of node id.

    """

    node_id: Optional[str]
