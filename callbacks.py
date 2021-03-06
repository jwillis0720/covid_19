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

            'https://jordanspubliccovidbucket.s3-us-east-2.amazonaws.com/covid19data/MASTER_ALL_NEW.pkl', compression='gzip')
        MASTER_PID = pd.read_pickle(
            'https://jordanspubliccovidbucket.s3-us-east-2.amazonaws.com/covid19data/MASTER_PID_NEW.pkl', compression='gzip')
        DATE_MAPPER = pd.DataFrame(MASTER_ALL['Date'].unique(), columns=['Date'])
        KEY_VALUE = dict(zip(list(MASTER_PID.index), list(
            MASTER_PID['location'].str.replace('US', 'United States'))))
        KEY_VALUE = pd.DataFrame(list(KEY_VALUE.values()), index=KEY_VALUE.keys(), columns=['name'])
        # MASTER_ALL = MASTER_ALL.set_index(['Date', 'forcast'])
        # eventually

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
                html.Span(forcast_seven),
                html.Span(className='tooltiptext', children=[
                    """Worldwide total case count. \n{} is the increase of cases in the past 24 hours.""".format(
                        up_triangle), '\n', html.I(className='wi wi-wind wi-towards-nne'), """ is the predicted cases in the next 24 hours"""
                ])])]


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
                html.Span(forcast_seven),
                html.Span(className='tooltiptext', children=[
                    """Worldwide total deaths count. \n{} is the increase of deaths in the past 24 hours.""".format(
                        up_triangle), html.Br(),
                    html.I(className='wi wi-wind wi-towards-nne'),
                    " is the predicted deaths in the next 24 hours"
                ])])]


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
        indicator = 'increase'
    else:
        symbol = down_tirangle
        indicator = 'deacrease'
    if seven_day < 0:
        class_name = "wi wi-wind wi-towards-nne"
        second_indicator = 'increase'
    else:
        class_name = "wi wi-wind wi-towards-sse"
        second_indicator = 'decrease'
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
                html.Span(seven_day),
                html.Span(className='tooltiptext', children=[
                    """Worldwide mortality rate. Total deaths divided by total cases. \n{} is the {} mortality rate  in the past 24 hours.""".format(
                        symbol, indicator), html.Br(),
                    html.I(className='wi wi-wind {}'.format(class_name)),
                    " is the predicted {} mortality rate in the next 24 hours".format(second_indicator)
                ])])]


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
        indicator = 'increase'
    else:
        symbol = down_tirangle
        c_name = 'down-triangle'
        indicator = 'decrease'
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
                html.Span(round(abs(change_to_tomorrow), 2)),
                html.Span(className='tooltiptext', children=[
                    """Worldwide growth factor. Percentage growth of confirmed cases. \n{} is the {} growth rate  in the past 24 hours.""".format(
                        symbol, indicator), html.Br(),
                    html.I(className='wi wi-wind {}'.format(class_name)),
                    " is the predicted {} growth rate in the next 24 hours".format(indicator)
                ])])]


