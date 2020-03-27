# Import from S3:
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
    from plotly.subplots import make_subplots
except ImportError:
    sys.exit('Please install dash, e.g, pip install dash')


def get_data():

    global JHU_RECENT
    global DATE_MAPPER
    global JHU_TIME
    global CSBS
    global CENTROID_MAPPER
    global MERGED_CSBS_JHU

    jhu_df = pd.read_csv(
        'https://jordansdatabucket.s3-us-west-2.amazonaws.com/covid19data/jhu_df.csv.gz', index_col=0)
    jhu_df_time = pd.read_csv(
        'https://jordansdatabucket.s3-us-west-2.amazonaws.com/covid19data/jhu_df_time.csv.gz', index_col=0)
    csbs_df = pd.read_csv(
        'https://jordansdatabucket.s3-us-west-2.amazonaws.com/covid19data/csbs_df.csv.gz', index_col=0)
    # per_day_stats_by_country = pd.read_csv(
    #     'https://jordansdatabucket.s3-us-west-2.amazonaws.com/covid19data/country_df_per_day.csv.gz', index_col=0)
    # per_day_stats_by_state = pd.read_csv(
    #     'https://jordansdatabucket.s3-us-west-2.amazonaws.com/covid19data/provence_df_per_day.csv.gz', index_col=0)

    jhu_df_time['Date'] = pd.to_datetime(jhu_df_time['Date'])
    jhu_df['Date'] = pd.to_datetime(jhu_df['Date'])
    csbs_df['Date'] = pd.to_datetime(csbs_df['Date'])

    date_mapper = pd.DataFrame(
        jhu_df_time['Date'].unique(), columns=['Date'])
    date_mapper['Date_text'] = date_mapper['Date'].dt.strftime('%m/%d/%y')

    # JHU and CSBS are out of sync, so we should use the latest date from JHU
    latest_date = jhu_df_time.sort_values('Date')['Date'].iloc[-1]
    merge = pd.concat([jhu_df, csbs_df[csbs_df['Date'] == latest_date]])
    merge = merge.fillna('')

    # Countries without a code may be a problem
    problem_countries = merge[merge['country_code'] == '']['country'].tolist()

    # I know for a fact Namibia has no coud
    merge.loc[merge['country'] == 'Namibia', 'country_code'] = ''

    # Lets grab the centroids from this great spread sheet
    centroid_mapper = pd.read_csv('country_centroids_az8.csv')
    problem_states = merge[~merge['country_code'].isin(
        centroid_mapper['iso_a2'])]
    new_merge = merge.merge(
        centroid_mapper, left_on='country_code', right_on='iso_a2')
    # new_merge['case_rate'] = new_merge['confirmed']/new_merge['pop_est'] * 100
    # new_merge['death_rate'] = new_merge['deaths']/new_merge['pop_est'] * 100
    # new_merge['confirmed_no_death'] = new_merge['confirmed'] - \
    #     new_merge['deaths']

    # If something is has the same name for continent and subregion, lets just add the word _subregion
    new_merge.loc[new_merge['continent'] == new_merge['subregion'],
                  'subregion'] = new_merge['subregion'] + ' Subregion'

    # # Lets remove the US Data since we are doubel counting htis by merging CSBSS
    new_merge_no_us = new_merge[~((new_merge['country'] == 'US') & (
        new_merge['province'] == ''))]
    MERGED_CSBS_JHU = new_merge
    JHU_TIME = jhu_df_time
    JHU_RECENT = jhu_df
    DATE_MAPPER = date_mapper
    CSBS = csbs_df
    CENTROID_MAPPER = centroid_mapper
    MERGE_NO_US = new_merge_no_us
    return MERGE_NO_US, MERGED_CSBS_JHU, JHU_TIME, JHU_RECENT, DATE_MAPPER, CSBS, CENTROID_MAPPER
