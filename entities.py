import pandas as pd
import numpy as np

# player class
class Player:
    def __init__(self):
        self.info = {}
        self.adv_info = {}
        self.headers = [u'GAME_ID', u'TEAM_ID', 
                   u'TEAM_ABBREVIATION', u'TEAM_CITY', 
                   u'PLAYER_ID', u'PLAYER_NAME', 
                   u'START_POSITION', u'COMMENT', 
                   u'MIN', u'FGM', u'FGA', 
                   u'FG_PCT', u'FG3M', u'FG3A', 
                   u'FG3_PCT', u'FTM', u'FTA', u'FT_PCT', 
                   u'OREB', u'DREB', u'REB', u'AST', 
                   u'STL', u'BLK', u'TO', u'PF', u'PTS', 
                   u'PLUS_MINUS']
                   
        self.adv_headers = [
                "GAME_ID", 
                "TEAM_ID", 
                "TEAM_ABBREVIATION", 
                "TEAM_CITY", 
                "PLAYER_ID", 
                "PLAYER_NAME", 
                "START_POSITION", 
                "COMMENT", 
                "MIN", 
                "OFF_RATING", 
                "DEF_RATING", 
                "NET_RATING", 
                "AST_PCT", 
                "AST_TOV", 
                "AST_RATIO", 
                "OREB_PCT", 
                "DREB_PCT", 
                "REB_PCT", 
                "TM_TOV_PCT", 
                "EFG_PCT", 
                "TS_PCT", 
                "USG_PCT", 
                "PACE", 
                "PIE"
            ]
        for h in self.headers:
            self.info[h] = []
        for h in self.adv_headers:
            self.adv_info[h] = []

        self.cost = None
    
    # adds game info from boxscore data
    def add_game_from_boxscore(self, data, boxtype):
        if boxtype == 'normal':
            this_headers = self.headers
        elif boxtype == 'advanced':
            this_headers = self.adv_headers
            
        assert len(data) == len(this_headers)
        for i in range(len(data)):
            if boxtype == 'normal':
                self.info[this_headers[i]].append(data[i])
            elif boxtype == 'advanced':
                self.adv_info[this_headers[i]].append(data[i])

    #add the cost of the player from DK 
    def add_cost_from_DK(self, data):
        pass

    # predict the given stat:
    # [PTS, FG3M, REB, AST, STL, BLK, TO]
    # 
    """ currently uses span-6 EWMA but we can change this """
    def predict(self, stat):
        # note: if a player is missing games, it still calculates weights (see is_na flag in documentation)
        return float(pd.stats.moments.ewma(pd.Series(self.info[stat]), span=6).tail(1))
    
    def fppp_stats(self):
        historical_fp = []
        for i in range(len(self.info['GAME_ID'])):
            historical_fp.append(self.calculate_fp(game_number=i))
        fppp = np.divide(historical, self.adv_info['PACE'])
        return np.average(fppp), np.std(fppp)

    def minutes_stats(self):
        return np.average(self.info['MIN']), np.std(self.info['MIN'])

    def possessions_model(self):
        num_iters = 300000
        results = []
        average_fppp, std_fppp = self.fppp_stats()
        average_min, std_min = self.minutes_stats()

        # TODO: Project pace using Vegas Over Unders!!!!!
        pace = 95 
        for i in range(num_iters):
            fppp = np.random.normal(average_fppp, std_fppp)
            minutes = np.random.normal(average_min, std_min)
            results.append(((float(minutes)/48.0) * pace) * fppp)



        #implement simulator here

    # calculates the number of fantasy points scored in the players nth game
    # where n = game_number
    # if game_number = 'predict' then it predicts using all the information so far
    def calculate_fp(self, game_number="predict", site="DraftKings"):
        if site == "DraftKings":
            fp = 0
            doubled = 0
            weights = {'PTS': 1.0, 'FG3M': 0.5, 'REB': 1.25, 'AST': 1.5, 'STL': 2.0, 'BLK': 2.0, 'TO': -0.5}
            for s, w in weights.iteritems():
                if game_number == "predict":
                    v = self.predict(s)
                else:
                    if game_number > len(self.info[s]):
                        print "Invalid game number"
                        return False
                    v = self.info[s][game_number]
                    if v == None:
                        #print "Error: " + self.info['COMMENT'][game_number]
                        return None
                fp += v * w
                if s in ['PTS', 'REB', 'AST', 'BLK', 'STL']:
                    if v >= 10.0:
                        doubled += 1
            if doubled == 2:
                fp += 1.5
            elif doubled >= 3:
                fp += 4.5 # assume that you get both DD and TD bonus
            return fp if not np.isnan(fp) else 0.0
        elif site == "FanDuel":
            fp = 0
            weights = {'PTS': 1.0, 'REB': 1.2, 'AST': 1.5, 'STL': 2.0, 'BLK': 2.0, 'TO': -1.0}
            for s, w in weights.iteritems():
                if game_number == 'predict':
                    v = self.predict(s)
                else:
                    if game_number > len(self.info[s]):
                        print 'Invalid game number'
                        return False
                    v = self.info[s][game_number]
                    if v == None:
                        #print 'Error: ' + self.info['COMMENT'][game_number]
                        return None
                fp += v * w
            return fp if not np.isnan(fp) else 0.0
        else:
            return "Not yet supported"

    def calculate_fp_variance(self, site="DraftKings", scaled=True):
        fp = []
        for i in range(len(self.info['PTS'])):
            if self.info['PTS'][i] != None:
                fp.append(self.calculate_fp(i, site))

        if scaled:
            return np.var(fp)/(self.calculate_fp('predict',site))**2
        else:
            return np.var(fp)
        
    def get_info(self):
        return self.info
    
    def get_adv_info(self):
        return self.adv_info
    
    def get_name(self):
        return self.info['PLAYER_NAME'][-1]
    
    def __repr__(self):
        return self.get_name()
    
    def __str__(self):
        return self.get_name()

