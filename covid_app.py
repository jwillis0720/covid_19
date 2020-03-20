import sys
import warnings
import plotly.graph_objects as go

try:
    import dash
    import dash_core_components as dcc
    import dash_html_components as html
    from dash.exceptions import PreventUpdate
    import dash_table
    from dash.dependencies import Input, Output
except ImportError:
    sys.exit('Please install dash, e.g, pip install dash')


import numpy as np
import pandas as pd
import argparse

states_abbreviations_mapper = {
    'AK': 'Alaska',
    'AL': 'Alabama',
    'AR': 'Arkansas',
    'AS': 'American Samoa',
    'AZ': 'Arizona',
    'CA': 'California',
    'CO': 'Colorado',
    'CT': 'Connecticut',
    'DC': 'District of Columbia',
    'DE': 'Delaware',
    'FL': 'Florida',
    'GA': 'Georgia',
    'GU': 'Guam',
    'HI': 'Hawaii',
    'IA': 'Iowa',
    'ID': 'Idaho',
    'IL': 'Illinois',
    'IN': 'Indiana',
    'KS': 'Kansas',
    'KY': 'Kentucky',
    'LA': 'Louisiana',
    'MA': 'Massachusetts',
    'MD': 'Maryland',
    'ME': 'Maine',
    'MI': 'Michigan',
    'MN': 'Minnesota',
    'MO': 'Missouri',
    'MP': 'Northern Mariana Islands',
    'MS': 'Mississippi',
    'MT': 'Montana',
    'NA': 'National',
    'NC': 'North Carolina',
    'ND': 'North Dakota',
    'NE': 'Nebraska',
    'NH': 'New Hampshire',
    'NJ': 'New Jersey',
    'NM': 'New Mexico',
    'NV': 'Nevada',
    'NY': 'New York',
    'OH': 'Ohio',
    'OK': 'Oklahoma',
    'OR': 'Oregon',
    'PA': 'Pennsylvania',
    'PR': 'Puerto Rico',
    'RI': 'Rhode Island',
    'SC': 'South Carolina',
    'SD': 'South Dakota',
    'TN': 'Tennessee',
    'TX': 'Texas',
    'UT': 'Utah',
    'VA': 'Virginia',
    'VI': 'Virgin Islands',
    'VT': 'Vermont',
    'WA': 'Washington',
    'WI': 'Wisconsin',
    'WV': 'West Virginia',
    'WY': 'Wyoming'
}


warnings.filterwarnings(
    "ignore", category=pd.core.common.SettingWithCopyWarning)
BASE_URL = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/'
TS_CONFIRMED_CASES = 'csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Confirmed.csv'
TS_DEATH_CASES = 'csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Deaths.csv'
TS_RECOVERED_CASES = 'csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Recovered.csv'


def get_time_series(url):
    time_series_df = pd.read_csv(BASE_URL+url)
    return time_series_df.set_index(
        ['Province/State', 'Country/Region', 'Lat', 'Long']).transpose().unstack(
            fill_value="").reset_index().rename({'level_4': 'Date', 0: 'Cases'}, axis=1)


def parse_into_city(df):
    df['City'] = df['Province/State'].apply(
        lambda x: x.split(', ')[0] if len(x.split(', ')) == 2 else "")
    df['State'] = df['Province/State'].apply(
        lambda x: states_abbreviations_mapper[x.split(', ')[1].replace('.', '').strip()] if len(x.split(', ')) == 2 else x)
    return df[df['City'] == ''], df[df['City'] != '']


# Confirmed Cases
confirmed_cases = get_time_series(TS_CONFIRMED_CASES)
us_confirmed_cases = confirmed_cases[confirmed_cases['Country/Region'] == 'US']
world_confirmed_cases = confirmed_cases[confirmed_cases['Country/Region'] != 'US']

# US Specific confirmed cases. Can parse out by city too
us_confirmed_cases_by_state, us_confirmed_cases_by_city = parse_into_city(
    us_confirmed_cases)

# Death Cases
death_cases = get_time_series(TS_DEATH_CASES)
us_death_cases = death_cases[death_cases['Country/Region'] == 'US']
world_death_cases = death_cases[death_cases['Country/Region'] != 'US']

# US Specific death cases. Can parse out by city too
us_death_cases_by_state, us_death_cases_by_city = parse_into_city(
    us_death_cases)

# Recovered Cases
recovered_cases = get_time_series(TS_RECOVERED_CASES)
us_recovered_cases = recovered_cases[recovered_cases['Country/Region'] == 'US']
world_recovered_cases = recovered_cases[recovered_cases['Country/Region'] != 'US']

# US Specific death cases. Can parse out by city too
us_recovered_cases_by_state, us_recovered_cases_by_city = parse_into_city(
    us_recovered_cases)

# Coerce dates
us_confirmed_cases_by_city['Date'] = pd.to_datetime(
    us_confirmed_cases_by_city['Date'], format='%m/%d/%y')

