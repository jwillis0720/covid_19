import ast
from urllib.parse import urlparse, parse_qs, urlencode
import dash
from dash.dependencies import Input, Output, State
import dash_html_components as html
import dash_core_components as dcc
import callbacks

# to generate the tinyurl:
from pyshorteners import Shortener


def get_meta():
    meta_tags = [
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

    return meta_tags


app = dash.Dash(__name__, meta_tags=get_meta())
app.title = "COVID-19 Infection Dashboard"

app.config['suppress_callback_exceptions'] = True

# Serve layout in a function so we can update it dynamically
# Must go after the app is initialized


def serve_layout():
    callbacks.serve_data()
    return html.Div([
        dcc.Location(id='url', refresh=False),
        html.Div(id='page-layout')])


app.layout = serve_layout


# URL STATE FUNCTIONS
def encode_state(component_ids_zipped, values):
    """
    return a urlencoded string that encodes the current state of the app
    (as identified by component_ids+values)
    First encodes as a list of tuples of tuples of :
    (component_id, (parameter, value))
    This then gets encoded by urlencode as two separate querystring parameters
    e.g. ('tabs', ('value', 'cs_tab')) will get encoded as:
          ?tabs=value&tabs=cs_tab
    """

    statelist = [(component_ids_zipped[0][i],
                  (component_ids_zipped[1][i],
                   values[i]))
                 for i in range(len(values))
                 if values[i] is not None]

    print(statelist)
    params = urlencode(statelist,  doseq=True)
    print(params)
    return f'?{params}'


def parse_state(url):
    """
    Returns a dict that summarizes the state of the app at the time that the
    querystring url was generated.
    The querystring parameters come in pairs (see above), e.g.:
              ?tabs=value&tabs=cs_tab
    This will then be encoded as dictionary with the component_id as key
    (e.g. 'tabs') and a list (param, value) pairs (e.g. ('value', 'cs_tab')
    for that component_id as the item.
    lists (somewhat hackily detected by the first char=='['), get evaluated
    using ast.
    Numbers are appropriately cast as either int or float.
    """

    parse_result = urlparse(url)

    statedict = parse_qs(parse_result.query)
    if statedict:
        for key, value in statedict.items():
            statedict[key] = list(map(list, zip(value[0::2], value[1::2])))
            # go through every parsed value pv and check whether it is a list
            # or a number and cast appropriately:
            for pv in statedict[key]:
                # if it's a list
                if isinstance(pv[1], str) and pv[1][0] == '[':
                    pv[1] = ast.literal_eval(pv[1])

                # if it's a number
                if (isinstance(pv[1], str) and
                        pv[1].lstrip('-').replace('.', '', 1).isdigit()):

                    if pv[1].isdigit():
                        pv[1] = int(pv[1])
                    else:
                        pv[1] = float(pv[1])
    else:  # return empty dict
        statedict = dict()
    return statedict


def apply_value_from_querystring(params):
    """
    Funky function wrapper that looks up the component_id in the
    querystring parameter statedict, and if it finds it, loops
    through the (param, value) combinations in the (item) list
    and assign the right value to the right parameter.
    Every component that is saved in the querystring needs to be wrapped
    in this function in order for the saved parameters to be assigned
    during loading.
    """
    def wrapper(func):
        def apply_value(*args, **kwargs):
            if 'id' in kwargs and kwargs['id'] in params:
                param_values = params[kwargs['id']]
                for pv in param_values:
                    kwargs[pv[0]] = pv[1]
            return func(*args, **kwargs)
        return apply_value
    return wrapper

# LAYOUT SPECIFIC FUNCTIONS


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


def get_counter_cards():
    return [html.Div(id='cases-card',
                     className='card',
                     children=callbacks.get_total_cases()),

            html.Div(id='deaths-card',
                     className='card',
                     children=callbacks.get_total_deaths()),

            html.Div(id='mortality-card',
                     className='card',
                     children=callbacks.get_mortality_rate()),
            html.Div(id='growth-card',
                     className='card',
                     children=callbacks.get_growth_rate())]


def layout_header(params):
    header = html.Div(
        id="header",
        className='container',
        children=[
            html.Div(
                id="description",
                children=[
                    html.Div(className='title-div', children=[
                        html.H1(children=[
                            "COVID-19 ",
                            html.Span('Infection Dashboard')])]
                    ),
                    html.Div(className='bottom-div', children=[
                        html.H2(html.A('Jordan R. Willis PhD',
                                       href='http://jordanrwillis.com', target='_blank')),
                        html.Button(id="learn-more-button", className='button', n_clicks=0, children=[
                            html.Div(id='slide', children=html.A('Learn More'))])])]),
            html.Div(
                id='counters-container',
                children=get_counter_cards(),
            )
        ])
    return header


def get_map_dials(params):
    return [
        apply_value_from_querystring(params)(dcc.Checklist)(id='check-locations',
                                                            labelClassName='map-list',
                                                            options=[
                                                                {'label': 'Country',
                                                                 'value': 'country'},
                                                                {'label': 'Province/State',
                                                                 'value': 'province'},
                                                                {'label': 'County',
                                                                 'value': 'county'}],
                                                            value=['country', 'province']),
        html.H3(id="map-title"),
        apply_value_from_querystring(params)(dcc.Checklist)(id='check-metrics',
                                                            labelClassName='map-list',
                                                            options=[
                                                                {'label': 'Confirmed',
                                                                 'value': 'confirmed'},
                                                                {'label': 'Deaths',
                                                                 'value': 'deaths'}],
                                                            value=[
                                                                'confirmed', 'deaths'])]


def get_tabs_container(params):
    return apply_value_from_querystring(params)(dcc.Tabs)(
        id='tabs-values', parent_className='tabs-container', className='custom-tabs',
        children=[
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


def layout_app(params):
    return html.Div(id='app-container', className='app-container', children=[
        html.Div(id='left-container', className='left-container', children=[
            html.Div(id='slider-container', className='container',
                     children=[
                       html.H4('Slide to Change Date'),
                       apply_value_from_querystring(params)(dcc.Slider)(
                           id='date_slider',
                           min=callbacks.get_min_date(),
                           max=callbacks.get_max_date(),
                           step=1,
                           value=callbacks.get_max_date(),
                           marks=callbacks.get_date_marks()
                       )]),

            html.Div(id='map-container', className='container', children=[
                html.Div(id='map-dials', children=get_map_dials(params)),
                dcc.Graph(id='map')
            ])]),
        html.Div(id='right-container', className='container', children=[
            html.H4('Select For Comparisons'),
            html.Div(id='location-dropdown',
                     children=[
                         apply_value_from_querystring(params)(dcc.Dropdown)(
                             id='dropdown_container',
                             options=callbacks.get_dropdown_options(),
                             value=['worldwide'],
                             multi=True,
                             style={'position': 'relative',
                                    'zIndex': '3', 'font-size': '75%'}
                         )
                     ]),
            html.Div(id='tabs-container',
                     children=[
                         get_tabs_container(params)
                     ]),
            html.Div(id='sub-options', children=[
                apply_value_from_querystring(params)(dcc.RadioItems)(
                    id='log-check',
                    options=[{'label': 'Log', 'value': 'log'}, {
                        'label': 'Linear', 'value': 'linear'}],
                    value='log'),
                apply_value_from_querystring(params)(dcc.RadioItems)(
                    id='deaths-confirmed',
                    options=[{'label': 'Confirmed', 'value': 'confirmed'},
                             {'label': 'Deaths', 'value': 'deaths'}],
                    value='confirmed')]),
            dcc.Graph(id='content-readout')]),
        html.Div(id='table-container', className='container')
    ])


def build_layout(params):
    # Every time we serve the layout, we remake the Data:
    # callbacks.serve_data()
    return html.Div(id='root-container', children=[
        layout_header(params),
        layout_app(params),
        markdown_popup(),
        # html.Button(id="tiny-url", className='button', n_clicks=0, children=[
        #     html.Div(id='tiny_url_div', children=html.A('Learn More'))])

    ])


# List of component (id, parameter) tuples. Can be be any parameter
# not just (., 'value'), and the value van be either a single value or a list:
component_ids = [
    ('date_slider', 'value'),
    ('check-locations', 'value'),
    ('check-metrics', 'value'),
    ('dropdown_container', 'value'),
    ('tabs-values', 'value')
]

# Turn the list of 4 (id, param) tuples into a list of
# one component id tuple (len=4) and one parameter tuple (len=4):
component_ids_zipped = list(zip(*component_ids))

@app.callback(Output('page-layout', 'children'),
              [Input('url', 'href')])
def page_load(href):
    """
    Upon page load, take the url, parse the querystring, and use the
    resulting state dictionary to build up the layout.
    """
    if not href:
        return []
    state = parse_state(href)
    return build_layout(state)


@app.callback(Output('url', 'search'),
              inputs=[Input(id, param) for (id, param) in component_ids])
def update_url_state(*values):
    """
    When any of the (id, param) values changes, this callback gets triggered.
    Passes the list of component id's, the list of component parameters
    (zipped together in component_ids_zipped), and the value to encode_state()
    and return a properly formed querystring.
    """
    return encode_state(component_ids_zipped, values)


@app.callback(Output('tiny_url', 'children'),
              [Input('tinyurl-button', 'n_clicks')],
              [State('url', 'href')])
def return_short(n_clicks, state):
    """
    Return a tinyurl whenever the `tinyurl-button` is clicked:
    """
    if not state or not n_clicks:
        return "No url to shorten"
    elif n_clicks > 0 and state:
        shortener = Shortener()
        return shortener.tinyurl.short('http://127.0.0.1:8050' + state)


callbacks.register_callbacks(app)
application = app.server


if __name__ == '__main__':
    app.run_server(debug=True)
