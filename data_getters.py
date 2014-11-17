import os
from urllib2 import Request, urlopen, URLError
import json

#To get boxscores, we can use stats.nba.com. Boxscores come in JSON format.
#Just change the GameID 
#GameID format is 0021###### - where the first digit after 0021 decides the year, and then the numbers just count up from 000001
#http://stats.nba.com/stats/boxscore?GameID=0021300001&RangeType=0&StartPeriod=0&EndPeriod=0&StartRange=0&EndRange=0

# downloads game jsons from a given year to a given location
# gets the games from start_game to end_game, inclusive
def download_gamelog_jsons(year, location, start_game=1, end_game=1230):
    y = year % 10
    for g in xrange(start_game, end_game+1):
        print g
        url = 'http://stats.nba.com/stats/boxscore?GameID=0021' + str(y) + "%05d" % (g) + '&RangeType=0&StartPeriod=0&EndPeriod=0&StartRange=0&EndRange=0'
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