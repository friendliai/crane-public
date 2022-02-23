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

"""Module dealing with job commands."""

from __future__ import annotations

import concurrent.futures
import shlex
from datetime import datetime
from itertools import cycle
from pathlib import Path
from typing import Any, Iterable, Iterator, List

import typer

import crane.common.constant as C
from crane.cli.common.cli import check_connection
from crane.cli.common.display import build_time_delta, error, info, warn
from crane.cli.user.typing import UserClientContext
from crane.common.api_model import MCInspectResponse
from crane.common.model import log, mini_cluster
from crane.common.model.mini_cluster import State
from crane.common.util.functool import arg_group, expand_arg_group
from crane.common.util.pretty import tabulate_rows
from crane.lib import SyncUserClient
from crane.lib.common.exception import BaseCraneAPIException

app = typer.Typer()


@arg_group
class FilterJobsOption:
    """Argument group for filtering jobs."""

    ctx: UserClientContext
    id_or_name: str = typer.Argument(
        None, help="""Job ID or name, or its prefix (the first n letters of id/name)."""
    )
    tags: List[str] = typer.Option([], "--tag", "-t", help="List of job tags")

    @property
    def client(self) -> SyncUserClient:
        """Return crane user client."""
        return self.ctx.obj

    def filter_jobs(self, status_list: list[str]) -> list[str]:
        """Return list of job id given job status list."""
        return self.client.job.filter(self.id_or_name, self.tags, status_list)

    def get_job(self) -> str:
        """Return single job id.

        Raise error if filter rules do not resolve to a single job.
        """
        if self.id_or_name is None and not self.tags:
            error("Either id_or_name or tags should be provided")

        job_list = self.client.job.filter(self.id_or_name, self.tags)
        if not job_list:
            error("No jobs found.")

        if len(job_list) > 1:
            error("More than one job found.")

        return job_list[0]


# Note: Order of `check_connection` and `expand_arg_group` is important.
#       `check_connection` assumes that ctx: UserClientContext is the first argument


@app.command("list")
@check_connection
@expand_arg_group
def list_job(
    job_filter: FilterJobsOption,
    list_all: bool = typer.Option(False, "--all", "-a"),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Prints the names of jobs only.",
        envvar="CRANE_CLI_QUIET",
    ),
):
    """List jobs with given query."""
    client = job_filter.client

    def job_status_iter() -> Iterator[MCInspectResponse]:
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(client.job.inspect, job_id) for job_id in jobs]
            for future in concurrent.futures.as_completed(futures):
                yield future.result()

    states = _get_state_filter(list_all)

    try:
        jobs = job_filter.filter_jobs(states)
        sorted_job_status = _sort_job_by_creation(job_status_iter())

        if not jobs:
            warn("No jobs found.")
            return

        if quiet:
            for job_status in sorted_job_status:
                info(job_status.name)
            return

        columns: list[Any] = [
            ("name", str),
            ("tags", List[str]),
            ("created", str),
            ("status", str),
            ("GPU", str),
        ]

        rows = [_build_job_status_row(job_status) for job_status in sorted_job_status]

        info(tabulate_rows(rows, columns))
    except BaseCraneAPIException as e:
        error(str(e))


