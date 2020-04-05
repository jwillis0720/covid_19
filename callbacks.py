import dash
import dash_core_components as dcc
import plotly.express as px
import plotly.colors
import pandas as pd
import plots
import dash_table
from datetime import date, timedelta
from dash.dependencies import Input, Output, State
from pprint import pprint

# Setting up Sizes and Colors
GREEN_TO_YELLOW = ['#808080', '#a19e79', '#c1bd70', '#e0dc63', '#fffd50']
ORANGE_TO_RED = ['#ffa500', '#ff8c00', '#ff7000', '#ff4e00', '#ff0000']
SIZES_BIN = [5, 10, 30, 60]
DEATHS_BIN = [1, 2, 100, 1000, 1000000]
CASES_BIN = [1, 10, 1000, 10000, 10000000]


def get_date_slider():
    how_many_labels = (len(DATE_MAPPER))//10
    marks = {k: {'label': v}
             for k, v in list(DATE_MAPPER['Date'].dt.strftime(
                 '%m/%d').to_dict().items())[::how_many_labels]}
    return dcc.Slider(
        id='date_slider',
        min=DATE_MAPPER.index[0],
        max=DATE_MAPPER.index[-1],
        step=1,
        value=DATE_MAPPER.index[-1],
        marks=marks
    )


def get_total_cases():
    return "{:,}".format(JHU_RECENT['confirmed'].sum())


def get_total_deaths():
    return "{:,}".format(JHU_RECENT['deaths'].sum())


def get_mortality_rate():
    return "{:.3}%".format(JHU_RECENT['deaths'].sum()/JHU_RECENT['confirmed'].sum()*100)


def get_growth_rate():
    x = JHU_TIME.groupby('Date').sum().pct_change()[
        'confirmed'][-10:].mean()
    return "{:.3}".format(1+x)


def get_dropdown():
    countries = [{'label': x, 'value': "COUNTRY_{0}".format(
        x)} for x in JHU_DF_AGG_COUNTRY['country'].unique()]
    countries.append({'label': 'Worldwide', 'value': 'worldwide'})
    provinces = [{'label': x, 'value': "PROVINCE_{0}".format(
        x)} for x in JHU_DF_AGG_PROVINCE['province'].unique()]
    state = [{'label': x, 'value': "STATE_{0}".format(
        x)} for x in CSBS_DF_AGG_STATE['state'].unique()]
    counties = [{'label': x+" County", 'value': "COUNTY_{0}".format(
        x)} for x in CSBS_DF_AGG_COUNTY['county'].unique()]

    # Post HOc Correciton
    for index in countries:
        if index['label'] == 'US':
            index['label'] = 'United States'

    dd = dcc.Dropdown(
        id='dropdown_container',
        options=countries+provinces+state+counties,
        value=['worldwide', 'COUNTRY_US', 'STATE_New York'],
        multi=True
    )
    return dd


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

    jhu_df = pd.read_csv(
        'https://jordansdatabucket.s3-us-west-2.amazonaws.com/covid19data/jhu_df.csv.gz', index_col=0)
    jhu_df_time = pd.read_csv(
        'https://jordansdatabucket.s3-us-west-2.amazonaws.com/covid19data/jhu_df_time.csv.gz', index_col=0)
    csbs_df = pd.read_csv(
        'https://jordansdatabucket.s3-us-west-2.amazonaws.com/covid19data/csbs_df.csv.gz', index_col=0)

    jhu_df_time['Date'] = pd.to_datetime(jhu_df_time['Date'])
    jhu_df['Date'] = pd.to_datetime(jhu_df['Date'])
    csbs_df['Date'] = pd.to_datetime(csbs_df['Date'])

    date_mapper = pd.DataFrame(
        jhu_df_time['Date'].unique(), columns=['Date'])
    date_mapper['Date_text'] = date_mapper['Date'].dt.strftime('%m/%d/%y')

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
    DATE_MAPPER = date_mapper
    CSBS = csbs_df
    CENTROID_MAPPER = centroid_mapper

    JHU_DF_AGG_COUNTRY = JHU_TIME.sort_values('confirmed')[::-1].groupby(['Date', 'country']).agg(
        {'lat': 'first', 'lon': 'first', 'confirmed': 'sum', 'deaths': 'sum'}).reset_index()

    JHU_DF_AGG_PROVINCE = JHU_TIME[JHU_TIME['province'] != ''].sort_values('confirmed')[::-1].groupby(['Date', 'province']).agg(
        {'lat': 'first', 'lon': 'first', 'confirmed': 'sum', 'deaths': 'sum'}).reset_index()

    CSBS_DF_AGG_STATE = CSBS[CSBS['province'] != ''].sort_values('confirmed')[::-1].groupby(['Date', 'province']).agg(
        {'lat': 'first', 'lon': 'first', 'confirmed': 'sum', 'deaths': 'sum'}).reset_index().rename({'province': 'state'}, axis=1)

    CSBS_DF_AGG_COUNTY = CSBS[CSBS['county'] != ''].sort_values('confirmed')[::-1].groupby(['Date', 'county']).agg(
        {'lat': 'first', 'lon': 'first', 'confirmed': 'sum', 'deaths': 'sum'}).reset_index()

    if ret:
        return JHU_RECENT, JHU_TIME, CSBS, DATE_MAPPER


