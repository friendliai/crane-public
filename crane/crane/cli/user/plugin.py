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

"""Crane cli Plugin manager."""

import pkg_resources
import typer

CRANE_CLI_PLUGIN_ENTRYPOINT = "cranecli.plugins"


def register_plugins(app: typer.Typer) -> None:
    """Register crane cli plugins to typer app."""
    plugin_versions = {}

    for entry_points in pkg_resources.iter_entry_points(CRANE_CLI_PLUGIN_ENTRYPOINT):
        plugin_module = entry_points.load()
        dist = pkg_resources.get_distribution(plugin_module.__package__)
        plugin_versions[entry_points.name] = dist.version

        app.add_typer(getattr(plugin_module, "app"))

    version_str = ", ".join(f"{name}={ver}" for name, ver in plugin_versions.items())

    if app.registered_callback is None:

        def _mock():
            pass

        app.callback()(_mock)

    assert app.registered_callback
    app.registered_callback.callback.__doc__ = f"Crane CLI\tplugins: {version_str}"
