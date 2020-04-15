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


def upload_file(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        s3_client.upload_file(
            file_name, bucket, object_name,  ExtraArgs={'ACL': 'public-read'})
    except ClientError as e:
        logging.error(e)
        return False
    return True


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
        timestamp += pandas.to_datetime(d)
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
    df = pandas.DataFrame({'id': ids, 'lat': lats, 'lon': lons, 'Timestamp': timestamp, 'Date': "", 'province': province,
                           'country_code': country_code, 'country': country, 'county': county, 'confirmed': confirmed, 'deaths': deaths})
    df['source'] = source
    df['Date'] = df['Timestamp'].dt.date
    df['Date'] = pandas.to_datetime(df['Date'])
    return df


def parse_current_date_api_json(json, source):
    for_pandas = []
    confirmed = []
    deaths = []
    recovered = []
    for location in json['locations']:
        entry = {
            'id': location['id'],
            'lat': location['coordinates']['latitude'],
            'lon': location['coordinates']['longitude'],
            'Timestamp': pandas.to_datetime(location['last_updated']),
            'Date': "",
            'province': location['province'],
            'country_code': location['country_code'],
            'country': location['country'],
            'county': '',
            'confirmed': location['latest']['confirmed'],
            'deaths': location['latest']['deaths']}
        if 'county' in location.keys():
            entry['county'] = location['county']
        if 'state' in location.keys():
            entry['state'] = location['state']
        entry['source'] = source
        for_pandas.append(entry)
    df = pd.DataFrame(for_pandas)
    df['Date'] = df['Timestamp'].dt.date
    df['Date'] = pandas.to_datetime(df['Date'])
    return df


def per_x_cases(grouper, df):
    new_cases_by_country = []
    date_mapper = pd.DataFrame(
        df['Date'].unique(), columns=['Date']).sort_values('Date').reset_index(drop=True)
    dates = date_mapper['Date']
    # print(dates)
    sub_group = df[df[grouper] != ""]
    groupers = sub_group[grouper].unique()

    for group in groupers:
        sub_country = sub_group[sub_group[grouper] == group]
        new_cases_by_country.append(
            {grouper: group, 'Date': dates[0],
             'New Cases': sub_country.loc[sub_country['Date'] == dates[0], 'confirmed'].sum(),
             'New Deaths': 0})
        for date_index in range(1, len(dates)):
            current_date = dates[date_index]
            day_before = dates[date_index-1]
            # print(current_date,day_before)
            t_c, t_d = sub_country.loc[sub_country['Date']
                                       == current_date, :].sum()[['confirmed', 'deaths']]

            y_c, y_d = sub_country.loc[sub_country['Date']
                                       == day_before, :].sum()[['confirmed', 'deaths']]

            new_cases = t_c - y_c
            new_deaths = t_d - y_d
            if new_cases < 0:
                new_cases = 0
            if new_deaths < 0:
                new_deaths = 0
                print(current_date, day_before, t_c, y_c, group)
                # return sub_country
            new_cases_by_country.append(
                {grouper: group, 'Date': current_date, 'New Cases': new_cases,
                 'New Deaths': new_deaths})
    return pd.DataFrame(new_cases_by_country)


def backfill_new_counties(df):
    date_range = pd.date_range(pd.to_datetime(
        '2020-1-22'), df['Date'].max(), freq='1D')
    unique_group = ['country', 'province', 'county']
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
        sub_df['Timestamp'] = pd.to_datetime(sub_df['Date'], utc=True)
        sub_dfs.append(sub_df)
    all_concat = pd.concat(sub_dfs)
    assert((all_concat.groupby(['province', 'country', 'county']).count() == len(
        date_range)).all().all())
    return all_concat


# Get current streaming API
covid19_csbs = COVID19Py.COVID19(data_source="csbs").getAll(timelines=True)
covid19_jhu = COVID19Py.COVID19(data_source="jhu").getAll(timelines=True)


# Gets current values
jhu_current = parse_current_date_api_json(covid19_jhu, 'JHU')
csbs_current = parse_current_date_api_json(covid19_csbs, 'CSBS')

# Gets timeline values
jhu_time = parse_timeline_date_api_json(covid19_jhu, 'JHU')

# Get Date text
csbs_current['Date_text'] = csbs_current['Timestamp'].dt.strftime('%m/%d/%y')
jhu_time['Date_text'] = jhu_time['Timestamp'].dt.strftime('%m/%d/%y')
jhu_current['Date_text'] = jhu_current['Timestamp'].dt.strftime('%m/%d/%y')


# Lets get the current one
csbs_df_past = pd.read_csv(
    'https://jordansdatabucket.s3-us-west-2.amazonaws.com/covid19data/csbs_df.csv.gz', index_col=0)
csbs_df_past['Timestamp'] = pd.to_datetime(csbs_df_past['Date'])
csbs_df_past['Date'] = csbs_df_past['Timestamp'].dt.date
csbs_df_past['Date'] = pandas.to_datetime(csbs_df_past['Date'])
csbs_df_past['Date_text'] = csbs_df_past['Timestamp'].dt.strftime('%m/%d/%y')

csbs_current = csbs_current.drop('id', axis=1)
# sort for columns
csbs_df_past = csbs_df_past[csbs_current.columns]

# This should be okay since we stored it this way
csbs_df_past = csbs_df_past.sort_values('confirmed')[::-1].groupby(
    ['lat', 'lon', 'Date', 'province', 'country_code', 'country', 'county', 'source']).head(1)

# Before we merge lets write out todays date
today = date.today()
csbs_current.to_csv(
    'Data/csbs_df_Archive_{}_{}_{}.csv.gz'.format(today.month, today.day, today.year))
print('Data/csbs_df_Archive_{}_{}_{}.csv.gz'.format(today.month, today.day, today.year))

# # Lets add together the past and current
csbs_new = pd.concat([csbs_df_past, csbs_current])

# Finally we can backfill
csbs_new = backfill_new_counties(csbs_new)


# # lets ensure that csbs_new has just one date
csbs_new = csbs_new.sort_values('confirmed').groupby(
    ['Date', 'province', 'country_code', 'country', 'county', 'source']).head(1)
csbs_new['Timestamp'] = pandas.to_datetime(csbs_new['Timestamp'], utc=True)
csbs_new['Date_text'] = csbs_new['Timestamp'].dt.strftime('%m/%d/%y')

jhu_time = jhu_time.drop('id', axis=1)
jhu_current = jhu_current.drop('id', axis=1)
csbs_new = csbs_new[jhu_time.columns]
jhu_current = jhu_current[jhu_time.columns]

assert(
    (jhu_time.groupby(['Date', 'country', 'province']).count() == 1).all().all())
assert((csbs_new.groupby(
    ['Date', 'country', 'province', 'county']).count() == 1).all().all())
assert((jhu_current.groupby(
    ['Date', 'country', 'province', 'county']).count() == 1).all().all())
assert(list(jhu_current.columns) == list(csbs_new.columns))

assert((csbs_new.groupby(['country', 'province', 'county']).count() == len(
    csbs_new['Date'].unique())).all().all())

# Lets Write everything out
jhu_current.to_csv('Data/jhu_df.csv.gz', compression='gzip')

# Write Out Time Course
jhu_time.to_csv('Data/jhu_df_time.csv.gz', compression='gzip')

# Write out Current CSV
csbs_new.to_csv('Data/csbs_df.csv.gz', compression='gzip')


JHU_DF_AGG_COUNTRY = jhu_time.sort_values('confirmed')[::-1].groupby(['Date', 'country']).agg(
    {'lat': 'first', 'lon': 'first', 'confirmed': 'sum', 'deaths': 'sum'}).reset_index()

JHU_DF_AGG_PROVINCE = jhu_time[jhu_time['province'] != ''].sort_values('confirmed')[::-1].groupby(['Date', 'country', 'province']).agg(
    {'lat': 'first', 'lon': 'first', 'confirmed': 'sum', 'deaths': 'sum'}).reset_index()

CSBS_DF_AGG_STATE = csbs_new[csbs_new['province'] != ''].sort_values('confirmed')[::-1].groupby(['Date', 'country', 'province']).agg(
    {'lat': 'first', 'lon': 'first', 'confirmed': 'sum', 'deaths': 'sum'}).reset_index().rename({'province': 'state'}, axis=1)

CSBS_DF_AGG_COUNTY = csbs_new[csbs_new['county'] != ''].sort_values('confirmed')[::-1].groupby(['Date', 'country', 'province', 'county']).agg(
    {'lat': 'first', 'lon': 'first', 'confirmed': 'sum', 'deaths': 'sum'}).reset_index()


def run_prediction(sub_df):
    print('Running', sub_df['country'].iloc[0])
    prediction_df = predict(sub_df, 7)
    return pd.concat([sub_df, prediction_df]).ffill().fillna(0)


pool = multiprocessing.Pool()


gb = JHU_DF_AGG_COUNTRY.groupby('country')
print("Running MP on countries")
JHU_DF_AGG_COUNTRY = pd.concat(pool.map(run_prediction, [i[1] for i in gb]))
JHU_DF_AGG_COUNTRY['granularity'] = 'country'
JHU_DF_AGG_COUNTRY['Text_Confirmed'] = JHU_DF_AGG_COUNTRY['forcast'].apply(lambda x: "" if not x else "**Predicted**<br>") + JHU_DF_AGG_COUNTRY['country'] + "<br> Total Cases: " + JHU_DF_AGG_COUNTRY['confirmed'].apply(
    lambda x: "{:,}".format(int(x)))
JHU_DF_AGG_COUNTRY['Text_Deaths'] = JHU_DF_AGG_COUNTRY['forcast'].apply(lambda x: "" if not x else "**Predicted**<br>") + JHU_DF_AGG_COUNTRY['country'] + "<br> Total Deaths: " + JHU_DF_AGG_COUNTRY['deaths'].apply(
    lambda x: "{:,}".format(int(x)))
JHU_DF_AGG_COUNTRY.to_csv('Data/JHU_DF_AGG_COUNTRY.csv.gz', compression='gzip')


print("Running MP on Provinces")
gb = JHU_DF_AGG_PROVINCE.groupby(['country', 'province'])
JHU_DF_AGG_PROVINCE = pd.concat(pool.map(run_prediction, [i[1] for i in gb]))
JHU_DF_AGG_PROVINCE['granularity'] = 'province'
JHU_DF_AGG_PROVINCE['Text_Confirmed'] = JHU_DF_AGG_PROVINCE['forcast'].apply(lambda x: "" if not x else "**Predicted**<br>") + JHU_DF_AGG_PROVINCE['province'] + ", " + JHU_DF_AGG_PROVINCE['country'] + "<br> Total Cases: " + JHU_DF_AGG_PROVINCE['confirmed'].apply(
    lambda x: "{:,}".format(int(x)))
JHU_DF_AGG_PROVINCE['Text_Deaths'] = JHU_DF_AGG_PROVINCE['forcast'].apply(lambda x: "" if not x else "**Predicted**<br>") + JHU_DF_AGG_PROVINCE['province'] + ", " + JHU_DF_AGG_PROVINCE['country'] + "<br> Total Deaths: " + JHU_DF_AGG_PROVINCE['deaths'].apply(
    lambda x: "{:,}".format(int(x)))

JHU_DF_AGG_PROVINCE.to_csv('Data/JHU_DF_AGG_PROVINCE.csv.gz', compression='gzip')

print("Running MP on States")
gb = CSBS_DF_AGG_STATE.groupby(['country', 'state'])
CSBS_DF_AGG_STATE = pd.concat(pool.map(run_prediction, [i[1] for i in gb]))
CSBS_DF_AGG_STATE['granularity'] = 'state'
CSBS_DF_AGG_STATE['Text_Confirmed'] = CSBS_DF_AGG_STATE['forcast'].apply(lambda x: "" if not x else "**Predicted**<br>") + CSBS_DF_AGG_STATE['state'] + ", " + CSBS_DF_AGG_STATE['country'] + "<br> Total Cases: " + CSBS_DF_AGG_STATE['confirmed'].apply(
    lambda x: "{:,}".format(int(x)))
CSBS_DF_AGG_STATE['Text_Deaths'] = CSBS_DF_AGG_STATE['forcast'].apply(lambda x: "" if not x else "**Predicted**<br>") + CSBS_DF_AGG_STATE['state'] + ", " + CSBS_DF_AGG_STATE['country'] + "<br> Total Deaths: " + CSBS_DF_AGG_STATE['deaths'].apply(
    lambda x: "{:,}".format(int(x)))
CSBS_DF_AGG_STATE.to_csv('Data/CSBS_DF_AGG_STATE.csv.gz', compression='gzip')


gb = CSBS_DF_AGG_COUNTY.groupby(['country', 'province', 'county'])
CSBS_DF_AGG_COUNTY = pd.concat(pool.map(run_prediction, [i[1] for i in gb]))
CSBS_DF_AGG_COUNTY['granularity'] = 'county'
CSBS_DF_AGG_COUNTY['Text_Confirmed'] = CSBS_DF_AGG_COUNTY['forcast'].apply(lambda x: "" if not x else "**Predicted**<br>") + CSBS_DF_AGG_COUNTY['county'] + ", " + CSBS_DF_AGG_COUNTY['province'] + "<br> Total Cases: " + CSBS_DF_AGG_COUNTY['confirmed'].apply(
    lambda x: "{:,}".format(int(x)))
CSBS_DF_AGG_COUNTY['Text_Deaths'] = CSBS_DF_AGG_COUNTY['forcast'].apply(lambda x: "" if not x else "**Predicted**<br>") + CSBS_DF_AGG_COUNTY['county'] + ", " + CSBS_DF_AGG_COUNTY['province'] + "<br> Total Deaths: " + CSBS_DF_AGG_COUNTY['deaths'].apply(
    lambda x: "{:,}".format(int(x)))
CSBS_DF_AGG_COUNTY.to_csv('Data/CSBS_DF_AGG_COUNTY.csv.gz', compression='gzip')
# Master df has all our entries with
master_df = pd.concat([JHU_DF_AGG_COUNTRY, JHU_DF_AGG_PROVINCE, CSBS_DF_AGG_STATE, CSBS_DF_AGG_COUNTY])

columns = ['Date', 'country', 'province', 'state', 'county', 'granularity']
master_df = master_df[columns+[i for i in master_df.columns if i not in columns]
                      ].reset_index(drop=True).fillna('N/A')

worldwide_df = master_df[master_df['granularity'] == 'country'].groupby(['Date', 'forcast']).sum().reset_index()
worldwide_df['country'] = 'worldwide'
worldwide_df['Text_Confirmed'] = 'Worldwide <br>'
master_df = master_df.append(worldwide_df).reset_index(drop=True)
# For latest date, the dataframes we merged each have a different last reported date (CSBS is faster than JHU), so we have to groupby and ask the minmal date from each gruop
latest_date = master_df[master_df['forcast'] == False].groupby('granularity').tail(1)['Date'].min()

# Master_latest has all our entries in it and thus should be used by everything.
master_latest = master_df[master_df['Date'] == latest_date].reset_index(drop=True)

pid = ['country', 'province', 'state', 'county', 'granularity']
assert(len(master_latest) == len(master_df[master_df['Date'] == latest_date].groupby(pid)))

# Now join the master df with the pID number from the latest
master_pid = master_latest.reset_index().set_index(pid).rename({'index': 'pid'}, axis=1)
master_df = master_df.set_index(pid).join(master_pid['pid']).reset_index().set_index(['pid', 'Date']).sort_index()

# Finally, set the pid back as the index
master_latest = master_pid.reset_index().set_index('pid')

# Master Latest has all the entries at the latest non forcast date. The index is the pID
# Master DF has all the entries with all dates. The index is the pID and Date
MASTER_PID = master_latest
MASTER_ALL = master_df

# Those predictions which are less than 0
MASTER_ALL.loc[MASTER_ALL['confirmed'] < 0, 'confirmed'] = 0.0
MASTER_ALL.loc[MASTER_ALL['deaths'] < 0, 'deaths'] = 0.0

max_size = 1500

bins, ret_bins = pd.qcut(MASTER_ALL[(MASTER_ALL['confirmed'] >= 1) & (MASTER_ALL['country'] != 'worldwide')]['confirmed'], q=[
    0, .5, 0.6, 0.70, 0.75, 0.8, 0.85, 0.9, 0.95, 0.999, 1], duplicates='drop', retbins=True)
yellows = ["#606056", "#6e6e56", "#7b7c55", "#898a54", "#979953",
           "#a5a850", "#b4b74d", "#c3c649", "#d2d643", "#e2e53c"]
reds = ["#5a4f4f", "#704d4d", "#854b4a", "#994746", "#ac4340",
        "#be3c3a", "#cf3531", "#e02a27", "#f01c19", "#ff0000"]
labels = np.geomspace(1, max_size, num=len(ret_bins)-1)
MASTER_ALL['CSize'] = pd.cut(MASTER_ALL['confirmed'], bins=ret_bins, labels=labels).astype(float).fillna(0)
MASTER_ALL['DSize'] = pd.cut(MASTER_ALL['deaths'], bins=ret_bins, labels=labels).astype(float).fillna(0)
MASTER_ALL['CColor'] = pd.cut(MASTER_ALL['confirmed'], bins=ret_bins,
                              labels=yellows).astype(str).replace({'nan': 'white'})
MASTER_ALL['DColor'] = pd.cut(MASTER_ALL['deaths'], bins=ret_bins,
                              labels=reds).astype(str).replace({'nan': 'white'})
DATE_MAPPER = pd.DataFrame(MASTER_ALL.index.get_level_values('Date').unique())

KEY_VALUE = dict(zip(list(MASTER_PID.index), list(
    MASTER_PID['Text_Confirmed'].str.split('<br>').str.get(0).str.replace('US', 'United States'))))
KEY_VALUE = pd.DataFrame(list(KEY_VALUE.values()), index=KEY_VALUE.keys(), columns=['name'])

MASTER_ALL.to_pickle('Data/MASTER_ALL.pkl', compression='gzip')
MASTER_PID.to_pickle('Data/MASTER_PID.pkl', compression='gzip')


print('Syncing Data')
ea = ExtraArgs = {'ACL': 'public-read'}
gs = [i for i in (glob.glob('Data/*.pkl') + glob.glob('Data/*.csv.gz')) if 'Archive' not in i]
for file in gs:
    upload_file(file, 'jordansdatabucket', os.path.join(
        'covid19data', os.path.basename(file)))
    print("Uploaded " + os.path.basename(file))
