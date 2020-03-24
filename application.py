import sys
import warnings
import numpy as np
import pandas as pd
import argparse
import pprint
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

# Import from S3:
jhu_df = pd.read_csv(
    'https://jordansdatabucket.s3-us-west-2.amazonaws.com/covid19data/jhu_df.csv.gz', index_col=0)
jhu_df_time = pd.read_csv(
    'https://jordansdatabucket.s3-us-west-2.amazonaws.com/covid19data/jhu_df_time.csv.gz', index_col=0)
csbs_df = pd.read_csv(
    'https://jordansdatabucket.s3-us-west-2.amazonaws.com/covid19data/csbs_df.csv.gz', index_col=0)
per_day_stats_by_country = pd.read_csv(
    'https://jordansdatabucket.s3-us-west-2.amazonaws.com/covid19data/country_df_per_day.csv.gz', index_col=0)
per_day_stats_by_state = pd.read_csv(
    'https://jordansdatabucket.s3-us-west-2.amazonaws.com/covid19data/provence_df_per_day.csv.gz', index_col=0)

jhu_df_time['Date'] = pd.to_datetime(jhu_df_time['Date'])
jhu_df['Date'] = pd.to_datetime(jhu_df['Date'])
csbs_df['Date'] = pd.to_datetime(csbs_df['Date'])

date_mapper = pd.DataFrame(
    jhu_df_time['Date'].unique(), columns=['Date'])
date_mapper['Date_text'] = date_mapper['Date'].dt.strftime('%m/%d/%y')
min_date = date_mapper.index[0]
max_date = date_mapper.index[-1]


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


