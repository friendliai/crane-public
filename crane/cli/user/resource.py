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

"""Crane user cli resource commands."""

import typer

import crane.common.constant as C
from crane.cli.common.cli import check_connection
from crane.cli.user.typing import UserClientContext
from crane.common.model.resource import PhysicalCluster

app = typer.Typer()


@app.command("all")
@check_connection
def cluster_resource(ctx: UserClientContext):
    """Show all cluster resource."""
    client = ctx.obj
    resource_state = client.resource.cluster_resource()

    free_gpu_num = _get_num_gpu(resource_state.released)
    busy_gpu_num = _get_num_gpu(resource_state.acquired)

    typer.echo(
        C.Template.RESOURCE_ALL.format(
            free_gpu_num=free_gpu_num, busy_gpu_num=busy_gpu_num
        )
    )


def _get_num_gpu(resource_group: PhysicalCluster) -> int:
    return resource_group.as_logical().reduce().num_gpu