def get_relative_card():
    sub_df = MASTER_ALL.reset_index().set_index(['forcast'])
    sub_df = sub_df[sub_df['country'] == 'worldwide']
    sub_diff = sub_df[['per_capita_confirmed', 'per_capita_deaths']].diff()
    latest_capita = sub_df.loc[False].iloc[-1]['per_capita_confirmed']
    yesterday = sub_df.loc[False].iloc[-2]['per_capita_confirmed']
    seven_days = sub_df.loc[True].iloc[0]['per_capita_confirmed']
    latest_capita = "1 in {} ".format(int(1/latest_capita))
    yesterday = "1 in {} ".format(int(1/yesterday))
    seven_days = "1 in {} ".format(int(1/seven_days))
    # forcast_seven_days = sub_diff.loc[True].iloc[0]  # .sum()
    # total_cases = "{:,}".format(int(total_confirmed['confirmed']))
    # change_in_cases = "{:,} ".format(int(twenty_four_confirmed['confirmed']))
    # forcast_seven = "{:,}".format(int(forcast_seven_days['confirmed']))
    return [html.H3('Per Capita'),
            html.P(id='total-cases', children=latest_capita),
            html.Div(className='change-card', children=[
                html.Span(children=[
                    up_triangle]),
                html.Span(yesterday),
                html.Span(html.I(className="wi wi-wind wi-towards-nne")),
                html.Span(seven_days),
                html.Span(className='tooltiptext', children=[
                    """Worldwide cases per global population. \n{} is the increase in per capita cases in the past 24 hours.""".format(
                        up_triangle), html.Br(),
                    html.I(className='wi wi-wind wi-towards-nne'),
                    " is the predicted increase in per capita cases in the next 24 hours"
                ])])]


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

        # print(relative_check)

        # Date INT comes from the slider and can only return integers:
        official_date = DATE_MAPPER.iloc[date_value]['Date']
        # print(official_date)
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

    @app.callback(Output('table-div', 'children'),
                  [Input('dropdown_container', 'value'),
                   Input('tabs-table-values', 'value')])
    def render_table(values, tab):
        data_entries = []
        # print(tab, tab.strip() == 'deaths_tab')
        last_date = MASTER_ALL.reset_index().groupby('forcast').tail(1)['Date'].iloc[0]
        forcast_date = MASTER_ALL.reset_index().groupby('forcast').tail(1)['Date'].iloc[-1]
        for value in values:
            # print(value)
            sort_me = ['Date', 'Location']
            sub_df = MASTER_ALL.reset_index()
            sub_df = sub_df[sub_df['PID'] == value]
            sub_df = sub_df.set_index('Date')
            entry = {'Date': last_date.strftime('%D'),
                     'Location': sub_df['Text_Confirmed'].str.split('<br>').str.get(0).iloc[0]}
            if tab != 'deaths_tab':
                metric = 'confirmed'
            else:
                metric = 'deaths'

            confirmed = sub_df.loc[last_date, metric]
            confirmed_24 = sub_df[metric].diff().loc[last_date]
            confirmed_tomorrow = sub_df[metric].diff().loc[last_date+timedelta(days=1)]
            confirmed_seven_days = sub_df[metric].diff().loc[last_date:last_date+timedelta(days=7)].sum()
            growth_rate = sub_df[metric].pct_change().loc[last_date]
            growth_rate_seven = sub_df[metric].pct_change().loc[last_date+timedelta(days=7)]
            realtive_risk = int(1/sub_df.loc[last_date, 'per_capita_{}'.format(metric)])
            entry['Confirmed'] = int(confirmed)
            entry['New'] = "+{:,}".format(int(confirmed_24))
            entry['+1 Day'] = "+{:,}".format(int(confirmed_tomorrow))
            entry['+7 Days'] = "+{:,}".format(int(confirmed_seven_days))
            entry['Relative'] = "1 in {:,}".format(realtive_risk)
            entry['Growth Rate'] = "{}%".format(round(growth_rate*100, 2))
            entry['+7 Days GR'] = "{}%".format(round(round(growth_rate_seven*100,
                                                           2) - round(growth_rate*100, 2), 2))

            data_entries.append(entry)
        df = pd.DataFrame(data_entries)
        df = df[sort_me + [i for i in df.columns if i not in sort_me]]
        df = df.fillna('-')
        df = df.sort_values('Confirmed')[::-1]
        df['Confirmed'] = df.apply(lambda x: "{:,}".format(x['Confirmed']), axis=1)
        return dash_table.DataTable(id='dash-table',
                                    columns=[{'name': i, 'id': i}
                                             for i in df.columns],
                                    style_header={
                                        'backgroundColor': "#2D3142",
                                        'color': 'white'},
                                    style_cell={
                                        'backgroundColor': "#4F5D75",
                                        'color': 'white',
                                        'font-family': 'Fira Sans'},
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
