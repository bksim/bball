import datetime
import os
import json
import csv
from entities import Player, Game
import numpy as np

# write predictions to excel sheet
def write_predictions(player_data, model_type, vegas_lines, def_ratings, off_ratings, excel_fn, dfs_site, minutes_adj = None):
	# key: NBA version, value: DK version
	predictions = {}
	if model_type == "ema":
		for p in player_data:
			if p.get_aliases()['DraftKings'] != p.get_aliases()['NBA']:
				predictions[p.get_aliases()['DraftKings']] = p.calculate_fp(game_number="predict", site=dfs_site)
				predictions[p.get_aliases()['NBA']] = p.calculate_fp(game_number="predict", site=dfs_site)
			else:
				predictions[p.get_name()] = p.calculate_fp(game_number="predict", site=dfs_site)
		with open(excel_fn, 'wb') as f:
			writer = csv.writer(f)
			for k, v in predictions.iteritems():
				writer.writerow([k, v])
		return predictions
	elif model_type == "possessions":
		assert dfs_site == "DraftKings"
		for p in player_data:
			pace = calculate_pace(p.get_info()['TEAM_ABBREVIATION'][-1], vegas_lines, def_ratings, off_ratings)

			if p.get_aliases()['DraftKings'] != p.get_aliases()['NBA']:
				predictions[p.get_aliases()['DraftKings']] = p.possessions_model(pace, minutes_adj)
				predictions[p.get_aliases()['NBA']] = p.possessions_model(pace, minutes_adj)
			else:
				predictions[p.get_name()] = p.possessions_model(pace, minutes_adj)
		
		with open(excel_fn, 'wb') as f:
			writer = csv.writer(f)
			for k, v in predictions.iteritems():
				writer.writerow([k, v['predicted_fp'], v['predicted_sd']])

		predictions_modified = {}
		for k in predictions:
			predictions_modified[k] = predictions[k]['predicted_fp']
		return predictions_modified

# finish this function by finishing the lookup table
def calculate_pace(team, vegas_lines, def_ratings, off_ratings):
    #keys: city names as on covers.com, values: nba team_abbreviation
	lookup = {
		'Atlanta': 'ATL', 
		'Boston': 'BOS', 
		'Brooklyn': 'BKN',
		'Charlotte': 'CHA',
		'Chicago': 'CHI',
		'Cleveland': 'CLE',
		'Dallas': 'DAL',
		'Denver': 'DEN',
		'Detroit': 'DET',
		'Golden State': 'GSW',
		'Houston': 'HOU',
		'Indiana': 'IND',
		'L.A. Clippers': 'LAC',
		'L.A. Lakers': 'LAL',
		'Memphis': 'MEM',
		'Miami': 'MIA',
		'Milwaukee': 'MIL',
		'Minnesota': 'MIN',
		'New Orleans': 'NOP',
		'New York': 'NYK',
		'Oklahoma City': 'OKC',
		'Orlando': 'ORL',
		'Philadelphia': 'PHI',
		'Phoenix': 'PHX',
		'Portland': 'POR',
		'Sacramento': 'SAC',
		'San Antonio': 'SAS',
		'Toronto': 'TOR',
		'Utah': 'UTA',
		'Washington': 'WAS'
	} 

	# 1. calculate pts predicted for home away. home+away=ou, away-home=spread, so away=(ou+spread)/2, home=ou-away
	# 2. get player's team's off rating and opposing team's def rating and average to get RATING
	# 3. calculate PTS_PREDICTED / (RATING / 100) = pace
	for k in vegas_lines:
		away = k.split('@')[0]
		home = k.split('@')[1]

		if team == lookup[away]:
			pts_predicted = float(vegas_lines[k][0] + vegas_lines[k][1])/2.0
			avg_rating = float(off_ratings[lookup[away]] + def_ratings[lookup[home]])/2.0
			return pts_predicted / (avg_rating / 100.0)
		elif team == lookup[home]:
			pts_predicted = float(vegas_lines[k][0]) - float(vegas_lines[k][0] + vegas_lines[k][1])/2.0
			avg_rating = float(off_ratings[lookup[home]] + def_ratings[lookup[away]])/2.0
			return pts_predicted / (avg_rating / 100.0)

	return False