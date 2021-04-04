
# ESPyN

[![ci status](https://github.com/reddigari/ESPyN/actions/workflows/ci.yml/badge.svg)](https://github.com/reddigari/ESPyN/actions)
![coverage](https://reddigari-github-badges.s3.amazonaws.com/espyn-coverage-develop.svg)

This library uses the (private and wholly undocumented) ESPN Fantasy Football
API to retrieve data about __public__ leagues. It includes object models of
leagues, teams, players, and stat lines (at the player-week and team-week
levels).


## Getting Started

Use the `League` object to retrieve and interact with a fantasy league.
It needs the league ID, which is visible in the URL when viewing
the league on the ESPN website.

```Python
from espyn import League

league = League(1603206, season=2020)
print(league)
print("Average weekly score", league.average_score())
```

```
ESPN League 1603206 - The Ocho, Dos - 10 teams
Average weekly score: 94.19874999999999
```

Inspect teams through the `.teams` attribute, or the `.get_team_by_id()` method.

```Python
team = league.get_team_by_id(7)
print(team)
print("Points for:", team.points_for)
print("Points against:", team.points_against)
```

```
Team 7 : Samir Reddigari : Le'Veon On A Prayer : 3-9-0
Points for: 850.6
Points against: 1165.3000000000002
```

(My team had a rough 2020.)

The API request made when the `League` instance is created contains scores from
every matchup for the season.

```Python
matchup = league.get_matchup(number=1, team_id=7)
print(matchup)
print("Boxscore loaded:", matchup.boxscore_loaded)
```

```
Matchup #1 : Team Lupinacci (89.8)✅ @ Le'Veon On A Prayer (74.3)
Boxscore loaded: False
```

Boxscores for individual weeks can be loaded by setting the `boxscore`
parameter. This will require another API request, and will include information
about each team's roster and player stats.

```Python
matchup = league.get_matchup(number=1, team_id=7, boxscore=True)
print("Boxscore loaded:", matchup.boxscore_loaded)
print(matchup.home_data)
for slot in matchup.home_data[0].slots:
    if slot.slot not in ("BENCH", "INJURED"):
        print(slot)
```

```
Boxscore loaded: True
[Scoring Period 1 : 74.3 points]
WR : Michael Thomas, WR, NO : 1.7 points
RB : Ezekiel Elliott, RB, DAL : 24.7 points
RB : Le'Veon Bell, RB, KC : 4.6 points
WR : Cooper Kupp, WR, LAR : 4.0 points
QB : Drew Brees, QB, NO : 14.4 points
FLEX : Raheem Mostert, RB, SF : 21.1 points
K : Justin Tucker, K, BAL : 9.0 points
TE : Hayden Hurst, TE, ATL : 3.8 points
D/ST : Vikings D/ST, D/ST, MIN : -9.0 points
```

Note that `Matchup.home_data` is a list; many ESPN leagues use multi-week
matchups during the playoffs. In this case, the list will contain
multiple `TeamWeek` instances. ESPN refers to each NFL week as a "scoring period."
A matchup contains one or more scoring periods. Use the `League.matchup_num_to_week()`
method to inspect the mapping.


## Caching

Retrieving each scoring period's boxscore requires a separate API request. (It's
possible this is untrue, and I have not tinkered with the API endpoint sufficiently.)
Caching the responses is recommended:

```Python
from espyn import League
from espyn.caches import LocalCache

cache = LocalCache("/path/to/cache/directory")
league = League(<LEAGUE_ID>, <SEASON>, cache)
```

The respones from all API calls will be cached as JSON files in the specifcied
directory, and neither the constructor nor methods with `boxscore=True` will
make network requests if the necessary file is in the cache.
