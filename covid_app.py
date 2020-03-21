import sys
import warnings
import numpy as np
import pandas as pd
import argparse

try:
    import dash
    import dash_core_components as dcc
    import dash_html_components as html
    from dash.exceptions import PreventUpdate
    import dash_table
    from dash.dependencies import Input, Output, State
    import plotly.graph_objects as go
    import plotly.express as px
except ImportError:
    sys.exit('Please install dash, e.g, pip install dash')

# Cancel copy warnings of pandas
warnings.filterwarnings(
    "ignore", category=pd.core.common.SettingWithCopyWarning)

# Initialize APP
app = dash.Dash(__name__,
                meta_tags=[
                    {"name": "viewport",
                        "content": "width=device-width, initial-scale=1.0"}
                ]
                )

# Parse Data
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


BASE_URL = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/'
TS_CONFIRMED_CASES = 'csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Confirmed.csv'
TS_DEATH_CASES = 'csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Deaths.csv'
TS_RECOVERED_CASES = 'csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Recovered.csv'
mapbox_access_token = "pk.eyJ1IjoiandpbGxpczA3MjAiLCJhIjoiY2s4MHhoYmF6MDFoODNpcnVyNGR2bWk1bSJ9.YNwklD1Aa6DihVblHr3GVg"
#mapbox_style = "mapbox://styles/plotlymapbox/cjvprkf3t1kns1cqjxuxmwixz"
mapbox_style = 'dark'


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

us_death_cases_by_city['Date'] = pd.to_datetime(
    us_death_cases_by_city['Date'], format='%m/%d/%y')

us_death_cases_by_state['Date'] = pd.to_datetime(
    us_death_cases_by_state['Date'], format='%m/%d/%y')

to_date_cases_by_city = us_confirmed_cases_by_city.groupby(
    ['City', 'State'], as_index=False).sum()


date_mapper = pd.DataFrame(
    us_confirmed_cases_by_city['Date'].unique(), columns=['Date'])
date_mapper['Date_text'] = date_mapper['Date'].dt.strftime('%m/%d/%y')

min_date = min(date_mapper.index)
max_date = max(date_mapper.index)

# Cumulative:
cumm_df = []
for day, date_text in zip(date_mapper['Date'], date_mapper['Date_text']):
    death_df = us_death_cases_by_state[us_death_cases_by_state['Date'] <= day].groupby(
        ['State', 'Lat', 'Long']).sum().reset_index()
    death_df['Text'] = death_df['State'] + \
        " Deaths: "+death_df['Cases'].astype(str)
    death_df['Date'] = date_text
    death_df['Metric'] = 'Death'
    ongoing_df = us_confirmed_cases_by_state[us_confirmed_cases_by_state['Date'] <= day].groupby(
        ['State', 'Lat', 'Long']).sum().reset_index()
    ongoing_df['Text'] = ongoing_df['State'] + \
        " Cases: "+ongoing_df['Cases'].astype(str)
    ongoing_df['Date'] = date_text
    ongoing_df['Metric'] = 'Ongoing'

    for death_row in death_df.iterrows():
        state = death_row[1]['State']
        deaths = death_row[1]['Cases']
        #rint('before',ongoing_df.loc[ongoing_df['State'] == state,'Cases'].iloc[0])
        ongoing_df.loc[ongoing_df['State'] == state, 'Cases'] -= deaths
        #print('after',ongoing_df.loc[ongoing_df['State'] == state,'Cases'].iloc[0])

    cumm_df += [ongoing_df, death_df]
ongoing_death_by_state_df = pd.concat(cumm_df)
# Dash Help Components
# I Use these so I simply don't clutter the layout


