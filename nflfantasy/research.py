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


class Rankings:
    """
    """


class FantasyPointsAgainst:
    """
    """


class Projections:
    """
    """


class ScoringLeaders:
    """
    """


class PlayerTrends:
    """
    """


class Players:
    """
    """
    url = "https://fantasy.nfl.com/research/players"

    _league_id: typing.Literal[0] = 0
    _position: typing.Union[typing.Literal["O"], int] = "O"
    _stat_category: typing.Literal["stats"] = "stats"
    _stat_season: int = datetime.datetime.today().year
    _stat_type: typing.Literal["seasonStats", "weekStats"] = "seasonStats"
    _stat_week: typing.Optional[int] = None

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def league_id(self) -> typing.Literal[0]:
        """
        """
        return self._league_id

    @league_id.setter
    def league_id(self, value: int) -> None:
        if value != 0:
            raise ValueError(value)
        self._league_id = value

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
    def stat_category(self) -> typing.Literal["stats"]:
        """
        """
        return self._stat_category

    @stat_category.setter
    def stat_category(self, value: str) -> None:
        if value != "stats":
            raise ValueError(value)
        self._stat_category = value

    @property
    def stat_season(self) -> int:
        """
        """
        return self._stat_season

    @stat_season.setter
    def stat_season(self, value: int) -> None:
        self._stat_season = value

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

    @property
    def stat_week(self) -> int:
        """
        """
        return self._stat_week

    @stat_week.setter
    def stat_week(self, value: typing.Optional[int]) -> None:
        if self.stat_type == "seasonStats":
            self._stat_week = None
        elif self.stat_type == "weekStats":
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

        team = self._team(dataframe.iloc[:, 0])
        opponent = self._opponent(dataframe.iloc[:, 1])
        dataframe.drop(columns=dataframe.columns[:2], inplace=True)

        return pd.concat([team, opponent, dataframe], axis=1)

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
