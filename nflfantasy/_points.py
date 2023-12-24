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

    def __init__(self, path: pathlib.Path):
        self._path = path

        with open(self.path, "r", encoding="utf-8") as file:
            self._scheme = json.load(file)

    def __repr__(self) -> str:
        return f"{type(self).__name__}(path={self.path})"

    def __getitem__(self, item: typing.Tuple[str, str]) -> float:
        return self.scheme[item[0]][item[1]]

    @property
    def path(self) -> pathlib.Path:
        """
        """
        return self._path

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

    def __init__(self, path: pathlib.Path = default):
        super().__init__(path)


class Kickers(PointScheme):
    """
    """
    default = pathlib.Path("data", "points", "kickers.json")

    def __init__(self, path: pathlib.Path = default):
        super().__init__(path)


class DefenseST(PointScheme):
    """
    """
    default = pathlib.Path("data", "points", "defensest.json")

    def __init__(self, path: pathlib.Path = default):
        super().__init__(path)


class Scheme:
    """
    """
    def __init__(
        self, offense: pathlib.Path = Offense.default, kickers: pathlib.Path = Kickers.default,
        defensest: pathlib.Path = DefenseST.default
    ):
        self._offense = Offense(offense)
        self._kickers = Kickers(kickers)
        self._defensest = DefenseST(defensest)

    def __repr__(self) -> str:
        keys = ["offense", "kickers", "defensest"]
        arguments = ", ".join(f"{k}={self.__getattribute__(k)}" for k in keys)
        return f"{type(self).__name__}({arguments})"

    @property
    def offense(self) -> Offense:
        """
        """
        return self._offense
    
    @offense.setter
    def offense(self, value: Offense) -> None:
        if not isinstance(value, Offense):
            raise TypeError(value)
        
        if not self._offense.keys == value.keys:
            raise ValueError(value)
        
        self._offense = value

    @property
    def kickers(self) -> Kickers:
        """
        """
        return self._kickers
    
    @kickers.setter
    def kickers(self, value: Kickers) -> None:
        if not isinstance(value, Kickers):
            raise TypeError(value)
        
        if not self._kickers.keys == value.keys:
            raise ValueError(value)
        
        self._kickers = value

    @property
    def defensest(self) -> DefenseST:
        """
        """
        return self._defensest
    
    @defensest.setter
    def defensest(self, value: DefenseST) -> None:
        if not isinstance(value, DefenseST):
            raise TypeError(value)
        
        if not self._defensest.keys == value.keys:
            raise ValueError(value)
        
        self._defensest = value

    def new_record(
        self, category: typing.Literal["offense", "kickers", "defensest"]
    ) -> "Record":
        """
        :param category:
        :return:
        :raise ValueError:
        """
        if category == "offense":
            scheme = self.offense
        elif category == "kickers":
            scheme = self.kickers
        elif category == "defensest":
            scheme = self.defensest
        else:
            raise ValueError(category)
        
        return Record(scheme)


class Record:
    """
    """
    def __init__(self, scheme: PointScheme):
        self._scheme = scheme
        self._values = pd.Series({k: 0 for k in self.scheme.index})

    def __repr__(self) -> str:
        return f"{type(self).__name__}(record={self.record})"

    @property
    def scheme(self) -> pd.Series:
        """
        """
        return pd.Series({k: self._scheme[k] for k in self._scheme.keys})
    
    @property
    def values(self) -> pd.Series:
        """
        """
        return self._values
    
    @values.setter
    def values(self, value: pd.Series) -> None:
        if not self.scheme.index.equals(value.index):
            raise ValueError(value)
        self._values = value
    
    @property
    def points(self) -> pd.Series:
        """
        """
        return self.scheme * self.values
    
    @property
    def record(self) -> pd.DataFrame:
        """
        """
        return pd.DataFrame(
            {"scheme": self.scheme, "values": self.values, "points": self.points}
        )
    
    @property
    def total(self) -> float:
        """
        """
        return self.record["points"].sum()


class Scorecard:
    """
    """
    def __init__(self, records: typing.List[Record]):
        self._records = list(records)

    @property
    def records(self) -> typing.List[Record]:
        """
        """
        return self._records
    
    @records.setter
    def records(self, value: typing.List[Record]) -> None:
        if not all(isinstance(x, Record) for x in value):
            raise ValueError(value)
        self._records = value

    @property
    def offense(self) -> pd.DataFrame:
        """
        """
        return self.scorecard("offense")
    
    @property
    def kickers(self) -> pd.DataFrame:
        """
        """
        return self.scorecard("kickers")
    
    @property
    def defensest(self) -> pd.DataFrame:
        """
        """
        return self.scorecard("defensest")
    
    @property
    def points(self) -> pd.Series:
        """
        """
        return pd.concat(
            [self.offense["points"], self.kickers["points"], self.defensest["points"]]
        ).reset_index(drop=True)
    
    @property
    def total(self) -> float:
        """
        """
        return self.points.sum()
    
    def scorecard(self, category: str) -> pd.DataFrame:
        """
        :param category:
        :return:
        """
        if category == "offense":
            scheme = Offense
        elif category == "kickers":
            scheme = Kickers
        elif category == "defensest":
            scheme = DefenseST
        else:
            raise ValueError(category)
        
        records = list(filter(lambda x: isinstance(x._scheme, scheme), self.records))
        frame = pd.DataFrame(x.record["values"] for x in records).reset_index(drop=True)
        frame.loc[:, "points"] = pd.Series([x.total for x in self.records])

        return frame
