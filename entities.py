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
        return float(pd.stats.moments.ewma(pd.Series(self.info[stat]), span=10).tail(1))
    
    ####################### POSSESSIONS MODEL CODE ########################
    """
    calculates fantasy points per possession for this player; average and std returned
    fantasy points per possession = fantasy points / number of possessions
    FP / (number of possessions) = FP / (#possessions / 48 min * (MINUTES/48.0)) = 48*FP/(pace*min)
    """
    def fppp_stats(self):
        historical_fp = []
        for i in range(len(self.info['GAME_ID'])): 
            temp = self.calculate_fp(game_number=i)
            if temp is not None:
                historical_fp.append(self.calculate_fp(game_number=i))
        # are you supposed to use the player's own pace here or the team's pace?
        pace = [p for p in self.adv_info['PACE'] if p is not None]
        minutes = [(float(m.split(':')[0]) + float(m.split(':')[1])/60.0) for m in self.info['MIN'] if m is not None]
        
        fppp = 48.0*np.array(np.divide(historical_fp, np.multiply(pace, minutes)))
        return np.average(fppp), np.std(fppp), fppp

    def minutes_stats(self):
        minutes = [(float(m.split(':')[0]) + float(m.split(':')[1])/60.0) for m in self.info['MIN'] if m is not None]
        return np.average(minutes), np.std(minutes), minutes

    def possessions_model(self, pace):
        num_iters = 300000
        results = []
        average_fppp, std_fppp, fppp = self.fppp_stats()
        average_min, std_min, minutes = self.minutes_stats()

        # TODO: Project pace using Vegas Over Unders!!!!!
        # get projected pace from vegas over under
        #for i in range(num_iters):
        #    fppp = np.random.normal(average_fppp, std_fppp)
        #    minutes = np.random.normal(average_min, std_min)
        #    results.append(((float(minutes)/48.0) * pace) * fppp)
        #implement simulator here

        #assumes a player will play same minutes as his average on season, can change this for injuries, etc
        #cant just multiply avg(fppp)*avg(minutes)*pace/48 because could have correlation
        #E(XY) != E(X)E(Y) in general
        fpppmin = np.multiply(fppp, minutes)
        #print self.info['PLAYER_NAME']
        #print pd.stats.moments.ewma(pd.Series(fpppmin), span=6).tail(1)
        if len(fpppmin) > 0:
            predicted_fp = float(pd.stats.moments.ewma(pd.Series(fpppmin), span=10).tail(1))*pace/48.0
        else:
            predicted_fp = 0.0
        #predicted_fp = np.mean(fpppmin)*pace/48.0
        predicted_sd = np.std(fpppmin)*pace/48.0

        predicted_fp = predicted_fp if not np.isnan(predicted_fp) else 0.0
        predicted_sd = predicted_sd if not np.isnan(predicted_sd) else 0.0
        return {'predicted_fp': predicted_fp, 'predicted_sd': predicted_sd}

    ######################## END POSSESSIONS MODEL CODE ######################




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
            