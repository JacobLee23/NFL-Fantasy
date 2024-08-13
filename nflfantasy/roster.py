"""
Interfaces for manipulating fantasy football rosters.
"""

import io
import typing

import pandas as pd


class Player(typing.NamedTuple):
    """
    .. py:attribute:: position

        The position code of the player's roster position.
    
    .. py:attribute:: injured_reserve

        Whether the player is eligible to be placed on the Injured Reserve (IR) list.
    """
    position: str
    injured_reserve: bool


class Positions:
    """
    Interface for manipulating roster position schemata.

    .. py:attribute:: offense

        Offensive (Quarterback, Wide Receiver, Running Back, Tight End) roster position codes.

    .. py:attribute:: flex

        Flex roster position code.
    
    .. py:attribute:: dst

        Defense/Special Teams roster position code.

    .. py:attribute:: kicker

        Kicker roster position code.

    .. py:attribute:: bench

        Bench roster position code.

    .. py:attribute:: injured_reserve

        Injured Reserve roster position code

    .. note::

        Each roster position listed above must be designated an integer number of roster slots
        (though that number can be 0).

    :param schema: The number of roster slots available for each roster position
    """
    offense: typing.Tuple[str, ...] = ("QB", "WR", "RB", "TE")
    flex: str
    dst: str
    kicker: str = "K"
    bench: str = "BN"
    injured_reserve: str = "IR"

    def __init__(self, schema: typing.Dict[str, int]):
        if sorted(schema) != sorted(self.positions):
            raise KeyError(schema)
        if not all(isinstance(x, int) for x in schema.values()):
            raise ValueError(schema)

        self._schema = {k: schema[k] for k in self.positions}
        self._series = pd.Series(self.schema)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(schema={self.schema!r})"

    def __str__(self) -> str:
        with io.StringIO() as buffer:
            self.series.to_string(buffer)

        return buffer.read()

    def __len__(self) -> int:
        return sum(self.schema.values())

    def __contains__(self, item: str) -> bool:
        return item in self.positions

    @classmethod
    def flexable(cls, position: str) -> bool:
        """
        :param position: The position code of the roster position to check
        :return: Whether the given roster position can be moved to the flex position
        """
        return position in cls.offense and position != "QB"

    @property
    def positions(self) -> typing.Tuple[str, ...]:
        """
        The string representations of all valid roster positions.
        """
        return (*self.offense, self.flex, self.dst, self.kicker, self.bench, self.injured_reserve)

    @property
    def schema(self) -> typing.Dict[str, int]:
        """
        A mapping of each roster position code to the number of roster slots available to the
        corresponding position.
        """
        return self._schema

    @property
    def series(self) -> pd.Series:
        """
        A :class:`pd.Series` representaiton of :py:attr:`schema`.
        """
        return self._series

    def moveable(self, player: Player, destination: str) -> bool:
        """
        Determines whether a given player can be moved to a given roster position based on their
        listed position.

        The table below describes the roster slots that a given position can occupy:

        +-------+-------+-------+-------+-------+-------+-------+
        |       | QB    | RB    | WR    | TE    | D/ST  | K     |
        +=======+=======+=======+=======+=======+=======+=======+
        | QB    | X     |       |       |       |       |       |
        +-------+-------+-------+-------+-------+-------+-------+
        | RB    |       | X     |       |       |       |       |
        +-------+-------+-------+-------+-------+-------+-------+
        | WR    |       |       | X     |       |       |       |
        +-------+-------+-------+-------+-------+-------+-------+
        | TE    |       |       |       | X     |       |       |
        +-------+-------+-------+-------+-------+-------+-------+
        | FLEX  |       | X     | X     | X     |       |       |
        +-------+-------+-------+-------+-------+-------+-------+
        | D/ST  |       |       |       |       | X     |       |
        +-------+-------+-------+-------+-------+-------+-------+
        | K     |       |       |       |       |       | X     |
        +-------+-------+-------+-------+-------+-------+-------+
        | BN    | X     | X     | X     | X     | X     | X     |
        +-------+-------+-------+-------+-------+-------+-------+
        | IR    | X*    | X*    | X*    | X*    | X*    | X*    |
        +-------+-------+-------+-------+-------+-------+-------+

        :param player: The player to check
        :param destination: The position code of the destination roster slot of the player
        :return: Whether the player can be moved to the specified roster slot
        :raise KeyError: The specified roster slot is not a valid roster position
        """
        self.validate(player)
        if destination not in self:
            raise KeyError(destination)

        return (
            destination == self.bench
            or destination == player.position
            or (player.injured_reserve and destination == self.injured_reserve)
            or (self.flexable(player.position) and destination == self.flex)
        )

    def validate(self, *players: Player) -> None:
        """
        :param players: One or more players to validate
        :raise ValueError: The player's position is not included in the roster position schema
        """
        for player in players:
            if player.position not in self:
                raise ValueError(player)


class PositionsESPN(Positions):
    """
    Roster position schema for ESPN Fantasy Football.
    """
    positions: typing.Tuple[str, ...] = ("QB", "RB", "WR", "TE")
    flex = "FLEX"
    dst = "D/ST"


