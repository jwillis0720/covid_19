import dash
import dash_core_components as dcc
import dash_html_components as html

import callbacks


def layout_header():
    header = html.Div(
        id="header",
        children=[
            html.Div(
                id="description",
                children=[
                    html.H1(
                        children=["COVID-19 ", html.Span('Infection Dashboard')]),
                    html.H2([html.A('Jordan R. Willis PhD',
                                    href='http://jordanrwillis.com', target='_blank')]),
                    html.Button(
                        id="learn-more-button", className='button', n_clicks=0, children=[
                            html.Div(id='slide', children=html.A('Learn More'))]),
                ]
            ),
            html.Div(
                id='counters-container',
                children=get_counter_cards(),
            )
        ])
    return header


def get_counter_cards():
    return [html.Div(id='cases-card',
                     className='card',
                     children=[
                         html.H3('Total Cases'),
                         html.P(id='total-cases',
                                children=[3000])]),
            html.Div(id='deaths-card',
                     className='card',
                     children=[
                         html.H3('Total Deaths'),
                         html.P(id='total-deaths',
                                children=[3000])]),
            html.Div(id='mortality-card',
                     className='card',
                     children=[
                         html.H3('Mortality Rate'),
                         html.P(id='mortality-rate',
                                children=[30000])]),
            html.Div(id='growth-card',
                     className='card',
                     children=[
                         html.H3('Growth Factor'),
                         html.P(id='growth-rate',
                                children=[3000])])]


def get_map_dials():
    return [
        dcc.Checklist(id='check-locations',
                      labelClassName='map-list',
                      options=[
                          {'label': 'Country',
                           'value': 'country'},
                          {'label': 'Province/State',
                           'value': 'province'},
                          {'label': 'County',
                           'value': 'county'}],
                      value=['country', 'province']),
        html.H3(id="map-title", children='Yesteryear'),
        dcc.Checklist(id='check-metrics',
                      labelClassName='map-list',
                      options=[
                          {'label': 'Confirmed',
                           'value': 'confirmed'},
                          {'label': 'Deaths',
                           'value': 'deaths'}],
                      value=[
                          'confirmed', 'deaths'])]


def get_tabs_container():
    return dcc.Tabs(id='tabs-values', parent_className='tabs-container', className='custom-tabs', children=[
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
        value='total_cases_graph')


def get_content_readout():
    return dcc.Loading(id='content-loading-container', className='content-container', type='cube')


def layout_app():
    return html.Div(id='app-container', className='app-container', children=[
        html.Div(id='left-container', className='left-container', children=[
            html.Div(id='slider-container',
                     children=callbacks.get_date_slider()),
            html.Div(id='map-container', children=[
                html.Div(id='map-dials', children=get_map_dials()),
                html.Div(id='map')
            ])
        ]),
        html.Div(id='right-container', className='right-container', children=[
            html.Div(id='location-dropdown',
                     children=callbacks.get_dropdown()),
            html.Div(id='tabs-container', children=get_tabs_container()),
            html.Div(id='content-readout', children=get_content_readout()),

        ])
    ])


def serve_dash_layout():
    return html.Div(id='root-container', children=[
        layout_header(),
        layout_app(),
        markdown_popup()
    ])


def markdown_popup():
    '''The style is toggled in a callback between display:block and none'''
    return html.Div(
        id="markdown",
        className="modal",
        style={"display": "none"},
        children=(
            html.Div(
                className="markdown-container",
                children=[
                    html.Div(
                        className="close-container",
                        children=html.Button(
                            "Close",
                            id="markdown_close",
                            n_clicks=0,
                            className="closeButton",
                        ),
                    ),
                    html.Div(
                        className="markdown-text",
                        children=[
                            dcc.Markdown(
                                children=open('ReadMeLine.md').readlines()
                            )
                        ],
                    ),
                ],
            )
        ),
    )