@app.command("add")
@check_connection
def add_job(  # pylint: disable=too-many-arguments,too-many-locals
    ctx: UserClientContext,
    image: str,
    resource: str,
    command: str = typer.Option(
        None,
        "--cmd",
        "-c",
        help="Command to run. If not provided, defaults to command in docker image.",
    ),
    envs: List[str] = typer.Option(
        [], "--env", "-e", help="Environment variables in [key]=[value] format."
    ),
    mounts: List[str] = typer.Option(
        [],
        "--mount",
        "-m",
        help="Mount config in [host_dir]:[container_dir]:[option] format."
        + "For host directory, Crane supports relative path as well.",
    ),
    ports: List[int] = typer.Option([], "--port", "-p", help="Assign private port."),
    public_ports: List[int] = typer.Option(
        [], "--public-port", "-pp", help="Assign public port."
    ),
    rdma: bool = typer.Option(False, help="If set, allow rdma use."),
    overlay: bool = typer.Option(
        False, " /--no-overlay", help="No AM overlay network needed."
    ),
    shm_size: str = typer.Option(
        "64m", "--shm-size", help="The size of /dev/shm in containers. Default is 64m."
    ),
    name: str = typer.Option(
        None, "--name", "-n", help="Job name. Must be unique per user"
    ),
    tags: List[str] = typer.Option([], "--tag", "-t", help="job tags"),
    shell: bool = typer.Option(
        False,
        "--shell/--no-shell",
        help="If true, the command will be executed through the shell.",
    ),
    # TODO: add e2etest with --init option
    init: bool = typer.Option(
        True, "--init/--no_init", help="If true, run an init inside the container."
    ),
):
    """Add a new job to crane cluster.

    Launch a job with [image] and [resource]
    image is specified in docker image format
    resource is specified as [app gpu]:[min gpu]:[max gpu]
        can be specified as [app gpu] or [app gpu]:[total gpu]
    """
    client = ctx.obj

    # TODO: What if user wants to reuse previous workspace regardless of modification?
    context_id: str | None = None
    if _is_workspace_initialized():
        context_id = client.ws.add()

    if shell:
        command = f"sh -c {shlex.quote(command)}"

    try:
        job_status = client.job.add(
            image,
            resource,
            command,
            envs,
            mounts,
            ports,
            public_ports,
            rdma,
            overlay,
            shm_size,
            name,
            tags,
            init,
            context_id,
        )
    except BaseCraneAPIException as e:
        error(str(e))

    messages = [f"Job ID:   {job_status.mc_id}"]
    messages.append(f"Job name: {job_status.name}")
    messages.append(
        f"Add time: {datetime.fromtimestamp(job_status.add_time).isoformat()}"
    )
    info("\n".join(messages))


@app.command("inspect")
@check_connection
@expand_arg_group
def stat_job(
    job_filter: FilterJobsOption,
    format_str: str = typer.Option(None, "--format", help="Formatting template."),
):
    """Show detailed job information."""
    try:
        job_id = job_filter.get_job()
        job_status = job_filter.client.job.inspect(job_id)
    except BaseCraneAPIException as e:
        error(str(e))

    if not format_str:
        info(str(job_status.to_yaml()))
    else:
        info(format_str.format(job_status))


