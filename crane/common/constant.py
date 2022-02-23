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

"""Common constants."""

import pathlib

from crane.common.util.const import Const

# configuration keys
LOCAL_CRANE_FOLDER = pathlib.Path.home() / ".crane"
LOCAL_CRANE_FOLDER.mkdir(exist_ok=True)
# we can't put crane.sock under setting file dir,
# as requests does not allow long hostname


class BaseURL(Const):
    """Common Endpoints for Crane components."""

    # docs
    DOCS = "/api/docs"
    REDOC = "/api/redoc"

    PING = "/api/ping"


class CLIEnv(Const):
    """Environment variables for crane cli."""

    IGNORE_WARNING = "CRANE_IGNORE_WARNING"


class CoreComponentEnv(Const):
    """Environment variables for crane core components."""

    DEBUG = "CRANE_DEBUG"
    COMP_CONFIG = "CRANE_COMPONENT_CONFIG"
    ETCD_CONFIG = "CRANE_ETCD_COMPONENT_CONFIG"

    ROOT_CREDENTIALS = "CRANE_ROOT_CREDENTIALS"


class DATABASE(Const):
    """Database related constants."""

    MEMORY = "sqlite://:memory:"


class Gateway(Const):
    """Gateway constants."""

    class URL(BaseURL):
        """Gateway url endpoints."""

        AUTH_DEVICE = "/api/user/auth/device"
        AUTH_DEVICE_TOKEN = "/api/user/auth/device/token"
        USER_DETAIL = "/api/user/me"

        # cluster
        CLUSTER_RESOURCE = "/api/cluster/resource"

        # TODO: remove (legacy)
        JOB_LOG = "/api/job/{mc_id}/log"

        # mini cluster
        MINI_CLUSTER_LIST = "/api/mini_cluster/"
        MINI_CLUSTER_DETAIL = "/api/mini_cluster/{mc_id}"
        MINI_CLUSTER_KILL = "/api/mini_cluster/{mc_id}/kill"

        # cargo
        CARGO_LIST = "/api/mini_cluster/{mc_id}/cargo/"
        CARGO_DETAIL = "/api/mini_cluster/{mc_id}/cargo/{cargo_id}"
        CARGO_KILL = "/api/mini_cluster/{mc_id}/cargo/{cargo_id}/kill"
        CARGO_LOG = "/api/mini_cluster/{mc_id}/cargo_id/{cargo_id}/log"

    class SOCKET(Const):
        """Gateway possible unix domain socket paths."""

        DISTRIBUTED = "/var/run/crane/crane-cli.sock"

    class ENV(Const):
        """Gateway environment variables."""

        KEYCLOAK_URL = "KC_URL"


class WsServer(Const):
    """Workspace server constants."""

    class URL(BaseURL):
        """Workspace server url endpoints."""

        WORKSPACE = "/api/ws"
        WORKSPACE_DETAIL = "/api/ws/{ws_id}"


class Config(Const):
    """Possible keys for configuration."""

    PROMETHEUS_CONFIG_DIR = "/etc/prometheus"


class KubeManager(Const):
    """Kubernetes Manager constants."""

    LABEL_PREFIX = "crane.io"


class Admin(Const):
    """Admin daemon constants."""

    class URL(BaseURL):
        """URL endpoints for admin daemon."""

        CLUSTER_STATUS = "/api/cluster"
        NODE_STATUS = "/api/node"

        INIT = "/api/node/init"
        JOIN = "/api/node/join"
        LEAVE = "/api/node/leave"

        PROMOTE = "/api/node/promote"
        DEMOTE = "/api/node/demote"

        INSTALL = "/api/node/install"

    class SOCKET(Const):
        """Admin daemon possible unix domain socket paths."""

        DISTRIBUTED = "/var/run/crane.sock"


DOCKERD_PATH = "/var/run/docker.sock"
CRANE_DOCKER_REPO = "snuspl/crane"


