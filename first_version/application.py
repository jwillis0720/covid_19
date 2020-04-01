import sys
import warnings
import numpy as np
import pandas as pd
import argparse
import pprint
import math
# Local Import
import data


from datetime import date, timedelta
try:
    import dash
    import dash_core_components as dcc
    import dash_html_components as html
    from dash.exceptions import PreventUpdate
    import dash_table
    import plotly
    from dash.dependencies import Input, Output, State
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
except ImportError:
    sys.exit('Please install dash, e.g, pip install dash')

# Cancel copy warnings of pandas
warnings.filterwarnings(
    "ignore", category=pd.core.common.SettingWithCopyWarning)

# Initialize APP
app = dash.Dash(__name__,
                meta_tags=[
                    {"name": "viewport",
                        "content": "width=device-width, initial-scale=1.0"},
                    {"name": "author",
                        "content": "Jordan R. Willis PhD"},

                    {"name": "description",
                        "content": "Hi! My name is Jordan. Here is my COVID-19 tracking application built in Dash and served by Flask and AWS. Timescale Resolution."},
                    {"name": "keywords",
                        "content": "COVID19,COVID-19,caronavirus,tracking,dash"},
                    {'property': 'og:image',
                        "content": "https://i.imgur.com/IOSVSbI.png"},
                    {'property': 'og:title',
                        "content": "Coronavirus 2019 - A tracking application"
                     },
                    {'property': 'og:description',
                        "content": "Hi! My name is Jordan. Here is my COVID-19 tracking application built in Dash and served by Flask and AWS. It is updated with various scraping APIS. Timescale Resolution."
                     }

                ]

                )
app.title = "Covid-19 Dashboard"


# mapbox_style = "mapbox://styles/plotlymapbox/cjvprkf3t1kns1cqjxuxmwixz"
# mapbox_style = 'mapbox://styles/mapbox/satellite-streets-v11'
# mapbox_style = 'white-bg'
mapbox_style = 'mapbox://styles/jwillis0720/ck89nznm609pg1ipadkyrelvb'
mapbox_access_token = open('.mapbox_token').readlines()[0]

MERGE_NO_US, MERGED_CSBS_JHU, JHU_TIME, JHU_RECENT, DATE_MAPPER, CSBS, CENTROID_MAPPER = data.get_data()

JHU_DF_AGG_COUNTRY = JHU_TIME.sort_values('confirmed')[::-1].groupby(['Date', 'country']).agg(
    {'lat': 'first', 'lon': 'first', 'confirmed': 'sum', 'deaths': 'sum'}).reset_index()

JHU_DF_AGG_PROVINCE = JHU_TIME[JHU_TIME['province'] != ''].sort_values('confirmed')[::-1].groupby(['Date', 'province']).agg(
    {'lat': 'first', 'lon': 'first', 'confirmed': 'sum', 'deaths': 'sum'}).reset_index()

CSBS_DF_AGG_STATE = CSBS[CSBS['province'] != ''].sort_values('confirmed')[::-1].groupby(['Date', 'province']).agg(
    {'lat': 'first', 'lon': 'first', 'confirmed': 'sum', 'deaths': 'sum'}).reset_index().rename({'province': 'state'}, axis=1)

CSBS_DF_AGG_COUNTY = CSBS[CSBS['county'] != ''].sort_values('confirmed')[::-1].groupby(['Date', 'county']).agg(
    {'lat': 'first', 'lon': 'first', 'confirmed': 'sum', 'deaths': 'sum'}).reset_index()