us_confirmed_cases_by_state['Date'] = pd.to_datetime(
    us_confirmed_cases_by_state['Date'], format='%m/%d/%y')

to_date_cases_by_city = us_confirmed_cases_by_city.groupby(
    ['City', 'State'], as_index=False).sum()


date_mapper = pd.DataFrame(
    us_confirmed_cases_by_city['Date'].unique(), columns=['Date'])
min_date = min(date_mapper.index)
max_date = max(date_mapper.index)


def get_date_slider():
    return dcc.Slider(
        id='date_slider',
        min=min_date,
        max=max_date,
        step=1,
        value=max_date,
        marks={k: {'label': v, 'style': {'color': 'black', 'font-size': '2em'}}
               for k, v in list(date_mapper['Date'].dt.strftime(
                   '%m/%d/%y').to_dict().items())[::5]}
    )


def get_dash_table():
    return dash_table.DataTable(
        id='interactive-table',
        columns=[{'name': 'City', 'id': 'City'}, {
            'name': 'Total Cases', 'id': 'Cases'}],
        style_table={'overflowY': 'scroll',
                     'width': '300px',
                     'maxHeight': '500px'},
        style_cell={
            'textAlign': 'center',
            'width': '125px',
            'padding': '5px'
        },
        style_header={
            'backgroundColor': 'white',
            'fontWeight': 'bold'
        },
        style_as_list_view=True
    )


def serve_dash_layout():
    return html.Div(
        className='twelve columns main-div',
        children=[
            html.Div([
                html.Div(className='container ten columns', style={'display': ''},
                         children=[
                             dcc.Graph(id='state-graph')
                ]),
                html.Div(className='container four columns data-table-holder', style={'position': 'relative'}, children=[
                    get_dash_table()
                ])
            ]),
            html.Div(
                className='ten columns', style={'display': 'inline-block'},
                children=[
                    html.Div(
                        children=[
                            get_date_slider()
                        ]),
                ]),
        ])


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.layout = serve_dash_layout


@app.callback(Output('state-graph', 'figure'),
              [Input('date_slider', 'value')])
def get_graph_state(date_int):
    official_date = date_mapper.iloc[date_int]['Date']
    print(date_int, official_date)

    df_confirmed_before = us_confirmed_cases_by_state[
        us_confirmed_cases_by_state['Date'] < official_date]
    df_confirmed_before = df_confirmed_before.groupby(
        'Province/State Country/Region Lat Long'.split(), as_index=False).sum()
    df_confirmed_today = us_confirmed_cases_by_state[us_confirmed_cases_by_state['Date'] == official_date]

    df_confirmed_before['text'] = df_confirmed_before['Province/State'] + '<br>Total Cases Before {}: '.format(
        official_date.strftime('%m/%d/%y')) + df_confirmed_before['Cases'].astype(str)
    df_confirmed_today['text'] = df_confirmed_today['Province/State'] + '<br>Total New Cases On {}: '.format(
        official_date.strftime('%m/%d/%y')) + df_confirmed_today['Cases'].astype(str)
    fig = go.Figure()
    fig.add_trace(go.Scattergeo(
        locationmode='USA-states',
        lon=df_confirmed_before['Long'],
        lat=df_confirmed_before['Lat'],
        text=df_confirmed_before['text'],
        customdata=df_confirmed_before['Province/State'],
        hoverinfo='text',
        marker=dict(
            size=df_confirmed_before['Cases'],
            color='blue',
            line_color='rgb(40,40,40)',
            line_width=0.5,
            sizemode='area')
    ))

    fig.add_trace(go.Scattergeo(
        locationmode='USA-states',
        lon=df_confirmed_today['Long']+.11,
        lat=df_confirmed_today['Lat']-.15,
        text=df_confirmed_today['text'],
        customdata=df_confirmed_today['Province/State'],
        hoverinfo='text',
        marker=dict(
            size=df_confirmed_today['Cases'],
            color='red',
            line_color='rgb(40,40,40)',
            line_width=0.5,
            sizemode='area')
    ))

    fig.update_layout(
        title_text='The Corona Is Coming',
        autosize=False,
        showlegend=False,
        width=1000,
        height=600,
        geo=dict(
            scope='usa',
        )
    )
    return fig


@app.callback(
    Output('interactive-table', 'data'),
    [Input('state-graph', 'hoverData')])
def display_table_data(selectedData):
    if not selectedData:
        raise PreventUpdate
    state = selectedData['points'][0]['customdata']
    df = to_date_cases_by_city[to_date_cases_by_city['State'] == state]
    return df.sort_values('Cases')[::-1].to_dict('records')

# @app.callback(Output('updatemode-output-container', 'children'),
#               [Input('date_slider', 'value')])


# def display_value(value):
#     return 'Linear Value: {}'.format(date_mapper.iloc[int(value)].dt.strftime('%m/%d/%y').iloc[0])


if __name__ == '__main__':
    app.run_server(debug=True, port=8050)