# game class
class Game:
    def __init__(self):
        self.away_info = {} 
        self.home_info = {}
        self.headers = [u'GAME_DATE_EST', 
                        u'GAME_SEQUENCE', 
                        u'GAME_ID', 
                        u'TEAM_ID', 
                        u'TEAM_ABBREVIATION', 
                        u'TEAM_CITY_NAME', 
                        u'TEAM_WINS_LOSSES', 
                        u'PTS_QTR1', 
                        u'PTS_QTR2', 
                        u'PTS_QTR3', 
                        u'PTS_QTR4', 
                        u'PTS_OT1', 
                        u'PTS_OT2', 
                        u'PTS_OT3', 
                        u'PTS_OT4', 
                        u'PTS_OT5', 
                        u'PTS_OT6', 
                        u'PTS_OT7', 
                        u'PTS_OT8', 
                        u'PTS_OT9', 
                        u'PTS_OT10', 
                        u'PTS']
        self.adv_headers = [
                "GAME_ID", 
                "TEAM_ID", 
                "TEAM_NAME", 
                "TEAM_ABBREVIATION", 
                "TEAM_CITY", 
                "MIN", 
                "OFF_RATING", 
                "DEF_RATING", 
                "NET_RATING", 
                "AST_PCT", 
                "AST_TOV", 
                "AST_RATIO", 
                "OREB_PCT", 
                "DREB_PCT", 
                "REB_PCT", 
                "TM_TOV_PCT", 
                "EFG_PCT", 
                "TS_PCT", 
                "USG_PCT", 
                "PACE", 
                "PIE"]

    def add_data_from_boxscore(self, data, home_id, away_id, boxtype):
        if boxtype == 'normal':
            headertype = self.headers
        elif boxtype == 'advanced':
            headertype = self.adv_headers

        assert len(data[0]) == len(headertype)
        assert len(data[1]) == len(headertype)
        index = 0
        if data[0][headertype.index('TEAM_ID')] == home_id:
            home_index = 0
            away_index = 1
        elif data[0][headertype.index('TEAM_ID')] == away_id:
            away_index = 0
            home_index = 1
        for header in headertype:
            self.away_info[header] = data[away_index][index]
            self.home_info[header] = data[home_index][index]
            index += 1
    
    def get_home_id(self):
        return self.home_info['TEAM_ID']

    def get_away_id(self):
        return self.away_info['TEAM_ID']

    def get_home_abb(self):
        return self.home_info['TEAM_ABBREVIATION']

    def get_away_abb(self):
        return self.away_info['TEAM_ABBREVIATION']

    def get_game_id(self):
        return self.home_info['GAME_ID']

    def __repr__(self):
        date = self.home_info['GAME_DATE_EST'].split('T')[0]
        return date + "/Home: " + str(self.home_info['TEAM_ABBREVIATION']) + " " + str(self.home_info['PTS']) + ", Away: " + str(self.away_info['TEAM_ABBREVIATION']) + " " + str(self.away_info['PTS'])
    
    def __str__(self):
        date = self.home_info['GAME_DATE_EST'].split('T')[0]
        return date + "/Home: " + str(self.home_info['TEAM_ABBREVIATION']) + " " + str(self.home_info['PTS']) + ", Away: " + str(self.away_info['TEAM_ABBREVIATION']) + " " + str(self.away_info['PTS'])
            