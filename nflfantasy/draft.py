"""
"""

import itertools
import typing

import numpy as np
import pandas as pd

from .roster import Player, Roster


class SnakeDraft:
    """
    :param rosters:
    :param rounds:
    """
    _size: int
    _picks: typing.Iterator[typing.Tuple[int, int]]
    _results: pd.DataFrame

    def __init__(self, rosters: typing.Sequence[Roster], nrounds: int):
        self._rosters = tuple(rosters)
        self._nrounds = nrounds

        self.reset()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(nrounds={self.nrounds}, nteams={self.nteams})"

    def __len__(self) -> int:
        return self._size

    @property
    def results(self) -> typing.Optional[pd.DataFrame]:
        """
        :return:
        """
        return self._results

    @property
    def rosters(self) -> typing.Tuple[Roster]:
        """
        :return:
        """
        return self._rosters

    @property
    def nrounds(self) -> int:
        """
        :return:
        """
        return self._nrounds

    @property
    def nteams(self) -> int:
        """
        :return:
        """
        return len(self.rosters)

    @property
    def volume(self) -> int:
        """
        :return:
        """
        return self.nrounds * self.nteams

    @property
    def rounds(self) -> pd.DataFrame:
        """
        :return:
        """
        dataframe = pd.DataFrame(
            index=pd.Index(range(1, self.nrounds + 1), name="Round"),
            columns=pd.Index(list(map(id, self.rosters)), name="Roster ID")
        )
        for i, v in enumerate(dataframe.index.values):
            dataframe.iloc[i, :] = pd.Series(
                (v, i * self.nteams + x) for x in (
                    range(1, self.nteams + 1) if i % 2 == 0 else range(self.nteams, 0, -1)
                )
            )

        return dataframe

    def peek(self) -> typing.Union[typing.Tuple[int, int], typing.Tuple[None, None]]:
        """
        Retrieves the round and pick numbers of the next draft pick without affecting the state of
        the draft.

        :return: The round and pick numbers of the next draft pick
        """
        try:
            peek = next(self._picks)
        except StopIteration:
            return None, None
        self._picks = itertools.chain([peek], self._picks)

        return peek

    def push(self, player: Player) -> typing.Tuple[int, int]:
        """
        Appends a player to the draft results.

        :param player: The player to append to the draft results
        :return: The round and pick numbers of the drafted player
        :raise ValueError: The player could not be added to the corresponding roster
        """
        nround, pick = next(self._picks)
        roster = self.get_team(pick)

        added = roster.add(player)
        if player not in added:
            raise ValueError(f"Could not add player {player!r} to roster of team {roster!r}")

        self.results.loc[nround, id(roster)] = player
        self._size += 1

        return nround, pick

    def pop(self) -> typing.Optional[Player]:
        """
        Removes the most recently drafted player from the draft results.

        :return: The player removed from the draft results
        :raise ValueError: The player could not be dropped from the corresponding roster
        """
        if len(self) == 0:
            return None

        nround, pick = self.peek()
        nround = self.nrounds if nround is None else (
            nround - 1 if (pick - 1) % self.nteams == 0 else nround
        )
        pick = self.volume if pick is None else pick - 1
        roster = self.get_team(pick)
        player = self.results.loc[nround, id(roster)]

        dropped = roster.drop(player)
        if player not in dropped:
            raise ValueError(f"Could not drop player {player!r} from roster of team {roster!r}")

        self.results.loc[nround, id(roster)] = np.nan
        self._size -= 1

        self._picks = itertools.chain([(nround, pick)], self._picks)

        return player

    def reset(self) -> None:
        """
        Clears the draft results and resets the draft pick order.
        """
        self._size = 0
        self._picks = ((i // self.nteams + 1, i + 1) for i in range(self.volume))
        self._results = pd.DataFrame(
            index=pd.Index(range(1, self.nrounds + 1), name="Round"),
            columns=pd.Index(list(map(id, self.rosters)), name="Roster ID"),
        )

    def get_nround(self, pick: int) -> int:
        """
        :param pick: The number of the draft pick to lookup
        :return: The round number containing the specified pick number
        :raise ValueError: Invalid value ``pick`` passed
        """
        if not 1 <= pick <= self.volume:
            raise ValueError(pick)
        return (pick - 1) // self.nteams

    def get_team(self, pick: int) -> Roster:
        """
        :param pick: The number of the draft pick to lookup
        :return: The team scheduled to draft at the specified pick number
        """
        return self.rosters[
            (pick - 1) % self.nteams if self.get_nround(pick) % 2 == 1
            else self.nteams - ((pick - 1) % self.nteams + 1)
        ]
