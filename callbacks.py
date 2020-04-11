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


def serve_data(ret=False):
    global JHU_RECENT
    global DATE_MAPPER
    global JHU_TIME
    global CSBS
    global CENTROID_MAPPER
    global MERGED_CSBS_JHU
    global JHU_DF_AGG_COUNTRY
    global JHU_DF_AGG_PROVINCE
    global CSBS_DF_AGG_STATE
    global CSBS_DF_AGG_COUNTY
    global MAX_CONFIRMED

    jhu_df = pd.read_csv(
        'https://jordansdatabucket.s3-us-west-2.amazonaws.com/covid19data/jhu_df.csv.gz', index_col=0)
    jhu_df_time = pd.read_csv(
        'https://jordansdatabucket.s3-us-west-2.amazonaws.com/covid19data/jhu_df_time.csv.gz', index_col=0)
    csbs_df = pd.read_csv(
        'https://jordansdatabucket.s3-us-west-2.amazonaws.com/covid19data/csbs_df.csv.gz', index_col=0)

    jhu_df_time['Date'] = pd.to_datetime(jhu_df_time['Date'])
    jhu_df['Date'] = pd.to_datetime(jhu_df['Date'])
    csbs_df['Date'] = pd.to_datetime(csbs_df['Date'])

    # JHU and CSBS are out of sync, so we should use the latest date from JHU
    latest_date = jhu_df_time.sort_values('Date')['Date'].iloc[-1]
    merge = pd.concat([jhu_df, csbs_df[csbs_df['Date'] == latest_date]])
    merge = merge.fillna('')

    # Countries without a code may be a problem
    problem_countries = merge[merge['country_code'] == '']['country'].tolist()

    # I know for a fact Namibia has no coud
    merge.loc[merge['country'] == 'Namibia', 'country_code'] = ''

    # Lets grab the centroids from this great spread sheet
    centroid_mapper = pd.read_csv('./country_centroids_az8.csv')
    problem_states = merge[~merge['country_code'].isin(
        centroid_mapper['iso_a2'])]
    new_merge = merge.merge(
        centroid_mapper, left_on='country_code', right_on='iso_a2')

    # If something is has the same name for continent and subregion, lets just add the word _subregion
    new_merge.loc[new_merge['continent'] == new_merge['subregion'],
                  'subregion'] = new_merge['subregion'] + ' Subregion'

    # # Lets remove the US Data since we are doubel counting htis by merging CSBSS
    new_merge_no_us = new_merge[~((new_merge['country'] == 'US') & (
        new_merge['province'] == ''))]
    MERGED_CSBS_JHU = new_merge
    JHU_TIME = jhu_df_time
    JHU_RECENT = jhu_df
    CSBS = csbs_df
    CENTROID_MAPPER = centroid_mapper

    JHU_DF_AGG_COUNTRY = pd.read_csv(
        'https://jordansdatabucket.s3-us-west-2.amazonaws.com/covid19data/JHU_DF_AGG_COUNTRY.csv.gz', index_col=0, parse_dates=['Date'])

    JHU_DF_AGG_PROVINCE = pd.read_csv(
        'https://jordansdatabucket.s3-us-west-2.amazonaws.com/covid19data/JHU_DF_AGG_PROVINCE.csv.gz', index_col=0, parse_dates=['Date'])

    CSBS_DF_AGG_STATE = pd.read_csv(
        'https://jordansdatabucket.s3-us-west-2.amazonaws.com/covid19data/CSBS_DF_AGG_STATE.csv.gz', index_col=0, parse_dates=['Date'])

    CSBS_DF_AGG_COUNTY = pd.read_csv(
        'https://jordansdatabucket.s3-us-west-2.amazonaws.com/covid19data/CSBS_DF_AGG_COUNTY.csv.gz', index_col=0, parse_dates=['Date'])

    # Bin Data right here based on the confirmed cases including predictions
    bin_me = JHU_DF_AGG_COUNTRY[JHU_DF_AGG_COUNTRY['confirmed']
                                >= 1]['confirmed']
    bins, ret_bins = pd.qcut(bin_me, q=[
                             0, .5, 0.6, 0.70, 0.75, 0.8, 0.85, 0.9, 0.95, 0.999, 1], duplicates='drop', retbins=True)
    yellows = ["#606056", "#6e6e56", "#7b7c55", "#898a54", "#979953",
               "#a5a850", "#b4b74d", "#c3c649", "#d2d643", "#e2e53c"]
    reds = ["#5a4f4f", "#704d4d", "#854b4a", "#994746", "#ac4340",
            "#be3c3a", "#cf3531", "#e02a27", "#f01c19", "#ff0000"]

    max_size = 500
    labels = np.geomspace(1, 5000, num=len(ret_bins)-1)
    JHU_DF_AGG_COUNTRY['CSize'] = pd.cut(
        JHU_DF_AGG_COUNTRY['confirmed'], bins=ret_bins, labels=labels).astype(float).fillna(0)
    JHU_DF_AGG_PROVINCE['CSize'] = pd.cut(
        JHU_DF_AGG_PROVINCE['confirmed'], bins=ret_bins, labels=labels).astype(float).fillna(0)
    CSBS_DF_AGG_STATE['CSize'] = pd.cut(
        CSBS_DF_AGG_STATE['confirmed'], bins=ret_bins, labels=labels).astype(float).fillna(0)
    CSBS_DF_AGG_COUNTY['CSize'] = pd.cut(
        CSBS_DF_AGG_COUNTY['confirmed'], bins=ret_bins, labels=labels).astype(float).fillna(0)

    JHU_DF_AGG_COUNTRY['CColor'] = pd.cut(
        JHU_DF_AGG_COUNTRY['confirmed'], bins=ret_bins, labels=yellows).astype(str).replace({'nan': 'white'})
    JHU_DF_AGG_PROVINCE['CColor'] = pd.cut(
        JHU_DF_AGG_PROVINCE['confirmed'], bins=ret_bins, labels=yellows).astype(str).replace({'nan': 'white'})
    CSBS_DF_AGG_STATE['CColor'] = pd.cut(
        CSBS_DF_AGG_STATE['confirmed'], bins=ret_bins, labels=yellows).astype(str).replace({'nan': 'white'})
    CSBS_DF_AGG_COUNTY['CColor'] = pd.cut(
        CSBS_DF_AGG_COUNTY['confirmed'], bins=ret_bins, labels=yellows).astype(str).replace({'nan': 'white'})

    JHU_DF_AGG_COUNTRY['DSize'] = pd.cut(
        JHU_DF_AGG_COUNTRY['deaths'], bins=ret_bins, labels=labels).astype(float).fillna(0)
    JHU_DF_AGG_PROVINCE['DSize'] = pd.cut(
        JHU_DF_AGG_PROVINCE['deaths'], bins=ret_bins, labels=labels).astype(float).fillna(0)
    CSBS_DF_AGG_STATE['DSize'] = pd.cut(
        CSBS_DF_AGG_STATE['deaths'], bins=ret_bins, labels=labels).astype(float).fillna(0)
    CSBS_DF_AGG_COUNTY['DSize'] = pd.cut(
        CSBS_DF_AGG_COUNTY['deaths'], bins=ret_bins, labels=labels).astype(float).fillna(0)

    JHU_DF_AGG_COUNTRY['DColor'] = pd.cut(
        JHU_DF_AGG_COUNTRY['deaths'], bins=ret_bins, labels=reds).astype(str).replace({'nan': 'white'})
    JHU_DF_AGG_PROVINCE['DColor'] = pd.cut(
        JHU_DF_AGG_PROVINCE['deaths'], bins=ret_bins, labels=reds).astype(str).replace({'nan': 'white'})
    CSBS_DF_AGG_STATE['DColor'] = pd.cut(
        CSBS_DF_AGG_STATE['deaths'], bins=ret_bins, labels=reds).astype(str).replace({'nan': 'white'})
    CSBS_DF_AGG_COUNTY['DColor'] = pd.cut(
        CSBS_DF_AGG_COUNTY['deaths'], bins=ret_bins, labels=reds).astype(str).replace({'nan': 'white'})

    date_mapper = pd.DataFrame(
        JHU_DF_AGG_COUNTRY['Date'].unique(), columns=['Date'])
    date_mapper['Date_text'] = date_mapper['Date'].dt.strftime('%m/%d/%y')

    DATE_MAPPER = date_mapper
    MAX_CONFIRMED = max(JHU_DF_AGG_COUNTRY['confirmed'])

    if ret:
        return JHU_RECENT, JHU_TIME, CSBS, DATE_MAPPER


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
    total_cases = "{:,}".format(JHU_RECENT['confirmed'].sum())
    change_in_cases = "{:,}".format(
        int(JHU_TIME.groupby('Date').sum().diff().iloc[-1]['confirmed']))
    return [html.H3('Total Cases'),
            html.P(id='total-cases', children=total_cases),
            html.Div(className='change-card', children=[html.Span(className='up-triangle=', children=up_triangle), html.Span(change_in_cases)])]


