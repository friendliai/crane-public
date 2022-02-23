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

"""Setup Crane."""

import os
import json
from glob import glob
from pathlib import Path
from setuptools import find_packages, setup, Command
from setuptools.command.build_py import build_py as org_build_py
from setuptools.command.sdist import sdist as org_sdist
from setuptools.command.develop import develop as org_develop
from subprocess import check_call, check_output, CalledProcessError
from tempfile import TemporaryDirectory

import unasync


README = Path(__file__).parent / "README.md"

with open(README, "r") as fh:
    long_description = fh.read()


def git_clone(url: str, branch=None, dest=None) -> None:
    branch_args = [f"--branch={branch}"] if branch else []
    dest_args = [dest] if dest else []
    url = f"https://github.com/{url}"
    check_call(["git", "clone", "--depth=1", *branch_args, url, *dest_args])

def check_git_outputs(*args: str) -> str:
    output = check_output(["git", *args])
    return output.decode("utf-8").strip()


class checkpoint(Command):
    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            git_branch = check_git_outputs("rev-parse", "--abbrev-ref", "HEAD")
            git_commit = check_git_outputs("rev-list", "-1", "HEAD")
            git_timestamp = check_git_outputs("show", "-s", "--format=%ci", git_commit)

            ckpt_dict = {
                "git_branch": git_branch,
                "git_commit": git_commit,
                "git_timestamp": git_timestamp,
            }

            file = Path(__file__).parent / "crane/checkpoint.json"
            with open(file, "w") as f:
                json.dump(ckpt_dict, f)

        except CalledProcessError:
            if "NO_GIT_INFO" not in os.environ:
                raise


class genSyncAPI(Command):
    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        files = glob("crane/**/*.py", recursive=True)
        unasync.unasync_files(
            files,
            rules=[
                unasync.Rule(
                    "crane/lib/aio",
                    "crane/lib/sync",
                    additional_replacements={
                        "aio": "sync",
                        "anext": "next",
                        "await_if_coro": "return_non_coro",
                        "aclose": "close",
                        "aiter_lines": "iter_lines",
                        "async_sleep": "sync_sleep",
                    },
                )
            ],
        )


class build_py(org_build_py):
    def run(self):
        self.run_command("gen_sync_api")
        self.run_command("checkpoint")
        super().run()


class sdist(org_sdist):
    def run(self):
        self.run_command("gen_sync_api")
        self.run_command("checkpoint")
        super().run()


class develop(org_develop):
    def run(self):
        self.run_command("gen_sync_api")
        self.run_command("checkpoint")
        super().run()


COMMON_DEPS = [
    "ephemeral_port_reserve==1.1.4",
    "typing_extensions",
    "termcolor==1.1.0",
    "async_timeout==3.0.1",
    "mashumaro==2.2",
    "netifaces==0.10.9",
    "protobuf==3.11.3",
    "tabulate==0.8.6",
    "pydantic==1.8.2",
    "aiofiles==0.7.0",
    "httpx==0.16.1",
    "gql==3.0.0a6",
    "typer[all]==0.3.2",
    "rich==10.9.0",
    "python-dateutil==2.8.2",
]


setup(
    name="crane",
    version="0.3.2",
    author="snuspl",
    author_email="yuyupopo@snu.ac.kr",
    description="A GPU Cluster Manager for DL Workloads",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/snuspl/crane",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache 2.0 License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(
        exclude=(
            "tests",
            "tests.*",
        )
    ),
    cmdclass={
        "build_py": build_py,
        "sdist": sdist,
        "develop": develop,
        "checkpoint": checkpoint,
        "gen_sync_api": genSyncAPI,
    },
    entry_points={
        "console_scripts": [
            "crane = crane.cli.user:app",
        ]
    },
    include_package_data=True,
    install_requires=COMMON_DEPS,
)
