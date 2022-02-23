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

"""State transition logger for lifecycle objects."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Flag, auto
from typing import (
    TYPE_CHECKING,
    ClassVar,
    Generic,
    Iterable,
    List,
    Mapping,
    Sequence,
    Tuple,
    TypeVar,
    cast,
    overload,
)

from crane.common.model import dataclass
from crane.common.util.descriptor import cached_property
from crane.common.util.generic import GenericArgsHookMixin
from crane.common.util.serialization import CustomSerializeMixin, JsonValue

S = TypeVar("S", bound="State")
SH = TypeVar("SH", bound="State")


class State(Flag):
    """Base class for enum."""

    @staticmethod
    def __transitions__() -> Iterable[tuple[State, State]]:
        """Return valid transitions."""
        raise NotImplementedError

    @staticmethod
    def __init_state__() -> State:
        """Return initial state."""
        raise NotImplementedError

    def validate(self: State, next_: State) -> None:
        """Validate state transition.

        Args:
            next_ (State): next state

        Raises:
            StateTransitionError: if next state is invalid

        """
        if (self not in self._t_matrix) or (not next_ & self._t_matrix[self]):
            raise StateTransitionError(self, next_)

    @cached_property
    def _t_matrix(self) -> Mapping[State, State]:
        return dict(self.__transitions__())


class StateTransitionError(Exception):
    """Raised when invalid state transition occurs."""

    def __init__(self, curr: State, next_: State) -> None:
        """Initialize."""
        super().__init__(f"Invalid state transition from {curr} to {next_}")


@dataclass(frozen=True)
class StateHistory(
    GenericArgsHookMixin, Sequence[Tuple[S, float]], Generic[S], CustomSerializeMixin
):
    """History in the form of list of states with their transition times.

    Due to implementation details (limitations of pydantic and mashumaro),
    we store two lists instead one list of tuples.

    Note:
        Subclassing DataClassJSONSerializeMixin due to typing limitations.
        We cannot create generic typevars. Therefore, methods' return types are generics
        of `StateHistory`. Therefore, child classes' return types are `StateHistory`
        also. Adding a TYPE_CHECKING around `states` to avoid mashumaro error.

    """

    init_state: ClassVar[S]  # pylint: disable=invalid-name

    timestamps: Sequence[float]
    states: Sequence[S]

    @classmethod
    def _generic_args_hook(cls, args: tuple) -> None:
        """Initialize init_state."""
        state_cls = args[0]
        cls.init_state = state_cls.__init_state__()

    @classmethod
    def from_init(cls: type[StateHistory[S]]) -> StateHistory[S]:
        """Define class with a initial state."""
        history = cls([], [])
        return history.transition(cls.init_state)

    @property
    def curr(self) -> S:
        """Get the current state."""
        return self.states[-1]

    @property
    def timestamp(self) -> float:
        """Get the latest transition timestamp."""
        return self.timestamps[-1]

    @property
    def created(self) -> float:
        """Get the creation timestamp."""
        return self.timestamps[0]

    def transition(self, next_: S) -> StateHistory[S]:
        """Transition to next state.

        Raises:
            StateTransitionError: if next state is invalid

        Returns:
            StateHistory[S]: new history object

        """
        if self.states:
            self.curr.validate(next_)

        now = datetime.utcnow()
        timestamp = now.replace(tzinfo=timezone.utc).timestamp()

        return self.__class__(
            timestamps=[*self.timestamps, timestamp], states=[*self.states, next_]
        )

    def reset(self) -> StateHistory[S]:
        """Reset state history.

        Create a new state history with only the initial state.
        """
        return self.from_init()

    @overload
    def __getitem__(self, idx: int) -> tuple[S, float]:
        ...

    @overload
    def __getitem__(self, idx: slice) -> Sequence[tuple[S, float]]:
        ...

    def __getitem__(
        self, idx: int | slice
    ) -> tuple[S, float] | Sequence[tuple[S, float]]:
        """Get the idx'th state transition."""
        if isinstance(idx, int):
            return self.states[idx], self.timestamps[idx]
        return list(*zip(self.states[idx], self.timestamps[idx]))

    def __len__(self) -> int:
        return len(self.states)

    def _serialize(self) -> dict[str, JsonValue]:
        """Serialize into a dict."""
        return {
            "timestamps": list(self.timestamps),
            "states": [s.value for s in self.states],
        }

    @classmethod
    def _deserialize(cls, value: dict[str, JsonValue]) -> StateHistory[S]:
        """Create object from dict."""
        timestamps = cast(List[float], value["timestamps"])
        states = cast(List[int], value["states"])
        state_cls = cls.init_state.__class__
        return cls(
            timestamps=timestamps,
            states=[state_cls(s) for s in states],
        )


class StateEntityMixin(Generic[S]):
    """A mixin for entities with a state and state history."""

    if TYPE_CHECKING:
        state_history: StateHistory[S]

    @property
    def state(self) -> S:
        """Return current state."""
        return self.state_history.curr

    @state.setter
    def state(self, next_state: S) -> None:
        """Transition to next state.

        Raises:
            StateTransitionError: if transition to next state is invalid

        """
        self.state_history = self.state_history.transition(next_state)

    def reset_state(self) -> None:
        """Reset state history."""
        self.state_history = self.state_history.reset()


__all__ = ["auto"]
