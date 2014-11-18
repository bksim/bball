import os
from urllib2 import Request, urlopen, URLError
import json
import mechanize
import csv

# Downloads boxscores from stats.nba.com. Boxscores come in JSON format.
# GameID format is 0021##### - where the first digit after 0021 decides the year, 
# and then the numbers just count up from 00001
# For example: http://stats.nba.com/stats/boxscore?GameID=0021300001&RangeType=0&StartPeriod=0&EndPeriod=0&StartRange=0&EndRange=0

# downloads game jsons from a given year to a given location
# gets the games from start_game to end_game, inclusive
# type: normal for traditional box scores
#       advanced for advanced box scores
def download_gamelog_jsons(year, location, boxtype='normal', start_game=1, end_game=1230):
    y = year % 10
    for g in xrange(start_game, end_game+1):
        print g
        if boxtype == 'normal':
            url = 'http://stats.nba.com/stats/boxscore?GameID=0021' + str(y) + "%05d" % (g) + '&RangeType=0&StartPeriod=0&EndPeriod=0&StartRange=0&EndRange=0'
        elif boxtype == 'advanced':
            url = 'http://stats.nba.com/stats/boxscoreadvanced?GameID=0021' + str(y) + "%05d" % (g) + '&RangeType=0&StartPeriod=0&EndPeriod=0&StartRange=0&EndRange=0'

        req = Request(url)
        try:
            response = urlopen(req)
        except URLError as e:
            if hasattr(e, 'reason'):
                print 'We failed to reach a server.'
                print 'Reason: ', e.reason
            elif hasattr(e, 'code'):
                print 'The server couldn\'t fulfill the request.'
                print 'Error code: ', e.code
        else:
            # everything is fine
            data = response.read()
            json_data = json.loads(data)
            if json_data['resultSets'][1]['rowSet'][0][-1] is None:
                print "Downloaded until game " + str(g-1)
                break
            name = json_data['resultSets'][0]['rowSet'][0][5]
            mod_name = name.split('/')[0] + '-' + name.split('/')[1]
            print mod_name
            with open(location + '/' + mod_name + '.json', 'w') as outfile:
                json.dump(json.loads(data), outfile, sort_keys=True, indent=4, ensure_ascii=False)

# downloads 3x, 4x, 5x, 6x consistency data from Rotogrinders
def download_consistency_data(out_dir='rotogrinders_data'):       
    br = mechanize.Browser()
    result = br.open('https://rotogrinders.com/game-stats/nba/consistency.json?site=draftkings&range=season')
    result = json.load(result)
    players = result['data']
    fields = ['player', 'team', 'pos', 'salary', 'opp', 'gp', 'fppg', 'fpmax',
              'fpmin', 'floor', 'ceil', '%3x', '%4x', '%5x', '%6x']
    with open(out_dir + '/season_rotogrinders_consistency.csv', 'wb') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(fields)
        for player in players:
            row = []
            for field in fields:
                row.append(player[field])
            writer.writerow(row)

    result = br.open('https://rotogrinders.com/game-stats/nba/consistency.json?site=draftkings&range=3weeks')
    result = json.load(result)
    with open(out_dir + '/3weeks_rotogrinders_consistency.csv', 'wb') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(fields)
        for player in players:
            row = []
            for field in fields:
                row.append(player[field])
            writer.writerow(row)
