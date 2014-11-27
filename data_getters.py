import os
from urllib2 import Request, urlopen, URLError
import json
import mechanize
import csv
import re
import pdb
#import requests
from selenium import webdriver
from pprint import pprint
import time
import os
import numpy as np
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

# scrape offensive and def ratings from basketball-reference
# usage: year = 2014 #2013-2014
#def_ratings, off_ratings = get_def_ratings(teams, year) # may take a bit to hit all the teams
#print def_ratings
#print off_ratings
def get_def_ratings(year):
    teams = ['ATL','BOS','BRK','CHO','CHI','CLE','DAL','DEN','DET','GSW','HOU','IND','LAC','LAL','MEM',
         'MIA','MIL','MIN','NOP','NYK','OKC','ORL','PHI','PHO','POR','SAC','SAS','TOR','UTA','WAS']
    def_ratings = {}
    off_ratings = {}
    for team in teams:
        print team
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

# downloads all match standing CSVs given the list ids into the dump directory
#https://www.draftkings.com/contest/exportfullstandingscsv/2459960

# this doesn't work yet, LOGIN WALL dammit

# logs into DraftKings automatically given a contest id (need id because the failed login
# page that you get is easier to run selenium on than the standard login page)
def login(browser, id):
    browser.get('https://www.draftkings.com/contest/exportfullstandingscsv/' + str(id))
    login_link = browser.find_element_by_id("login-link")
    webdriver.ActionChains(browser).move_to_element(login_link).click(login_link).perform()
    # stupid site has a hidden elem and a unhidden elem, we need the unhidden
    username_elements = browser.find_elements_by_id("Username")
    username_elements[1].send_keys("theyellowman86")
    password_elements = browser.find_elements_by_id("Password")
    password_elements[1].send_keys("george4mvp")

    login_button = browser.find_element_by_id("buttonText")
    webdriver.ActionChains(browser).move_to_element(login_button).click(login_button).perform()
    time.sleep(3) #sleep to let the server process that we've logged in

def download_csv(ids):
    browser = webdriver.Firefox()
    login(browser,ids[0])
    time.sleep(40) #use this time to select the folder you want to download to
    browser.get('https://www.draftkings.com/contest/exportfullstandingscsv/' + str(ids[0]))
    '''
    sleep for 10 secs here to let you set firefox settings to auto download.
    if you don't, you will get infinite pop up windows asking you what you want 
    to do. technically, you can make a firefox profile to combat this, but its 
    too annoying, and this is low-hassle solution
    '''
    time.sleep(10) #gives you a chance to set firefox settings to auto download / set location of downloads

    # download rest of results automatically!
    for i in range(1,len(ids)):
        browser.get('https://www.draftkings.com/contest/exportfullstandingscsv/' + str(ids[i]))
        time.sleep(1)
        print i

def get_our_contest_ids():
    file_names = ['11212014contests.html', '11212014contests2.html']
    ids = set()
    contests = {}
    pattern = re.compile('^\$(\d*)')
    for file_name in file_names:
        soup = BeautifulSoup(open(file_name))
        divs = soup.find_all('div')
        desired_divs = []
        for div in divs:
            if div.text == "11/22/2014":
                desired_divs.append(div.previous_sibling.previous_sibling.previous_sibling.previous_sibling.previous_sibling)

        for div in desired_divs:
            results = div.find_all('a')
            for result in results:
                attributes = result.attrs
                if "data-cid" in attributes.keys():
                    ids.add(attributes['data-cid'])
                    contest_description = str(result.text).split(' ')
                    for word in contest_description:
                        if pattern.match(word) != None:
                            contests[attributes['data-cid']] = word
                            break 
    print ids

    return [id for id in ids], contests

# gets the cutoff value for a 50/50 contest given the contest_result csv file from DraftKings
def get_cutoff(contest_file):
    with open(contest_file, 'r') as csvfile:
        reader = csv.reader(csvfile)
        all_rows = list(reader)
        cutoff_index = (len(all_rows) - 1) / 2 
        print contest_file, all_rows[cutoff_index][4]
        return all_rows[cutoff_index][4]
     
# calculates the average and median cutoff for different 50/50 stakes
def cutoffs_stats(ids, contests):
    cutoffs = {}
    average_cutoffs = {}
    median_cutoffs = {}
    for id in ids:
        try:
            cutoff = get_cutoff(os.path.join('11192014_draftkings_contests_results', 'contest-standings-' + str(id) + '.csv'))
        except Exception:
            print 'contest cancelled'
        game_type = contests[id]
        if game_type not in cutoffs.keys():
            cutoffs[game_type] = []
        cutoffs[game_type].append(float(cutoff))
    for k in cutoffs.keys():
        average_cutoffs[k] = np.average(np.array(cutoffs[k]))
        median_cutoffs[k] = np.median(np.array(cutoffs[k]))
    return average_cutoffs, median_cutoffs
    

def get_vegas_lines(excel_fn, site='covers'):
    url = 'http://www.covers.com/odds/basketball/nba-spreads.aspx'

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
        html_page = response.read()
        soup = BeautifulSoup(html_page)
        lines = soup.find_all('tr', 'bg_row')
        line_info = {}
        for line in lines:
            teams = line.find_all('strong')
            teamstring = teams[0].contents[0]+teams[1].contents[0]
            temp = line.find_all('td', 'covers_top')[0]
            ou = temp.find_all('div','line_top')[0].contents[0].lstrip().rstrip()
            spread = temp.find_all('div','covers_bottom')[0].contents[0].lstrip().rstrip()
            line_info[teamstring] = [float(ou), float(spread)]
        with open(excel_fn, 'wb') as csvfile:
            writer = csv.writer(csvfile)
            for k, v in line_info.iteritems():
                writer.writerow([k, v[0], v[1]])
    return line_info



if __name__ == "__main__":
    d = 'draftkings scrapes/'
    fn = '20141119_draftkings_nba_lobby.htm'
    html_page = d + fn
    matches = get_all_ids(html_page)
    print matches

    '''
    with open(d + fn.split('.')[0] + '_results.txt', 'wb') as f:
        for m in matches:
            f.write(m['n'] + " /// " + str(m['id']) + '\n')
    '''
    ids = []
    contests = {}  
    for m in matches:
        if 'NBA' in str(m['n']) and '50/50' in str(m['n']):
            ids.append(m['id'])
            contests[m['id']] = m['a']

    pprint(cutoffs_stats(ids, contests))
    pdb.set_trace()
    #for m in matches:
    #   print m['n'] + " /// " + str(m['id'])
    download_csv(ids)