@app.command("kill")
@check_connection
@expand_arg_group
def kill_job(
    job_filter: FilterJobsOption,
    force: bool = typer.Option(False, "--force"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Automatic yes to prompt."),
):
    """Kill jobs (send a unix signal to each job)."""
    states_to_kill = [State.QUEUED, State.RUNNING, State.PAUSED]
    state_to_str = [i.name for i in states_to_kill]

    try:
        job_list = job_filter.filter_jobs(state_to_str)
        count = len(job_list)

        if not yes:
            messages = ["The following jobs will be killed:"]
            for job_id in job_list:
                messages.append(job_id)
            messages.append("Proceed?")
            typer.confirm("\n".join(messages), default=False, abort=True)

        client = job_filter.client

        for job_id in job_list:
            client.job.kill(job_id, force)
    except BaseCraneAPIException as e:
        error(str(e))

    info(f"Successfully killed {count} job{'s' if count > 1 else ''}.")


@app.command("remove")
@app.command("rm")
def remove_job(
    ctx: UserClientContext,
    id_or_name: str = typer.Argument(None),
    tags: List[str] = typer.Option([], "--tag", "-t", help="job tag"),
    force: bool = typer.Option(False, help="Force move a job."),
):
    """Remove multiple jobs.

    Removing a job will remove every information about the job including logs.
    You cannot remove a job that is not terminated unless forced.

    """
    # TODO: use executor to delete multiple jobs at once
    client = ctx.obj

    terminated_states = ["DONE", "INVALID", "ERROR"]

    try:
        job_list = client.job.filter(id_or_name, tags)
        if not job_list:
            warn("No jobs found.")
            return

        for job_id in job_list:
            job_status = client.job.inspect(job_id)
            if job_status.state_history.curr not in terminated_states:
                if force:
                    client.job.kill(job_id, force)
                else:
                    error(
                        f"You cannot remove a running job({job_id}). "
                        "Kill the job or force remove."
                    )
            client.job.delete(job_id)
            info(job_id)
    except BaseCraneAPIException as e:
        error(str(e))


# pylint: disable=too-many-arguments
@app.command("log")
@check_connection
@expand_arg_group
def log_job(
    job_filter: FilterJobsOption,
    follow: bool = typer.Option(False, "--follow", "-f"),
    stderr: bool = typer.Option(False, "--stderr", help="Prints stderr logs only."),
    stdout: bool = typer.Option(False, "--stdout", help="Prints stdout logs only."),
    timestamp: bool = typer.Option(False, "--timestamp", help="Show timestamp"),
    since: datetime = typer.Option(None, help="Timestamp in iso 8601 format"),
):
    """Get log of job."""
    if stdout and stderr:
        raise typer.BadParameter(
            "Either --stderr or --stdout allowed for option. \n"
            "Try 'crane job log --help' for help."
        )

    source = (
        log.LogSource.STDOUT if stdout else log.LogSource.STDERR if stderr else None
    )
    filter_ = log.LogFilter(source=source, since=since)

    client = job_filter.client

    try:
        job_id = job_filter.get_job()
        job_status = client.job.inspect(job_id)
        if job_status.state_history.curr is mini_cluster.State.QUEUED:
            warn("Job is queued.")
            return

        _print_logs(client.job.log(job_id, follow, filter_), timestamp=timestamp)
    except BaseCraneAPIException as e:
        error(str(e))


def _print_logs(log_stream: Iterator[log.Log], *, timestamp: bool):
    factory = ColorFactory()

    # TODO: container id is too long. find a replacement
    for log_line in log_stream:
        log_ = log_line.log.strip()

        header = f"{log_line.container_id} | "
        if timestamp:
            time_str = log_line.timestamp.strftime("%Y-%m-%d_%H:%M:%S")
            header = f"{header}{time_str} "
        header = typer.style(header, fg=factory.get_color(log_line.container_id))

        if log_line.source == "stderr":
            log_ = typer.style(log_, fg=typer.colors.RED)
        info(f"{header}{log_}")


def _build_job_status_row(job_status: MCInspectResponse) -> tuple:
    history = job_status.state_history
    state = history.curr
    if state in ("ERROR", "INVALID"):
        state = typer.style(state, typer.colors.BRIGHT_RED)

    created = build_time_delta(history.created)
    status = f"{state} {build_time_delta(history.timestamp)}"

    gpu_status = _build_gpu_status(job_status)
    return (job_status.name, job_status.tags, created, status, gpu_status)


def _build_gpu_status(job_status: MCInspectResponse) -> str:
    """Return gpu status in form {acquired}/{released}."""
    acquired_gpu = job_status.acquired_resource.as_logical().reduce().num_gpu
    requested_gpu = job_status.job_config.resource_spec.max_resource.num_gpu
    return f"{acquired_gpu}/{requested_gpu}"


def _get_state_filter(list_all: bool) -> list[str]:
    states = (
        []
        if list_all
        else [
            mini_cluster.State.QUEUED,
            mini_cluster.State.RUNNING,
            mini_cluster.State.PAUSED,
        ]
    )
    return [s.name for s in states]


def _sort_job_by_creation(
    job_list: Iterable[MCInspectResponse],
) -> Iterable[MCInspectResponse]:
    return sorted(job_list, key=lambda x: x.state_history.created, reverse=True)


def _is_workspace_initialized():
    config_path = Path.cwd() / C.Workspace.CONTEXT_DIR / C.Workspace.CONFIG_PATH
    return config_path.exists()


class ColorFactory:
    """Return a color associated with the given continer id."""

    text_colors = [
        typer.colors.BRIGHT_BLACK,
        typer.colors.BRIGHT_GREEN,
        typer.colors.BRIGHT_YELLOW,
        typer.colors.BRIGHT_BLUE,
        typer.colors.BRIGHT_MAGENTA,
        typer.colors.BRIGHT_CYAN,
        typer.colors.BRIGHT_WHITE,
    ]

    def __init__(self) -> None:
        """Initialize."""
        self.iter_color = iter(cycle(self.text_colors))
        self.container_id_to_color: dict[str, str] = {}

    def get_color(self, container_id: str) -> str:
        """Return color given container id."""
        if container_id not in self.container_id_to_color:
            self.container_id_to_color[container_id] = next(self.iter_color)
        return self.container_id_to_color[container_id]