def get_date_slider():
    return dcc.Slider(
        id='date_slider',
        min=min_date,
        max=max_date,
        step=1,
        value=0,
        marks={k: {'label': v, 'style': {'color': 'grey', 'font-size': '2rem'}}
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


def serve_dash_layout():
    return html.Div(
        id="root",
        children=[
            html.Div(
                id="header",
                children=[
                    #html.Img(id="logo", src=app.get_asset_url("dash-logo.png")),
                    html.H4(children="COVID-19 Infection Dashboard"),
                    html.P(
                        id="description",
                        children="Rates of Infections",
                    ),
                ],
            ),
            html.Div(
                id="app-container",
                children=[
                    html.Div(
                        id="left-column",
                        children=[

                            html.Div(
                                id="heatmap-container",
                                children=[
                                    html.P(
                                        "Heatmap of age adjusted mortality rates \
                            from poisonings in year {0}".format(
                                            2000
                                        ),
                                        id="heatmap-title",
                                    ),
                                    dcc.Graph(id='state-graph'),
                                ],
                            ),
                            html.Div(
                                id="slider-container",
                                children=[
                                    html.P(
                                        id="slider-text",
                                        children="Drag the slider to change the Date:",
                                    ),
                                    get_date_slider()
                                ],
                            ),
                        ],
                    ),
                    html.Div(
                        id="graph-container",
                        children=[
                            html.P(id="chart-selector",
                                   children="Select chart:"),
                            dcc.Dropdown(
                                options=[
                                    {
                                        "label": "Histogram of total number of deaths (single year)",
                                        "value": "show_absolute_deaths_single_year",
                                    },
                                    {
                                        "label": "Histogram of total number of deaths (1999-2016)",
                                        "value": "absolute_deaths_all_time",
                                    },
                                    {
                                        "label": "Age-adjusted death rate (single year)",
                                        "value": "show_death_rate_single_year",
                                    },
                                    {
                                        "label": "Trends in age-adjusted death rate (1999-2016)",
                                        "value": "death_rate_all_time",
                                    },
                                ],
                                value="show_death_rate_single_year",
                                id="chart-dropdown",
                            ),
                           get_dummy_graph('dummy2'),
                        ],
                    ),
                ],
            ),
        ],
    )


def get_dash_animation():
    px.set_mapbox_access_token(mapbox_access_token)
    fig = px.scatter_mapbox(ongoing_death_by_state_df, lat="Lat", lon="Long", size="Cases", animation_frame='Date', animation_group='State',
                            color='Metric', size_max=100, zoom=3.5, mapbox_style='dark', center=dict(lat=38.5266, lon=-96.7265), height=800)
    fig['layout']['updatemenus'][0]['buttons'][0]['args'][1]['frame']['duration'] = 100
    fig['layout']['updatemenus'][0]['buttons'][0]['args'][1]['transition']['duration'] = 0
    fig['layout']['updatemenus'][0]['buttons'][0]['args'][1]['transition']['easing'] = "cubic-in-out"
    fig['layout']['sliders'][0]['currentvalue']['xanchor'] = "center"
    fig['layout']['sliders'][0]['currentvalue']['prefix'] = ""
    return fig


app.layout = serve_dash_layout


@app.callback(Output('state-graph', 'figure'),
              [Input('date_slider', 'value')],
              [State('state-graph', 'figure')])
def get_graph_state(date_int, figure):
    # Get initial zoom and shit if the figure is already drawn
    if not figure:
        lat = 38.72490
        lon = -95.61446
        zoom = 3.5
    elif "layout" in figure:
        lat = figure["layout"]["mapbox"]["center"]["lat"]
        lon = figure["layout"]["mapbox"]["center"]["lon"]
        zoom = figure["layout"]["mapbox"]["zoom"]

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
    # Has to take in a figure state eventually
    fig = go.Figure()
    fig.add_trace(go.Scattermapbox(
        lon=df_confirmed_before['Long'],
        lat=df_confirmed_before['Lat'],
        text=df_confirmed_before['text'],
        customdata=df_confirmed_before['Province/State'],
        hoverinfo='text',
        textposition='top right',
        mode='markers',
        marker=dict(
            size=df_confirmed_before['Cases'].apply(
                lambda x: np.log2(x)*10 if x else 0),
            color='blue')))

    fig.add_trace(go.Scattermapbox(
        lon=df_confirmed_today['Long'] +
        np.random.normal(0, 0.2, len(df_confirmed_today['Long'])),
        lat=df_confirmed_today['Lat'] +
        np.random.normal(0, 0.2, len(df_confirmed_today['Lat'])),
        text=df_confirmed_today['text'],
        customdata=df_confirmed_today['Province/State'],
        hoverinfo='text',
        textposition='top right',
        mode='markers',
        marker=dict(
            size=df_confirmed_today['Cases'].apply(
                lambda x: np.log2(x)*10 if x else 0),
            color='yellow')))

    layout = dict(
        title_text='The Corona is Coming',
        autosize=True,
        showlegend=False,
        mapbox=dict(
            accesstoken=mapbox_access_token,
            style=mapbox_style,
            zoom=zoom,
            center=dict(lat=lat, lon=lon)
        ),
        hovermode="closest",
        margin=dict(r=0, l=0, t=0, b=0),
        dragmode="pan",
    )

    fig.update_layout(layout)
    return fig


# @app.callback(
#     Output('interactive-table', 'data'),
#     [Input('state-graph', 'hoverData')])
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
