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
        DATE_MAPPER = pd.DataFrame(MASTER_ALL.index.get_level_values('Date').unique())
        KEY_VALUE = dict(zip(list(MASTER_PID.index), list(
            MASTER_PID['Text_Confirmed'].str.split('<br>').str.get(0).str.replace('US', 'United States'))))
        KEY_VALUE = pd.DataFrame(list(KEY_VALUE.values()), index=KEY_VALUE.keys(), columns=['name'])

        if ret:
            return MASTER_ALL, MASTER_PID, DATE_MAPPER
        else:
            return

    # COUNTRY
    JHU_DF_AGG_COUNTRY = pd.read_csv(
        'https://jordansdatabucket.s3-us-west-2.amazonaws.com/covid19data/JHU_DF_AGG_COUNTRY.csv.gz', index_col=0, parse_dates=['Date'])
    JHU_DF_AGG_COUNTRY['granularity'] = 'country'
    JHU_DF_AGG_COUNTRY['Text_Confirmed'] = JHU_DF_AGG_COUNTRY['forcast'].apply(lambda x: "" if not x else "**Predicted**<br>") + JHU_DF_AGG_COUNTRY['country'] + "<br> Total Cases: " + JHU_DF_AGG_COUNTRY['confirmed'].apply(
        lambda x: "{:,}".format(int(x)))
    JHU_DF_AGG_COUNTRY['Text_Deaths'] = JHU_DF_AGG_COUNTRY['forcast'].apply(lambda x: "" if not x else "**Predicted**<br>") + JHU_DF_AGG_COUNTRY['country'] + "<br> Total Deaths: " + JHU_DF_AGG_COUNTRY['deaths'].apply(
        lambda x: "{:,}".format(int(x)))

    # Province
    JHU_DF_AGG_PROVINCE = pd.read_csv(
        'https://jordansdatabucket.s3-us-west-2.amazonaws.com/covid19data/JHU_DF_AGG_PROVINCE.csv.gz', index_col=0, parse_dates=['Date'])
    JHU_DF_AGG_PROVINCE['granularity'] = 'province'
    JHU_DF_AGG_PROVINCE['Text_Confirmed'] = JHU_DF_AGG_PROVINCE['forcast'].apply(lambda x: "" if not x else "**Predicted**<br>") + JHU_DF_AGG_PROVINCE['province'] + ", " + JHU_DF_AGG_PROVINCE['country'] + "<br> Total Cases: " + JHU_DF_AGG_PROVINCE['confirmed'].apply(
        lambda x: "{:,}".format(int(x)))
    JHU_DF_AGG_PROVINCE['Text_Deaths'] = JHU_DF_AGG_PROVINCE['forcast'].apply(lambda x: "" if not x else "**Predicted**<br>") + JHU_DF_AGG_PROVINCE['province'] + ", " + JHU_DF_AGG_PROVINCE['country'] + "<br> Total Deaths: " + JHU_DF_AGG_PROVINCE['deaths'].apply(
        lambda x: "{:,}".format(int(x)))

    # State
    CSBS_DF_AGG_STATE = pd.read_csv(
        'https://jordansdatabucket.s3-us-west-2.amazonaws.com/covid19data/CSBS_DF_AGG_STATE.csv.gz', index_col=0, parse_dates=['Date'])
    # CSBS_DF_AGG_STATE.rename({'state':'province'},axis=1 ,inplace=True)
    CSBS_DF_AGG_STATE['granularity'] = 'state'
    CSBS_DF_AGG_STATE['Text_Confirmed'] = CSBS_DF_AGG_STATE['forcast'].apply(lambda x: "" if not x else "**Predicted**<br>") + CSBS_DF_AGG_STATE['state'] + ", " + CSBS_DF_AGG_STATE['country'] + "<br> Total Cases: " + CSBS_DF_AGG_STATE['confirmed'].apply(
        lambda x: "{:,}".format(int(x)))
    CSBS_DF_AGG_STATE['Text_Deaths'] = CSBS_DF_AGG_STATE['forcast'].apply(lambda x: "" if not x else "**Predicted**<br>") + CSBS_DF_AGG_STATE['state'] + ", " + CSBS_DF_AGG_STATE['country'] + "<br> Total Deaths: " + CSBS_DF_AGG_STATE['deaths'].apply(
        lambda x: "{:,}".format(int(x)))

    # County
    CSBS_DF_AGG_COUNTY = pd.read_csv(
        'https://jordansdatabucket.s3-us-west-2.amazonaws.com/covid19data/CSBS_DF_AGG_COUNTY.csv.gz', index_col=0, parse_dates=['Date'])
    CSBS_DF_AGG_COUNTY['granularity'] = 'county'
    CSBS_DF_AGG_COUNTY['Text_Confirmed'] = CSBS_DF_AGG_COUNTY['forcast'].apply(lambda x: "" if not x else "**Predicted**<br>") + CSBS_DF_AGG_COUNTY['county'] + ", " + CSBS_DF_AGG_COUNTY['province'] + "<br> Total Cases: " + CSBS_DF_AGG_COUNTY['confirmed'].apply(
        lambda x: "{:,}".format(int(x)))
    CSBS_DF_AGG_COUNTY['Text_Deaths'] = CSBS_DF_AGG_COUNTY['forcast'].apply(lambda x: "" if not x else "**Predicted**<br>") + CSBS_DF_AGG_COUNTY['county'] + ", " + CSBS_DF_AGG_COUNTY['province'] + "<br> Total Deaths: " + CSBS_DF_AGG_COUNTY['deaths'].apply(
        lambda x: "{:,}".format(int(x)))

    # Master df has all our entries with
    master_df = pd.concat([JHU_DF_AGG_COUNTRY, JHU_DF_AGG_PROVINCE, CSBS_DF_AGG_STATE, CSBS_DF_AGG_COUNTY])

    columns = ['Date', 'country', 'province', 'state', 'county', 'granularity']
    master_df = master_df[columns+[i for i in master_df.columns if i not in columns]
                          ].reset_index(drop=True).fillna('N/A')

    worldwide_df = master_df[master_df['granularity'] == 'country'].groupby(['Date', 'forcast']).sum().reset_index()
    worldwide_df['country'] = 'worldwide'
    worldwide_df['Text_Confirmed'] = 'Worldwide <br>'
    master_df = master_df.append(worldwide_df).reset_index(drop=True)
    # For latest date, the dataframes we merged each have a different last reported date (CSBS is faster than JHU), so we have to groupby and ask the minmal date from each gruop
    latest_date = master_df[master_df['forcast'] == False].groupby('granularity').tail(1)['Date'].min()

    # Master_latest has all our entries in it and thus should be used by everything.
    master_latest = master_df[master_df['Date'] == latest_date].reset_index(drop=True)

    pid = ['country', 'province', 'state', 'county', 'granularity']
    assert(len(master_latest) == len(master_df[master_df['Date'] == latest_date].groupby(pid)))

    # Now join the master df with the pID number from the latest
    master_pid = master_latest.reset_index().set_index(pid).rename({'index': 'pid'}, axis=1)
    master_df = master_df.set_index(pid).join(master_pid['pid']).reset_index().set_index(['pid', 'Date']).sort_index()

    # Finally, set the pid back as the index
    master_latest = master_pid.reset_index().set_index('pid')

    # Master Latest has all the entries at the latest non forcast date. The index is the pID
    # Master DF has all the entries with all dates. The index is the pID and Date
    MASTER_PID = master_latest
    MASTER_ALL = master_df

    # Those predictions which are less than 0
    MASTER_ALL.loc[MASTER_ALL['confirmed'] < 0, 'confirmed'] = 0.0
    MASTER_ALL.loc[MASTER_ALL['deaths'] < 0, 'deaths'] = 0.0

    max_size = 1500

    bins, ret_bins = pd.qcut(MASTER_ALL[(MASTER_ALL['confirmed'] >= 1) & (MASTER_ALL['country'] != 'worldwide')]['confirmed'], q=[
        0, .5, 0.6, 0.70, 0.75, 0.8, 0.85, 0.9, 0.95, 0.999, 1], duplicates='drop', retbins=True)
    yellows = ["#606056", "#6e6e56", "#7b7c55", "#898a54", "#979953",
               "#a5a850", "#b4b74d", "#c3c649", "#d2d643", "#e2e53c"]
    reds = ["#5a4f4f", "#704d4d", "#854b4a", "#994746", "#ac4340",
            "#be3c3a", "#cf3531", "#e02a27", "#f01c19", "#ff0000"]
    labels = np.geomspace(1, max_size, num=len(ret_bins)-1)
    MASTER_ALL['CSize'] = pd.cut(MASTER_ALL['confirmed'], bins=ret_bins, labels=labels).astype(float).fillna(0)
    MASTER_ALL['DSize'] = pd.cut(MASTER_ALL['deaths'], bins=ret_bins, labels=labels).astype(float).fillna(0)
    MASTER_ALL['CColor'] = pd.cut(MASTER_ALL['confirmed'], bins=ret_bins,
                                  labels=yellows).astype(str).replace({'nan': 'white'})
    MASTER_ALL['DColor'] = pd.cut(MASTER_ALL['deaths'], bins=ret_bins,
                                  labels=reds).astype(str).replace({'nan': 'white'})
    DATE_MAPPER = pd.DataFrame(MASTER_ALL.index.get_level_values('Date').unique())

    KEY_VALUE = dict(zip(list(MASTER_PID.index), list(
        MASTER_PID['Text_Confirmed'].str.split('<br>').str.get(0).str.replace('US', 'United States'))))
    KEY_VALUE = pd.DataFrame(list(KEY_VALUE.values()), index=KEY_VALUE.keys(), columns=['name'])

    if ret:
        return MASTER_ALL, MASTER_PID, DATE_MAPPER


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
    return ""
    total_cases = "{:,}".format(JHU_RECENT['confirmed'].sum())
    change_in_cases = "{:,}".format(
        int(JHU_TIME.groupby('Date').sum().diff().iloc[-1]['confirmed']))
    return [html.H3('Total Cases'),
            html.P(id='total-cases', children=total_cases),
            html.Div(className='change-card', children=[html.Span(className='up-triangle=', children=up_triangle), html.Span(change_in_cases)])]


