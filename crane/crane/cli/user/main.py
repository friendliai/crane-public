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

"""Console script for crane_cli."""

import typer

from crane.cli.common.command import add_config_commands
from crane.cli.user import job, resource, user, workspace
from crane.cli.user.plugin import register_plugins
from crane.lib import SyncUserClient

app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]})

app.add_typer(user.app, name="user", help="user related commands")
app.add_typer(resource.app, name="resource", help="crane resource related commands")
app.add_typer(job.app, name="job", help="job related commands")
app.add_typer(workspace.app, name="ws", help="workspace related commands")

add_config_commands(app, SyncUserClient)

register_plugins(app)
