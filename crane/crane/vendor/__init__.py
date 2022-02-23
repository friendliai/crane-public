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

"""Crane vendor modules.

The vendor module is a place for code that concerns third-party frameworks
or software. Code here are not tied to Crane native submodules. They are rather
used by Crane submodules as an interface with third-party software.

async_elasticsearch/: asynchronous elasticsearch client
kubernetes/: Kubernetes client implementation. Wraps kubernetes_asyncio.
"""
