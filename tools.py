import pygsheets
import pandas as pd
# authorization
gc = pygsheets.authorize(
    service_file='.google/covid2019-272301-de83df95e692.json')


def write_pandas_to_gsheet(df, tabname):
    google_sheets = gc.open('Covid2019')

    # Get current tab named Pandas
    ws = google_sheets.worksheet_by_title(tabname)

    ws.set_dataframe(df, 'A1')
    print('Worksheet set at  : {}\n on tab {}'.format(google_sheets.url, tabname))
