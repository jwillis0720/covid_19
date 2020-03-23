import warnings
import pandas as pd
import glob
import os
import logging
import boto3
from botocore.exceptions import ClientError

# Cancel copy warnings of pandas
warnings.filterwarnings(
    "ignore", category=pd.core.common.SettingWithCopyWarning)

states_abbreviations_mapper = {
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


BASE_URL = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/'
TS_CONFIRMED_CASES = 'csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Confirmed.csv'
TS_DEATH_CASES = 'csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Deaths.csv'
TS_RECOVERED_CASES = 'csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Recovered.csv'


def get_time_series(url, outcome):
    time_series_df = pd.read_csv(BASE_URL+url)
    sub_df = time_series_df.set_index(
        ['Province/State', 'Country/Region', 'Lat', 'Long']).transpose().unstack(
            fill_value="").reset_index().rename({'level_4': 'Date', 0: outcome}, axis=1)
    sub_df['Date_text'] = sub_df['Date']
    sub_df['Date'] = pd.to_datetime(
        sub_df['Date'], format='%m/%d/%y')
    return sub_df


def parse_into_city(df):
    df['County'] = df['Province/State'].apply(
        lambda x: x.split(', ')[0] if len(x.split(', ')) == 2 and type(x) == str else "")
    df['Province/State'] = df['Province/State'].apply(
        lambda x: states_abbreviations_mapper[x.split(', ')[1].replace('.', '').strip()] if len(x.split(', ')) == 2 else x)
    return df


confirmed_cases = get_time_series(TS_CONFIRMED_CASES, 'Cases').fillna('')
confirmed_deaths = get_time_series(TS_DEATH_CASES, 'Deaths').fillna('')
confirmed_recovery = get_time_series(TS_RECOVERED_CASES, 'Recovery').fillna('')

# Confirmed Cases
confirmed_cases = parse_into_city(confirmed_cases)

# Confirmed Death
confirmed_deaths = parse_into_city(confirmed_deaths)

# Confirmed Recovery
confirmed_recovery = parse_into_city(confirmed_recovery)

# Merge them all together
merged_df = confirmed_cases.merge(
    confirmed_deaths, on=["Province/State", "Country/Region", "Lat", "Long", "Date", "Date_text", "County"]).merge(
    confirmed_recovery, on=["Province/State", "Country/Region", "Lat", "Long", "Date", "Date_text", "County"])


date_mapper = pd.DataFrame(
    merged_df['Date'].unique(), columns=['Date'])
date_mapper['Date_text'] = date_mapper['Date'].dt.strftime('%m/%d/%y')


centroid_country_mapper = merged_df.groupby(
    'Country/Region').apply(lambda x: x.sort_values('Cases')[::-1].iloc[0][['Lat', 'Long']])
centroid_country_mapper = {x[0]: {'Long': x[1]['Long'], 'Lat': x[1]['Lat']}
                           for x in centroid_country_mapper.iterrows()}  # Dash Help Components


def per_x_cases(grouper):
    new_cases_by_country = []
    dates = date_mapper['Date']
    sub_group = merged_df[merged_df[grouper] != ""]
    groupers = sub_group[grouper].unique()

    for group in groupers:
        sub_country = sub_group[sub_group[grouper] == group]
        new_cases_by_country.append(
            {grouper: group, 'Date': dates[0],
             'New Cases': sub_country.loc[sub_country['Date'] == dates[0], 'Cases'].sum(),
             'New Deaths': 0,
             'New Recovery': 0})
        for date_index in range(1, len(dates)):
            current_date = dates[date_index]
            day_before = dates[date_index-1]
            # print(current_date,day_before)
            t_c, t_d, t_r = sub_country.loc[sub_country['Date']
                                            == current_date, :].sum()[['Cases', 'Deaths', 'Recovery']]

            y_c, y_d, y_r = sub_country.loc[sub_country['Date']
                                            == day_before, :].sum()[['Cases', 'Deaths', 'Recovery']]

            new_cases = t_c - y_c
            new_deaths = t_d - y_d
            new_recovery = t_r - y_r
            new_cases_by_country.append(
                {grouper: group, 'Date': current_date, 'New Cases': new_cases,
                 'New Deaths': new_deaths, 'New Recovery': new_recovery})
    return pd.DataFrame(new_cases_by_country)


# These are by the day stats which will be useful
per_day_stats_by_state = per_x_cases('Province/State')
per_day_stats_by_country = per_x_cases('Country/Region')
per_day_stats_by_county = per_x_cases('County')


merged_df.to_csv('Data/Merged_df.csv.gz', compression='gzip')
per_day_stats_by_state.to_csv(
    'Data/per_day_stats_by_state.csv.gz', compression='gzip')
per_day_stats_by_country.to_csv(
    'Data/per_day_stats_by_country.csv.gz', compression='gzip')
per_day_stats_by_county.to_csv(
    'Data/per_day_stats_by_county.csv.gz', compression='gzip')

print('Generated Data')
print('Syncing Data')


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


ea = ExtraArgs = {'ACL': 'public-read'}
gs = glob.glob('Data/*.csv.gz')
for file in gs:
    upload_file(file, 'jordansdatabucket', os.path.join(
        'covid19data', os.path.basename(file)))
    print("Uploaded " + os.path.basename(file))
