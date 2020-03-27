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


def get_dummy_graph(id_):
    return dcc.Graph(
        id=id_,
        figure={
            'data': [
                {'x': [1, 2, 3], 'y': [4, 1, 2], 'type': 'bar', 'name': 'SF'},
                {'x': [1, 2, 3], 'y': [2, 4, 5],
                    'type': 'bar', 'name': u'Montréal'},
            ],
            'layout': {
                'title': 'Dash Data Visualization'
            }
        }
    )