class Component(Const):
    """Crane components."""

    class Image(Const):
        """Container component image definition."""

        INFLUXDB = "influxdb:1.8"
        NODE_EXPORTER = "quay.io/prometheus/node-exporter"
        CADVISOR = "gcr.io/google-containers/cadvisor:v0.34.0"
        KIBANA = "docker.elastic.co/kibana/kibana:7.10.2"
        BRIDGE = "alpine/socat:latest"
        ETCD = "quay.io/coreos/etcd:v3.5.0"
        TRAEFIK = "traefik:2.4"

        KEYCLOAK = f"{CRANE_DOCKER_REPO}:keycloak"
        FLUENTBIT = f"{CRANE_DOCKER_REPO}:fluent-bit"
        ELASTICSEARCH = f"{CRANE_DOCKER_REPO}:elasticsearch"
        PROMETHEUS = f"{CRANE_DOCKER_REPO}:prometheus"
        GRAFANA = f"{CRANE_DOCKER_REPO}:grafana"
        DCGM = f"{CRANE_DOCKER_REPO}:dcgm"

        BASE = f"{CRANE_DOCKER_REPO}:base"
        GATEWAY = f"{CRANE_DOCKER_REPO}:gateway"
        ADMIN = f"{CRANE_DOCKER_REPO}:admin"
        UTIL = f"{CRANE_DOCKER_REPO}:util"
        WS_SERVER = f"{CRANE_DOCKER_REPO}:ws-server"

    class Container(Const):
        """Names for container components."""

        KEYCLOAK = "CraneKeycloak"
        ELASTICSEARCH = "CraneElasticsearch"
        KIBANA = "CraneKibana"
        FLUENTBIT = "CraneNodeLogging"

        PROMETHEUS = "CranePrometheus"
        ADD_CONFIG = "CraneAddConfig"
        NODE_DISCOVERY = "CraneNodeDiscovery"
        UTIL = "CraneUtil"
        GRAFANA = "CraneGrafana"
        INFLUXDB = "CraneInfluxdb"

        DCGM = "CraneDCGM"
        NODE_EXPORTER = "CraneNodeExporter"
        CADVISOR = "CraneCadvisor"

        ADD_NODE = "CraneAddNode"
        ETCD = "CraneETCD"

        SCHEDULER = "CraneScheduler"
        NODE = "CraneNode"
        CARGO = "CraneCargo"
        OVERLAY = "CraneOverlay"
        GATEWAY = "CraneGateway"
        BILLING = "CraneBilling"
        TRAEFIK = "CraneTraefik"

        BRIDGE = "CraneGatewayBridge"
        WS_SERVER = "CraneWorkspaceServer"

    class Network(Const):
        """Names for network components."""

        BASE_OVERLAY = "CraneBaseOverlay"
        LOGGING_OVERLAY = "CraneLoggingOverlay"
        MONITOR_OVERLAY = "CraneMonitorOverlay"

    class Volume(Const):
        """Names for volume components."""

        ELASTICSEARCH = "CraneElasticsearch"
        MONITOR = "CraneMonitor"
        PROMETHEUS = "CranePrometheus"
        INFLUXDB = "CraneInfluxdb"
        ETCD = "CraneETCD"

    class Alias(Const):
        """Docker swarm network aliases."""

        ELASTICSEARCH = "elasticsearch"
        PROMETHEUS = "prometheus"
        INFLUXDB = "influxdb"
        ETCD = "etcd"
        NODE_MANAGER = "node-{host_ip}"
        DCGM_EXPORTER = "dcgm-{host_ip}"
        NODE_EXPORTER = "exporter-{host_ip}"
        CADVISOR = "cadvisor-{host_ip}"
        GATEWAY = "gateway"
        TRAEFIK = "traefik"
        WS_SERVER = "ws-server"

    class Port(Const):
        """Default service ports.

        Uses as container ports
        """

        KEYCLOAK = 8080
        KIBANA = 5601
        FLUENTBIT = 24224
        GRAFANA = 3000
        GATEWAY = 8000
        WS_SERVER = 8001

        # internal ports (not exposed)
        ETCD = 2379
        PROMETHEUS = 9090
        DCGM = 9400
        EXPORTER = 9100
        CADVISOR = 8080
        ELASTICSEARCH = 9200
        TRAEFIK = 8888  # TODO: enable the users to specify the port

    class Timeout(Const):
        """Timeout in seconds.

        Max time for a crane component to launch.
        """

        UTIL = 20


class Template(Const):
    """Crane cli message templates."""

    SIGN_IN_SUCCESS = "Successfully logged in to crane."
    SIGN_OUT_SUCCESS = "Successfully logged out of crane."

    RESOURCE_ALL = "Free: {free_gpu_num} / Busy: {busy_gpu_num}"

    JOIN_COMMAND = "craneadm join {token} {host_ip}"


class NetworkManager(Const):
    """Network Manager constants."""

    LABEL_PREFIX = "crane.io"
    ROOT_URL = "traefik"

    class Component(Const):
        """Component names."""

        TRAEFIK = "traefik"
        GATEWAY = "gateway"
        WORKSPACE = "workspace"
        KIBANA = "kibana"
        GRAFANA = "grafana"
        KEYCLOAK = "keycloak"


class ERM(Const):
    """ERM-related constants."""

    WATCH_TIMEOUT = 300


class Workspace(Const):
    """Workspace-related constants."""

    CONTEXT_DIR = ".crane"
    CONFIG_PATH = "config.yaml"
    CRANEIGNORE_PATH = ".craneignore"
    CONTENT_TAR_FILE = "ws_content.tar.gz"