def get_total_deaths():
    return ""
    total_cases = "{:,}".format(JHU_RECENT['deaths'].sum())
    change_in_cases = "{:,}".format(
        int(JHU_TIME.groupby('Date').sum().diff().iloc[-1]['deaths']))
    return [html.H3('Total Deaths'),
            html.P(id='total-deaths', children=total_cases),
            html.Div(className='change-card', children=[html.Span(className='up-triangle=', children=up_triangle), html.Span(change_in_cases)])]


def get_mortality_rate():
    return ""
    gb = JHU_TIME.groupby('Date').sum()
    mortality_rate_today = (gb['deaths']/gb['confirmed']).iloc[-1] * 100
    mortality_rate_yesterday = (gb['deaths']/gb['confirmed']).iloc[-2] * 100
    change_in_mortality_rate = round(
        mortality_rate_today - mortality_rate_yesterday, 2)
    if change_in_mortality_rate > 0:
        symbol = up_triangle
        c_name = 'up-triangle'
    else:
        symbol = down_tirangle
        c_name = 'down-triangle'
    return [html.H3('Mortality Rate'),
            html.P(id='mortality-rate',
                   children="{}%".format(round(mortality_rate_today, 2))),
            html.Div(
                className='change-card',
                children=[
                    html.Span(className=c_name, children=symbol),
                    html.Span("{}%".format(abs(change_in_mortality_rate)))])]


