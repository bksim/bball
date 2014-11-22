import os
from urllib2 import Request, urlopen, URLError
import json
import mechanize
import csv
import re
import requests
from bs4 import BeautifulSoup

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

# gets all game info in JSON format from a downloaded Lobby page.
def get_all_ids(html_page, html_type='lobby'):
    if html_type == 'lobby':
        soup = BeautifulSoup(open(html_page))

        matches = []
        for scr in soup.select('script'):
            if scr.string != None:
                s = scr.string
                if 'packagedContests' in s:
                    jsontext = s.split('var packagedContests = [')[1] .split('];')[0]
                    indiv = jsontext.split('},{')
                    indiv[0] = indiv[0][1:]
                    indiv[-1] = indiv[-1][0:-1]

                    for m in indiv:
                        matches.append(json.loads('{'+m+'}'))
        return matches
    else:
        return None


# write to excel sheet for donkjeff
# usage: write_jsons_to_excel('excel_gamedata_2014.xls', 'boxscores/2014')
import xlwt
def write_jsons_to_excel(excel_filename, json_directory):
    w = xlwt.Workbook()
    counter = 0
    for fn in os.listdir(json_directory):
        cursheet = w.add_sheet(fn.split(".")[0])
        with open(os.path.join(json_directory, fn)) as f:
            t = json.load(f)
            cursheet.write(0,0,'Date')
            cursheet.write(0,1,'Home Team')
            cursheet.write(0,2,'Home Score')
            cursheet.write(0,3,'Visiting Team')
            cursheet.write(0,4,'Visiting Score')
            home_id = t['resultSets'][0]['rowSet'][0][6]
            away_id = t['resultSets'][0]['rowSet'][0][7]
            
            idmap = {}
            idmap[t['resultSets'][1]['rowSet'][0][3]] = (t['resultSets'][1]['rowSet'][0][4],t['resultSets'][1]['rowSet'][0][21])
            idmap[t['resultSets'][1]['rowSet'][1][3]] = (t['resultSets'][1]['rowSet'][1][4],t['resultSets'][1]['rowSet'][1][21])
            
            # print metadata info
            cursheet.write(1,0,t['resultSets'][0]['rowSet'][0][0]) #date
            cursheet.write(1,1,idmap[home_id][0]) #home team
            cursheet.write(1,2,idmap[home_id][1])
            cursheet.write(1,3,idmap[away_id][0]) #visiting team
            cursheet.write(1,4,idmap[away_id][1])
    
            # print player stats
            for i in range(len(t['resultSets'][4]['headers'])):
                cursheet.write(2,i,t['resultSets'][4]['headers'][i])
            for j in range(len(t['resultSets'][4]['rowSet'])):
                for k in range(len(t['resultSets'][4]['rowSet'][j])):
                    cursheet.write(3+j, k, t['resultSets'][4]['rowSet'][j][k])
        
    w.save(excel_filename)


# scrape offensive and def ratings from basketball-reference
# usage: year = 2014 #2013-2014
#def_ratings, off_ratings = get_def_ratings(teams, year) # may take a bit to hit all the teams
#print def_ratings
#print off_ratings
def get_def_ratings(year):
    teams = ['ATL','BOS','BRK','CHA','CHI','CLE','DAL','DEN','DET','GSW','HOU','IND','LAC','LAL','MEM',
         'MIA','MIL','MIN','NOP','OKC','ORL','PHI','PHO','POR','SAC','SAS','TOR','UTA','WAS']
    def_ratings = {}
    off_ratings = {}
    for team in teams:
        team_url = 'http://www.basketball-reference.com/teams/' + team + '/'+ str(year) + '.html'
        req = Request(team_url)
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
            html_page = response.read()
            search = "Def Rtg</span></a>: "
            loc = html_page.find(search)
            def_ratings[team] = float(html_page[loc+len(search): loc+len(search)+5].rstrip(" "))
            
            search = "Off Rtg</span></a>: "
            loc = html_page.find(search)
            off_ratings[team] = float(html_page[loc+len(search): loc+len(search)+5].rstrip(" "))
    return def_ratings, off_ratings

if __name__ == "__main__":
    d = 'draftkings scrapes/'
    fn = '20141119_draftkings_nba_lobby.htm'
    html_page = d + fn
    matches = get_all_ids(html_page)

    with open(d + fn.split('.')[0] + '_results.txt', 'wb') as f:
        for m in matches:
            f.write(m['n'] + " /// " + str(m['id']) + '\n')
    
    #for m in matches:
    #   print m['n'] + " /// " + str(m['id'])

    #download_csv(None, None)

