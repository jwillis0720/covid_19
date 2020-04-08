from plotly import graph_objs as go
import math
import plotly.colors


mapbox_style = 'mapbox://styles/jwillis0720/ck89nznm609pg1ipadkyrelvb'
mapbox_access_token = open('./.mapbox_token').readlines()[0]
colors = plotly.colors.qualitative.Dark24
# remove black elment
colors.remove(colors[5])
# lets repeat it enough time sjust incase
colors = colors * 10


def plot_map(dataframe, metrics, cases_bins, death_bins, zoom, center):
    data_traces = []

    if not metrics or dataframe.empty:
        data_traces.append(go.Scattermapbox(
            lon=[],
            lat=[]
        ))

    if 'confirmed' in metrics and not dataframe.empty:
        # First Do Confirmed
        gb_confirmed = dataframe.groupby('confirmed_size')
        gb_groups = sorted(gb_confirmed.groups)
        for indexer in range(len(gb_groups)):
            try:
                plotting_df = gb_confirmed.get_group(gb_groups[indexer])
            except KeyError:
                print('No group in gb_cases{}'.format(gb_groups[indexer]))
                continue
            if indexer+1 == len(cases_bins)-1:
                max_ = int(
                    math.ceil(dataframe['confirmed'].max()/10000)) * 10000
                name = "{0:,}-{1:,}".format(int(cases_bins[indexer]), max_)
            else:
                name = "{0:,}-{1:,}".format(
                    cases_bins[indexer], cases_bins[indexer+1])
            data = go.Scattermapbox(
                lon=plotting_df['lon'],
                lat=plotting_df['lat'],
                customdata=plotting_df['lookup'],
                textposition='top right',
                text=plotting_df['Text_Cases'],
                hoverinfo='text',
                mode='markers',
                name=name,
                marker=dict(
                    opacity=0.75,
                    size=plotting_df['confirmed_size'],
                    color=plotting_df['case_colors']
                )
            )
            data_traces.append(data)

    if 'deaths' in metrics and not dataframe.empty:
        # Then Do Deaths
        gb_deaths = dataframe.groupby('death_size')
        gb_groups = sorted(gb_deaths.groups)
        for indexer in range(len(gb_groups)):
            try:
                plotting_df = gb_deaths.get_group(gb_groups[indexer])
            except KeyError:
                print('No group in gb_deaths {}'.format(gb_groups[indexer]))
                continue

            if indexer+1 == len(death_bins)-1:
                max_ = int(
                    math.ceil(dataframe['deaths'].max()/10000)) * 10000
                name = "{0:,}-{1:,}".format(int(death_bins[indexer]), max_)
            else:
                name = "{0:,}-{1:,}".format(
                    death_bins[indexer], death_bins[indexer+1])
            data = go.Scattermapbox(
                lon=plotting_df['lon'],
                lat=plotting_df['lat'],
                customdata=plotting_df['lookup'],
                textposition='top right',
                text=plotting_df['Text_Deaths'],
                hoverinfo='text',
                mode='markers',
                name=name,
                marker=dict(
                    opacity=0.75,
                    size=plotting_df['death_size'],
                    color=plotting_df['death_colors']
                )
            )
            data_traces.append(data)
    layout = dict(
        autosize=True,
        showlegend=True,
        mapbox=dict(
            accesstoken=mapbox_access_token,
            style=mapbox_style,
            zoom=zoom,
            center=center
        ),
        hovermode="closest",
        margin=dict(r=0, l=0, t=0, b=0),
        dragmode="pan",
        legend=dict(
            x_anchor='left',
            x=0.00,
            y=0.00,
            orientation='v',
            traceorder="normal",
            font=dict(
                family="sans-serif",
                color="white",
                size=12
            ),
            bgcolor='rgba(0,0,0,0.4)'
            #
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    return {'data': data_traces, 'layout': layout}


def total_confirmed_graph(values, JHU_DF_AGG_COUNTRY, JHU_DF_AGG_PROVINCE, CSBS_DF_AGG_STATE, CSBS_DF_AGG_COUNTY, log=False, metric='confirmed'):
    data_traces = []
    for enum_, item in enumerate(values):
        color_ = colors[enum_]
        if item == 'worldwide':
            sub_df = JHU_DF_AGG_COUNTRY.groupby(
                'Date').sum().reset_index()
            name = 'World'
        else:
            if item.split('_')[0] == 'COUNTRY':
                parent = 'None'
                name = item.split('_')[1].split(':')[0]
                sub_df = JHU_DF_AGG_COUNTRY[JHU_DF_AGG_COUNTRY['country'] == name].groupby(
                    'Date').sum().reset_index()

            elif item.split('_')[0] == 'PROVINCE':
                parent = item.split(':')[-1]
                name = item.split('_')[1].split(':')[0]
                sub_df = JHU_DF_AGG_PROVINCE[(JHU_DF_AGG_PROVINCE['province'] == name) & (JHU_DF_AGG_PROVINCE['country'] == parent)].groupby(
                    'Date').sum().reset_index()

            elif item.split('_')[0] == 'STATE':
                parent = item.split(':')[-1]
                name = item.split('_')[1].split(':')[0]
                sub_df = CSBS_DF_AGG_STATE[(CSBS_DF_AGG_STATE['state'] == name) & (CSBS_DF_AGG_STATE['country'] == parent)].groupby(
                    'Date').sum().reset_index()

            elif item.split('_')[0] == 'COUNTY':
                parent = item.split(':')[-1]
                name = item.split('_')[1].split(':')[0]
                sub_df = CSBS_DF_AGG_COUNTY[(CSBS_DF_AGG_COUNTY['county'] == name) & (CSBS_DF_AGG_COUNTY['province'] == parent)].groupby(
                    'Date').sum().reset_index()
            else:
                raise Exception('You have messed up {}'.format(item))

        if metric == 'confirmed':
            hovert = '%{x}<br>Confirmed Cases - %{y:,f}'
            y_axis_title = 'Total Cases'
        else:
            hovert = '%{x}<br>Confirmed Deaths - %{y:,f}'
            y_axis_title = 'Total Deaths'

        data_traces.append(
            go.Scatter(
                x=sub_df['Date'],
                y=sub_df[metric],
                name=name,
                showlegend=True,
                mode='lines+markers',
                hovertemplate=hovert,
                marker=dict(
                    color=color_,
                    size=2,
                    line=dict(
                        width=5,
                        color=color_),
                )))
    layout = dict(
        margin=dict(t=70, r=40, l=80, b=80),
        yaxis=dict(
            title=dict(text=y_axis_title, standoff=2),
            titlefont_size=12,
            tickfont_size=12,
            showgrid=True,
            color='white',
            side='left',
        ),
        xaxis=dict(
            color='white',
        ),
        autosize=True,
        showlegend=True,
        legend=dict(x=0, y=1, font=dict(color='white')),
        paper_bgcolor='#1f2630',
        plot_bgcolor='rgb(52,51,50)')
    if log:
        layout['yaxis']['type'] = 'log'
    return {'data': data_traces, 'layout': layout}


def per_day_confirmed(values, JHU_DF_AGG_COUNTRY, JHU_DF_AGG_PROVINCE, CSBS_DF_AGG_STATE, CSBS_DF_AGG_COUNTY, log=True, metric='confirmed'):

    data_traces = []
    for enum_, item in enumerate(values):
        color_ = colors[enum_]
        if item == 'worldwide':
            sub_df = JHU_DF_AGG_COUNTRY.groupby('Date').sum().reset_index()
            name = 'World'
        else:
            if item.split('_')[0] == 'COUNTRY':
                parent = 'None'
                name = item.split('_')[1].split(':')[0]
                sub_df = JHU_DF_AGG_COUNTRY[JHU_DF_AGG_COUNTRY['country'] == name].groupby(
                    'Date').sum().reset_index()

            elif item.split('_')[0] == 'PROVINCE':
                parent = item.split(':')[-1]
                name = item.split('_')[1].split(':')[0]
                sub_df = JHU_DF_AGG_PROVINCE[(JHU_DF_AGG_PROVINCE['province'] == name) & (JHU_DF_AGG_PROVINCE['country'] == parent)].groupby(
                    'Date').sum().reset_index()

            elif item.split('_')[0] == 'STATE':
                parent = item.split(':')[-1]
                name = item.split('_')[1].split(':')[0]
                sub_df = CSBS_DF_AGG_STATE[(CSBS_DF_AGG_STATE['state'] == name) & (CSBS_DF_AGG_STATE['country'] == parent)].groupby(
                    'Date').sum().reset_index()

            elif item.split('_')[0] == 'COUNTY':
                parent = item.split(':')[-1]
                name = item.split('_')[1].split(':')[0]
                sub_df = CSBS_DF_AGG_COUNTY[(CSBS_DF_AGG_COUNTY['county'] == name) & (CSBS_DF_AGG_COUNTY['province'] == parent)].groupby(
                    'Date').sum().reset_index()
            else:
                raise Exception('You have messed up {}'.format(item))

        xs = sub_df['Date']
        if metric == 'confirmed':
            ys = sub_df['confirmed'].diff().fillna(0)
            hovert = '%{x}<br>New Cases - %{y:,f}'
            y_axis_title = 'Confirmed Cases Per Day'
        else:
            ys = sub_df[metric].diff().fillna(0)
            hovert = '%{x}<br>New Deaths - %{y:,f}'
            y_axis_title = 'Deaths Per Day'

        data_traces.append(
            go.Bar(
                x=xs,
                y=ys,
                name=name,
                showlegend=True,
                hovertemplate=hovert,
                textfont=dict(size=14, color='white'),
                marker=dict(
                    color=color_,
                    line=dict(
                        color='white', width=0.5)
                )))

    layout = dict(
        margin=dict(t=70, r=40, l=80, b=80),

        yaxis=dict(
            title=dict(text=y_axis_title, standoff=2),
            titlefont_size=12,
            tickfont_size=12,
            showgrid=True,
            color='white',
            side='left',
        ),
        xaxis=dict(
            color='white'
        ),
        showlegend=True,
        legend=dict(x=0, y=1, font=dict(color='white')),
        paper_bgcolor='#1f2630',
        plot_bgcolor='rgb(52,51,50)',
        barmode='group',
        bargap=0.1)
    if log:
        layout['yaxis']['type'] = 'log'

    return {'data': data_traces, 'layout': layout}


def plot_exponential(values, JHU_DF_AGG_COUNTRY, JHU_DF_AGG_PROVINCE, CSBS_DF_AGG_STATE, CSBS_DF_AGG_COUNTY, log):
    backtrack = 7
    fig = go.Figure()
    max_number = 0
    for enum_, item in enumerate(values):
        if item == 'worldwide':
            location = 'World'
            full_report = JHU_DF_AGG_COUNTRY.groupby(
                'Date').sum().drop(['lat', 'lon'], axis=1)
        else:

            class_location = item.split('_')[0]
            location = item.split('_')[1].split(':')[0]
            parent = item.split('_')[1].split(':')[-1]
            # print(class_location, location, parent)
            if class_location == 'COUNTRY':
                full_report = JHU_DF_AGG_COUNTRY[JHU_DF_AGG_COUNTRY['country'] == location].groupby(
                    'Date').sum().drop(['lat', 'lon'], axis=1)

            elif class_location == 'PROVINCE':
                full_report = JHU_DF_AGG_PROVINCE[(JHU_DF_AGG_PROVINCE['province'] == location) & (JHU_DF_AGG_PROVINCE['country'] == parent)].groupby(
                    'Date').sum().drop(['lat', 'lon'], axis=1)
            elif class_location == 'STATE':
                full_report = CSBS_DF_AGG_STATE[(CSBS_DF_AGG_STATE['state'] == location) & (CSBS_DF_AGG_STATE['country'] == parent)].groupby(
                    'Date').sum().drop(['lat', 'lon'], axis=1)
            elif class_location == 'COUNTY':
                full_report = CSBS_DF_AGG_COUNTY[(CSBS_DF_AGG_COUNTY['county'] == location) & (CSBS_DF_AGG_COUNTY['province'] == parent)].groupby(
                    'Date').sum().drop(['lat', 'lon'], axis=1)
        per_day = full_report.diff()
        plottable = full_report.join(
            per_day, lsuffix='_cum', rsuffix='_diff')
        plottable = plottable.fillna(0)
        # print(item, plottable)

        xs = []
        ys = []
        dates = []
        indexes = plottable.index
        print(plottable)
        for indexer in range(1, len(indexes)):
            x = plottable.loc[indexes[indexer]]['confirmed_cum']
            if indexer > backtrack:
                y = plottable.loc[indexes[indexer-backtrack]                                  : indexes[indexer]].sum()['confirmed_diff']
            else:
                y = plottable.loc[: indexes[indexer]].sum()['confirmed_diff']
            # if y < 100 or x < 100:
            #     continue
            if x > max_number:
                max_number = x
            if y > max_number:
                max_number = y
            xs.append(x)
            ys.append(y)
            dates.append(indexes[indexer].strftime('%m/%d/%Y'))
        fig.add_trace(
            go.Scatter(
                x=xs,
                y=ys,
                mode='lines',
                name=location,
                text=dates,
                showlegend=False,
                legendgroup=item,
                line=dict(shape='linear', color=colors[enum_], width=3),
                marker=dict(
                    symbol='circle-open',
                    # size=7
                ),
                hovertemplate="On %{text} <br> Total Cases: %{x}<br> Cummulative Cases Last Week %{y}"
            )
        )
        fig.add_trace(
            go.Scatter(
                x=[xs[-1]],
                y=[ys[-1]],
                mode='markers',
                name=location,
                text=[dates[-1]],
                legendgroup=location,
                hoverlabel=dict(align='left'),
                marker=dict(
                    symbol='circle',
                    # size=18,
                    color=colors[enum_]
                ),
                hovertemplate="On %{text} <br> Total Cases: %{x}<br> Cummulative Cases Last Week %{y}"
            )
        )
    fig.add_trace(
        go.Scatter(
            x=[0, max_number],
            y=[0, max_number],
            mode='lines',
            name='Exponential',
            showlegend=False,
            line=dict(color='white', width=4, dash='dash')
        )
    )
    if log:
        fig.update_xaxes(type="log", dtick=1)
        fig.update_yaxes(type="log", dtick=1)

    fig.update_layout(
        yaxis=dict(
            title=dict(text='New Cases Previous {} Days'.format(
                backtrack), standoff=2),
            showgrid=True,
            color='white',
        ),
        margin=dict(t=20),
        xaxis=dict(
            color='white',
            showgrid=False,
            title=dict(text='Total Cases', standoff=1)
        ),
        autosize=True,
        showlegend=True,
        paper_bgcolor='#1f2630',
        plot_bgcolor='rgb(52,51,50)',
        legend=dict(x=0, y=1, font=dict(color='white')))

    annotations = []
    if log:
        x_ref = 5
        y_ref = 5.4
    else:
        x_ref = 8 * 10 ** 5
        y_ref = 8 * 10 ** 5
    annotations.append(dict(xref='x', x=x_ref, yref='y', y=y_ref,
                            text="Exponential Growth",
                            font=dict(family='Arial',
                                      color='white'),
                            showarrow=True,
                            startarrowsize=10,
                            arrowwidth=2,
                            arrowcolor='white',
                            arrowhead=2,
                            ))

    fig.update_layout(legend=dict(title='Click to Toggle'),
                      annotations=annotations)

    fig.update_layout(
        margin=dict(t=50, b=20, r=30, l=20, pad=0))
    return fig