def get_total_deaths():
    total_cases = "{:,}".format(JHU_RECENT['deaths'].sum())
    change_in_cases = "{:,}".format(
        int(JHU_TIME.groupby('Date').sum().diff().iloc[-1]['deaths']))
    return [html.H3('Total Deaths'),
            html.P(id='total-deaths', children=total_cases),
            html.Div(className='change-card', children=[html.Span(className='up-triangle=', children=up_triangle), html.Span(change_in_cases)])]


def get_mortality_rate():
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
    countries = [{'label': x, 'value': "COUNTRY_{0}:NONE".format(
        x)} for x in JHU_DF_AGG_COUNTRY['country'].unique()]
    countries.append({'label': 'Worldwide', 'value': 'worldwide'})
    provinces = [{'label': x, 'value': "PROVINCE_{0}:{1}".format(
        x, y)} for x, y in JHU_DF_AGG_PROVINCE.groupby(['province', 'country']).groups.keys()]
    state = [{'label': x, 'value': "STATE_{0}:{1}".format(
        x, y)} for x, y in CSBS_DF_AGG_STATE.groupby(['state', 'country']).groups.keys()]
    counties = [{'label': x+" County, "+y, 'value': "COUNTY_{0}:{1}".format(
        x, y)} for x, y in CSBS_DF_AGG_COUNTY.groupby(['county', 'province']).groups.keys()]
    # Post HOc Correciton
    for index in countries:
        if index['label'] == 'US':
            index['label'] = 'United States'

    return countries+provinces+state+counties


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