def get_growth_rate():
    return ""
    gb = JHU_TIME.groupby('Date').sum()
    todays_gf = gb.pct_change()['confirmed'].iloc[-1]*100
    yesterrday_gf = gb.pct_change()['confirmed'].iloc[-2]*100
    change_in_gf = todays_gf - yesterrday_gf
    todays_gf = round(todays_gf, 2)
    change_in_gf = round(change_in_gf, 2)
    if change_in_gf > 0:
        symbol = up_triangle
        c_name = 'up-triangle'
    else:
        symbol = down_tirangle
        c_name = 'down-triangle'
    return [html.H3('Growth Rate'),
            html.P(id='growth-rate',
                   children="{}%".format(todays_gf)),
            html.Div(
            className='change-card',
            children=[
                html.Span(className=c_name, children=symbol),
                html.Span("{}%".format(abs(change_in_gf)))])]


def get_dropdown_options():
    key_values = dict(zip(list(MASTER_PID.index), list(MASTER_PID['Text_Confirmed'].str.split('<br>').str.get(0))))
    return [{'label': key_values[x].replace('US', 'United States'), 'value':x} for x in key_values]


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
        print(ctx.triggered)
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
         Input("check-metrics", "value")],
        [State("map", 'figure'),
         State("map", "relayoutData")]
    )
    def render_map(date_value, locations_values, metrics_values, figure, relative_layout):
        return get_dummy_map()

        # Date INT comes from the slider and can only return integers:
        official_date = DATE_MAPPER.iloc[date_value]['Date']

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

        if 'country' not in locations_values:
            plotting_df = plotting_df[~plotting_df['granularity'] == 'country']

        if 'province' in locations_values:
            plotting_df = plotting_df[~plotting_df['granularity'].isin(['state', 'province'])]

        if 'county' in locations_values:
            plotting_df = plotting_df[~plotting_df['granularity'] == 'county']

        # print(plotting_df)
        # return get_dummy_map()
        return plots.plot_map(plotting_df, metrics_values, zoom, center)

    # @app.callback(Output('content-readout', 'figure'),
    #               [Input('dropdown_container', 'value'),
    #                Input('tabs-values', 'value'),
    #                Input('log-check', 'value'),
    #                Input('deaths-confirmed', 'value')])
    def render_tab_content(values, tabs, log, metric):
        if log == 'log':
            log = True
        else:
            log = False
        if tabs == 'total_cases_graph':
            # print(values, tabs)
            return plots.total_confirmed_graph(values, JHU_DF_AGG_COUNTRY, JHU_DF_AGG_PROVINCE, CSBS_DF_AGG_STATE, CSBS_DF_AGG_COUNTY, log, metric)
        elif tabs == 'per_day_cases':
            return plots.per_day_confirmed(values, JHU_DF_AGG_COUNTRY, JHU_DF_AGG_PROVINCE, CSBS_DF_AGG_STATE, CSBS_DF_AGG_COUNTY, log, metric)
        elif tabs == 'exponential':
            return plots.plot_exponential(values, JHU_DF_AGG_COUNTRY, JHU_DF_AGG_PROVINCE, CSBS_DF_AGG_STATE, CSBS_DF_AGG_COUNTY, log)
        elif tabs == 'gr':
            return plots.per_gr(values, JHU_DF_AGG_COUNTRY, JHU_DF_AGG_PROVINCE, CSBS_DF_AGG_STATE, CSBS_DF_AGG_COUNTY, log, metric)

    # @app.callback(Output('table-container', 'children'),
    #               [Input('dropdown_container', 'value')])
    def render_table(values):
        date = JHU_RECENT['Date_text'].iloc[0]
        data_entries = []
        for value in values:
            if value.split('_')[0] == 'worldwide':
                # confirmed, deaths = JHU_RECENT.sum()[['confirmed', 'deaths']]
                gb = JHU_TIME.groupby(['Date_text', 'Date']).sum()
                # 0 index will be date text
                date = gb.index[-1][0]
                confirmed, deaths = gb.iloc[-1][['confirmed', 'deaths']]
                confirmed_24, deaths_24 = gb.diff(
                ).iloc[-1][['confirmed', 'deaths']]
                print(confirmed_24, deaths_24)
                data_entries.append(
                    {'Date': date, 'Country': 'Worldwide',
                     'Province/State': 'N/A',
                     'County': 'N/A',
                     'Total Confirmed': "{:,}".format(int(confirmed)),
                     'Confirmed 24h': "+{:,}".format(int(confirmed_24)),
                     'Total Deaths': "{:,}".format(int(deaths)),
                     'Deaths 24h': "+{:,}".format(int(deaths_24))})
                continue
            else:
                sub_category = value.split('_')[0]
                location = value.split('_')[1].split(':')[0]
                parent = value.split('_')[1].split(':')[-1]
                if sub_category == 'COUNTRY':
                    sub_df = JHU_TIME[JHU_TIME['country'] == location]
                    gb = sub_df.groupby(['Date_text', 'Date']).sum()
                    date = gb.index[-1][0]
                    confirmed, deaths = gb.iloc[-1][['confirmed', 'deaths']]
                    confirmed_24, deaths_24 = gb.diff(
                    ).iloc[-1][['confirmed', 'deaths']]
                    print(confirmed_24, deaths_24)
                    data_entries.append({
                        'Date': date,
                        'Country': location,
                        'Province/State': 'N/A',
                        'County': 'N/A',
                        'Total Confirmed': "{:,}".format(int(confirmed)),
                        'Confirmed 24h': "+{:,}".format(int(confirmed_24)),
                        'Total Deaths': "{:,}".format(int(deaths)),
                        'Deaths 24h': "+{:,}".format(int(deaths_24))})
                    continue
                elif sub_category == 'PROVINCE':
                    gb = JHU_TIME[(JHU_TIME['province'] == location) & (JHU_TIME['country'] == parent)].groupby(
                        ['Date_text', 'Date', 'country', 'province']).sum()
                    date = gb.index[-1][0]
                    confirmed, deaths = gb.iloc[-1][['confirmed', 'deaths']]
                    confirmed_24, deaths_24 = gb.diff(
                    ).iloc[-1][['confirmed', 'deaths']]
                    # print(confirmed_24, deaths_24)
                    data_entries.append({
                        'Date': date,
                        'Country': parent,
                        'Province/State': location,
                        'County': 'N/A',
                        'Total Confirmed': "{:,}".format(int(confirmed)),
                        'Confirmed 24h': "+{:,}".format(int(confirmed_24)),
                        'Total Deaths': "{:,}".format(int(deaths)),
                        'Deaths 24h': "+{:,}".format(int(deaths_24))})

                    continue
                elif sub_category == 'STATE':
                    gb = CSBS[(CSBS['province'] == location) & (CSBS['country'] == parent)].groupby(
                        ['Date_text', 'Date']).sum()
                    date = gb.index[-1][0]
                    confirmed, deaths = gb.iloc[-1][['confirmed', 'deaths']]
                    confirmed_24, deaths_24 = gb.diff(
                    ).iloc[-1][['confirmed', 'deaths']]
                    # print(confirmed_24, deaths_24)
                    data_entries.append({
                        'Date': date,
                        'Country': parent,
                        'Province/State': location,
                        'County': 'N/A',
                        'Total Confirmed': "{:,}".format(int(confirmed)),
                        'Confirmed 24h': "+{:,}".format(int(confirmed_24)),
                        'Total Deaths': "{:,}".format(int(deaths)),
                        'Deaths 24h': "+{:,}".format(int(deaths_24))})
                elif sub_category == 'COUNTY':
                    gb = CSBS[(CSBS['county'] == location) & (CSBS['province'] == parent)].groupby(
                        ['Date_text', 'Date', 'country', 'province', 'county']).sum()
                    date = gb.index[-1][0]
                    country = gb.index[-1][2]
                    province = gb.index[-1][3]
                    confirmed, deaths = gb.iloc[-1][['confirmed', 'deaths']]
                    confirmed_24, deaths_24 = gb.diff(
                    ).iloc[-1][['confirmed', 'deaths']]
                    # print(confirmed_24, deaths_24)
                    data_entries.append({
                        'Date': date,
                        'Country': country,
                        'Province/State': province,
                        'County': location,
                        'Total Confirmed': "{:,}".format(int(confirmed)),
                        'Confirmed 24h': "+{:,}".format(int(confirmed_24)),
                        'Total Deaths': "{:,}".format(int(deaths)),
                        'Deaths 24h': "+{:,}".format(int(deaths_24))})
                else:
                    raise Exception("YOu done fucked up")
        df = pd.DataFrame(data_entries)

        # df = df[['Date', 'Country', 'Province/State',
        #          'County', 'Confirmed', 'Confirmed 24h', 'Deaths']]
        return dash_table.DataTable(id='table',
                                    columns=[{'name': i, 'id': i}
                                             for i in df.columns],
                                    style_header={
                                        'backgroundColor': 'rgb(30, 30, 30)',
                                        'color': 'white'},
                                    style_cell={
                                        'color': 'black'},
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
        # options = pd.DataFrame(dropdown_options)

        # # print(options)
        # new_loc = clickData['points'][0]['customdata']
        # if new_loc not in dropdown_selected:
        #     if new_loc not in list(options['value']):
        #         raise Exception(
        #             'new location {} does not exists in dropdown'.format(new_loc))
        #     dropdown_selected.append(new_loc)
        # else:
        #     print('already here {}'.format(new_loc))

        # return dropdown_selected

    @app.callback(Output('map-title', 'children'),
                  [Input('date_slider', 'value')])
    def update_map_title(date_int):
        "Reported Infections Map"
        official_date = DATE_MAPPER.iloc[date_int]['Date']
        if official_date.date() == date.today() - timedelta(days=1):
            return "Yesterday"
        if official_date.date() >= date.today():
            return "{} Prediciton**".format(official_date.strftime('%B %d, %Y'))

        return "{}".format(official_date.strftime('%B %d, %Y'))