def get_date_slider():
    how_many_labels = (len(date_mapper))//10
    marks = {k: {'label': v}
             for k, v in list(date_mapper['Date'].dt.strftime(
                 '%m/%d/%y').to_dict().items())[::how_many_labels]}
    last_key = list(marks.keys())[-1]
    todays_key = date_mapper.index[-1]
    # if last_key == todays_key:
    #     marks[last_key]['label'] == 'Today'
    # else:
    #     marks[todays_key] = {'label': 'Today'}

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
                                                value='country'),
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
                                    children=['Click Place on Map to Get More Information']),
                            dcc.Graph(id='per_date'),
                            dcc.Graph(id='per_date_line'),
                        ]),
                    html.Div(
                        id='table-container',
                        children=[])
                ]),
        ])


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
        normalizer = 'confirmed'
    elif 'active' in metrics:
        normalizer = 'Active'
    elif 'recovery' in metrics:
        normalizer = 'recovered'
    else:
        normalizer = 'deaths'

    official_date = date_mapper.iloc[date_int]['Date']
    # print(date_int, official_date)

    if group == 'country':
        country_mapper = jhu_df_time[
            jhu_df_time['Date'] == official_date].groupby(
            'country', as_index=False).apply(lambda x: x.sort_values('confirmed')[::-1].head(1)[['country', 'id', 'lat', 'lon']])
        sub_df = jhu_df_time[
            jhu_df_time['Date'] == official_date].groupby('country', as_index=False).sum()[['country', 'confirmed', 'deaths', 'recovered']].merge(
                country_mapper, on=['country'])
        sizeref = 2. * jhu_df_time.groupby(
            ['Date', group]).sum().max()[normalizer] / (20 ** 2)

        print(sub_df.columns)

    elif group == 'province':
        sub_df = jhu_df_time[jhu_df_time[group] != '']
        province_mapper = sub_df[
            sub_df['Date'] == official_date].groupby(
                group, as_index=False).apply(lambda x: x.sort_values('confirmed')[::-1].head(1)[[group, 'id', 'lat', 'lon']])
        sub_df = sub_df[
            sub_df['Date'] == official_date].groupby(group, as_index=False).sum()[['province', 'confirmed', 'deaths', 'recovered']].merge(province_mapper, on=['province'])

        # Now do it for the CSBS
        province_mapper = csbs_df.groupby(
            group, as_index=False).apply(lambda x: x.sort_values('confirmed')[::-1].head(1)[[group, 'id', 'lat', 'lon']])
        sub_df_csbs = csbs_df.groupby(group, as_index=False).sum()[
            ['province', 'confirmed', 'deaths', 'recovered']].merge(province_mapper, on=['province'])
        sub_df = pd.concat([sub_df, sub_df_csbs])

        sizeref = 2. * jhu_df_time.groupby(
            ['Date', group]).sum().max()[normalizer] / (20 ** 2)

    elif group == 'county':
        sub_df = csbs_df.groupby(
            ['county', 'state', 'lat', 'lon'], as_index=False).sum()
        sub_df.rename({'cases': 'confirmed'}, axis=1, inplace=1)
        sizeref = 2. * sub_df.max()[normalizer] / (20 ** 2)

    sub_df['Active'] = sub_df['confirmed'] - \
        sub_df['deaths'] - sub_df['recovered']
    sub_df['Text_Cases'] = sub_df[group] + '<br>Total Cases at {} : '.format(
        official_date.strftime('%m/%d/%y')) + sub_df['confirmed'].apply(lambda x: "{:,}".format(int(x)))
    sub_df['Text_Death'] = sub_df[group] + '<br>Total Deaths at {} : '.format(
        official_date.strftime('%m/%d/%y')) + sub_df['deaths'].apply(lambda x: "{:,}".format(int(x)))
    sub_df['Text_Recover'] = sub_df[group] + '<br>Total Recoveries at {} : '.format(
        official_date.strftime('%m/%d/%y')) + sub_df['recovered'].apply(lambda x: "{:,}".format(int(x)))

    sub_df['Text_Active'] = sub_df[group] + '<br>Total Active at {} : '.format(
        official_date.strftime('%m/%d/%y')) + sub_df['Active'].apply(lambda x: "{:,}".format(int(x)))

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
            name='recoveries',
            mode='markers',
            marker=dict(
                sizeref=sizeref,
                sizemin=10,
                size=sub_df['recovered'],
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
            name='active',
            mode='markers',
            marker=dict(
                sizeref=sizeref,
                sizemin=10,
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
            x=0.92,
            y=1,
            traceorder="normal",
            font=dict(
                family="sans-serif",
                size=14,
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
    official_date = date_mapper.iloc[date_int]['Date']
    if official_date.date() == date.today() - timedelta(days=1):
        return "Yesterday"
    return "{}".format(official_date.strftime('%B %d, %Y'))


@app.callback(Output('per_date', 'figure'),
              [Input('state-graph', 'clickData'),
               Input('radio-items', 'value')])
def update_new_case_graph(hoverData, group):

    if group == 'country' and hoverData:
        country = hoverData['points'][0]['customdata']
        sub_df = per_day_stats_by_country[per_day_stats_by_country['country'] == country]
    elif group == 'province' and hoverData:
        country = hoverData['points'][0]['customdata']
        sub_df = per_day_stats_by_state[per_day_stats_by_state['province'] == country]
        if sub_df.empty:
            country = "{} - No Data Available".format(country)
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


@app.callback(Output('per_date_line', 'figure'),
              [Input('state-graph', 'clickData'),
               Input('radio-items', 'value')])
def update_new_other_case_hover(hoverData, group):

    if group == 'country' and hoverData:
        country = hoverData['points'][0]['customdata']
        sub_df = per_day_stats_by_country[per_day_stats_by_country['country'] == country]
    elif group == 'province' and hoverData:
        country = hoverData['points'][0]['customdata']
        sub_df = per_day_stats_by_state[per_day_stats_by_state['province'] == country]
        if sub_df.empty:
            country = "{} - No Data Available".format(country)
    else:
        sub_df = per_day_stats_by_country.groupby('Date').sum().reset_index()
        country = 'World'

    dates = date_mapper['Date_text'].unique()
    # return px.line(sub_df, x='Date', y='New Cases')

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates,
                             y=sub_df['New Cases'],
                             name=country,
                             showlegend=False,
                             text=sub_df['New Cases'],
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
            color='white',
            showgrid=False,
        ),
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgb(52,51,50)')

    return fig


if __name__ == '__main__':
    app.run_server(debug=True, port=8050)
