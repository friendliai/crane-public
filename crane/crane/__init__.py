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

"""Crane, GPU Cluster Manager for DL training.

When a Job is submitted to the cluster, it goes into job queue (Queued)
When a Job is scheduled, it goes into running job pool (Running)
- At running state, each Job has ApplicationMaster(AM).
- AM receives MiniCluster.
- AM can create Tasks. A Task is a group of containers.
- AM can listen to events such as container dead or cancellation by user
When a Job is finished, it's at finished state (erased)

"""

__version__ = "0.3.2"