def build_hierarchical_dataframe(df, levels, value_column, color_columns=None):
    """
    Build a hierarchy of levels for Sunburst or Treemap charts.

    Levels are given starting from the bottom to the top of the hierarchy,
    ie the last level corresponds to the root.
    """
    df_all_trees = pd.DataFrame(columns=['id', 'parent', 'value', 'color'])
    for i, level in enumerate(levels):
        df_tree = pd.DataFrame(columns=['id', 'parent', 'value', 'color'])
        dfg = df.groupby(levels[i:]).sum()
        dfg = dfg.reset_index()
        df_tree['id'] = dfg[level].copy()
        if i < len(levels) - 1:
            df_tree['parent'] = dfg[levels[i+1]].copy()
        else:
            df_tree['parent'] = 'total'
        df_tree['value'] = dfg[value_column]
        df_all_trees = df_all_trees.append(df_tree, ignore_index=True)
    total = pd.Series(dict(id='total', parent='',
                              value=df[value_column].sum(),
                              color=""))
    df_all_trees = df_all_trees.append(total, ignore_index=True)
    return df_all_trees


def plot_sunburst():
    levels = ['continent', 'subregion', 'name', 'province']
    levels = levels[::-1]
    value_column = 'confirmed'
    df_higherarchy = build_hierarchical_dataframe(
        MERGE_NO_US, levels, value_column)
    df_higherarchy['color'] = df_higherarchy['value'] / \
        df_higherarchy['value'].sum()
    df_higherarchy = df_higherarchy.replace('total', 'Total<br>Cases')

    fig = make_subplots(
        1, 2, specs=[[{"type": "domain"}, {"type": "domain"}]], subplot_titles=("Cases", 'Deaths'))
    fig.add_trace(go.Sunburst(
        labels=df_higherarchy['id'],
        parents=df_higherarchy['parent'],
        values=df_higherarchy['value'],
        branchvalues='total',
        marker=dict(
            colors=df_higherarchy['color'],
            colorscale='aggrnyl',
            cmid=0.1),
        # cmid=MERGE_NO_US.groupby('name').sum()['confirmed'].mean()/MERGE_NO_US['confirmed'].sum()),
        hovertemplate='<b>%{label} </b> <br> Confirmed Cases: %{value}',
        insidetextorientation='radial',
        name='Confirmed',
        maxdepth=3,
        textfont=dict(size=25, color='black')
    ), 1, 1)

    levels = ['continent', 'subregion', 'name', 'province']
    levels = levels[::-1]
    value_column = 'deaths'
    df_higherarchy = build_hierarchical_dataframe(
        MERGE_NO_US, levels, value_column)
    df_higherarchy['color'] = df_higherarchy['value'] / \
        df_higherarchy['value'].sum()
    df_higherarchy = df_higherarchy.replace('total', 'Total<br>Deaths')

    fig.add_trace(go.Sunburst(
        labels=df_higherarchy['id'],
        parents=df_higherarchy['parent'],
        values=df_higherarchy['value'],
        branchvalues='total',
        marker=dict(
            colors=df_higherarchy['color'],
            colorscale='reds',
            cmin=0.6,
            cmid=MERGE_NO_US.groupby('name').sum()['deaths'].mean()/MERGE_NO_US['deaths'].sum()),
        hovertemplate='<b>%{label} </b> <br> Confirmed Deaths: %{value}',
        name='Deaths',
        maxdepth=3,
        textfont=dict(color='white'),
        insidetextorientation='horizontal'
    ), 1, 2)
    margine = 15
    fig.update_layout(
        uniformtext=dict(mode='hide', minsize=20),
        paper_bgcolor='rgb(0,0,0,0)',
        # title=dict(text='Click to Expand',
        #            font=dict(color='white', size=16)),
        margin=dict(l=0, r=0, t=0, b=0)
    )
    pprint.pprint(fig.data)
    pprint.pprint(fig.layout)
    return fig


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
        value=['worldwide', 'COUNTRY_US', 'COUNTRY_China'],
        multi=True
    )
    return dd


def get_date_slider():
    how_many_labels = (len(DATE_MAPPER))//10
    marks = {k: {'label': v}
             for k, v in list(DATE_MAPPER['Date'].dt.strftime(
                 '%m/%d/%y').to_dict().items())[::how_many_labels]}
    last_key = list(marks.keys())[-1]
    todays_key = DATE_MAPPER.index[-1]
    # if last_key == todays_key:
    #     marks[last_key]['label'] == 'Today'
    # else:
    #     marks[todays_key] = {'label': 'Today'}
    DATE_MAPPER
    return dcc.Slider(
        id='date_slider',
        min=DATE_MAPPER.index[0],
        max=DATE_MAPPER.index[-1],
        step=1,
        value=DATE_MAPPER.index[-1],
        marks=marks
    )


