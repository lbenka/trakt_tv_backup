import attr
import maya
from relaxml import converter
from trakt import Trakt
import json
from authenticate import authenticate


Trakt.configuration.defaults.client(
    id="647c69e4ed1ad13393bf6edd9d8f9fb6fe9faf405b44320a6b71ab960b4540a2",
    secret="f55b0a53c63af683588b47f6de94226b7572a6f83f40bd44c58a7c83fe1f2cb1",
)

Trakt.configuration.defaults.oauth.from_response(authenticate())


@attr.s
class Movie:
    id: str = attr.ib(converter=str)
    watched_date: maya.MayaDT = attr.ib(converter=maya.MayaDT)

    @classmethod
    def from_db(cls, row: dict):
        return cls(id=row.get("movie_id"), watched_date=int(str(row.get("date", {}).get("$$date", ""))[:-3]))

    def to_post(self):
        return {"movies": [{"watched_at": self.watched_date.iso8601(), "ids": {"imdb": self.id}}]}


@attr.s
class Episode:
    id: str = attr.ib(converter=str)
    episode: int = attr.ib(converter=int)
    watched_date: maya.MayaDT = attr.ib(converter=maya.MayaDT)
    tvdb_id: int = attr.ib(converter=int)
    season: int = attr.ib(converter=int)

    @classmethod
    def from_db(cls, row: dict):
        return cls(
            id=row.get("imdb_id"),
            watched_date=int(str(row.get("date", {}).get("$$date", ""))[:-3]),
            tvdb_id=row.get("tvdb_id"),
            season=row.get("season"),
            episode=row.get("episode"),
        )

    def to_post(self):
        return {
            "shows": [
                {
                    "ids": {"tvdb": self.tvdb_id, "imdb": self.id},
                    "seasons": [
                        {
                            "number": self.season,
                            "episodes": [{"watched_at": self.watched_date.iso8601(), "number": self.episode}],
                        }
                    ],
                }
            ]
        }


if __name__ == "__main__":
    uniques = set()
    raw_history = open("watched.txt", "r")

    for row in raw_history.readlines():
        row = json.loads(row)

        if row.get("movie_id"):
            parsed_row = Movie.from_db(row)
        else:
            parsed_row = Episode.from_db(row)
        
        if parsed_row.id in uniques:
            continue 
        
        response = Trakt["sync/history"].add(parsed_row.to_post())
        uniques.add(parsed_row.id)
        print(response)

    raw_history.close()
    print("finished")