def get_dummy_map(id_):
    us_cities = pd.read_csv(
        "https://raw.githubusercontent.com/plotly/datasets/master/us-cities-top-1k.csv")
    fig = px.scatter_mapbox(us_cities, lat="lat", lon="lon", hover_name="City", hover_data=["State", "Population"],
                            color_discrete_sequence=["fuchsia"], zoom=3, height=300)
    fig.update_layout(mapbox_style="open-street-map")
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    return dcc.Graph(id=id_, figure=fig)


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

        # Date INT comes from the slider and can only return integers:
        official_date = DATE_MAPPER.iloc[date_value]['Date']

        JHU_COUNTRY = JHU_DF_AGG_COUNTRY[JHU_DF_AGG_COUNTRY['Date']
                                         == official_date]
        JHU_PROVINCE = JHU_DF_AGG_PROVINCE[JHU_DF_AGG_PROVINCE['Date']
                                           == official_date]
        CSBS_STATE = CSBS_DF_AGG_STATE[CSBS_DF_AGG_STATE['Date']
                                       == official_date]
        CSBS_COUNTY = CSBS_DF_AGG_COUNTY[CSBS_DF_AGG_COUNTY['Date']
                                         == official_date]

        prediction = False
        if (JHU_COUNTRY['forcast'] == True).all():
            prediction = True
        # Initialize empty
        plot_data_frame = pd.DataFrame()
        SUB_DF_COUNTRY = pd.DataFrame()
        SUB_DF_PROVINCE = pd.DataFrame()
        SUB_DF_COUNTY = pd.DataFrame()

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

        if 'country' in locations_values:
            SUB_DF_COUNTRY = JHU_COUNTRY.rename(
                {'country': 'location'}, axis=1)
            SUB_DF_COUNTRY['Text_Cases'] = 'Country: '+SUB_DF_COUNTRY['location'] + \
                '<br>Total Cases:' + \
                SUB_DF_COUNTRY['confirmed'].apply(
                    lambda x: "{:,}".format(int(x)))
            SUB_DF_COUNTRY['Text_Deaths'] = 'Country: '+SUB_DF_COUNTRY['location'] + \
                '<br>Total Deaths:' + \
                SUB_DF_COUNTRY['deaths'].apply(lambda x: "{:,}".format(int(x)))
            SUB_DF_COUNTRY['type'] = 'country'
            SUB_DF_COUNTRY['source'] = 'JHU'
            SUB_DF_COUNTRY['lookup'] = 'COUNTRY' + \
                "_"+SUB_DF_COUNTRY['location']+':NONE'

        if 'province' in locations_values:
            SUB_DF_PROVINCE = JHU_PROVINCE.rename(
                {'province': 'location'}, axis=1)
            SUB_DF_PROVINCE['Text_Cases'] = 'Province: '+SUB_DF_PROVINCE['location'] +\
                '<br>Total Cases:' +\
                SUB_DF_PROVINCE['confirmed'].apply(
                lambda x: "{:,}".format(int(x)))
            SUB_DF_PROVINCE['Text_Deaths'] = 'Province: '+SUB_DF_PROVINCE['location'] +\
                '<br>Total Deaths:' +\
                SUB_DF_PROVINCE['deaths'].apply(
                lambda x: "{:,}".format(int(x)))
            SUB_DF_PROVINCE['source'] = 'JHU'
            SUB_DF_PROVINCE['type'] = 'province'
            SUB_DF_PROVINCE['lookup'] = "PROVINCE"+"_" +\
                SUB_DF_PROVINCE['location']+':'+SUB_DF_PROVINCE['country']

            temp_df = CSBS_STATE.rename({'state': 'location'}, axis=1)
            temp_df['Text_Cases'] = 'State: '+temp_df['location']+'<br>Total Cases:' +\
                temp_df['confirmed'].apply(lambda x: "{:,}".format(int(x)))
            temp_df['Text_Deaths'] = 'State: '+temp_df['location'] +\
                '<br>Total Deaths:' +\
                temp_df['deaths'].apply(lambda x: "{:,}".format(int(x)))
            temp_df['source'] = 'CSBS'
            temp_df['type'] = 'state'
            temp_df['lookup'] = "STATE"+"_" +\
                temp_df['location']+':'+temp_df['country']
            SUB_DF_PROVINCE = SUB_DF_PROVINCE.append(temp_df)
            print(SUB_DF_PROVINCE.columns)

        if 'county' in locations_values:
            SUB_DF_COUNTY = CSBS_COUNTY.rename({'county': 'location'}, axis=1)
            SUB_DF_COUNTY['Text_Cases'] = 'County: '+SUB_DF_COUNTY['location'] +\
                '<br>Total Cases:' +\
                SUB_DF_COUNTY['confirmed'].apply(
                lambda x: "{:,}".format(int(x)))
            SUB_DF_COUNTY['Text_Deaths'] = 'County: '+SUB_DF_COUNTY['location'] +\
                '<br>Total Deaths:' +\
                SUB_DF_COUNTY['deaths'].apply(lambda x: "{:,}".format(int(x)))
            SUB_DF_COUNTY['source'] = 'CSBS'
            SUB_DF_COUNTY['type'] = 'county'
            SUB_DF_COUNTY['lookup'] = "COUNTY"+"_" +\
                SUB_DF_COUNTY['location']+':' + SUB_DF_COUNTY['province']

        plot_data_frame = pd.concat(
            [SUB_DF_COUNTRY, SUB_DF_PROVINCE, SUB_DF_COUNTY])
        plot_data_frame['Text_Cases'] = "Date - {}<br>".format(
            official_date.strftime('%B %d, %Y')) + plot_data_frame['Text_Cases']
        plot_data_frame['Text_Deaths'] = "Date - {}<br>".format(
            official_date.strftime('%B %d, %Y')) + plot_data_frame['Text_Deaths']

        if prediction:
            plot_data_frame['Text_Cases'] = plot_data_frame['Text_Cases'].str.replace(
                'Total', 'Predicted')
        # print('plot_dataframe', plot_data_frame)
        return plots.plot_map(plot_data_frame, metrics_values, zoom, center)

    @app.callback(Output('content-readout', 'figure'),
                  [Input('dropdown_container', 'value'),
                   Input('tabs-values', 'value'),
                   Input('log-check', 'value'),
                   Input('deaths-confirmed', 'value')])
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

    @app.callback(Output('table-container', 'children'),
                  [Input('dropdown_container', 'value')])
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

        options = pd.DataFrame(dropdown_options)

        # print(options)
        new_loc = clickData['points'][0]['customdata']
        if new_loc not in dropdown_selected:
            if new_loc not in list(options['value']):
                raise Exception(
                    'new location {} does not exists in dropdown'.format(new_loc))
            dropdown_selected.append(new_loc)
        else:
            print('already here {}'.format(new_loc))

        return dropdown_selected

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