def serve_dash_layout():
    return html.Div(
        id='root_container',
        children=[
            html.Div(
                id="header",
                children=[
                    html.Div(
                        id="description",
                        children=[
                            html.H1(
                                children="COVID-19 Infection Dashboard"),
                            html.Div(
                                id='header-info', children=[
                                    "App by ",
                                    html.A(
                                        "Jordan R. Willis PhD", href="https://jordanrwillis.com", target="_blank"),
                                    # html.Br(),
                                    # "Data generated  nightly from Johns Hopkins ",
                                    # html.A(
                                    #     "CSSE repository", href='https://github.com/CSSEGISandData/COVID-19'),
                                    # html.Br(),
                                    # "Inspiration from ",
                                    # html.A(
                                    #     "CSSE", href="https://www.arcgis.com/apps/opsdashboard/index.html#/bda7594740fd40299423467b48e9ecf6"),
                                    # ", ",
                                    # html.A(
                                    #     "Bing", href='www.bing.com/covid'),
                                    # ", ",
                                    # html.A(
                                    #     "Dash Opioid Epidemic", href='https://dash-gallery.plotly.host/dash-opioid-epidemic/'),
                                ]
                            )]),
                    html.Div(id='counters', children=[
                        html.Div(id='total-cases-card', className='card',
                                 children=[html.H3('Total Cases'),
                                           html.P(id='total-cases',
                                                  children=[get_total_cases()])
                                           ]),
                        html.Div(id='total-deaths-card', className='card',
                                 children=[html.H3('Total Deaths'),
                                           html.P(id='total-deaths',
                                                  children=[get_total_deaths()])
                                           ]),
                                html.Div(id='mortality-card', className='card',
                                         children=[html.H3('Mortality Rate'),
                                                   html.P(id='mortality-rate',
                                                          children=[get_mortality_rate()])
                                                   ]),
                        html.Div(id='growth-rate-card', className='card',
                                 children=[html.H3('Growth Rate'),
                                           html.P(id='growth-rate',
                                                  children=[get_growth_rate()])
                                           ])
                    ])
                ]),
            html.Div(
                id="app-container",
                children=[
                    html.Div(
                        id="left-container",
                        children=[
                            html.Div(
                                id="slider-container",
                                children=[
                                    html.P(
                                        id="slider-text",
                                        children="Drag the Slider to Change the Reported Date:",
                                    ),
                                    get_date_slider()
                                ]),
                            html.Div(
                                id='map-container',
                                children=[
                                    html.Div(
                                        id='map-title-container',
                                        children=[
                                            dcc.Checklist(
                                                id='radio-items',
                                                labelClassName='radio-list',
                                                options=[
                                                    {'label': 'Country',
                                                     'value': 'country'},
                                                    {'label': 'Province/State',
                                                     'value': 'province'},
                                                    {'label': 'County',
                                                     'value': 'county'}
                                                ],
                                                value=['country', 'province']),
                                            html.P(
                                                id="map-title",
                                            ),
                                            dcc.Checklist(
                                                id='check-items',
                                                labelClassName='radio-list',
                                                options=[
                                                    {'label': 'Confirmed',
                                                     'value': 'confirmed'},
                                                    {'label': 'Deaths',
                                                     'value': 'deaths'}
                                                ],
                                                value=[
                                                    'confirmed', 'deaths']
                                            )]),
                                    dcc.Graph(id='plot-map')
                                ])
                        ]),
                    html.Div(
                        id="graph-container",
                        children=[
                            html.H5(id='graph-container-tile',
                                    children=['Click Place on Map or Chart to Update List']),
                            get_dropdown(),
                            # html.Div(id='tab-container', className='custom-tabs-container', children=[
                            dcc.Tabs(id='tabs-values', parent_className='tabs-container', className='custom-tabs', children=[
                                dcc.Tab(label='Total Cases',
                                        className='custom-tab',
                                        selected_className='custom-tab--selected',
                                        value='total_cases_graph'),
                                dcc.Tab(label='Cases Per Day',
                                        className='custom-tab',
                                        selected_className='custom-tab--selected',
                                        value='per_day_cases'),
                                dcc.Tab(label='Exponential',
                                        className='custom-tab',
                                        selected_className='custom-tab--selected',
                                        value='exponential')
                            ],
                                value='total_cases_graph'),


                            dcc.Loading(id='graph-loading-container',
                                        className='graph-container', type='cube')],

                    ),
                    # html.Div(
                    #     id='table-container',
                    #     children=[])
                ]),
        ])


