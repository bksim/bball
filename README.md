Daily pipeline:

1. In analyze_boxscores.ipynb, run

`data_getters.download_gamelog_jsons(2014,'boxscores/2014',start_game=X, end_game=1230)`

where X is the first game that has not already been downloaded. The program will automatically stop once the last game that is available is downloaded.

2. Run the next two code blocks in `analyze_boxscores.ipynb`, which load the Player class and two functions for loading JSON's and writing predictions.

3. Run the next code block, making sure to change `latest_day = datetime.date(2014,11,16)` into the correct day. All days before and including `latest_day` will be used to make predictions.

4. Paste the results of the model `model_predictions.csv` into the appropriate salary optimization sheet in excel.
`