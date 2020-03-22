import sys
import warnings
import numpy as np
import pandas as pd
import argparse
import pprint
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
# mapbox_style = "mapbox://styles/plotlymapbox/cjvprkf3t1kns1cqjxuxmwixz"
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

us_recovered_cases_by_state['Date'] = pd.to_datetime(
    us_recovered_cases_by_state['Date'], format='%m/%d/%y')

us_recovered_cases_by_state['Date'] = pd.to_datetime(
    us_recovered_cases_by_state['Date'], format='%m/%d/%y')

world_confirmed_cases['Date'] = pd.to_datetime(
    world_confirmed_cases['Date'], format='%m/%d/%y')

world_death_cases['Date'] = pd.to_datetime(
    world_death_cases['Date'], format='%m/%d/%y')

world_recovered_cases['Date'] = pd.to_datetime(
    world_recovered_cases['Date'], format='%m/%d/%y')


to_date_cases_by_city = us_confirmed_cases_by_city.groupby(
    ['City', 'State'], as_index=False).sum()


date_mapper = pd.DataFrame(
    us_confirmed_cases_by_city['Date'].unique(), columns=['Date'])
date_mapper['Date_text'] = date_mapper['Date'].dt.strftime('%m/%d/%y')

min_date = min(date_mapper.index)
max_date = max(date_mapper.index)


centroid_country_mapper = world_confirmed_cases.groupby(
    'Country/Region').apply(lambda x: x.sort_values('Cases')[::-1].iloc[0][['Lat', 'Long']])
centroid_country_mapper = {x[0]: {'Long': x[1]['Long'], 'Lat': x[1]['Lat']}
                           for x in centroid_country_mapper.iterrows()}  # Dash Help Components
# I Use these so I simply don't clutter the layout


