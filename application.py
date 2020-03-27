import sys
import warnings
import numpy as np
import pandas as pd
import argparse
import pprint

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


# mapbox_style = "mapbox://styles/plotlymapbox/cjvprkf3t1kns1cqjxuxmwixz"
mapbox_style = 'dark'
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
        maxdepth=2,
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
        maxdepth=2,
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
                                            dcc.RadioItems(
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
                                                value='province'),
                                            html.P(
                                                id="map-title",
                                            ),
                                            dcc.Checklist(
                                                id='check-items',
                                                labelClassName='radio-list',
                                                options=[
                                                    {'label': 'Cases',
                                                     'value': 'cases'},
                                                    {'label': u'Deaths',
                                                     'value': 'deaths'}
                                                ],
                                                value=[
                                                    'cases']
                                            )]),
                                    # get_dummy_graph(grap)
                                    dcc.Graph(id='state-graph')
                                ])
                        ]),
                    html.Div(
                        id="graph-container",
                        children=[
                            html.H5(id='graph-container-tile',
                                    children=['Click Place on Map or Chart to Get More Information']),

                            dcc.Graph(id='per_date_line',
                                      figure=plot_sunburst()),
                            dcc.Loading(dcc.Graph(id='per_date')),
                        ]),
                    html.Div(
                        id='table-container',
                        children=[])
                ]),
        ])


app.layout = serve_dash_layout

# We must expose this for Elastic Bean Stalk to Run
application = app.server


@app.callback(Output('state-graph', 'figure'),
              [Input('date_slider', 'value'),
               Input('radio-items', 'value'),
               Input('check-items', 'value')],
              [State('state-graph', 'figure')])