app.layout = serve_dash_layout

# We must expose this for Elastic Bean Stalk to Run
application = app.server


def get_total_cases():
    return "{:,}".format(JHU_RECENT['confirmed'].sum())


def get_total_deaths():
    return "{:,}".format(JHU_RECENT['deaths'].sum())


def get_mortality_rate():
    return "{:.3}%".format(JHU_RECENT['deaths'].sum()/JHU_RECENT['confirmed'].sum()*100)


def get_growth_rate():
    x = JHU_TIME.groupby('Date').sum().pct_change()[
        'confirmed'][-10:].mean()*100
    return "{:.4}%".format(x)


@app.callback(Output('plot-map', 'figure'),
              [Input('date_slider', 'value'),
               Input('radio-items', 'value'),
               Input('check-items', 'value')],
              [State('plot-map', 'figure'),
               State('plot-map', 'relayoutData')])
def plot_map(date_int, group, metrics, figure, relay):
    pprint.pprint(relay)
    # Date INT comes from the slider and can only return integers:
    official_date = DATE_MAPPER.iloc[date_int]['Date']

    # Lets trim down the dataframes
    JHU_TIME_DATE = JHU_TIME[JHU_TIME['Date'] == official_date]
    CSBS_TIME_DATE = CSBS[CSBS['Date'] == official_date]

    # Initialize empty
    plot_data_frame = pd.DataFrame()
    SUB_DF_COUNTRY = pd.DataFrame()
    SUB_DF_PROVINCE = pd.DataFrame()
    SUB_DF_COUNTY = pd.DataFrame()

    if relay:
        if 'mapbox.center' in relay.keys():
            center = dict(lat=relay['mapbox.center']['lat'],
                          lon=relay['mapbox.center']['lon'])
            zoom = relay['mapbox.zoom']
        else:
            zoom = 2.0,
            center = dict(lat=20.74, lon=15.4)
    else:
        zoom = 2.0,
        center = dict(lat=20.74, lon=15.4)
        # {'mapbox.bearing': 0,
        #  'mapbox.center': {'lat': 39.06944801157573, 'lon': -63.32395235178592},
        #  'mapbox.pitch': 0,
        # 'mapbox.zoom': 2.4811482816327537}

    if 'country' in group:
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

    if 'province' in group:
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

    if 'county' in group:
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

    # Setting up Sizes and Colors
    grey_to_yellow = ['#808080', '#a19e79',
                      '#c1bd70', '#e0dc63', '#fffd50']
    orange_to_red = ['#ffa500', '#ff8c00', '#ff7000', '#ff4e00', '#ff0000']

    sizes = [5, 10, 30, 60]

    death_bins = [1, 2, 100, 1000, 1000000]
    cases_bins = [1, 10, 1000, 10000, 10000000]
    if not plot_data_frame.empty:
        plot_data_frame['death_size'] = pd.cut(
            plot_data_frame['deaths'], bins=death_bins, include_lowest=True, labels=sizes)
        plot_data_frame['confirmed_size'] = pd.cut(
            plot_data_frame['confirmed'], bins=cases_bins, include_lowest=True, labels=sizes)

        plot_data_frame['death_colors'] = plot_data_frame['death_size'].apply(
            lambda x: dict(zip(sizes, orange_to_red))[x])
        plot_data_frame['case_colors'] = plot_data_frame['confirmed_size'].apply(
            lambda x: dict(zip(sizes, grey_to_yellow))[x])

    # And Plot the DataSet
    data_traces = []

    if not metrics or plot_data_frame.empty:
        data_traces.append(go.Scattermapbox(
            lon=[],
            lat=[]
        ))

    if 'confirmed' in metrics and not plot_data_frame.empty:
        # First Do Confirmed
        gb_confirmed = plot_data_frame.groupby('confirmed_size')
        gb_groups = sorted(gb_confirmed.groups)
        for indexer in range(len(gb_groups)):
            plotting_df = gb_confirmed.get_group(gb_groups[indexer])
            if indexer+1 == len(cases_bins)-1:
                max_ = int(
                    math.ceil(plot_data_frame['confirmed'].max()/10000)) * 10000
                name = "{0:,}-{1:,}".format(int(cases_bins[indexer]), max_)
            else:
                name = "{0:,}-{1:,}".format(
                    cases_bins[indexer], cases_bins[indexer+1])
            data = go.Scattermapbox(
                lon=plotting_df['lon'],
                lat=plotting_df['lat'],
                customdata=plotting_df['location'] + "_" +
                plotting_df['source'] + "_" + plotting_df['type']+"_confirmed",
                textposition='top right',
                text=plotting_df['Text_Cases'],
                hoverinfo='text',
                mode='markers',
                name=name,
                marker=dict(
                    opacity=0.75,
                    size=plotting_df['confirmed_size'],
                    color=plotting_df['case_colors']
                )
            )
            data_traces.append(data)

    if 'deaths' in metrics and not plot_data_frame.empty:
        # Then Do Deaths
        gb_deaths = plot_data_frame.groupby('death_size')
        gb_groups = sorted(gb_deaths.groups)
        for indexer in range(len(gb_groups)):
            try:
                plotting_df = gb_deaths.get_group(gb_groups[indexer])
            except KeyError:
                print('No group in gb_deaths {}'.format(gb_groups[indexer]))

            if indexer+1 == len(death_bins)-1:
                max_ = int(
                    math.ceil(plot_data_frame['deaths'].max()/10000)) * 10000
                name = "{0:,}-{1:,}".format(int(death_bins[indexer]), max_)
            else:
                name = "{0:,}-{1:,}".format(
                    death_bins[indexer], death_bins[indexer+1])
            data = go.Scattermapbox(
                lon=plotting_df['lon'],
                lat=plotting_df['lat'],
                customdata=plotting_df['location'],
                textposition='top right',
                text=plotting_df['Text_Deaths'],
                hoverinfo='text',
                mode='markers',
                name=name,
                marker=dict(
                    opacity=0.75,
                    size=plotting_df['death_size'],
                    color=plotting_df['death_colors']
                )
            )
            data_traces.append(data)

    layout = dict(
        autosize=True,
        showlegend=True,
        mapbox=dict(
            accesstoken=mapbox_access_token,
            style=mapbox_style,
            zoom=zoom,
            center=center
        ),
        hovermode="closest",
        margin=dict(r=0, l=0, t=0, b=0),
        dragmode="pan",
        legend=dict(
            x=0.012,
            y=0.12,
            orientation='h',
            traceorder="normal",
            font=dict(
                family="sans-serif",
                # size=12,
                color="white"
            ),
            bgcolor='rgba(0,0,0,0)',
        )
    )

    return {'data': data_traces, 'layout': layout}