def register_callbacks(app):
    # Learn more popup
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

        # If a person clicks learn more then the display turns to block
        # If anything else is clicked change the markdown to display:none
        if prop_id == "learn-more-button":
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
        pprint(relative_layout)

        # Date INT comes from the slider and can only return integers:
        official_date = DATE_MAPPER.iloc[date_value]['Date']

        # Lets trim down the dataframes
        JHU_TIME_DATE = JHU_TIME[JHU_TIME['Date'] == official_date]
        CSBS_TIME_DATE = CSBS[CSBS['Date'] == official_date]

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
            SUB_DF_COUNTRY = JHU_TIME_DATE.sort_values('confirmed')[::-1].groupby(['country']).agg(
                {'lat': 'first', 'lon': 'first', 'confirmed': 'sum', 'deaths': 'sum'}).reset_index().rename({'country': 'location'}, axis=1)
            SUB_DF_COUNTRY['Text_Cases'] = 'Country: '+SUB_DF_COUNTRY['location'] + \
                '<br>Total Cases:' + \
                SUB_DF_COUNTRY['confirmed'].apply(
                    lambda x: "{:,}".format(int(x)))
            SUB_DF_COUNTRY['Text_Deaths'] = 'Country: '+SUB_DF_COUNTRY['location'] + \
                '<br>Total Deaths:' + \
                SUB_DF_COUNTRY['deaths'].apply(lambda x: "{:,}".format(int(x)))
            SUB_DF_COUNTRY['type'] = 'country'
            SUB_DF_COUNTRY['source'] = 'JHU'

        if 'province' in locations_values:
            SUB_DF_PROVINCE = JHU_TIME_DATE[JHU_TIME_DATE['province'] != ''].sort_values('confirmed')[::-1].groupby(['province']).agg(
                {'lat': 'first', 'lon': 'first', 'confirmed': 'sum', 'deaths': 'sum'}).reset_index().rename({'province': 'location'}, axis=1)
            SUB_DF_PROVINCE['Text_Cases'] = 'Province: '+SUB_DF_PROVINCE['location'] + \
                '<br>Total Cases:' + \
                SUB_DF_PROVINCE['confirmed'].apply(
                    lambda x: "{:,}".format(int(x)))
            SUB_DF_PROVINCE['Text_Deaths'] = 'Province: '+SUB_DF_PROVINCE['location'] + \
                '<br>Total Deaths:' + \
                SUB_DF_PROVINCE['deaths'].apply(
                lambda x: "{:,}".format(int(x)))
            SUB_DF_PROVINCE['source'] = 'JHU'
            SUB_DF_PROVINCE['type'] = 'province'

            temp_df = CSBS_TIME_DATE[CSBS_TIME_DATE['province'] != ''].sort_values('confirmed')[::-1].groupby(['province']).agg(
                {'lat': 'first', 'lon': 'first', 'confirmed': 'sum', 'deaths': 'sum'}).reset_index().rename({'province': 'location'}, axis=1)

            temp_df['Text_Cases'] = 'State: '+temp_df['location']+'<br>Total Cases:' + \
                temp_df['confirmed'].apply(lambda x: "{:,}".format(int(x)))
            temp_df['Text_Deaths'] = 'State: '+temp_df['location'] + \
                '<br>Total Deaths:' + \
                temp_df['deaths'].apply(lambda x: "{:,}".format(int(x)))
            temp_df['source'] = 'CSBS'
            temp_df['type'] = 'state'
            SUB_DF_PROVINCE = SUB_DF_PROVINCE.append(temp_df)

        if 'county' in locations_values:
            SUB_DF_COUNTY = CSBS_TIME_DATE[CSBS_TIME_DATE['county'] != ''].sort_values('confirmed')[::-1].groupby(['county']).agg(
                {'lat': 'first', 'lon': 'first', 'confirmed': 'sum', 'deaths': 'sum'}).reset_index().rename({'county': 'location'}, axis=1)
            SUB_DF_COUNTY['Text_Cases'] = 'County: '+SUB_DF_COUNTY['location'] + \
                '<br>Total Cases:' + \
                SUB_DF_COUNTY['confirmed'].apply(
                    lambda x: "{:,}".format(int(x)))
            SUB_DF_COUNTY['Text_Deaths'] = 'County: '+SUB_DF_COUNTY['location'] + \
                '<br>Total Deaths:' + \
                SUB_DF_COUNTY['deaths'].apply(lambda x: "{:,}".format(int(x)))
            SUB_DF_COUNTY['source'] = 'CSBS'
            SUB_DF_COUNTY['type'] = 'county'

        plot_data_frame = pd.concat(
            [SUB_DF_COUNTRY, SUB_DF_PROVINCE, SUB_DF_COUNTY])
        if not plot_data_frame.empty:
            plot_data_frame['death_size'] = pd.cut(
                plot_data_frame['deaths'], bins=DEATHS_BIN, include_lowest=True, labels=SIZES_BIN)
            plot_data_frame['confirmed_size'] = pd.cut(
                plot_data_frame['confirmed'], bins=CASES_BIN, include_lowest=True, labels=SIZES_BIN)
            plot_data_frame['death_colors'] = plot_data_frame['death_size'].apply(
                lambda x: dict(zip(SIZES_BIN, ORANGE_TO_RED))[x])
            plot_data_frame['case_colors'] = plot_data_frame['confirmed_size'].apply(
                lambda x: dict(zip(SIZES_BIN, GREEN_TO_YELLOW))[x])

        return plots.plot_map(plot_data_frame, metrics_values, CASES_BIN, DEATHS_BIN, zoom, center)

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
            print(values, tabs)
            return plots.total_confirmed_graph(values, JHU_DF_AGG_COUNTRY, JHU_DF_AGG_PROVINCE, CSBS_DF_AGG_STATE, CSBS_DF_AGG_COUNTY, log, metric)
        elif tabs == 'per_day_cases':
            return plots.per_day_confirmed(values, JHU_DF_AGG_COUNTRY, JHU_DF_AGG_PROVINCE, CSBS_DF_AGG_STATE, CSBS_DF_AGG_COUNTY, log, metric)
        elif tabs == 'exponential':
            return plots.plot_exponential(values, JHU_DF_AGG_COUNTRY, JHU_DF_AGG_PROVINCE, CSBS_DF_AGG_STATE, CSBS_DF_AGG_COUNTY, log)

    @app.callback(Output('table-container', 'children'),
                  [Input('dropdown_container', 'value')])
    def render_table(values):
        date = JHU_RECENT['Date_text'].iloc[0]
        data_entries = []
        for value in values:
            sub_category = value.split('_')[0]
            # print(sub_category)
            if sub_category == 'worldwide':
                confirmed, deaths = JHU_RECENT.sum()[['confirmed', 'deaths']]
                data_entries.append(
                    {'Date': date, 'Country': 'Worldwide', 'Province/State': 'N/A', 'County': 'N/A', 'Confirmed': confirmed, 'Deaths': deaths})
                continue
            elif sub_category == 'COUNTRY':
                c = value.split('_')[1]
                sub_df = JHU_RECENT[JHU_RECENT['country'] == c]
                data_entries.append(
                    {'Date': date, 'Country': c, 'Province/State': 'N/A', 'County': 'N/A', 'Confirmed': sub_df['confirmed'], 'Deaths': sub_df['deaths']})
                continue
            elif sub_category == 'PROVINCE':
                c = value.split('_')[1]
                drint('province')
                sub_df = JHU_RECENT[JHU_RECENT['province'] == c].groupby(
                    ['country', 'province']).sum().reset_index()
                data_entries.append(
                    {'Date': date, 'Country': sub_df['country'], 'Province/State': sub_df['province'], 'County': 'N/A', 'Confirmed': sub_df['confirmed'], 'Deaths': sub_df['deaths']})
                continue
            elif sub_category == 'STATE':
                c = value.split('_')[1]
                print('State')
                sub_df = CSBS[CSBS['province'] == c].groupby(
                    ['country', 'province']).sum().reset_index()
                print(sub_df)
                data_entries.append(
                    {'Date': date, 'Country': sub_df['country'], 'Province/State': sub_df['province'], 'County': 'N/A', 'Confirmed': sub_df['confirmed'], 'Deaths': sub_df['deaths']})
                continue
            elif sub_category == 'COUNTY':
                print(value.split('_')[1])
                c = value.split('_')[1]
                sub_df = CSBS[CSBS['county'] == c].groupby(
                    ['country', 'province', 'county']).sum().reset_index()
                for i in sub_df.iterrows():
                    s = i[1]
                    data_entries.append(
                        {'Date': date, 'Country': s['country'], 'Province/State': s['province'], 'County': s['county'], 'Confirmed': s['confirmed'], 'Deaths': s['deaths']})
            else:
                raise Exception("YOu done fucked up")
        df = pd.DataFrame(data_entries)
        return dash_table.DataTable(id='table', columns=[{'name': i, 'id': i} for i in df.columns], data=df.to_dict('records'))

    @app.callback(
        Output('dropdown_container', 'value'),
        [Input('map', 'clickData')],
        [State('dropdown_container', 'value'),
         State('dropdown_container', 'options')])
    def display_click_data(clickData, dropdown_selected, dropdown_options):
        if not clickData:
            return dropdown_selected

        # A vector for our new items
        new = []
        label_dataframes = pd.DataFrame(dropdown_options)
        label_dataframes['cat'] = label_dataframes['value'].str.split(
            '_').str.get(0)
        label_dataframes['name'] = label_dataframes['value'].str.split(
            '_').str.get(1)
        clickdata_name = clickData['points'][0]['customdata'].split('_')[0]
        clickdata_category = clickData['points'][0]['text'].split(':')[
            0].upper()
        sub_label_df = label_dataframes[label_dataframes['cat']
                                        == clickdata_category]
        n_ = sub_label_df.loc[sub_label_df['name']
                              == clickdata_name, 'name']
        try:
            new_addition = clickdata_category+"_"+n_.iloc[0]
            print(new_addition)
        except IndexError:
            pprint.pprint(clickData)
            print('not found', clickdata_name, clickdata_category)
            return dropdown_selected
        if new_addition not in list(label_dataframes['value']):
            print('Warning, cant find {}'.format(new_addition))
        else:
            print("We found it {}".format(new_addition))
            if new_addition not in dropdown_selected:
                new = dropdown_selected+[new_addition]
                return new

        return dropdown_selected

    @app.callback(Output('map-title', 'children'),
                  [Input('date_slider', 'value')])
    def update_map_title(date_int):
        "Reported Infections Map"
        official_date = DATE_MAPPER.iloc[date_int]['Date']
        if official_date.date() == date.today() - timedelta(days=1):
            return "Yesterday"
        return "{}".format(official_date.strftime('%B %d, %Y'))
