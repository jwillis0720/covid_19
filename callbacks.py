import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import plotly.colors
import pandas as pd
import plots
import dash_table
from datetime import date, timedelta
import ast
import datetime
import numpy as np
from dash.dependencies import Input, Output, State
from pprint import pprint
from urllib.parse import urlparse, parse_qs, urlencode


# Setting up Sizes and Colors
GREEN_TO_YELLOW = ['#808080', '#a19e79', '#c1bd70', '#e0dc63', '#fffd50']
ORANGE_TO_RED = ['#ffa500', '#ff8c00', '#ff7000', '#ff4e00', '#ff0000']
SIZES_BIN = [5, 10, 30, 60]
DEATHS_BIN = [1, 20, 100, 1000, 1000000]
CASES_BIN = [1, 200, 1000, 50000, 10000000]

up_triangle = "▲"
down_tirangle = "▼"

'''All the functions in the callback need access to the GLOBAL DATA served in callbacks.serveData'''


def serve_data(ret=False, serve_local=False):
    global MASTER_ALL
    global MASTER_PID
    global DATE_MAPPER
    global KEY_VALUE

    if serve_local:
        MASTER_ALL = pd.read_pickle('Data/MASTER_ALL.pkl', compression='gzip')
        MASTER_PID = pd.read_pickle('Data/MASTER_PID.pkl', compression='gzip')

    else:
        print('Grabbing from S3')
        MASTER_ALL = pd.read_pickle(
            'https://jordansdatabucket.s3-us-west-2.amazonaws.com/covid19data/MASTER_ALL_NEW.pkl', compression='gzip')
        MASTER_PID = pd.read_pickle(
            'https://jordansdatabucket.s3-us-west-2.amazonaws.com/covid19data/MASTER_PID_NEW.pkl', compression='gzip')
        DATE_MAPPER = pd.DataFrame(MASTER_ALL['Date'].unique(), columns=['Date'])
        KEY_VALUE = dict(zip(list(MASTER_PID.index), list(
            MASTER_PID['location'].str.replace('US', 'United States'))))
        KEY_VALUE = pd.DataFrame(list(KEY_VALUE.values()), index=KEY_VALUE.keys(), columns=['name'])
        #MASTER_ALL = MASTER_ALL.set_index(['Date', 'forcast'])
        # eventually
        if 'per_capita_confirmed' not in MASTER_ALL.columns:
            MASTER_ALL['per_capita_confirmed'] = MASTER_ALL['confirmed']/MASTER_ALL['pop']
            MASTER_ALL['per_capita_deaths'] = MASTER_ALL['deaths']/MASTER_ALL['pop']
            max_size = 1500

            bins, ret_bins = pd.qcut(MASTER_ALL[(MASTER_ALL['per_capita_confirmed'] >= 0) & (MASTER_ALL['country'] != 'worldwide')]['per_capita_confirmed'], q=[
                0, .5, 0.6, 0.70, 0.75, 0.8, 0.85, 0.9, 0.95, 0.999, 1], duplicates='drop', retbins=True)
            yellows = ["#606056", "#6e6e56", "#7b7c55", "#898a54", "#979953",
                       "#a5a850", "#b4b74d", "#c3c649", "#d2d643", "#e2e53c"]
            reds = ["#5a4f4f", "#704d4d", "#854b4a", "#994746", "#ac4340",
                    "#be3c3a", "#cf3531", "#e02a27", "#f01c19", "#ff0000"]
            labels = np.geomspace(1, max_size, num=len(ret_bins)-1)
            MASTER_ALL['per_capita_CSize'] = pd.cut(MASTER_ALL['per_capita_confirmed'],
                                                    bins=ret_bins, labels=labels).astype(float).fillna(0)
            MASTER_ALL['per_capita_DSize'] = pd.cut(MASTER_ALL['per_capita_deaths'],
                                                    bins=ret_bins, labels=labels).astype(float).fillna(0)
            MASTER_ALL['per_capita_CColor'] = pd.cut(MASTER_ALL['per_capita_confirmed'], bins=ret_bins,
                                                     labels=yellows[2:]).astype(str).replace({'nan': 'white'})
            MASTER_ALL['per_capita_DColor'] = pd.cut(MASTER_ALL['per_capita_deaths'], bins=ret_bins,
                                                     labels=reds[2:]).astype(str).replace({'nan': 'white'})

        MASTER_ALL = MASTER_ALL.set_index(['Date', 'forcast'])
    if ret:
        return MASTER_ALL, MASTER_PID, DATE_MAPPER, KEY_VALUE
    else:
        return


