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


# mapbox_style = "mapbox://styles/plotlymapbox/cjvprkf3t1kns1cqjxuxmwixz"
mapbox_style = 'dark'
mapbox_access_token = open('.mapbox_token').readlines()[0]

# Import from S3:
merged_df = pd.read_csv(
    'https://jordansdatabucket.s3-us-west-2.amazonaws.com/covid19data/Merged_df.csv.gz', index_col=0).fillna('')
per_day_stats_by_state = pd.read_csv(
    'https://jordansdatabucket.s3-us-west-2.amazonaws.com/covid19data/per_day_stats_by_state.csv.gz', index_col=0)
per_day_stats_by_country = pd.read_csv(
    'https://jordansdatabucket.s3-us-west-2.amazonaws.com/covid19data/per_day_stats_by_country.csv.gz', index_col=0)
per_day_stats_by_county = pd.read_csv(
    'https://jordansdatabucket.s3-us-west-2.amazonaws.com/covid19data/per_day_stats_by_county.csv.gz', index_col=0)


merged_df['Date'] = pd.to_datetime(merged_df['Date'])
merged_df['Active'] = merged_df['Cases'] - \
    merged_df['Deaths'] - merged_df['Recovery']
per_day_stats_by_state['Date'] = pd.to_datetime(
    per_day_stats_by_state['Date']).fillna('')
per_day_stats_by_country['Date'] = pd.to_datetime(
    per_day_stats_by_country['Date']).fillna('')
per_day_stats_by_county['Date'] = pd.to_datetime(
    per_day_stats_by_county['Date']).fillna('')

date_mapper = pd.DataFrame(
    merged_df['Date'].unique(), columns=['Date'])
date_mapper['Date_text'] = date_mapper['Date'].dt.strftime('%m/%d/%y')
min_date = min(date_mapper.index)
max_date = max(date_mapper.index)

centroid_country_mapper = merged_df.groupby(
    'Country/Region').apply(lambda x: x.sort_values('Cases')[::-1].iloc[0][['Lat', 'Long']])
