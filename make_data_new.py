from datetime import date, timedelta
import warnings
import pandas as pd
import glob
import os
import logging
import pickle
import boto3
from botocore.exceptions import ClientError
import COVID19Py
import pandas
import sys
import numpy as np
from sklearn import preprocessing
from pmdarima.arima import auto_arima
import multiprocessing

warnings.simplefilter(
    "ignore", UserWarning)

# Cancel copy warnings of pandas
warnings.filterwarnings(
    "ignore", category=pd.core.common.SettingWithCopyWarning)

states_lookups = {
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


def predict(sub_df, days):
    sub_df['forcast'] = False
    base_date = sub_df.sort_values('Date')['Date'].iloc[-1]
    date_list = [base_date +
                 timedelta(days=x) for x in range(1, days+1)]
    forcasts = []
    upper_bounds = []
    lower_bounds = []
    for metric in ['confirmed', 'deaths']:
        fit = sub_df[metric]
        stepwise_model = auto_arima(
            fit,
            seasonal=False,
            trace=False,
            out_of_sample_size=2,
            error_action='ignore',
            suppress_warnings=True)
        model_fit = stepwise_model.fit(fit)
        forcast, conf = model_fit.predict(days, return_conf_int=True)
        forcasts.append(forcast)
        upper_bounds.append(conf[:, 1])
        lower_bounds.append(conf[:, 0])
    return pd.DataFrame({'Date': date_list,
                         'confirmed': forcasts[0],
                         'confirmed_upper': upper_bounds[0],
                         'confirmed_lower': lower_bounds[0],
                         'deaths': forcasts[1],
                         'deaths_upper': upper_bounds[1],
                         'deaths_lower': lower_bounds[1],
                         'forcast': True}).ffill().reset_index(drop=True)


def backfill_new_counties(df, key=['county', 'state', 'FIPS']):
    date_range = pd.date_range(pd.to_datetime(
        '2020-1-22'), df['Date'].max(), freq='1D')
    unique_group = key
    gb = df.groupby(unique_group)
    sub_dfs = []
    for g in gb.groups:
        sub_df = gb.get_group(g)
        sub_df = (
            sub_df.groupby('Date')
            .head(1)
            .set_index('Date')
            .reindex(date_range)
            .fillna(dict.fromkeys(['confirmed', 'deaths'], 0))
            .bfill()
            .ffill()
            .reset_index()
            .rename({'index': 'Date'}, axis=1))
        sub_df['Date_text'] = sub_df['Date'].dt.strftime('%m/%d/%y')
        sub_dfs.append(sub_df)
    all_concat = pd.concat(sub_dfs)
    assert((all_concat.groupby(key).count() == len(
        date_range)).all().all())
    return all_concat


def parse_timeline_date_api_json(json, source):
    for_pandas = []

    status_dfs = []
    if 'timelines' not in json['locations'][0].keys():
        raise ReferenceError('This is not a timeline json')

    dates = []
    timestamp = []
    confirmed = []
    deaths = []
    location = []
    ids = []
    lats = []
    lons = []
    province = []
    country_code = []
    country = []
    county = []
    for location in json['locations']:
        d = list(location['timelines']['confirmed']['timeline'].keys())
        size_len = len(d)
        confirmed_ = list(location['timelines']
                          ['confirmed']['timeline'].values())
        deaths_ = list(location['timelines']['deaths']['timeline'].values())
        timestamp += pd.to_datetime(d)
        assert(len(confirmed_) == len(deaths_) == size_len)
        ids += [location['id']]*size_len
        lats += [location['coordinates']['latitude']]*size_len
        lons += [location['coordinates']['longitude']]*size_len
        province += [location['province']]*size_len
        country_code += [location['country_code']]*size_len
        country += [location['country']]*size_len
        if 'county' in location.keys():
            county += [location['county']]*size_len
        else:
            county += ['']*size_len
        confirmed += confirmed_
        deaths += deaths_

    # print(len(lats),len(lons),len(timestamp))
    df = pd.DataFrame({'id': ids, 'lat': lats, 'lon': lons, 'Timestamp': timestamp, 'Date': "", 'province': province,
                       'country_code': country_code, 'country': country, 'county': county, 'confirmed': confirmed, 'deaths': deaths})
    df['source'] = source
    df['Date'] = df['Timestamp'].dt.date
    df['Date'] = pd.to_datetime(df['Date'])
    return df


def run_prediction(sub_df):
    location = sub_df[['country', 'state', 'county', 'granularity']].agg(','.join, axis=1).iloc[0]
    print('Running Location', location)
    prediction_df = predict(sub_df, 14)
    return pd.concat([sub_df, prediction_df]).ffill().fillna(0)


# COUNTRY
jhu_time = parse_timeline_date_api_json(COVID19Py.COVID19(data_source="jhu").getAll(timelines=True), 'JHU')

JHU_DF_AGG_COUNTRY = jhu_time.sort_values('confirmed')[::-1].groupby(['Date', 'country']).agg(
    {'lat': 'first', 'lon': 'first', 'confirmed': 'sum', 'deaths': 'sum', 'country_code': 'first'}).reset_index()

world_info = pd.read_csv('country_centroids_az8.csv')

manual_lookup_pop = {'Diamond Princess': 2670,
                     'Kosovo': 1810463,
                     'MS Zaandam': 615,
                     'Namibia': 2190000.0,
                     'Western Sahara': 500000}

merge_country = JHU_DF_AGG_COUNTRY.merge(world_info, left_on='country_code', right_on='iso_a2', how='left')
merge_country.loc[merge_country['pop_est'].isna(), 'pop_est'] = merge_country.loc[merge_country['pop_est'].isna(),
                                                                                  :].apply(lambda x: manual_lookup_pop[x['country']], axis=1)
merge_country.loc[merge_country['pop_est'] < 0, 'pop_est'] = merge_country.loc[merge_country['pop_est']
                                                                               < 0, :].apply(lambda x: manual_lookup_pop[x['country']], axis=1)
merge_country['state'] = ''
merge_country['county'] = ''
merge_country = merge_country[['Date', 'country', 'state', 'county', 'lat', 'lon',
                               'pop_est', 'confirmed', 'deaths', 'country_code']].rename({'pop_est': 'pop'}, axis=1)
merge_country['granularity'] = 'country'

# COUNTY
# Get some county info from Jack Parmer
county_info = pd.read_csv('https://raw.githubusercontent.com/jackparmer/mapbox-counties/master/lat_lon_counties.csv',
                          index_col=0, parse_dates=True, thousands=',')
county_info.columns = [i.strip() for i in county_info.columns]
county_info['WaterAreami2'] = county_info['WaterAreami2'].str.replace(',', '').str.replace('-', '0.0').astype(float)

# Here is the NY conent with FIPS but nothing else
ny_times_counties = pd.read_csv('https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv', parse_dates=['date']).rename(
    {'date': 'Date', 'cases': 'confirmed', 'fips': 'FIPS'}, axis=1).fillna(0)
ny_times_counties['FIPS'] = ny_times_counties['FIPS'].astype(int)
ny_times_counties = backfill_new_counties(ny_times_counties)
ny_times_counties['FIPS'] = ny_times_counties['FIPS'].astype(int)

# Here is the mergedcounties with the population info
merged_counties = ny_times_counties.merge(county_info, left_on='FIPS', right_on='FIPS', how='left')
merged_counties['country'] = 'United States'
merged_counties = merged_counties[['Date', 'country', 'state', 'county', 'Latitude', 'Longitude', 'Population(2010)', 'confirmed', 'deaths', 'FIPS']].rename(
    {'Latitude': 'lat', 'Longitude': 'lon', 'Population(2010)': 'pop'}, axis=1)
merged_counties['granularity'] = 'county'

# STATE
# Here is the NY state info
# Get state info from county by grouping by
state_info = county_info.groupby('State').agg({'Latitude': 'mean', 'Longitude': 'mean', 'Population(2010)': 'sum',
                                               'LandAreami2': 'sum', 'WaterAreami2': 'sum', 'TotalAreami2': 'sum'}).reset_index()
state_info['State'] = state_info['State'].apply(lambda x: states_lookups[x])

ny_times_states = pd.read_csv('https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-states.csv', parse_dates=['date']).rename(
    {'date': 'Date', 'cases': 'confirmed', 'fips': 'FIPS'}, axis=1).fillna(0)
ny_times_states = backfill_new_counties(ny_times_states, ['state'])

# Merging it with the state info from above
merged_states = ny_times_states.merge(state_info, left_on='state', right_on='State', how='left').drop('State', axis=1)
merged_states['county'] = ''
merged_states['country'] = 'United States'
merged_states = merged_states[['Date', 'country', 'state', 'county', 'Latitude', 'Longitude', 'Population(2010)', 'confirmed', 'deaths', 'FIPS']].rename(
    {'Latitude': 'lat', 'Longitude': 'lon', 'Population(2010)': 'pop'}, axis=1)
merged_states['granularity'] = 'state'

MASTER_ALL = pd.concat([merge_country, merged_states, merged_counties])

gb = MASTER_ALL.groupby(['country', 'state', 'county', 'granularity'])

print("Running PREDICTIONS")
pool = multiprocessing.Pool()
MASTER_ALL = pd.concat(pool.map(run_prediction, [i[1] for i in gb]))
MASTER_ALL.to_pickle('test_new.pkl', compression='gzip')
