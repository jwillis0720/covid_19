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
        textfont=dict(size=25, color='white'),
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
                    html.H4(
                        children="COVID-19 Infection Dashboard"),
                    html.Div(
                        id="description",
                        children=[
                            "COVID-19 Infection App by ",
                            html.A(
                                "Jordan R. Willis PhD", href="https://jordanrwillis.com", target="_blank"),
                            html.Br(),
                            "Data generated  nightly from Johns Hopkins ",
                            html.A(
                                "CSSE repository", href='https://github.com/CSSEGISandData/COVID-19'),
                            html.Br(),
                            "Inspiration from ",
                            html.A(
                                "CSSE", href="https://www.arcgis.com/apps/opsdashboard/index.html#/bda7594740fd40299423467b48e9ecf6"),
                            ", ",
                            html.A(
                                "Bing", href='www.bing.com/covid'),
                            ", ",
                           html.A(
                                "Dash Opioid Epidemic", href='https://dash-gallery.plotly.host/dash-opioid-epidemic/'),
                            "."]
                    ),
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
                                    children=['Click Place on Map or Chart to Get More Information']),

                            # dcc.Graph(id='per_date_line',
                            #           figure=plot_sunburst()),
                            dcc.Loading(
                                className='loading-container', children=[dcc.Graph(id='per_date')], type='cube'),
                        ]),
                    # html.Div(
                    #     id='table-container',
                    #     children=[])
                ]),
        ])


app.layout = serve_dash_layout

# We must expose this for Elastic Bean Stalk to Run
application = app.server


@app.callback(Output('plot-map', 'figure'),
              [Input('date_slider', 'value'),
               Input('radio-items', 'value'),
               Input('check-items', 'value')],
              [State('plot-map', 'figure')])
def plot_map(date_int, group, metrics, figure):
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

    death_bins = [0, 2, 100, 1000, 1000000]
    cases_bins = [0, 10, 1000, 10000, 10000000]

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

    if not metrics:
        data_traces.append(go.Scattermapbox(
            lon=[],
            lat=[]
        ))

    if 'confirmed' in metrics:
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

    if 'deaths' in metrics:
        # Then Do Deaths
        gb_deaths = plot_data_frame.groupby('death_size')
        gb_groups = sorted(gb_deaths.groups)
        for indexer in range(len(gb_groups)):
            plotting_df = gb_deaths.get_group(gb_groups[indexer])
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
            zoom=1.5,
            center=dict(lat=20.74, lon=15.4)
        ),
        hovermode="closest",
        margin=dict(r=0, l=0, t=0, b=0),
        dragmode="pan",
        legend=dict(
            x=0.88,
            y=0.05,
            traceorder="normal",
            font=dict(
                family="sans-serif",
                size=16,
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


@app.callback(Output('per_date', 'figure'),
              [Input('plot-map', 'clickData'),
               Input('radio-items', 'value')])
def update_new_case_graph(hoverData, group):
    pprint.pprint(hoverData)

    if group == 'country' and hoverData:
        selection = hoverData['points'][0]['customdata']
        print(selection)
        sub_df = JHU_TIME[JHU_TIME['country'] == selection]
        # Just incase a country with provinces is selected
        sub_df = sub_df.groupby('Date').sum()
    elif group == 'province' and hoverData:
        selection = hoverData['points'][0]['customdata']
        print(selection)
        if selection in list(JHU_TIME['province']):
            sub_df = JHU_TIME[JHU_TIME['province'] == selection]
        else:
            sub_df = CSBS[CSBS['province'] == selection]

        print(sub_df)
        sub_df = sub_df.groupby(['province', 'Date']).sum().reset_index()
        # sub_df = per_day_stats_by_state[per_day_stats_by_state['province'] == country]

    elif group == 'county' and hoverData:
        selection = hoverData['points'][0]['customdata']
        print(selection)
        sub_df = CSBS[CSBS['county'] == selection]

    #     if sub_df.empty:
    #         country = "{} - No Data Available".format(country)
    #     sub_df_time = ""
    else:
        sub_df = JHU_TIME.groupby('Date').sum().reset_index()
        # sub_df_time = JHU_TIME.groupby('Date').sum().reset_index()
        selection = 'World'

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    dates = DATE_MAPPER['Date_text'].unique()
    fig.add_trace(go.Bar(x=dates,
                         y=sub_df['confirmed'].diff().fillna(
                             0),
                         name=selection,
                         showlegend=False,
                         text=sub_df['confirmed'].diff().fillna(0),
                         textposition='auto',
                         hovertemplate='Date - %{x}<br>New Cases - %{y:,f}',

                         marker=dict(
                             color='white',
                             line=dict(
                                 color='white')
                         )))
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=sub_df['confirmed'],
            name=selection,
            showlegend=False,
            mode='lines+markers',
            hovertemplate='Date - %{x}<br>Confirmed Cases - %{y:,f}',
            marker=dict(
                color='yellow',
                size=0.1,
                line=dict(
                    width=10,
                    color='yellow')
            )), secondary_y=True)

    fig.update_layout(
        title=dict(text='New Cases Per Day: {}'.format(
            selection), font=dict(color='white', size=24)),
        xaxis_tickfont_size=14,
        yaxis=dict(
            title=dict(text='New Cases', standoff=2),
            titlefont_size=18,
            tickfont_size=18,
            showgrid=False,
            color='white',
            side='left',
        ),
        xaxis=dict(
            title='Date',
            color='white'
        ),
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgb(52,51,50)',
        barmode='group',
        bargap=0.15,  # gap between bars of adjacent location coordinates.
        bargroupgap=0.1)

    fig.update_layout(
        yaxis2=dict(
            title=dict(text='Total Cases', standoff=2),
            titlefont_size=18,
            tickfont_size=18,
            showgrid=False,
            color='yellow',
            side='right',
        ),

    )

    return fig


if __name__ == '__main__':
    app.run_server(debug=True, port=8050)
