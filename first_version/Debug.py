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
mapbox_style = 'mapbox://styles/jwillis0720/ck89nznm609pg1ipadkyrelvb'
mapbox_access_token = open('.mapbox_token').readlines()[0]

MERGE_NO_US, MERGED_CSBS_JHU, JHU_TIME, JHU_RECENT, DATE_MAPPER, CSBS, CENTROID_MAPPER = data.get_data()


def plot_map(date_int, group, metrics, figure):
    # Date INT comes from the slider and can only return integers:
    official_date = DATE_MAPPER.iloc[date_int]['Date']

    plot_data_frame = pd.DataFrame()
    JHU_TIME_DATE = JHU_TIME[JHU_TIME['Date'] == official_date]
    CSBS_TIME_DATE = CSBS[CSBS['Date'] == official_date]
    SUB_DF_COUNTRY = pd.DataFrame()
    SUB_DF_PROVINCE = pd.DataFrame()
    SUB_DF_COUNTY = pd.DataFrame()

    if 'country' in group:
        SUB_DF_COUNTRY = JHU_TIME_DATE.sort_values('confirmed')[::-1].groupby(['country']).agg(
            {'lat': 'first', 'lon': 'first', 'confirmed': 'sum', 'deaths': 'sum'}).reset_index().rename({'country': 'location'}, axis=1)
    if 'province' in group:
        SUB_DF_PROVINCE = JHU_TIME_DATE[JHU_TIME_DATE['province'] != ''].sort_values('confirmed')[::-1].groupby(['province']).agg(
            {'lat': 'first', 'lon': 'first', 'confirmed': 'sum', 'deaths': 'sum'}).reset_index()
        SUB_DF_PROVINCE = SUB_DF_PROVINCE.append(CSBS_TIME_DATE[CSBS_TIME_DATE['province'] != ''].sort_values('confirmed')[::-1].groupby(['province']).agg(
            {'lat': 'first', 'lon': 'first', 'confirmed': 'sum', 'deaths': 'sum'}).reset_index()).rename({'province': 'location'}, axis=1)
    if 'county' in group:
        SUB_DF_COUNTY = CSBS_TIME_DATE[CSBS_TIME_DATE['county'] != ''].sort_values('confirmed')[::-1].groupby(['county']).agg(
            {'lat': 'first', 'lon': 'first', 'confirmed': 'sum', 'deaths': 'sum'}).reset_index().rename({'county': 'location'}, axis=1)

    plot_data_frame = pd.concat(
        [SUB_DF_COUNTRY, SUB_DF_PROVINCE, SUB_DF_COUNTY])
    return plot_data_frame


print(plot_map(64, ['country', 'province', 'county'], [], []))