@app.callback(Output('map-title', 'children'),
              [Input('date_slider', 'value')])
def update_description(date_int):
    "Reported Infections Map"
    official_date = DATE_MAPPER.iloc[date_int]['Date']
    if official_date.date() == date.today() - timedelta(days=1):
        return "Yesterday"
    return "{}".format(official_date.strftime('%B %d, %Y'))


@app.callback(Output('graph-loading-container', 'children'),
              [Input('tabs-values', 'value'),
               Input('dropdown_container', 'value')])
def render_tab_content(tab, values):
    if tab == 'total_cases_graph':
        return dcc.Graph(
            id='minute-p',
            className='loading_graph',
            figure=total_case_graph(values))
    elif tab == 'per_day_cases':
        return dcc.Graph(
            id='minute-p',
            className='loading_graph',
            figure=per_day_case_graph(values))

    elif tab == 'exponential':
        return dcc.Graph(
            id='expoential-graph',
            className='loading_graph',
            figure=plot_exponential(values))


def total_case_graph(values):
    colors = plotly.colors.qualitative.Dark24
    pprint.pprint(values)
    fig = go.Figure()
    for enum_, item in enumerate(values):
        color_ = colors[enum_]
        if item == 'worldwide':
            sub_df = JHU_DF_AGG_COUNTRY.groupby('Date').sum().reset_index()
            name = 'World'
        else:
            if item.split('_')[0] == 'COUNTRY':
                name = item.split('_')[1]
                sub_df = JHU_DF_AGG_COUNTRY[JHU_DF_AGG_COUNTRY['country'] == name].groupby(
                    'Date').sum().reset_index()

            elif item.split('_')[0] == 'PROVINCE':
                name = item.split('_')[1]
                sub_df = JHU_DF_AGG_PROVINCE[JHU_DF_AGG_PROVINCE['province'] == name].groupby(
                    'Date').sum().reset_index()

            elif item.split('_')[0] == 'STATE':
                name = item.split('_')[1]
                sub_df = CSBS_DF_AGG_STATE[CSBS_DF_AGG_STATE['state'] == name].groupby(
                    'Date').sum().reset_index()

            elif item.split('_')[0] == 'COUNTY':
                name = item.split('_')[1]
                sub_df = CSBS_DF_AGG_COUNTY[CSBS_DF_AGG_COUNTY['county'] == name].groupby(
                    'Date').sum().reset_index()
            else:
                raise Exception('You have messed up {}'.format(item))

        fig.add_trace(
            go.Scatter(
                x=sub_df['Date'],
                y=sub_df['confirmed'],
                name=name,
                showlegend=True,
                mode='lines+markers',
                hovertemplate='%{x}<br>Confirmed Cases - %{y:,f}',
                marker=dict(
                    color=color_,
                    size=2,
                    line=dict(
                        width=5,
                        color=color_),
                )))

    fig.update_layout(
        # xaxis_tickfont_size=22,
        yaxis=dict(
            title=dict(text='Total Cases', standoff=2),
            titlefont_size=12,
            tickfont_size=12,
            showgrid=True,
            color='white',
            side='left',
        ),
        xaxis=dict(
            color='white'
        ),
        autosize=True,
        showlegend=True,
        legend=dict(x=0, y=1, font=dict(color='white')),
        paper_bgcolor='#1f2630',
        plot_bgcolor='rgb(52,51,50)',
        margin=dict(t=20, pad=10, b=20, r=20, l=20))

    return fig


