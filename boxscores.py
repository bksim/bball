import datetime
import os
import json
import csv
from entities import Player, Game
import numpy as np

# loads jsons to memory from box score directory
# loads jsons up until and including end_date
def load_jsons_to_memory(box_score_directory, end_date):
    players = []
    player_ids = []
    games = []
    for fn in os.listdir(box_score_directory):
        datestring = fn.split('-')[0]
        year = int(datestring[0:4])
        month = int(datestring[4:6])
        day = int(datestring[6:8])
        if datetime.date(year, month, day) <= end_date:
            with open(os.path.join(box_score_directory, fn)) as f:
                t = json.load(f)
                names = [t['resultSets'][i]['name'] for i in range(len(t['resultSets']))]
                for player_data in t['resultSets'][names.index('PlayerStats')]['rowSet']:
                    # can optimize here by keeping sorted list of player_ids but too lazy
                    try:
                        ind = player_ids.index(player_data[4])
                        players[ind].add_game_from_boxscore(player_data, 'normal')
                    # player not in player_ids
                    except ValueError:
                        player_ids.append(player_data[4])
                        temp_player = Player()
                        temp_player.add_game_from_boxscore(player_data, 'normal')
                        players.append(temp_player)
                # add advanced stats. would roll it in with code above but not sure if order is guaranteed
                # to be the same for advanced stats as it is for normal stats
                for player_data in t['resultSets'][names.index('sqlPlayersAdvanced')]['rowSet']:
                    # can optimize here by keeping sorted list of player_ids but too lazy
                    try:
                        ind = player_ids.index(player_data[4])
                        players[ind].add_game_from_boxscore(player_data, 'advanced')
                    # player not in player_ids
                    except ValueError:
                        player_ids.append(player_data[4])
                        temp_player = Player()
                        temp_player.add_game_from_boxscore(player_data, 'advanced')
                        players.append(temp_player)
                game_summary = t['resultSets'][names.index('GameSummary')]['rowSet'][0]
                temp_game = Game()
                temp_game.add_data_from_boxscore(t['resultSets'][names.index('LineScore')]['rowSet'], 
                                                 game_summary[6], game_summary[7], 'advanced')
                games.append(temp_game)
    return players, games

# write predictions to excel sheet
def write_predictions(player_data, excel_fn, dfs_site):
    predictions = {}
    for p in player_data:
        predictions[p.get_name()] = p.calculate_fp(game_number="predict", site=dfs_site)
    with open(excel_fn, 'wb') as f:
        writer = csv.writer(f)
        for k, v in predictions.iteritems():
            writer.writerow([k, v])
    return True