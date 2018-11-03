from espyn.league import League
import pprint

pp = pprint.PrettyPrinter()
l = League(1603206)
matchups = l.get_all_matchups(8)
for m in matchups:
    pp.pprint(m)
    pp.pprint(m.home_data)
    pp.pprint(m.home_data.slots)
