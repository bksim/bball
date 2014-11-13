import mechanize
import json
import csv

br = mechanize.Browser()
result = br.open('https://rotogrinders.com/game-stats/nba/consistency.json?site=draftkings&range=season')
result = json.load(result)
players = result['data']
fields = ['player', 'team', 'pos', 'salary', 'opp', 'gp', 'fppg', 'fpmax',
          'fpmin', 'floor', 'ceil', '%3x', '%4x', '%5x', '%6x']
with open('season_rotogrinders_consistency.csv', 'w') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(fields)
    for player in players:
        row = []
        for field in fields:
            row.append(player[field])
        writer.writerow(row)


result = br.open('https://rotogrinders.com/game-stats/nba/consistency.json?site=draftkings&range=3weeks')
result = json.load(result)
with open('3weeks_rotogrinders_consistency.csv', 'w') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(fields)
    for player in players:
        row = []
        for field in fields:
            row.append(player[field])
        writer.writerow(row)
