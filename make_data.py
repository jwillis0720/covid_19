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


covid19_csbs = COVID19Py.COVID19(data_source="csbs").getAll(timelines=True)
covid19_jhu = COVID19Py.COVID19(data_source="jhu").getAll(timelines=True)


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


def parse_api_json(json, source):
    for_pandas = []
    confirmed = []
    deaths = []
    recovered = []
    for location in json['locations']:
        timeline_entry = {}
        entry = {
            'id': location['id'],
            'lat': location['coordinates']['latitude'],
            'lon': location['coordinates']['longitude'],
            'Date': pandas.to_datetime(location['last_updated']),
            'province': location['province'],
            'country_code': location['country_code'],
            'country': location['country'],
            'confirmed': location['latest']['confirmed'],
            'deaths': location['latest']['deaths'],
            'recovered': location['latest']['recovered'],
            'county': ''}
        if 'county' in location.keys():
            entry['county'] = location['county']
        if 'state' in location.keys():
            entry['state'] = location['state']
        entry['source'] = source
        for_pandas.append(entry)

        if 'timelines' in location.keys():
            for status in location['timelines']:
                for date in location['timelines'][status]['timeline']:
                    sub_entry = {'id': location['id'],
                                 'Date': pandas.to_datetime(date),
                                 status: location['timelines'][status]['timeline'][date]}
                    if status == 'confirmed':
                        confirmed.append(sub_entry)
                    elif status == 'deaths':
                        deaths.append(sub_entry)
                    else:
                        recovered.append(sub_entry)
    if confirmed:
        # return confirmed,deaths,recovered
        timeline_df = pandas.DataFrame(confirmed)
        if deaths:
            timeline_df = timeline_df.merge(
                pandas.DataFrame(deaths), on=['id', 'Date'])
        else:
            timeline_df['deaths'] = 0
        if recovered:
            timeline_df = timeline_df.merge(
                pandas.DataFrame(recovered), on=['id', 'Date'])
        else:
            timeline_df['recovered'] = 0.0

        main_df = pandas.DataFrame(for_pandas)
        timeline_df = timeline_df.merge(
            main_df[['id', 'lat', 'lon', 'province', 'country_code', 'country', 'source']], on=['id'])

        return main_df, timeline_df
    else:
        return pandas.DataFrame(for_pandas)


def per_x_cases(grouper, df, date_mapper):
    new_cases_by_country = []
    dates = date_mapper['Date']
    sub_group = df[df[grouper] != ""]
    groupers = sub_group[grouper].unique()

    for group in groupers:
        sub_country = sub_group[sub_group[grouper] == group]
        new_cases_by_country.append(
            {grouper: group, 'Date': dates[0],
             'New Cases': sub_country.loc[sub_country['Date'] == dates[0], 'confirmed'].sum(),
             'New Deaths': 0,
             'New Recovery': 0})
        for date_index in range(1, len(dates)):
            current_date = dates[date_index]
            day_before = dates[date_index-1]
            # print(current_date,day_before)
            t_c, t_d, t_r = sub_country.loc[sub_country['Date']
                                            == current_date, :].sum()[['confirmed', 'deaths', 'recovered']]

            y_c, y_d, y_r = sub_country.loc[sub_country['Date']
                                            == day_before, :].sum()[['confirmed', 'deaths', 'recovered']]

            new_cases = t_c - y_c
            new_deaths = t_d - y_d
            new_recovery = t_r - y_r
            new_cases_by_country.append(
                {grouper: group, 'Date': current_date, 'New Cases': new_cases,
                 'New Deaths': new_deaths, 'New Recovery': new_recovery})
    return pd.DataFrame(new_cases_by_country)


jhu_df, jhu_df_time = parse_api_json(covid19_jhu, 'JHU')
csbs_df = parse_api_json(covid19_csbs, 'CSBS')

# This will probably be a bug someday
# jhu_df_time = jhu_df_time[jhu_df_time['province'].str.split(
#     ', ').str.len() == 1]

date_mapper = pd.DataFrame(
    jhu_df_time['Date'].unique(), columns=['Date'])
date_mapper['Date_text'] = date_mapper['Date'].dt.strftime('%m/%d/%y')

provence_df_per_day = per_x_cases('province', jhu_df_time, date_mapper)
country_df_per_day = per_x_cases('country', jhu_df_time, date_mapper)
print('Generated Data')

jhu_df.to_csv('Data/jhu_df.csv.gz', compression='gzip')
jhu_df_time.to_csv('Data/jhu_df_time.csv.gz', compression='gzip')
csbs_df.to_csv('Data/csbs_df.csv.gz', compression='gzip')
provence_df_per_day.to_csv(
    'Data/provence_df_per_day.csv.gz', compression='gzip')
country_df_per_day.to_csv('Data/country_df_per_day.csv.gz', compression='gzip')


print('Syncing Data')
ea = ExtraArgs = {'ACL': 'public-read'}
gs = glob.glob('Data/*.csv.gz')
for file in gs:
    upload_file(file, 'jordansdatabucket', os.path.join(
        'covid19data', os.path.basename(file)))
    print("Uploaded " + os.path.basename(file))
