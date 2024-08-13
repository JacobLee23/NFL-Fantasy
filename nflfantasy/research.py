"""
"""

import datetime
import io
import re
import typing

import bs4
import numpy as np
import pandas as pd
import requests


class Research:
    """
    """
    url: str

    _position: typing.Union[typing.Literal["O"], int] = "O"
    _stat_category: typing.Literal["stats", "projectedStats"]
    _stat_season: int = datetime.datetime.today().year
    _stat_type: typing.Literal[
        "seasonStats", "seasonProjectedStats", "weekStats", "weekProjectedStats"
    ] = "seasonStats"
    _stat_week: typing.Optional[int] = None

    def __init__(
        self, *, position: typing.Union[str, int] = _position,
        stat_season: int = _stat_season,
        stat_type: str = _stat_type, stat_week: typing.Optional[int] = _stat_week
    ):
        self.position = position
        self.stat_season = stat_season
        self.stat_type = stat_type
        self.stat_week = stat_week

    @property
    def league_id(self) -> typing.Literal[0]:
        """
        """
        return 0

    @property
    def position(self) -> typing.Union[typing.Literal["O"], int]:
        """
        Options:

        - ``"O"``: All Offense
        - `1`: QB
        - `2`: RB
        - `3`: WR
        - `4`: TE
        - `7`: K
        - `8`: DEF
        """
        return self._position

    @position.setter
    def position(self, value: typing.Union[str, int]) -> None:
        if value not in ("O", 1, 2, 3, 4, 7, 8):
            raise ValueError(value)
        self._position = value

    @property
    def stat_category(self) -> typing.Literal["stats", "projectedStats"]:
        """
        """
        return self._stat_category

    @property
    def stat_season(self) -> int:
        """
        """
        return self._stat_season

    @stat_season.setter
    def stat_season(self, value: int) -> None:
        self._stat_season = value

    @property
    def stat_type(self) -> typing.Literal[
        "seasonStats", "seasonProjectedStats", "weekStats", "weekProjectedStats"
    ]:
        """
        """
        return self._stat_type

    @stat_type.setter
    def stat_type(self, value: str) -> None:
        if value not in ("seasonStats", "seasonProjectedStats", "weekStats", "weekProjectedStats"):
            raise ValueError(value)
        self._stat_type = value

        if value in ("seasonStats", "seasonProjectedStats"):
            self.week = None

    @property
    def stat_week(self) -> int:
        """
        """
        return self._stat_week

    @stat_week.setter
    def stat_week(self, value: typing.Optional[int]) -> None:
        if self.stat_type in ("seasonStats", "seasonProjectedStats"):
            self._stat_week = None
        elif self.stat_type in ("weekStats", "weekProjectedStats"):
            if value is None:
                raise ValueError(value)
            self._stat_week = value

    def get(self, **kwargs) -> pd.DataFrame:
        """
        :return:
        """
        params = {
            "leagueId": self.league_id,
            "position": self.position,
            "statCategory": self.stat_category,
            "statSeason": self.stat_season,
            "statType": self.stat_type,
            "statWeek": self.stat_week
        }
        dataframes = []

        offset = 1
        while True:

            with requests.get(
                self.url, params={"offset": offset, **params}, timeout=1000, **kwargs
            ) as response:
                soup = bs4.BeautifulSoup(response.text, features="lxml")

            with io.StringIO(str(soup.select_one("#primaryContent table"))) as buffer:
                try:
                    dataframes.append(pd.read_html(buffer)[0])
                except ValueError:
                    break

            offset += 25

        dataframe = pd.concat(dataframes).reset_index(drop=True).replace("-", 0)

        return self._refine(dataframe)

    def _refine(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        :param dataframe:
        :return:
        """
        team = self._team(dataframe.iloc[:, 0])
        opponent = self._opponent(dataframe.iloc[:, 1])

        if dataframe.columns[2][1] == "GP":
            series = pd.Series(
                dataframe.iloc[:, 2], index=dataframe.index, name=("GP", "GP")
            )
            return pd.concat(
                [team, opponent, series, dataframe.drop(columns=dataframe.columns[:3])], axis=1
            )
        else:
            return pd.concat(
                [team, opponent, dataframe.drop(columns=dataframe.columns[:2])], axis=1
            )

    def _team(self, series: pd.Series) -> pd.DataFrame:
        """
        :param series:
        :return:
        """
        dataframe = pd.DataFrame(
            index=series.index, columns=pd.MultiIndex.from_tuples(
                [("Player", "Name"), ("Player", "Position"), ("Player", "Team")]
            )
        )

        regex = re.compile(r"^(.*)\s(QB|RB|WR|TE|K|DEF)\b")
        dataframe.loc[:, ("Player", "Name")] = series.apply(lambda x: regex.search(x).group(1))
        dataframe.loc[:, ("Player", "Position")] = series.apply(lambda x: regex.search(x).group(2))

        regex = re.compile(r"(QB|RB|WR|TE|K|DEF)\s-\s([A-Z]{2,3})")
        index = ~series.apply(regex.search).isna()
        dataframe.loc[index, ("Player", "Team")] = series.loc[index].apply(
            lambda x: regex.search(x).group(2)
        )

        return dataframe

    def _opponent(self, series: pd.Series) -> pd.DataFrame:
        """
        :param series:
        :return:
        """
        dataframe = pd.DataFrame(
            index=series.index, columns=pd.MultiIndex.from_tuples(
                [("Opponent", "Home/Away"), ("Opponent", "Team")]
            )
        )

        dataframe.loc[:, ("Opponent", "Home/Away")] = "H"
        dataframe.loc[series.str.contains("@"), ("Opponent", "Home/Away")] = "A"
        dataframe.loc[series == "Bye", ("Opponent", "Home/Away")] = np.nan

        regex = re.compile(r"[A-Z]{2,3}")
        index = ~series.apply(regex.search).isna()
        dataframe.loc[index, ("Opponent", "Team")] = series.loc[index].apply(
            lambda x: regex.search(x).group()
        )

        return dataframe


class Rankings:
    """
    """


class FantasyPointsAgainst:
    """
    """


class Projections(Research):
    """
    """
    url = "https://fantasy.nfl.com/research/projections"

    _stat_category = "projectedStats"

    def __init__(self, **kwargs):
        super().__init__(stat_type="seasonProjectedStats", **kwargs)

    @property
    def stat_type(self) -> typing.Literal["seasonProjectedStats", "weekProjectedStats"]:
        """
        """
        return self._stat_type

    @stat_type.setter
    def stat_type(self, value: str) -> None:
        if value not in ("seasonProjectedStats", "weekProjectedStats"):
            raise ValueError(value)
        self._stat_type = value

        if value == "seasonProjectedStats":
            self.week = None


class ScoringLeaders:
    """
    """


class PlayerTrends:
    """
    """


class Players(Research):
    """
    """
    url = "https://fantasy.nfl.com/research/players"

    _stat_category = "stats"

    def __init__(self, **kwargs):
        super().__init__(stat_type="seasonStats", **kwargs)

    @property
    def stat_type(self) -> typing.Literal["seasonStats", "weekStats"]:
        """
        """
        return self._stat_type

    @stat_type.setter
    def stat_type(self, value: str) -> None:
        if value not in ("seasonStats", "weekStats"):
            raise ValueError(value)
        self._stat_type = value

        if value == "seasonStats":
            self.week = None