class PositionsYahoo(Positions):
    """
    Roster position schema for Yahoo! Sports Fantasy Football.
    """
    flex = "W-R-T"
    dst = "DEF"


class Roster:
    """
    Interface for manipulating rosters, given a roster position schema.

    :param positions: A roster position schema
    :param players: One or more players to include in the roster
    """
    def __init__(self, positions: Positions, *players: Player):
        self._positions = positions
        self._roster = {
            k: tuple(
                None for _ in range(self.positions.schema[k])
            ) for k in self.positions.positions
        }

        self.add(*players)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(positions={self.positions!r}, roster={self.roster!r})"

    def __str__(self) -> str:
        with io.StringIO() as buffer:
            self.series.to_string(buffer)

        return buffer.read()

    @property
    def positions(self) -> Positions:
        """
        The roster position schema.
        """
        return self._positions

    @property
    def roster(self) -> typing.Dict[str, typing.Tuple[typing.Optional[Player], ...]]:
        """
        The roster.
        """
        return self._roster

    @property
    def series(self) -> pd.Series:
        """
        A :class:`pd.Series` representation of :py:attr:`roster`.
        """
        tuples = [(k, i) for k, v in self.positions.schema.items() for i in range(v)]
        index = pd.MultiIndex.from_tuples(tuples=tuples, names=("position", "slot"))

        return pd.Series([self.roster[x[0]][x[1]] for x in tuples], index=index)

    def move(
        self, player: Player, destination: str, *, replace: typing.Optional[Player] = None
    ) -> None:
        """
        Moves a player within a roster to a different roster slot.

        :param player: The player to move
        :param destination: The position code of the roster slot to which to move ``player``
        :raise ValueError: The player cannot be moved to the specified roster slot
        """
        self.positions.validate(player)
        if not self.positions.moveable(player, destination):
            raise ValueError(player, destination)
        if len(self.roster[destination]) == self.positions[destination] and replace is None:
            raise ValueError(replace)

        source: str
        if player in self.roster[player.position]:
            source = player.position
        elif player in self.roster[self.positions.flex]:
            source = self.positions.flex
        elif player in self.roster[self.positions.bench]:
            source = self.positions.bench
        else:
            raise ValueError(player)

        self.roster[source], self.roster[destination] = replace, player

    def add(self, *players: Player) -> typing.List[Player]:
        """
        Attempts to add one or more players to the roster.

        :param players: The player(s) to add to the roster
        :return: A list of players successfully added to the roster
        """
        self.positions.validate(*players)

        added = []
        for player in players:

            position: str
            if len(self.roster[player.position]) < self.positions[player.position]:
                position = player.position
            elif (
                self.positions.flexable(player.position)
                and len(self.roster[self.positions.flex]) < self.positions[self.positions.flex]
            ):
                position = self.positions.flex
            elif len(self.roster[self.positions.bench]) < self.positions[self.positions.bench]:
                position = self.positions.bench
            else:
                continue

            self.roster[position][self.roster[position].index(None)] = player
            added.append(player)

        return added

    def drop(self, *players: Player) -> typing.List[Player]:
        """
        Attempts to drop one or more players from the roster.

        :param players: The player(s) to drop from the roster
        :return: A list of players successfully dropped from the roster
        """
        self.positions.validate(*players)

        dropped = []
        for player in players:

            if player not in self.roster[player.position]:
                raise ValueError(player)

            if player in self.roster[player.position]:
                position = player.position
            elif player in self.roster[self.positions.flex]:
                position = self.positions.flex
            elif player in self.roster[self.positions.bench]:
                position = self.positions.bench
            else:
                continue

            self.roster[position][self.roster[position].index(player)] = None

            dropped.append(player)

        return dropped

    def transaction(
        self, *,
        add: typing.Optional[typing.Union[Player, typing.Sequence[Player]]] = None,
        drop: typing.Optional[typing.Union[Player, typing.Sequence[Player]]] = None
    ) -> typing.Dict[str, typing.List[Player]]:
        """
        Attempts to add/drop one or more players to/from the roster.

        :param add: The player(s) to add to the roster
        :param drop: The player(s) to drop from the roster
        :return: A summary of the transaction
        """
        return {
            "+": self.add(add) if isinstance(add, Player) else self.add(*add),
            "-": self.drop(drop) if isinstance(drop, Player) else self.drop(*drop)
        }

    def trade(
        self, other: "Roster", *,
        add: typing.Union[Player, typing.Sequence[Player]],
        drop: typing.Union[Player, typing.Sequence[Player]]
    ) -> None:
        """
        Attempts to trade one or more players with another roster. Traded-for players are added to
        the roster and dropped from the other roster; Traded-away players are dropped from the
        roster and added to the other roster.

        :param other: The roster with which to enact the trade
        :param add: The player(s) to add to the roster
        :param drop: The player(s) to drop from the roster
        :return: A summary of the trade
        """
        return {
            id(self): {
                "+": self.add(add) if isinstance(add, Player) else self.add(*add),
                "-": self.drop(drop) if isinstance(drop, Player) else self.drop(*drop)
            }, id(other): {
                "+": other.add(drop) if isinstance(drop, Player) else other.add(*drop),
                "-": other.drop(add) if isinstance(add, Player) else other.drop(*add)
            }
        }