def per_day_case_graph(values):
    colors = plotly.colors.qualitative.Dark24
    pprint.pprint(values)
    fig = go.Figure()
    # fig = plotly.subplots.make_subplots(specs=[[{"secondary_y": True}]])
    for enum_, item in enumerate(values):
        color_ = colors[enum_]
        if item == 'worldwide':
            sub_df = JHU_DF_AGG_COUNTRY.groupby('Date').sum().reset_index()
            name = 'World'
        else:
            if item.split('_')[0] == 'COUNTRY':
                name = item.split('_')[1]
                sub_df = JHU_DF_AGG_COUNTRY[JHU_DF_AGG_COUNTRY['country'] == name].groupby(
                    'Date').sum().reset_index()

            elif item.split('_')[0] == 'PROVINCE':
                name = item.split('_')[1]
                sub_df = JHU_DF_AGG_PROVINCE[JHU_DF_AGG_PROVINCE['province'] == name].groupby(
                    'Date').sum().reset_index()

            elif item.split('_')[0] == 'STATE':
                name = item.split('_')[1]
                sub_df = CSBS_DF_AGG_STATE[CSBS_DF_AGG_STATE['state'] == name].groupby(
                    'Date').sum().reset_index()

            elif item.split('_')[0] == 'COUNTY':
                name = item.split('_')[1]
                sub_df = CSBS_DF_AGG_COUNTY[CSBS_DF_AGG_COUNTY['county'] == name].groupby(
                    'Date').sum().reset_index()
            else:
                raise Exception('You have messed up {}'.format(item))

        xs = sub_df['Date']
        ys = sub_df['confirmed'].diff().fillna(0)
        fig.add_trace(
            go.Bar(
                x=xs,
                y=ys,
                name=name,
                showlegend=True,
                # text=ys,
                # textposition='outside',
                hovertemplate='%{x}<br>New Cases - %{y:,f}',
                # texttemplate='%{text:.2s}',
                textfont=dict(size=14, color='white'),
                marker=dict(
                    color=color_,
                    line=dict(
                        color='white', width=0.5)
                )))

    fig.update_layout(
        yaxis=dict(
            title=dict(text='New Cases', standoff=2),
            titlefont_size=12,
            tickfont_size=12,
            showgrid=True,
            color='white',
            side='left',
        ),
        xaxis=dict(
            color='white'
        ),
        showlegend=True,
        legend=dict(x=0, y=1, font=dict(color='white')),
        paper_bgcolor='#1f2630',
        plot_bgcolor='rgb(52,51,50)',
        barmode='group',
        bargap=0.1,
        margin=dict(t=20, pad=10, b=20, r=20, l=20))

    return fig


