#!/usr/bin/env python3
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

"""Defines exceptions for crane.core.admin."""


class BaseCraneException(Exception):
    """Crane error.

    All crane exceptions inherit this class.
    """


##########
# CLI    #
##########
class BaseCLIException(BaseCraneException):
    """Crane CLI error."""


##########
# Admin  #
##########
class BaseAdminUserException(BaseCraneException):
    """Crane admin daemon bad user request."""


class NotPartOfClusterException(BaseAdminUserException):
    """This node is not part of the cluster."""


class AlreadyPartOfClusterException(BaseAdminUserException):
    """This node is already part of a cluster."""


class AlreadyLeaderException(BaseAdminUserException):
    """This node is already a leader."""


class AlreadyFollowerException(BaseAdminUserException):
    """This node is already a follower."""


class NotLeaderException(BaseAdminUserException):
    """This operation is only permitted to leader nodes."""


class NodeNotUniqueException(BaseAdminUserException):
    """The specified node doesn't identify a unique node."""


class NodeDoesNotExistException(BaseAdminUserException):
    """The specified node doesn't exist."""


class LeaderLeaveNotForcedException(BaseAdminUserException):
    """Leader nodes cannot leave the cluster without forcing."""


# exceptions that are used internally only by admin
class BaseAdminInternalException(BaseCraneException):
    """Crane admin daemon server error."""


class ContainerTimeoutException(BaseAdminInternalException):
    """A container component setup experienced a time-out."""


class OnetimeContainerFailException(BaseAdminInternalException):
    """An ephemeral container component failed during setup."""


class ContainerPreflightError(BaseAdminUserException):
    """Preflight on a container failed."""


#################
# Miscellaneous #
#################


class DoesNotExistError(KeyError):
    """The object does not exist."""


class AlreadyExistError(KeyError):
    """The object already exists."""
