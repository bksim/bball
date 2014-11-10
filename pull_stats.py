import mechanize
import pdb
from bs4 import BeautifulSoup
import json
import os

positions = {}
positions[15] = 'C'
positions[16] = 'PG'
positions[17] = 'PF'
positions[25] = 'SG'
positions[26] = 'SF'

br = mechanize.Browser()

for key in positions.keys():
    result = br.open('https://rotogrinders.com/team-stats/nba-allowed.json?sport=nba&position=' + str(key) + '&site=draftkings&range=season')
    data = json.loads(result.get_data())
    with open(os.path.join("position_vs_defense", positions[key] + '_pts_allowed.json'), 'w') as outfile:
        json.dump(data, outfile)


for key in positions.keys():
    result = br.open('https://rotogrinders.com/team-stats/nba-earned.json?sport=nba&position=' + str(key) + '&site=draftkings&range=season')
    data = json.loads(result.get_data())
    with open(os.path.join('position_vs_defense', positions[key] + '_pts_earned.json'), 'w') as outfile:
        json.dump(data, outfile)