def plot_exponential(value):
    backtrack = 7
    log = True
    fig = go.Figure()
    colors = plotly.colors.qualitative.Dark24
    max_number = 0
    for enum_, item in enumerate(value):
        if item == 'worldwide':
            location = 'World'
            full_report = JHU_DF_AGG_COUNTRY.groupby(
                'Date').sum().drop(['lat', 'lon'], axis=1)
        else:
            class_location, location = item.split('_')
            if class_location == 'COUNTRY':
                full_report = JHU_DF_AGG_COUNTRY[JHU_DF_AGG_COUNTRY['country'] == location].groupby(
                    'Date').sum().drop(['lat', 'lon'], axis=1)

            elif class_location == 'PROVINCE':
                full_report = JHU_DF_AGG_PROVINCE[JHU_DF_AGG_PROVINCE['province'] == location].groupby(
                    'Date').sum().drop(['lat', 'lon'], axis=1)
            elif class_location == 'STATE':
                full_report = CSBS_DF_AGG_STATE[CSBS_DF_AGG_STATE['state'] == location].groupby(
                    'Date').sum().drop(['lat', 'lon'], axis=1)
            elif class_location == 'COUNTY':
                full_report = CSBS_DF_AGG_COUNTY[CSBS_DF_AGG_COUNTY['county'] == location].groupby(
                    'Date').sum().drop(['lat', 'lon'], axis=1)
        per_day = full_report.diff()
        plottable = full_report.join(
            per_day, lsuffix='_cum', rsuffix='_diff')
        plottable = plottable.fillna(0)

        xs = []
        ys = []
        dates = []
        indexes = plottable.index
        for indexer in range(1, len(indexes)):
            x = plottable.loc[indexes[indexer]]['confirmed_cum']
            if indexer > backtrack:
                y = plottable.loc[indexes[indexer-backtrack]: indexes[indexer]].sum()['confirmed_diff']
            else:
                y = plottable.loc[: indexes[indexer]].sum()['confirmed_diff']
            if y < 100 or x < 100:
                continue
            if x > max_number:
                max_number = x
            if y > max_number:
                max_number = y
            xs.append(x)
            ys.append(y)
            dates.append(indexes[indexer].strftime('%m/%d/%Y'))
        fig.add_trace(
            go.Scatter(
                x=xs,
                y=ys,
                mode='lines',
                name=location,
                text=dates,
                showlegend=False,
                legendgroup=item,
                line=dict(shape='linear', color=colors[enum_], width=3),
                marker=dict(
                    symbol='circle-open',
                    # size=7
                ),
                hovertemplate="On %{text} <br> Total Cases: %{x}<br> Cummulative Cases Last Week %{y}"
            )
        )
        fig.add_trace(
            go.Scatter(
                x=[xs[-1]],
                y=[ys[-1]],
                mode='markers',
                name=location,
                text=[dates[-1]],
                legendgroup=location,
                hoverlabel=dict(align='left'),
                marker=dict(
                    symbol='circle',
                    # size=18,
                    color=colors[enum_]
                ),
                hovertemplate="On %{text} <br> Total Cases: %{x}<br> Cummulative Cases Last Week %{y}"
            )
        )
    fig.add_trace(
        go.Scatter(
            x=[100, max_number],
            y=[100, max_number],
            mode='lines',
            name='Exponential',
            showlegend=False,
            line=dict(color='white', width=4, dash='dash')
        )
    )
    if log:
        fig.update_xaxes(type="log", dtick=1)
        fig.update_yaxes(type="log", dtick=1)

    fig.update_layout(
        # xaxis_tickfont_size=22,
        yaxis=dict(
            title=dict(text='New Cases Previous {} Days'.format(
                backtrack), standoff=2),
            # titlefont_size=22,
            # tickfont_size=22,
            showgrid=True,
            color='white',
        ),
        margin=dict(t=20),
        xaxis=dict(
            color='white',
            showgrid=False,
            title=dict(text='Total Cases', standoff=1)
        ),
        autosize=True,
        showlegend=True,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgb(52,51,50)',
        legend=dict(x=0, y=1, font=dict(color='white')))

    # print(max_number, np.log10(max_number))
    annotations = []
    annotations.append(dict(xref='x', x=6-1, yref='y', y=6-0.6,

                            # xanchor='center', yanchor='middle',
                            text="Exponential Growth",
                            font=dict(family='Arial',
                                      #   size=20,
                                      color='white'),
                            showarrow=True,
                            startarrowsize=10,
                            arrowwidth=2,
                            arrowcolor='white',
                            arrowhead=2,
                            ))

    fig.update_layout(legend=dict(title='Click to Toggle'),
                      annotations=annotations)

    fig.update_layout(
        margin=dict(t=20, b=20, r=30, l=20, pad=0))
    return fig


