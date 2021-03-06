import ast
from urllib.parse import urlparse, parse_qs, urlencode
import dash
from dash.dependencies import Input, Output, State
import dash_html_components as html
import dash_core_components as dcc
import callbacks
import warnings
import pandas as pd
# /
# to generate the tinyurl:

# Cancel copy warnings of pandas
warnings.filterwarnings(
    "ignore", category=pd.core.common.SettingWithCopyWarning)


def get_meta():
    meta_tags = [
        {"name": "viewport",
         "content": "width=device-width, initial-scale=1.0"},
        {"name": "author",
         "content": "Jordan R. Willis PhD"},
        { 'name':"google-site-verification",'content':"vEErPS3AZ_ZswYYV84KWjY5BAcnw_V_xvI8Hb4n_Mu0"},
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


# external CSS stylesheets
external_stylesheets = [
    'https://cdnjs.cloudflare.com/ajax/libs/weather-icons/2.0.9/css/weather-icons.min.css',
    'https://cdnjs.cloudflare.com/ajax/libs/weather-icons/2.0.9/css/weather-icons-wind.min.css']


app = dash.Dash(__name__, meta_tags=get_meta(), external_stylesheets=external_stylesheets)
app.title = "COVID-19 Bored"

app.config['suppress_callback_exceptions'] = True
app.index_string = open('assets/customIndex.html').read()

# Serve layout in a function so we can update it dynamically
# Must go after the app is initialized


def serve_layout():
    callbacks.serve_data(serve_local=False)
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

    # print(statelist)
    params = urlencode(statelist,  doseq=True)
    # print(params)
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
                     className='card tooltip',
                     children=callbacks.get_total_cases()),

            html.Div(id='deaths-card',
                     className='card tooltip',
                     children=callbacks.get_total_deaths()),

            html.Div(id='mortality-card',
                     className='card tooltip',
                     children=callbacks.get_mortality_rate()),
            html.Div(id='growth-card',
                     className='card tooltip',
                     children=callbacks.get_growth_rate()),
            html.Div(id='relative-card-confirm',
                     className='card tooltip',
                     children=callbacks.get_relative_card())]


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
                            "COVID-19 Bored"])]
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
                                                            options=[{'label': 'Country',
                                                                      'value': 'country'},
                                                                     {'label': 'State',
                                                                      'value': 'province'},
                                                                     {'label': 'County',
                                                                      'value': 'county'}],
                                                            value=['country']),
        html.H3(id="map-title"),
        apply_value_from_querystring(params)(dcc.RadioItems)(id='check-metrics',
                                                             labelClassName='map-list',
                                                             options=[
                                                                {'label': 'Confirmed',
                                                                 'value': 'confirmed'},
                                                                {'label': 'Deaths',
                                                                 'value': 'deaths'}],
                                                             value='confirmed')]


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
                    value='exponential'),
            dcc.Tab(label='Growth Rate',
                    className='custom-tab',
                    selected_className='custom-tab--selected',
                    value='gr'),

        ],
        value='total_cases_graph')


def get_table_tabs_container(params):
    return apply_value_from_querystring(params)(dcc.Tabs)(
        id='tabs-table-values', parent_className='tabs-container', className='custom-tabs',
        children=[
            dcc.Tab(label='Confirmed Cases',
                    className='custom-tab',
                    selected_className='custom-tab--selected',
                    value='conf-tab'),
            dcc.Tab(label='Confirmed Deaths',
                    className='custom-tab',
                    selected_className='custom-tab--selected',
                    value='deaths_tab'),

        ],
        value='conf-tab'
    )


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
                           value=callbacks.get_max_date()-14,
                           marks=callbacks.get_date_marks()
                       )]),

            html.Div(id='map-container', className='container', children=[
                html.Div(id='map-dials', children=get_map_dials(params)),
                dcc.Graph(id='map'),
                apply_value_from_querystring(params)(dcc.Checklist)(
                    id='relative_rate_check',
                    options=[{'label': 'Show Relative Rate', 'value': 'relative'}],
                    value=['relative']
                )
            ])]),
        html.Div(id='right-container', className='container', children=[
            html.H4('Select For Comparisons'),
            html.Div(id='location-dropdown',
                     children=[
                         apply_value_from_querystring(params)(dcc.Dropdown)(
                             id='dropdown_container',
                             options=callbacks.get_dropdown_options(),
                             value=callbacks.get_default_dropdown(),
                             multi=True,
                             style={'position': 'relative',
                                    'zIndex': '3'},
                             placeholder='Select a location..'
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
                    value='confirmed'),
                apply_value_from_querystring(params)(dcc.Checklist)(
                    id='prediction',
                    options=[{'label': 'Show Predictions', 'value': 'prediction'}],
                    value=['prediction']
                )]),
            dcc.Graph(id='content-readout')]),
        html.Div(id='table-container', className='container', children=[
            get_table_tabs_container(params),
            html.Div(id='table-div')])
    ])


def build_layout(params):
    # Every time we serve the layout, we remake the Data:
    # callbacks.serve_data()
    return html.Div(id='root-container', children=[
        layout_header(params),
        layout_app(params),
        markdown_popup(),
        # html.Button(id="tiny-url", className='button', n_clicks=0, children=[
        # html.Div(id='tiny_url_div', children=html.A('Get Link'))]),
        # html.Div(id='url-container', style={'display': 'none'})
    ])


# List of component (id, parameter) tuples. Can be be any parameter
# not just (., 'value'), and the value van be either a single value or a list:
component_ids = [
    ('date_slider', 'value'),
    ('check-locations', 'value'),
    ('check-metrics', 'value'),
    ('dropdown_container', 'value'),
    ('tabs-values', 'value'),
    ('log-check', 'value'),
    ('deaths-confirmed', 'value'),
    ('prediction', 'value'),
    ('relative_rate_check', 'value'),
    ('tabs-table-values', 'value')
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


callbacks.register_callbacks(app)
application = app.server


if __name__ == '__main__':
    app.run_server(debug=True)
