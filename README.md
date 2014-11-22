## Daily pipeline

### Model

1. In `model.ipynb` run the code block containing `data_getters.download_gamelog_jsons(2014,'boxscores/2014',start_game=X, end_game=1230)` where X is the first game that has not already been downloaded. The program will automatically stop once the last game that is available is downloaded.

2. Run the next code block, making sure to change `latest_day = datetime.date(2014,11,16)` into the correct day. All days before and including `latest_day` will be used to make predictions.

3. Paste the results of the model `model_predictions.csv` into the appropriate salary optimization sheet in excel.

### Optimization

1. Export daily player information to CSV and place in first five columns of the appropriate sheet in `DK Salary Optimization Sheets`.

2. Copy/paste results from `model_predictions.csv` into the `Model` column of the sheet

3. Make discretionary changes if desired, then click `Data -> Solver` and solve using the Simplex LP algorithm.

### Meta-analysis

1. Go to DraftKings lobby and save the lobby source code as `draftkings scrapes/YYYYMMDD_draftkings_nba_lobby.htm`.

2. Go to the main function in data_getters.py, change the variable `fn` to the name of the downloaded `.htm` file, and run, generating a list of all games and their ID's.

3. Run selenium script on logged in DK account to download the `.csv` info for each of these games.