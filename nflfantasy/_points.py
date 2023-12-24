"""
"""

import json
import pandas as pd
import pathlib
import typing


class PointScheme:
    """
    """
    default: pathlib.Path

    def __init__(self, scheme: pathlib.Path):
        with open(scheme, "r", encoding="utf-8") as file:
            self._scheme = json.load(file)

    def __getattr__(self, name: str) -> typing.Dict[str, float]:
        return self.scheme[name]

    def __getitem__(self, item: typing.Tuple[str, str]) -> float:
        return self.scheme[item[0]][item[1]]

    @property
    def scheme(self) -> typing.Dict[str, typing.Dict[str, float]]:
        """
        """
        return self._scheme

    @property
    def keys(self) -> typing.List[typing.Tuple[str, str]]:
        """
        """
        return [
            (a, b) for a, z in self.scheme.items() for b in z
        ]


class Offense(PointScheme):
    """
    """
    default = pathlib.Path("data", "points", "offense.json")

    def __init__(self, scheme: pathlib.Path):
        super().__init__(scheme)


class Kickers(PointScheme):
    """
    """
    default = pathlib.Path("data", "points", "kickers.json")

    def __init__(self, scheme: pathlib.Path):
        super().__init__(scheme)


class DefenseST(PointScheme):
    """
    """
    default = pathlib.Path("data", "points", "defensest.json")

    def __init__(self, scheme: pathlib.Path):
        super().__init__(scheme)


class Scorecard:
    """
    """
    def __init__(
        self,
        offense: pathlib.Path = Offense.default,
        kickers: pathlib.Path = Kickers.default,
        defensest: pathlib.Path = DefenseST.default
    ):
        self._offense = Offense(offense)
        self._kickers = Kickers(kickers)
        self._defensest = DefenseST(defensest)

    @property
    def offense(self) -> pd.DataFrame:
        """
        """
        return self._scheme(self._offense)

    @property
    def kickers(self) -> Kickers:
        """
        """
        return self._scheme(self._kickers)

    @property
    def defensest(self) -> DefenseST:
        """
        """
        return self._scheme(self._defensest)

    def _scheme(self, scheme: PointScheme) -> pd.Series:
        """
        :param scheme:
        :return:
        """
        return pd.Series({k: scheme[k] for k in scheme.keys})
