from datetime import date
import warnings
import pandas as pd
import glob
import os
import logging
import boto3
from botocore.exceptions import ClientError
import COVID19Py
import pandas

# Cancel copy warnings of pandas
warnings.filterwarnings(
    "ignore", category=pd.core.common.SettingWithCopyWarning)


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
        response = s3_client.upload_file(
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

print('Syncing Data')
ea = ExtraArgs = {'ACL': 'public-read'}
gs = glob.glob('Data/*.csv.gz')
for file in gs:
    upload_file(file, 'jordansdatabucket', os.path.join(
        'covid19data', os.path.basename(file)))
    print("Uploaded " + os.path.basename(file))