def get_graph_state(date_int, group, metrics, figure):
    if not figure:
        lat = 15.74
        lon = -1.4
        zoom = 1.6
    elif "layout" in figure:
        lat = figure["layout"]["mapbox"]['center']["lat"]
        lon = figure["layout"]["mapbox"]['center']["lon"]
        zoom = figure["layout"]["mapbox"]["zoom"]

    if 'cases' in metrics:
        normalizer = 'confirmed'
    elif 'active' in metrics:
        normalizer = 'Active'
    elif 'recovery' in metrics:
        normalizer = 'recovered'
    else:
        normalizer = 'deaths'

    official_date = DATE_MAPPER.iloc[date_int]['Date']
    # print(date_int, official_date)

    if group == 'country':
        country_mapper = JHU_TIME[
            JHU_TIME['Date'] == official_date].groupby(
            'country', as_index=False).apply(lambda x: x.sort_values('confirmed')[::-1].head(1)[['country', 'lat', 'lon']])
        sub_df = JHU_TIME[
            JHU_TIME['Date'] == official_date].groupby('country', as_index=False).sum()[['country', 'confirmed', 'deaths']].merge(
                country_mapper, on=['country'])
        sizeref = 2. * JHU_TIME.groupby(
            ['Date', group]).sum().max()[normalizer] / (20 ** 2)

        print(sub_df.columns)

    elif group == 'province':
        sub_df = JHU_TIME[JHU_TIME[group] != '']
        province_mapper = sub_df[
            sub_df['Date'] == official_date].groupby(
                group, as_index=False).apply(lambda x: x.sort_values('confirmed')[::-1].head(1)[[group, 'lat', 'lon']])
        sub_df = sub_df[
            sub_df['Date'] == official_date].groupby(group, as_index=False).sum()[['province', 'confirmed', 'deaths']].merge(province_mapper, on=['province'])

        # Now do it for the CSBS
        province_mapper = CSBS.groupby(
            group, as_index=False).apply(lambda x: x.sort_values('confirmed')[::-1].head(1)[[group,  'lat', 'lon']])
        sub_df_csbs = CSBS[CSBS[group] != '']
        sub_df_csbs = sub_df_csbs[sub_df_csbs['Date'] == official_date]

        sub_df_csbs = sub_df_csbs.groupby(group, as_index=False).sum()[
            ['province', 'confirmed', 'deaths']].merge(province_mapper, on=['province'])
        sub_df = pd.concat([sub_df, sub_df_csbs])

        sizeref = 2. * JHU_TIME.groupby(
            ['Date', group]).sum().max()[normalizer] / (20 ** 2)

    elif group == 'county':
        sub_df = CSBS[CSBS['Date'] == official_date]
        sub_df = sub_df.sort_values('confirmed').groupby(
            ['county', 'province', 'lat', 'lon'], as_index=False).head(1)
        sub_df.rename({'cases': 'confirmed'}, axis=1, inplace=1)
        sizeref = 2. * sub_df.max()[normalizer] / (20 ** 2)

    sub_df['Text_Cases'] = sub_df[group] + '<br>Total Cases at {} : '.format(
        official_date.strftime('%m/%d/%y')) + sub_df['confirmed'].apply(lambda x: "{:,}".format(int(x)))
    sub_df['Text_Death'] = sub_df[group] + '<br>Total Deaths at {} : '.format(
        official_date.strftime('%m/%d/%y')) + sub_df['deaths'].apply(lambda x: "{:,}".format(int(x)))

    sub_df.loc[sub_df['confirmed'] < 0, 'confirmed'] = 0

    fig = go.Figure()
    if 'cases' in metrics:
        fig.add_trace(go.Scattermapbox(
            lon=sub_df['lon'].astype(float) +
            np.random.normal(0, .02, len(sub_df['lon'])),
            lat=sub_df['lat'].astype(float) +
            np.random.normal(0, .02, len(sub_df['lat'])),
            customdata=sub_df[group],
            textposition='top right',
            text=sub_df['Text_Cases'],
            hoverinfo='text',
            mode='markers',
            name='cases',
            marker=dict(
                sizeref=sizeref,
                sizemin=10,
                size=sub_df['confirmed'],
                color='yellow')))

    if 'deaths' in metrics:
        fig.add_trace(go.Scattermapbox(
            lon=sub_df['lon'] +
            np.random.normal(0, .02, len(sub_df['lon'])),
            lat=sub_df['lat'] +
            np.random.normal(0, .02, len(sub_df['lat'])),
            customdata=sub_df[group],
            textposition='top right',
            text=sub_df['Text_Death'],
            hoverinfo='text',
            name='deaths',
            mode='markers',
            marker=dict(
                sizeref=sizeref,
                sizemin=10,
                size=sub_df['deaths'],
                color='red')))

    if not metrics:
        fig.add_trace(go.Scattermapbox(
            lon=[],
            lat=[]
        ))
    layout = dict(
        title_text='The Corona is Coming',
        autosize=True,
        showlegend=True,
        mapbox=dict(
            accesstoken=mapbox_access_token,
            style=mapbox_style,
            zoom=zoom,
            center=dict(lat=lat, lon=lon)
        ),
        hovermode="closest",
        margin=dict(r=0, l=0, t=0, b=0),
        dragmode="pan",
        legend=dict(
            x=0.05,
            y=0.1,
            traceorder="normal",
            font=dict(
                family="sans-serif",
                size=24,
                color="white"
            ),
            bgcolor='rgba(0,0,0,0)',
            # bordercolor="",
            # borderwidth=2
        )
    )

    fig.update_layout(layout)
    return fig


@app.callback(Output('map-title', 'children'),
              [Input('date_slider', 'value')])
def update_description(date_int):
    "Reported Infections Map"
    official_date = DATE_MAPPER.iloc[date_int]['Date']
    if official_date.date() == date.today() - timedelta(days=1):
        return "Yesterday"
    return "{}".format(official_date.strftime('%B %d, %Y'))


@app.callback(Output('per_date', 'figure'),
              [Input('state-graph', 'clickData'),
               Input('radio-items', 'value')])
def update_new_case_graph(hoverData, group):

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
        #sub_df = per_day_stats_by_state[per_day_stats_by_state['province'] == country]

    elif group == 'county' and hoverData:
        selection = hoverData['points'][0]['customdata']
        print(selection)
        sub_df = CSBS[CSBS['county'] == selection]

    #     if sub_df.empty:
    #         country = "{} - No Data Available".format(country)
    #     sub_df_time = ""
    else:
        sub_df = JHU_TIME.groupby('Date').sum().reset_index()
        #sub_df_time = JHU_TIME.groupby('Date').sum().reset_index()
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
