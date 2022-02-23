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

"""Utilities for networking."""

from __future__ import annotations

import ipaddress
import logging
from functools import lru_cache
from socket import error as SocketError

import ephemeral_port_reserve
import netifaces
from pydantic.dataclasses import dataclass

from crane.common.util.process import ProcessException, check_output
from crane.common.util.serialization import DataClassJSONSerializeMixin
from crane.common.util.store import DoesNotExistError

logger = logging.getLogger(__name__)


@dataclass
class EndPoint(DataClassJSONSerializeMixin):
    """Network endpoint.

    (ip, port) or url must be specified.

    Args:
        ip (str): IP address
        port (int): port number
        url (str): URL

    Raises:
        ValueError: If arguments are not fully specified

    """

    ip: str
    port: int

    @staticmethod
    def from_url(url: str) -> EndPoint:
        """Create endpoint from url.

        Args:
            url (str): URL string

        Returns:
            EndPoint: endpoint object

        """
        ip, port = url.split(":")
        return EndPoint(ip=ip, port=int(port))

    @property
    def url(self) -> str:
        """Return url string."""
        return f"{self.ip}:{self.port}"


@lru_cache(maxsize=None)
def get_available_ip_address() -> list[str]:
    """Return list of ip addresses available on this node.

    Does not include docker0 ip address.

    Returns:
        list[str]: list of ip addresses

    """
    interfaces = []
    for name in netifaces.interfaces():
        if name in ("docker0", "docker_gwbridge", "lo"):
            continue
        interface = netifaces.ifaddresses(name)
        inet_interfaces = interface.get(netifaces.AF_INET, [])
        for inet_interface in inet_interfaces:
            addr = inet_interface.get("addr")
            if (addr is not None) and (addr != "127.0.0.1"):
                interfaces.append(addr)

    return interfaces


def get_ip_address(subnet: str) -> str:
    """Given a subnet, return available ip address.

    Args:
        subnet (str): subnet address in CIDR

    Returns:
        str: ip address

    """
    network = ipaddress.ip_network(subnet)
    ip_address_list = get_available_ip_address()
    for ip in ip_address_list:
        ip_addr = ipaddress.ip_address(ip)
        if ip_addr in network:
            return ip
    raise ValueError(f"Could not find ip address for subnet {subnet}")


def get_empty_port(ip: str | None = None, desired_port: int | None = None) -> int:
    """Find an empty port number.

    Once a port is reserved, other requests won't touch it for 60 seconds.

    Args:
        ip (str | None): location to get port. Defaults to localhost.
        desired_port (int | None): desired port. Defaults to any empty port.

    Returns:
        int: [description]

    Raises:
        DoesNotExistError: if no port resource is available.

    """
    ip = ip or "127.0.0.1"
    desired_port = desired_port or 0
    try:
        return int(ephemeral_port_reserve.reserve(ip, desired_port))
    except SocketError as e:
        raise DoesNotExistError from e


async def is_node_alive(ip: str) -> bool:
    """Check if node is alive.

    Args:
        ip (str): ip of the node

    Returns:
        bool: True if node is alive

    """
    try:
        result = await check_output(f"ping -c1 {ip}")
        return bool(result)
    except ProcessException:
        return False