def get_default_dropdown():
    return KEY_VALUE[KEY_VALUE['name'].str.strip().isin(['Worldwide', 'United States'])].index


def get_min_date():
    return DATE_MAPPER.index[0]


def get_max_date():
    return DATE_MAPPER.index[-1]


def get_date_marks():
    how_many_labels = (len(DATE_MAPPER))//10
    marks = {k: {'label': v}
             for k, v in list(DATE_MAPPER['Date'].dt.strftime(
                 '%m/%d').to_dict().items())[::how_many_labels]}
    if len(DATE_MAPPER)-1 not in marks.keys():
        marks[len(DATE_MAPPER)-1] = {'label': ''}
    return marks


def get_total_cases():
    sub_df = MASTER_ALL.reset_index().set_index(['forcast'])
    sub_df = sub_df[sub_df['country'] == 'worldwide']
    sub_diff = sub_df[['confirmed', 'deaths']].diff()
    total_confirmed = sub_diff.loc[False].sum()
    twenty_four_confirmed = sub_diff.loc[False].iloc[-1]
    forcast_seven_days = sub_diff.loc[True].iloc[0]  # .sum()
    total_cases = "{:,}".format(int(total_confirmed['confirmed']))
    change_in_cases = "{:,} ".format(int(twenty_four_confirmed['confirmed']))
    forcast_seven = "{:,}".format(int(forcast_seven_days['confirmed']))
    return [html.H3('Total Cases'),
            html.P(id='total-cases', children=total_cases),
            html.Div(className='change-card', children=[
                html.Span(children=[
                    up_triangle]),
                html.Span(change_in_cases),
                html.Span(html.I(className="wi wi-wind wi-towards-nne")),
                html.Span(forcast_seven)])]


def get_total_deaths():
    sub_df = MASTER_ALL.reset_index().set_index(['forcast'])
    sub_df = sub_df[sub_df['country'] == 'worldwide']
    sub_diff = sub_df[['confirmed', 'deaths']].diff()
    total_confirmed = sub_diff.loc[False].sum()
    twenty_four_confirmed = sub_diff.loc[False].iloc[-1]
    forcast_seven_days = sub_diff.loc[True].iloc[0]  # .sum()
    total_cases = "{:,}".format(int(total_confirmed['deaths']))
    change_in_cases = "{:,} ".format(int(twenty_four_confirmed['deaths']))
    forcast_seven = "{:,}".format(int(forcast_seven_days['deaths']))
    return [html.H3('Total Deaths'),
            html.P(id='total-deaths', children=total_cases),
            html.Div(className='change-card', children=[
                html.Span(children=[
                    up_triangle]),
                html.Span(change_in_cases),
                html.Span(html.I(className="wi wi-wind wi-towards-nne")),
                html.Span(forcast_seven)])]


def get_mortality_rate():
    sub_df = MASTER_ALL.reset_index().set_index(['forcast'])
    sub_df = sub_df[sub_df['country'] == 'worldwide']
    sub_df = sub_df[['confirmed', 'deaths']]
    sub_df['mr'] = sub_df['deaths']/sub_df['confirmed'] * 100
    mortality_rate_today = sub_df.loc[False].iloc[-1]['mr']
    change_in_mortality_rate = round(mortality_rate_today - sub_df.loc[False].iloc[-2]['mr'], 2)
    seven_day = round(mortality_rate_today-sub_df.loc[True].iloc[0]['mr'], 2)
    if change_in_mortality_rate > 0:
        symbol = up_triangle
    else:
        symbol = down_tirangle
    if seven_day < 0:
        class_name = "wi wi-wind wi-towards-nne"
    else:
        class_name = "wi wi-wind wi-towards-sse"
    change_in_mortality_rate = abs(change_in_mortality_rate)
    seven_day = abs(seven_day)
    # print(mortality_rate_today, sub_df.loc[True].iloc[-1]['mr'], sub_df.loc[False].iloc[0]['mr'])
    return [html.H3('Mortality Rate'),
            html.P(id='mortality-rate',
                   children="{}%".format(round(mortality_rate_today, 2))),
            html.Div(className='change-card', children=[
                html.Span(children=[
                     symbol]),
                html.Span("{} ".format(change_in_mortality_rate)),
                html.Span(html.I(className=class_name)),
                html.Span(seven_day)])]