centroid_country_mapper = {x[0]: {'Long': x[1]['Long'], 'Lat': x[1]['Lat']}
                           for x in centroid_country_mapper.iterrows()}


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
        value=max_date,
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
                                id="slider-container",
                                children=[
                                    html.P(
                                        id="slider-text",
                                        children="Drag the Slider to Change the Reported Date:",
                                    ),
                                    get_date_slider()
                                ],
                            ),

                            html.Div(
                                id="heatmap-container",
                                children=[
                                    html.Div(id='heatmap-header', children=[

                                        dcc.RadioItems(
                                            id='radio-items',
                                            labelClassName='radio-list',
                                            options=[
                                                {'label': 'Country',
                                                    'value': 'Country/Region'},
                                                {'label': 'State/Province',
                                                 'value': 'Province/State'},
                                                # {'label': 'County',
                                                #  'value': 'County'}
                                            ],
                                            value='Country/Region'),
                                        html.P(
                                            id="heatmap-title",
                                        ),
                                        dcc.Checklist(
                                            id='check-items',
                                            labelClassName='radio-list',
                                            options=[
                                                {'label': 'Cases',
                                                    'value': 'cases'},
                                                {'label': u'Deaths',
                                                    'value': 'deaths'},
                                                {'label': 'Recoveries',
                                                    'value': 'recovery'},
                                                {'label': 'Active Cases',
                                                    'value': 'active'}
                                            ],
                                            value=['cases', 'deaths']
                                        ),
                                    ]),
                                    dcc.Graph(id='state-graph')
                                ],
                            ),

                        ],
                    ),
                    html.Div(
                        id="graph-container",
                        children=[
                           html.P(id='graph-container-tile'),
                           dcc.Graph(id='per_date'),
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
        normalizer = 'Cases'
    elif 'active' in metrics:
        normalizer = 'Active'
    elif 'recovery' in metrics:
        normalizer = 'Recovery'
    else:
        normalizer = 'Deaths'

    #print(group, metrics)

    official_date = date_mapper.iloc[date_int]['Date']
    #print(date_int, official_date)

    if group == 'Country/Region':
        sub_df = merged_df[(merged_df['Date'] == official_date) & (merged_df[group] != "")].groupby(
            group).sum().reset_index()
        sub_df['Lat'] = sub_df['Country/Region'].apply(
            lambda x: centroid_country_mapper[x]['Lat'])
        sub_df['Long'] = sub_df['Country/Region'].apply(
            lambda x: centroid_country_mapper[x]['Long'])

        sizeref = 2. * merged_df.groupby(
            ['Date', group]).sum().max()[normalizer] / (20 ** 2)

    elif group == 'Province/State':
        sub_df = merged_df[(merged_df['Date'] == official_date) & (merged_df[group] != "") & (merged_df['County'] == '')].groupby(
            group).sum().reset_index()
        county_df = merged_df[(merged_df['Date'] == official_date) & (merged_df['County'] != '')].groupby(
            group).sum().reset_index()
        sub_df = sub_df.merge(county_df, on=[
                              'Province/State'], suffixes=('', '_county'), how='outer').fillna(0)
        sub_df['Cases'] = sub_df['Cases'] + sub_df['Cases_county']
        sub_df['Deaths'] = sub_df['Deaths'] + sub_df['Deaths_county']
        sub_df['Recovery'] = sub_df['Deaths'] + sub_df['Recovery_county']
        sizeref = 2. * merged_df.groupby(
            ['Date', group]).sum().max()[normalizer] / (20 ** 2)

    else:
        sub_df = merged_df[(merged_df['Date'] == official_date) & (merged_df['County'] != '')].groupby(
            group).sum().reset_index()
        sizeref = 2. * merged_df.groupby(
            ['Date', group]).sum().max()[normalizer] / (50 ** 2)

    sub_df['Active'] = sub_df['Cases'] - sub_df['Deaths'] - sub_df['Recovery']
    sub_df['Text_Cases'] = sub_df[group] + '<br>Total Cases at {} : '.format(
        official_date.strftime('%m/%d/%y')) + sub_df['Cases'].apply(lambda x: "{:,}".format(int(x)))
    sub_df['Text_Death'] = sub_df[group] + '<br>Total Deaths at {} : '.format(
        official_date.strftime('%m/%d/%y')) + sub_df['Deaths'].apply(lambda x: "{:,}".format(int(x)))
    sub_df['Text_Recover'] = sub_df[group] + '<br>Total Recoveries at {} : '.format(
        official_date.strftime('%m/%d/%y')) + sub_df['Recovery'].apply(lambda x: "{:,}".format(int(x)))

    sub_df['Text_Active'] = sub_df[group] + '<br>Total Active at {} : '.format(
        official_date.strftime('%m/%d/%y')) + sub_df['Active'].apply(lambda x: "{:,}".format(int(x)))

    fig = go.Figure()
    if 'cases' in metrics:
        fig.add_trace(go.Scattermapbox(
            lon=sub_df['Long'] +
            np.random.normal(0, .02, len(sub_df['Long'])),
            lat=sub_df['Lat'] +
            np.random.normal(0, .02, len(sub_df['Lat'])),
            customdata=sub_df[group],
            textposition='top right',
            text=sub_df['Text_Cases'],
            hoverinfo='text',
            mode='markers',
            marker=dict(
                sizeref=sizeref,
                sizemin=3,
                size=sub_df['Cases'],
                color='yellow')))

    if 'deaths' in metrics:
        fig.add_trace(go.Scattermapbox(
            lon=sub_df['Long'] +
            np.random.normal(0, .02, len(sub_df['Long'])),
            lat=sub_df['Lat'] +
            np.random.normal(0, .02, len(sub_df['Lat'])),
            customdata=sub_df[group],
            textposition='top right',
            text=sub_df['Text_Death'],
            hoverinfo='text',
            mode='markers',
            marker=dict(
                sizeref=sizeref,
                sizemin=3,
                size=sub_df['Deaths'],
                color='red')))

    if 'recovery' in metrics:
        fig.add_trace(go.Scattermapbox(
            lon=sub_df['Long'] +
            np.random.normal(0, .02, len(sub_df['Long'])),
            lat=sub_df['Lat'] +
            np.random.normal(0, .02, len(sub_df['Lat'])),
            customdata=sub_df[group],
            textposition='top right',
            text=sub_df['Text_Recover'],
            hoverinfo='text',
            mode='markers',
            marker=dict(
                sizeref=sizeref,
                sizemin=3,
                size=sub_df['Recovery'],
                color='green')))
    if 'active' in metrics:
        fig.add_trace(go.Scattermapbox(
            lon=sub_df['Long'] +
            np.random.normal(0, .02, len(sub_df['Long'])),
            lat=sub_df['Lat'] +
            np.random.normal(0, .02, len(sub_df['Lat'])),
            customdata=sub_df[group],
            textposition='top right',
            text=sub_df['Text_Active'],
            hoverinfo='text',
            mode='markers',
            marker=dict(
                sizeref=sizeref,
                sizemin=3,
                size=sub_df['Active'],
                color='orange')))

    if not metrics:
        fig.add_trace(go.Scattermapbox(
            lon=[],
            lat=[]
        ))
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


@app.callback(Output('per_date', 'figure'),
              [Input('state-graph', 'clickData'),
               Input('radio-items', 'value')])
def update_new_case_graph(hoverData, group):

    if group == 'Country/Region' and hoverData:
        country = hoverData['points'][0]['customdata']
        sub_df = per_day_stats_by_country[per_day_stats_by_country['Country/Region'] == country]
    elif group == 'Province/State' and hoverData:
        country = hoverData['points'][0]['customdata']
        sub_df = per_day_stats_by_state[per_day_stats_by_state['Province/State'] == country]
    else:
        sub_df = per_day_stats_by_country.groupby('Date').sum().reset_index()
        country = 'World'

    dates = date_mapper['Date_text'].unique()
    fig = go.Figure()
    fig.add_trace(go.Bar(x=dates,
                         y=sub_df['New Cases'],
                         name=country,
                         showlegend=False,
                         text=sub_df['New Cases'],
                         textposition='auto',
                         texttemplate='%{y:,f}',
                         hovertemplate='Date - %{x}<br>New Cases - %{y:,f}',

                         marker=dict(
                             color='white',
                             line=dict(
                                 color='white')
                         )))

    fig.update_layout(
        title=dict(text='New Cases Per Day: {}'.format(
            country), font=dict(color='white', size=24)),
        xaxis_tickfont_size=14,
        yaxis=dict(
            title=dict(text='New Cases', standoff=2),
            titlefont_size=18,
            tickfont_size=18,
            showgrid=False,
            color='white',
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
        bargroupgap=0.1)  # gap between bars of the same location coordinate.

    return fig


if __name__ == '__main__':
    app.run_server(debug=True, port=8050)
