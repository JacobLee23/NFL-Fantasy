"""
"""

import json
import pathlib
import typing

import pandas as pd


class Scoring:
    """
    .. py:attribute:: espn

        Path to JSON file containing ESPN default scoring schema

    .. py:attribute:: yahoo

        Path to JSON file containing Yahoo! Sports default scoring schema
    """
    espn = pathlib.Path(__file__).parent / "data" / "espn" / "scoring.json"
    yahoo = pathlib.Path(__file__).parent / "data" / "yahoo" / "scoring.json"

    def __init__(self, path: typing.Union[pathlib.Path, str]):
        self._path = pathlib.Path(path)

        with open(self.path, "r", encoding="utf-8") as file:
            self._schema = json.load(file)

        self._series = pd.Series(
            [z for x in self.schema.values() for y in x.values() for z in y.values()],
            pd.MultiIndex.from_tuples(
                [(x, y, z) for x in self.schema for y in self.schema[x] for z in self.schema[x][y]]
            )
        )

    @property
    def path(self) -> pathlib.Path:
        """
        """
        return self._path

    @property
    def schema(self) -> typing.Dict[str, typing.Dict[str, typing.Dict[str, typing.Any]]]:
        """
        """
        return self._schema

    @property
    def series(self) -> pd.Series:
        """
        """
        return self._series


class ESPN(Scoring):
    """
    """
    def __init__(self, path: typing.Union[pathlib.Path, str] = Scoring.espn):
        super().__init__(path)

    @property
    def offense(self) -> pd.Series:
        """
        """
        return self.series.loc["OFF"]
    
    @property
    def kicking(self) -> pd.Series:
        """
        """
        return self.series.loc["K"]
    
    @property
    def punting(self) -> pd.Series:
        """
        """
        return self.series.loc["P"]
    
    @property
    def defense_idp(self) -> pd.Series:
        """
        """
        return self.series.loc["IDP"]
    
    @property
    def defensest(self) -> pd.Series:
        """
        """
        return self.series.loc["D/ST"]
    
    @property
    def head_coach(self) -> pd.Series:
        """
        """
        return self.series.loc["HC"]


class Yahoo(Scoring):
    """
    """
    def __init__(self, path: typing.Union[pathlib.Path, str] = Scoring.yahoo):
        super().__init__(path)

    @property
    def offense(self) -> pd.Series:
        """
        """
        return self.series.loc["OFF"]

    @property
    def defense(self) -> pd.Series:
        """
        """
        return self.series.loc["DEF"]

    @property
    def kicking(self) -> pd.Series:
        """
        """
        return self.series.loc["K"]
