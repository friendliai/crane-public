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

"""Utilities for creating processes."""

from __future__ import annotations

import abc
import asyncio
import logging
import os
import shlex

from async_timeout import timeout
from termcolor import colored

logger = logging.getLogger(__name__)


class ProcessException(Exception):
    """Raised when a process exits with non-zero exit status."""


async def check_output(cmd: str) -> str:
    """Run command and return output.

    Args:
        cmd (str): Command to run

    Raises:
        ProcessException: If process exit with non-zero status

    Returns:
        str: stdout

    """
    logger.debug(colored(cmd, "red"))
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        logger.warning(stderr.decode())
        logger.warning(stdout.decode())
        raise ProcessException(proc.returncode)

    return stdout.decode().strip()


# remote process


class RemoteInterface(abc.ABC):
    """Remote process class interface."""

    @abc.abstractmethod
    async def check(self) -> None:
        """Checks if remote host is available.

        Raises:
            ProcessException: if remote host is not available.

        """

    @abc.abstractmethod
    async def exec(self, cmd: str) -> str:
        """Execute a command in remote machine.

        Args:
            cmd (str): command

        Raises:
            ProcessException: If process exit with non-zero status

        Returns:
            str: stdout of process.

        """


class RemoteHost(RemoteInterface):
    """Handles running commands on remote machines.

    Args:
        host_ip (str): remote host
        port (int): port on remote machine, defaults to 22

    """

    def __init__(self, host_ip: str, port: int = 22) -> None:
        """Initialize."""
        self.host_ip = host_ip
        self.port = port

    async def check(self) -> None:
        """Checks if ssh is available.

        Waits for 5 seconds.
        """
        try:
            async with timeout(5):
                await self.exec("exit")
        except asyncio.TimeoutError:
            raise ProcessException("ssh timed out") from None

    async def exec(self, cmd: str) -> str:
        """Execute a command."""
        cmd = shlex.quote(cmd)
        remote_cmd = f"ssh -p {self.port} {self.host_ip} {cmd}"
        logger.info(colored(f"$ {remote_cmd}", "red"))

        return await check_output(remote_cmd)


class BatchRemoteHost(RemoteInterface):
    """A remote host decorator that execute commands in batch.

    Args:
        host_list (list[RemoteHost]): list of remote hosts

    """

    def __init__(self, host_list: list[RemoteHost]) -> None:
        """Initialize."""
        self.host_list = host_list

    async def check(self) -> None:
        """Check if all hosts are available."""
        futures = [rh.check() for rh in self.host_list]
        await asyncio.gather(*futures)

    async def exec(self, cmd: str) -> str:
        """Execute a command concurrently to all endpoints.

        Args:
            cmd (str): command

        Raises:
            ProcessException: If process exit with non-zero status

        Returns:
            str: stdout of process.

        """
        futures = [rh.exec(cmd) for rh in self.host_list]
        stdout_list = await asyncio.gather(*futures)
        return "\n".join(
            f"[{host}] {stdout}" for stdout, host in zip(stdout_list, self.host_list)
        )


class VenvRemoteHost(RemoteInterface):
    """A remote host manager with virtual env support.

    Args:
        host (RemoteHost): remote host object
        venv_path (str): a virtualenv path

    """

    def __init__(self, host: RemoteHost, venv_path: str) -> None:
        """Initialize."""
        self.host = host
        self.venv_path = venv_path

    async def check(self) -> None:
        """Check if ssh is available, and venv_path exists."""
        await self.host.check()
        cmd = f"ls {str(self.venv_path)}"
        await self.host.exec(cmd)

    async def exec(self, cmd: str) -> str:
        """Execute a command in a virtualenv setting."""
        activate_cmd = f"source {os.path.join(self.venv_path, 'bin/activate')}"
        cmd = activate_cmd + "; " + cmd
        cmd = f"bash -c {shlex.quote(cmd)}"
        return await self.host.exec(cmd)
