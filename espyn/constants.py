ENDPOINT = ("https://fantasy.espn.com/apis/v3/games/ffl/seasons/{}/segments/0/leagues/{}"
            "?view=mMatchupScore&view=mScoreboard&view=mSettings&view=mStatus&view=mTeam"
            "&view=modular&view=mNav&view=mBoxscore")

SLOTS = {
    0: "QB",
    2: "RB",
    3: "RB/WR",
    4: "WR",
    6: "TE",
    7: "OP",  # offensive utility player
    10: "LB",
    11: "DL",
    14: "DB",
    15: "DP", # defensive utility player
    16: "D/ST",
    17: "K",
    18: "P",
    19: "COACH",
    20: "BENCH",
    21: "INJURED",
    23: "FLEX",
    24: "EDR"  # edge rusher
}

POSITIONS = {
    1: "QB",
    2: "RB",
    3: "WR",
    4: "TE",
    5: "K",
    7: "P",
    9: "DT",
    10: "DE",
    11: "LB",
    12: "CB",
    13: "S",  # safety
    14: "COACH",
    16: "D/ST"
}

PRO_TEAMS = {
    0: "Free Agent",
    1: "ATL",
    2: "BUF",
    3: "CHI",
    4: "CIN",
    5: "CLE",
    6: "DAL",
    7: "DEN",
    8: "DET",
    9: "GB",
    10: "TEN",
    11: "IND",
    12: "KC",
    13: "LV",
    14: "LAR",
    15: "MIA",
    16: "MIN",
    17: "NE",
    18: "NO",
    19: "NYG",
    20: "NYJ",
    21: "PHI",
    22: "ARI",
    23: "PIT",
    24: "LAC",
    25: "SF",
    26: "SEA",
    27: "TB",
    28: "WSH",
    29: "CAR",
    30: "JAX",
    33: "BAL",
    34: "HOU"
}

# missing codes for punt, ko, and block TD returns,
# and probably more
STAT_CODES = {
    0: "pass_att",
    1: "pass_cmp",
    3: "pass_yds",
    4: "pass_td",
    5: "every_5_pass_yds",
    19: "2pt_pass_or_rec",
    20: "int",
    23: "rush_att",
    24: "rush_yds",
    25: "rush_td",
    26: "2pt_rush",
    39: "rush_yds_per_att",
    41: "rec",
    42: "rec_yds",
    43: "rec_td",
    58: "tgt",
    60: "rec_yds_per_rec",
    72: "fum_lost",
    89: "0_pts_allowed",
    90: "1-6_pts_allowed",
    91: "7-13_pts_allowed",
    92: "14-17_pts_allowed",
    95: "def_int",
    96: "fum_recov",
    97: "block",
    98: "safety",
    99: "sack",
    101: "td_ko_return",
    102: "td_punt_return",
    103: "td_int_return",
    104: "td_fum_return",
    123: "28-34_pts_allowed",
    124: "35-45_pts_allowed",
    125: "46+_pts_allowed",
    128: "0-99_yds_allowed",
    129: "100-199_yds_allowed",
    130: "200-299_yds_allowed",
    132: "350-399_yds_allowed",
    133: "400-449_yds_allowed",
    134: "450-499_yds_allowed",
    135: "500-549_yds_allowed",
    136: "550+_yds_allowed"
}

SEASON_OVER = 999
