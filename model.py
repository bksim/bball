import datetime
import os
import json
import csv
from entities import Player, Game
import numpy as np

# write predictions to excel sheet
def write_predictions(player_data, model_type, excel_fn, dfs_site):
	predictions = {}
	if model_type == "ema":
		for p in player_data:
			predictions[p.get_name()] = p.calculate_fp(game_number="predict", site=dfs_site)
		with open(excel_fn, 'wb') as f:
			writer = csv.writer(f)
			for k, v in predictions.iteritems():
				writer.writerow([k, v])
		return True
	elif model_type == "possessions":
		assert dfs_site == "DraftKings"
		for p in player_data:
			pace = 95.0 # what should this be???
			predictions[p.get_name()] = p.possessions_model(pace)
		with open(excel_fn, 'wb') as f:
			writer = csv.writer(f)
			for k, v in predictions.iteritems():
				writer.writerow([k, v['predicted_fp'], v['predicted_sd']])
		return True