def get_date_slider():
    how_many_labels = (len(date_mapper))//10
    marks = {k: {'label': v}
             for k, v in list(date_mapper['Date'].dt.strftime(
                 '%m/%d/%y').to_dict().items())[::how_many_labels]}
    last_key = list(marks.keys())[-1]
    todays_key = date_mapper.index[-1]
    if last_key == todays_key:
        marks[last_key]['label'] == 'Today'
    else:
        marks[todays_key] = {'label': 'Today'}

    return dcc.Slider(
        id='date_slider',
        min=min_date,
        max=max_date,
        step=1,
        value=0,
        marks=marks
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
                    # html.Img(id="logo", src=app.get_asset_url("dash-logo.png")),
                    html.H4(children="COVID-19 Infection Dashboard"),
                    html.P(
                        id="map-description",
                        children=["COVID-19 Infection Information"]
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
                                        children="Drag the Slider to Change the Reported Date:",
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
                                   children="Hover Charts"),
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

# We must expose this for Elastic Bean Stalk to Run
application = app.server


@app.callback(Output('state-graph', 'figure'),
              [Input('date_slider', 'value')],
              [State('state-graph', 'figure')])
def get_graph_state(date_int, figure):
    # Get initial zoom and shit if the figure is already drawn
    if not figure:
        lat = 15.74
        lon = -1.4
        zoom = 1.6
    elif "layout" in figure:
        lat = figure["layout"]["mapbox"]['center']["lat"]
        lon = figure["layout"]["mapbox"]['center']["lon"]
        zoom = figure["layout"]["mapbox"]["zoom"]

    # if figure:
    #     pprint(figure)
    sizeref = 2. * world_confirmed_cases.groupby(
        ['Date', 'Country/Region']).sum().max()['Cases'] / (20 ** 2)
    official_date = date_mapper.iloc[date_int]['Date']
    print(date_int, official_date)
    df_confirmed = us_confirmed_cases_by_state[
        us_confirmed_cases_by_state['Date'] == official_date].groupby('Province/State Country/Region Lat Long'.split(), as_index=False).sum()
    df_confirmed.rename({'Cases': 'Ongoing'}, axis=1, inplace=1)
    df_confirmed['text'] = df_confirmed['Province/State'] + '<br>Total Cases {}: '.format(
        official_date.strftime('%m/%d/%y')) + df_confirmed['Ongoing'].astype(str)

    df_death = us_death_cases_by_state[
        us_death_cases_by_state['Date'] == official_date].groupby('Province/State Country/Region Lat Long'.split(), as_index=False).sum()
    df_death.rename({'Cases': 'Deaths'}, axis=1, inplace=1)
    df_death['text'] = df_death['Province/State'] + '<br>Total Deaths {}: '.format(
        official_date.strftime('%m/%d/%y')) + df_death['Deaths'].astype(str)

    df_recover = us_recovered_cases_by_state[
        us_recovered_cases_by_state['Date'] == official_date].groupby('Province/State Country/Region Lat Long'.split(), as_index=False).sum()
    df_recover.rename({'Cases': 'Recovered'}, axis=1, inplace=1)
    df_recover['text'] = df_recover['Province/State'] + '<br>Total Recovered {}: '.format(
        official_date.strftime('%m/%d/%y')) + df_recover['Recovered'].astype(str)

    # Has to take in a figure state eventually
    fig = go.Figure()
    fig.add_trace(go.Scattermapbox(
        lon=df_confirmed['Long'] +
        np.random.normal(0, .02, len(df_confirmed['Long'])),
        lat=df_confirmed['Lat'] +
        np.random.normal(0, .02, len(df_confirmed['Lat'])),
        text=df_confirmed['text'],
        customdata=df_confirmed['Province/State'],
        hoverinfo='text',
        textposition='top right',
        mode='markers',
        marker=dict(
            sizeref=sizeref,
            sizemin=3,
            size=df_confirmed['Ongoing'],
            color='yellow')))

    fig.add_trace(go.Scattermapbox(
        lon=df_death['Long']+np.random.normal(0, .02, len(df_death['Long'])),
        lat=df_death['Lat']+np.random.normal(0, .02, len(df_death['Long'])),
        text=df_death['text'],
        customdata=df_death['Province/State'],
        hoverinfo='text',
        textposition='top right',
        mode='markers',
        marker=dict(
            sizeref=sizeref,
            sizemin=2,
            size=df_death['Deaths'],
            color='red')))

    fig.add_trace(go.Scattermapbox(
        lon=df_recover['Long'] +
        np.random.normal(0, .05, len(df_recover['Long'])),
        lat=df_recover['Lat']+np.random.normal(0, .05, len(df_recover['Lat'])),
        text=df_recover['text'],
        customdata=df_recover['Province/State'],
        hoverinfo='text',
        textposition='top right',
        mode='markers',
        marker=dict(
            sizeref=sizeref,
            sizemin=2,
            size=df_recover['Recovered'],
            color='green')))

    world_confirmed = world_confirmed_cases[
        world_confirmed_cases['Date'] == official_date].groupby('Country/Region'.split(), as_index=False).sum()
    world_confirmed.rename({'Cases': 'Ongoing'}, axis=1, inplace=1)
    world_confirmed['text'] = world_confirmed['Country/Region'] + '<br>Total Cases {}: '.format(
        official_date.strftime('%m/%d/%y')) + world_confirmed['Ongoing'].map('{:,}'.format)
    world_confirmed['Lat'] = world_confirmed['Country/Region'].apply(
        lambda x: centroid_country_mapper[x]['Lat'])
    world_confirmed['Long'] = world_confirmed['Country/Region'].apply(
        lambda x: centroid_country_mapper[x]['Long'])

    world_dead = world_death_cases[
        world_death_cases['Date'] == official_date].groupby('Country/Region'.split(), as_index=False).sum()
    world_dead.rename({'Cases': 'Dead'}, axis=1, inplace=1)
    world_dead['text'] = world_dead['Country/Region'] + '<br>Total Dead {}: '.format(
        official_date.strftime('%m/%d/%y')) + world_dead['Dead'].map('{:,}'.format)
    world_dead['Lat'] = world_dead['Country/Region'].apply(
        lambda x: centroid_country_mapper[x]['Lat'])
    world_dead['Long'] = world_dead['Country/Region'].apply(
        lambda x: centroid_country_mapper[x]['Long'])

    world_recovered = world_recovered_cases[
        world_recovered_cases['Date'] == official_date].groupby('Country/Region'.split(), as_index=False).sum()
    world_recovered.rename({'Cases': 'Recovered'}, axis=1, inplace=1)
    world_recovered['text'] = world_recovered['Country/Region'] + '<br>Total Recovered {}: '.format(
        official_date.strftime('%m/%d/%y')) + world_recovered['Recovered'].map('{:,}'.format)
    world_recovered['Lat'] = world_recovered['Country/Region'].apply(
        lambda x: centroid_country_mapper[x]['Lat'])
    world_recovered['Long'] = world_recovered['Country/Region'].apply(
        lambda x: centroid_country_mapper[x]['Long'])

    fig.add_trace(go.Scattermapbox(
        lon=world_confirmed['Long'],
        lat=world_confirmed['Lat'],
        text=world_confirmed['text'],
        customdata=world_confirmed['Country/Region'],
        hoverinfo='text',
        textposition='top right',
        mode='markers',
        marker=dict(
            sizeref=sizeref,
            sizemin=3,
            size=world_confirmed['Ongoing'],
            color='yellow')))

    fig.add_trace(go.Scattermapbox(
        lon=world_dead['Long'] +
        np.random.normal(0, .05, len(world_dead['Long'])),
        lat=world_dead['Lat']+np.random.normal(0, .05, len(world_dead['Lat'])),
        text=world_dead['text'],
        customdata=world_dead['Country/Region'],
        hoverinfo='text',
        textposition='top right',
        mode='markers',
        marker=dict(
            sizeref=sizeref,
            sizemin=3,
            size=world_dead['Dead'],
            color='red')))

    fig.add_trace(go.Scattermapbox(
        lon=world_recovered['Long'] +
        np.random.normal(0, .05, len(world_recovered['Long'])),
        lat=world_recovered['Lat'] +
        np.random.normal(0, .05, len(world_recovered['Lat'])),
        text=world_recovered['text'],
        customdata=world_recovered['Country/Region'],
        hoverinfo='text',
        textposition='top right',
        mode='markers',
        marker=dict(
            sizeref=sizeref,
            sizemin=3,
            size=world_recovered['Recovered'],
            color='green')))

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

@app.callback(Output('heatmap-title', 'children'),
              [Input('date_slider', 'value')])
def update_description(date_int):
    "Reported Infections Map"
    official_date = date_mapper.iloc[date_int]['Date']
    return "{}".format(official_date.strftime('%B %d, %Y'))


def display_table_data(selectedData):
    if not selectedData:
        raise PreventUpdate
    state = selectedData['points'][0]['customdata']
    df = to_date_cases_by_city[to_date_cases_by_city['State'] == state]
    return df.sort_values('Cases')[::-1].to_dict('records')


if __name__ == '__main__':
    app.run_server(debug=True, port=8050)