# @app.callback(
#     Output('hover-data', 'children'),
#     [Input('basic-interactions', 'hoverData')])
# def display_hover_data(hoverData):
#     return json.dumps(hoverData, indent=2)


@app.callback(
    Output('dropdown_container', 'value'),
    [Input('plot-map', 'clickData')],
    [State('dropdown_container', 'value'),
     State('dropdown_container', 'options')])
def display_click_data(clickData, dropdown_selected, dropdown_options):
    if not clickData:
        return dropdown_selected
    new = []
    label_dataframes = pd.DataFrame(dropdown_options)
    label_dataframes['cat'] = label_dataframes['value'].str.split(
        '_').str.get(0)
    label_dataframes['name'] = label_dataframes['value'].str.split(
        '_').str.get(1)

    clickdata_name = clickData['points'][0]['customdata'].split('_')[0]
    clickdata_category = clickData['points'][0]['text'].split(':')[0].upper()
    # print(clickdata_name, clickdata_category)
    sub_label_df = label_dataframes[label_dataframes['cat']
                                    == clickdata_category]
    n_ = sub_label_df.loc[sub_label_df['name']
                          == clickdata_name, 'name']
    # print(n_.iloc[0])

    # pprint.pprint((clickData))
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


# @app.callback(
#     Output('table-container', 'children'),
#     [Input('basic-interactions', 'selectedData')])
# def display_selected_data(selectedData):
#     return json.dumps(selectedData, indent=2)


# @app.callback(
#     Output('table-container', 'children'),
#     [Input('basic-interactions', 'relayoutData')])
# def display_relayout_data(relayoutData):
#     return json.dumps(relayoutData, indent=2)


if __name__ == '__main__':
    app.run_server(debug=True, port=8050)