def get_growth_rate():
    sub_df = MASTER_ALL.reset_index().set_index(['forcast'])
    sub_df = sub_df[sub_df['country'] == 'worldwide']
    sub_df = sub_df[['confirmed', 'deaths']].pct_change() * 100
    sub_df_diff = sub_df.diff()
    todays_gf = sub_df.loc[False].iloc[-1]['confirmed']
    change_in_gf = sub_df_diff.loc[False].iloc[-1]['confirmed']
    change_to_tomorrow = sub_df_diff.loc[True].iloc[0]['confirmed']
    # print(change_to_tomorrow)
    if change_in_gf > 0:
        symbol = up_triangle
        c_name = 'up-triangle'
    else:
        symbol = down_tirangle
        c_name = 'down-triangle'
    if change_to_tomorrow > 0:
        class_name = "wi wi-wind wi-towards-nne"
    else:
        class_name = "wi wi-wind wi-towards-sse"
    return [html.H3('Growth Rate'),
            html.P(id='growth-rate',
                   children="{}%".format(round(abs(todays_gf), 2))),
            html.Div(className='change-card', children=[
                html.Span(children=[
                     symbol]),
                html.Span("{} ".format(round(abs(change_in_gf), 2))),
                html.Span(html.I(className=class_name)),
                html.Span(round(abs(change_to_tomorrow), 2))])]


def get_dropdown_options():
    sorted_index = list(MASTER_PID.sort_values('confirmed')[:: -1].index)
    sorted_txt = list(MASTER_PID.sort_values('confirmed')[:: -1]['Text_Confirmed'].str.split('<br>').str.get(0))
    key_values = dict(zip(sorted_index, sorted_txt))
    options = [{'label': key_values[x].replace('US', 'United States'), 'value': x} for x in key_values]
    # print(options)
    return options


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
                'title': 'Dash {} Visualization'.format(id_)
            }
        }
    )


def get_dummy_map():
    us_cities = pd.read_csv(
        "https://raw.githubusercontent.com/plotly/datasets/master/us-cities-top-1k.csv")
    fig = px.scatter_mapbox(us_cities, lat="lat", lon="lon", hover_name="City", hover_data=["State", "Population"],
                            color_discrete_sequence=["fuchsia"], zoom=3, height=300)
    fig.update_layout(mapbox_style="open-street-map")
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    return fig


'''Now for the magic of the callback functions which we serve app too'''


