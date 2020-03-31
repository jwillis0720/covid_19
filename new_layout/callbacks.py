import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc


def get_date_slider():
    markers = {0: {'label': '01/22/20'},
               6: {'label': '01/28/20'},
               12: {'label': '02/03/20'},
               18: {'label': '02/09/20'},
               24: {'label': '02/15/20'},
               30: {'label': '02/21/20'},
               36: {'label': '02/27/20'},
               42: {'label': '03/04/20'},
               48: {'label': '03/10/20'},
               54: {'label': '03/16/20'},
               60: {'label': '03/22/20'},
               66: {'label': '03/28/20'}}
    return dcc.Slider(
        id='date_slider',
        min=0,
        max=66,
        step=1,
        value=66,
        marks=markers
    )


def get_dropdown():
    dd = dcc.Dropdown(
        id='dropdown_container',
        options=[{'label': 'United States', 'value': 'COUNTRY_US'},
                 {'label': 'Worldwide', 'value': 'worldwide'},
                 {'label': 'China', 'value': 'COUNTRY_CHINA'}],
        value=['worldwide', 'COUNTRY_US', 'COUNTRY_China'],
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
        Output("map", "children"),
        [Input("date_slider", "value")]
    )
    def render_map(value):
        return get_dummy_graph('map-render')

    @app.callback(
        Output("content-readout", "children"),
        [Input("date_slider", "value")]
    )
    def render_graph(value):
        return get_dummy_graph('graphene')