def register_callbacks(app):
    @app.callback(
        Output("markdown", "style"),
        [Input("learn-more-button", "n_clicks"),
         Input("markdown_close", "n_clicks")],
    )
    def update_click_output(button_click, close_click):
        ctx = dash.callback_context
        # print(ctx.triggered)
        prop_id = ""
        if ctx.triggered:
            prop_id = ctx.triggered[0]["prop_id"].split(".")[0]
            n_clicks = ctx.triggered[0]["value"]

        # If a person clicks learn more then the display turns to block
        # If anything else is clicked change the markdown to display:none
        if prop_id == "learn-more-button" and n_clicks > 0:
            return {"display": "block"}
        else:
            return {"display": "none"}

    @app.callback(
        Output("map", "figure"),
        [Input("date_slider", "value"),
         Input("check-locations", "value"),
         Input("check-metrics", "value"),
         Input('relative_rate_check', 'value')],
        [State("map", 'figure'),
         State("map", "relayoutData")]
    )
    def render_map(date_value, locations_values, metrics_values, relative_check, figure, relative_layout):

        print(relative_check)

        # Date INT comes from the slider and can only return integers:
        official_date = DATE_MAPPER.iloc[date_value]['Date']
        print(official_date)
        plotting_df = MASTER_ALL.reset_index()[MASTER_ALL.reset_index()['Date'] == official_date]
        plotting_df = plotting_df[plotting_df['country'] != 'worldwide']

        if relative_layout:
            if 'mapbox.center' in relative_layout.keys():
                center = dict(lat=relative_layout['mapbox.center']['lat'],
                              lon=relative_layout['mapbox.center']['lon'])
                zoom = relative_layout['mapbox.zoom']
            else:
                zoom = 2.0,
                center = dict(lat=20.74, lon=15.4)
        else:
            zoom = 0.5,
            center = dict(lat=19.75, lon=-34.2)

        if 'province' in locations_values:
            locations_values.append('state')
        plotting_df = plotting_df[plotting_df['granularity'].isin(locations_values)]
        return plots.plot_map(plotting_df, metrics_values, zoom, center, relative_check)

    @app.callback(Output('content-readout', 'figure'),
                  [Input('dropdown_container', 'value'),
                   Input('tabs-values', 'value'),
                   Input('log-check', 'value'),
                   Input('deaths-confirmed', 'value'),
                   Input('prediction', 'value')],
                  [State('content-readout', 'relayoutData')])
    def render_tab_content(values, tabs, log, metric, predict, graph_state):
        gs = None
        if log == 'log':
            log = True
        else:
            log = False
        if graph_state:
            if 'xaxis.range[0]' in graph_state:
                gs = graph_state
        else:
            gs = None
        if tabs == 'total_cases_graph':
            return plots.total_confirmed_graph(values, MASTER_ALL, KEY_VALUE, log, metric, predict, gs)
        elif tabs == 'per_day_cases':
            return plots.per_day_confirmed(values, MASTER_ALL, KEY_VALUE, log, metric, predict, gs)
        elif tabs == 'exponential':
            return plots.plot_exponential(values, MASTER_ALL, KEY_VALUE, log, predict, gs)
        elif tabs == 'gr':
            return plots.per_gr(values, MASTER_ALL, KEY_VALUE, log, metric, predict, gs)

    @app.callback(Output('table-container', 'children'),
                  [Input('dropdown_container', 'value')])
    def render_table(values):
        data_entries = []
        last_date = MASTER_ALL.reset_index().groupby('forcast').tail(1)['Date'].iloc[0]
        forcast_date = MASTER_ALL.reset_index().groupby('forcast').tail(1)['Date'].iloc[-1]
        for value in values:
            # print(value)
            sort_me = ['Date', 'Location']
            sub_df = MASTER_ALL.reset_index()
            sub_df = sub_df[sub_df['PID'] == value]
            sub_df = sub_df.set_index('Date')
            confirmed = sub_df.loc[last_date, 'confirmed']
            deaths = sub_df.loc[last_date, 'deaths']
            confirmed_24 = sub_df['confirmed'].diff().loc[last_date]
            deaths_24 = sub_df['deaths'].diff().loc[last_date]
            entry = {'Date': last_date.strftime('%D'),
                     'Location': sub_df['Text_Confirmed'].str.split('<br>').str.get(0).iloc[0],
                     'Total Confirmed': int(confirmed),
                     'Confirmed 24h': "+{:,}".format(int(confirmed_24)),
                     'Total Deaths': "+{:,}".format(int(deaths)),
                     'Deaths 24h': "+{:,}".format(int(deaths_24))}
            data_entries.append(entry)
        df = pd.DataFrame(data_entries)
        df = df[sort_me + [i for i in df.columns if i not in sort_me]]
        df = df.fillna('-')
        df = df.sort_values('Total Confirmed')[::-1]
        df['Total Confirmed'] = df.apply(lambda x: "{:,}".format(x['Total Confirmed']), axis=1)
        return dash_table.DataTable(id='table',
                                    columns=[{'name': i, 'id': i}
                                             for i in df.columns],
                                    style_header={
                                        'backgroundColor': 'rgb(30, 30, 30)',
                                        'color': 'white'},
                                    style_cell={
                                        'color': 'black'},
                                    style_as_list_view=True,
                                    data=df.to_dict('records'))

    @app.callback(
        Output('dropdown_container', 'value'),
        [Input('map', 'clickData')],
        [State('dropdown_container', 'value'),
         State('dropdown_container', 'options')])
    def display_click_data(clickData, dropdown_selected, dropdown_options):
        if not clickData:
            return dropdown_selected
        pid = clickData['points'][0]['customdata']
        if int(pid) not in dropdown_selected:
            dropdown_selected.append(int(pid))
        return dropdown_selected

    @app.callback(Output('map-title', 'children'),
                  [Input('date_slider', 'value')])
    def update_map_title(date_int):
        "Reported Infections Map"
        official_date = DATE_MAPPER.iloc[date_int]['Date']
        if official_date.date() == date.today() - timedelta(days=1):
            return "Yesterday"
        if official_date.date() >= date.today():
            return "{}¹".format(official_date.strftime('%B %d, %Y'))

        return "{}".format(official_date.strftime('%B %d, %Y'))
