from plotly import graph_objs as go
import math
import numpy as np
import plotly.colors
from datetime import date, timedelta


mapbox_style = 'mapbox://styles/jwillis0720/ck89nznm609pg1ipadkyrelvb'
mapbox_access_token = open('./.mapbox_token').readlines()[0]
colors = plotly.colors.qualitative.Dark24
# remove black elment
colors.remove(colors[5])
# lets repeat it enough time sjust incase
colors = colors * 10


def get_rgb_with_opacity(hex_color, opacity=0.5):
    h = hex_color.lstrip('#')
    return 'rgba'+'{}'.format(tuple(list(int(h[i:i+2], 16) for i in (0, 2, 4))+[opacity]))


def plot_map(dataframe, metrics, zoom, center):
    data_traces = []

    # sizeref_confirmed = 2. * max(max_confirmed) / (120 ** 2)
    # sizeref_death = 2. * max(dataframe['deaths']) / (120 ** 2)
    if not metrics or dataframe.empty:
        data_traces.append(go.Scattermapbox(
            lon=[],
            lat=[]
        ))

    dataframe = dataframe[dataframe['CSize'] > 0]
    if 'confirmed' in metrics and not dataframe.empty:
        # First Do Confirmed
        gb_confirmed = dataframe.groupby('CSize')
        gb_groups = sorted(gb_confirmed.groups)
        for indexer in range(len(gb_groups)):
            try:
                plotting_df = gb_confirmed.get_group(gb_groups[indexer])
            except KeyError:
                print('No group in gb_cases{}'.format(gb_groups[indexer]))
                continue
            #  if indexer+1 == len(cases_bins)-1:
            max_scale = 100000
            if plotting_df['confirmed'].max() < 100000:
                max_scale = 10000
            if plotting_df['confirmed'].max() < 10000:
                max_scale = 1000
            if plotting_df['confirmed'].max() < 1000:
                max_scale = 100
            if plotting_df['confirmed'].max() < 100:
                max_scale = 10
            if plotting_df['confirmed'].max() < 10:
                max_scale = 1

            min_scale = 10000
            if plotting_df['confirmed'].min() < 10000:
                min_scale = 1000
            if plotting_df['confirmed'].min() < 1000:
                min_scale = 100
            if plotting_df['confirmed'].min() < 100:
                min_scale = 10
            if plotting_df['confirmed'].min() < 10:
                min_scale = 1
            max_ = int(
                math.ceil(plotting_df['confirmed'].max()/max_scale)) * max_scale
            if max_ == 1:
                max_ += 1
            min_ = int(
                math.ceil(plotting_df['confirmed'].min()/min_scale)) * min_scale
            name = "{0:,}-{1:,}".format(min_, max_)
            sizes = plotting_df['confirmed']
            sizes[sizes < 1] = 1
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
                    opacity=0.8,
                    sizemin=3,
                    size=plotting_df['CSize'],
                    # colorscale=[[0, 'rgb(0,0,255)'], [1, 'rgb(255,0,0)']],
                    color=plotting_df['CColor'],
                    sizemode='area'
                )
            )
            data_traces.append(data)

    if 'deaths' in metrics and not dataframe.empty:
          # First Do Confirmed
        dataframe = dataframe[dataframe['DSize'] > 0]
        gb_deaths = dataframe.groupby('DSize')
        gb_groups = sorted(gb_deaths.groups)
        for indexer in range(len(gb_groups)):
            try:
                plotting_df = gb_deaths.get_group(gb_groups[indexer])
            except KeyError:
                print('No group in gb_cases{}'.format(gb_groups[indexer]))
                continue
            max_scale = 100000
            if plotting_df['deaths'].max() < 100000:
                max_scale = 10000
            if plotting_df['deaths'].max() < 10000:
                max_scale = 1000
            if plotting_df['deaths'].max() < 1000:
                max_scale = 100
            if plotting_df['deaths'].max() < 100:
                max_scale = 10
            if plotting_df['deaths'].max() < 10:
                max_scale = 1

            min_scale = 10000
            if plotting_df['deaths'].min() < 10000:
                min_scale = 1000
            if plotting_df['deaths'].min() < 1000:
                min_scale = 100
            if plotting_df['deaths'].min() < 100:
                min_scale = 10
            if plotting_df['deaths'].min() < 10:
                min_scale = 1
            max_ = int(
                math.ceil(plotting_df['deaths'].max()/max_scale)) * max_scale
            if max_ == 1:
                max_ += 1
            min_ = int(
                math.ceil(plotting_df['deaths'].min()/min_scale)) * min_scale
            name = "{0:,}-{1:,}".format(min_, max_)
            sizes = plotting_df['deaths']
            sizes[sizes < 1] = 1
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
                    opacity=0.8,
                    sizemin=3,
                    size=plotting_df['DSize'],
                    # colorscale=[[0, 'rgb(0,0,255)'], [1, 'rgb(255,0,0)']],
                    color=plotting_df['DColor'],
                    sizemode='area'
                )
            )
            data_traces.append(data)

    annotations = []
    layout = dict(
        autosize=True,
        showlegend=True,
        annotations=annotations,
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
        color_rgba = get_rgb_with_opacity(color_, opacity=0.2)

        if item == 'worldwide':
            sub_df = JHU_DF_AGG_COUNTRY.groupby(
                ['Date', 'forcast']).sum().reset_index()
            name = 'World'
        else:
            if item.split('_')[0] == 'COUNTRY':
                parent = 'None'
                name = item.split('_')[1].split(':')[0]
                sub_df = JHU_DF_AGG_COUNTRY[JHU_DF_AGG_COUNTRY['country'] == name].groupby(
                    ['Date', 'forcast']).sum().reset_index()

            elif item.split('_')[0] == 'PROVINCE':
                parent = item.split(':')[-1]
                name = item.split('_')[1].split(':')[0]
                sub_df = JHU_DF_AGG_PROVINCE[(JHU_DF_AGG_PROVINCE['province'] == name) & (JHU_DF_AGG_PROVINCE['country'] == parent)].groupby(
                    ['Date', 'forcast']).sum().reset_index()

            elif item.split('_')[0] == 'STATE':
                parent = item.split(':')[-1]
                name = item.split('_')[1].split(':')[0]
                sub_df = CSBS_DF_AGG_STATE[(CSBS_DF_AGG_STATE['state'] == name) & (CSBS_DF_AGG_STATE['country'] == parent)].groupby(
                    ['Date', 'forcast']).sum().reset_index()

            elif item.split('_')[0] == 'COUNTY':
                parent = item.split(':')[-1]
                name = item.split('_')[1].split(':')[0]
                sub_df = CSBS_DF_AGG_COUNTY[(CSBS_DF_AGG_COUNTY['county'] == name) & (CSBS_DF_AGG_COUNTY['province'] == parent)].groupby(
                    ['Date', 'forcast']).sum().reset_index()
            else:
                raise Exception('You have messed up {}'.format(item))

        if metric == 'confirmed':
            hovert = '%{x}<br>Confirmed Cases - %{y:,f}'
            y_axis_title = 'Total Cases'
        else:
            hovert = '%{x}<br>Confirmed Deaths - %{y:,f}'
            y_axis_title = 'Total Deaths'

        # First add the confidence interval
        forcast = sub_df[sub_df['forcast'] == True]
        dates = list(forcast['Date'])
        xs = dates + dates[::-1]
        uppers = list(forcast['{}_upper'.format(metric)])
        lowers = list(forcast['{}_lower'.format(metric)])
        ys = uppers + lowers[::-1]
        data_traces.append(
            go.Scatter(
                x=xs,
                y=ys,
                fill='toself',
                hoverinfo='none',
                showlegend=False,
                line_color='rgba(255,255,255,0)'
            ))

        # Then add the full lineA
        forcast = sub_df[sub_df['forcast'] == True]
        dates = [forcast['Date'].iloc[0] - timedelta(days=1)] + list(forcast['Date'])
        ys = sub_df[sub_df['Date'].isin(dates)][metric]
        # print(ys)
        data_traces.append(
            go.Scatter(
                x=dates,
                y=ys,
                showlegend=False,
                mode='lines+markers',
                hovertemplate=hovert.replace('Confirmed', 'Predicted'),
                name=name,
                marker=dict(
                    size=9,
                    symbol='circle-open',
                ),
                line=dict(
                    color=color_,
                    width=2,
                    dash='dashdot'
                )
            ))

        sub_df = sub_df[sub_df['forcast'] == False]
        # Add full line without prediction:
        data_traces.append(
            go.Scatter(
                x=sub_df['Date'],
                y=sub_df[metric],
                showlegend=True,
                mode='lines+markers',
                name=name,
                hovertemplate=hovert,
                marker=dict(
                    color=color_,
                    size=9,
                ),
                line=dict(
                    color=color_,
                    width=2,
                    dash='solid'
                )))
    shapes = []
    forcast_date = JHU_DF_AGG_COUNTRY[JHU_DF_AGG_COUNTRY['forcast'] == True]['Date'].iloc[0]
    start_date = JHU_DF_AGG_COUNTRY['Date'].iloc[0]
    end_date_range = JHU_DF_AGG_COUNTRY['Date'].iloc[-1]
    end_date = JHU_DF_AGG_COUNTRY[JHU_DF_AGG_COUNTRY['forcast'] == True]['Date'].iloc[-1]
    shapes.append(
        dict(
            type='rect',
            xref="x",
            yref='paper',
            x0=forcast_date-timedelta(days=1),
            y0=0,
            x1=end_date+timedelta(days=1),
            y1=1,
            line=dict(
                color='white', width=0),
            fillcolor='rgba(255,255,255,0.05)'
        ))

    layout = dict(
        margin=dict(t=70, r=40, l=80, b=80),
        shapes=shapes,
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
            range=[start_date-timedelta(days=1), end_date_range+timedelta(days=1)]
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
    offset_group = 0
    for enum_, item in enumerate(values):
        color_ = colors[enum_]
        if item == 'worldwide':
            sub_df = JHU_DF_AGG_COUNTRY.groupby(['Date', 'forcast']).sum().reset_index()
            name = 'World'
            offset_group = 1
        else:
            if item.split('_')[0] == 'COUNTRY':
                parent = 'None'
                name = item.split('_')[1].split(':')[0]
                sub_df = JHU_DF_AGG_COUNTRY[JHU_DF_AGG_COUNTRY['country'] == name].groupby(
                    ['Date', 'forcast']).sum().reset_index()

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
            hovert = '%{x}<br>New Cases - %{y:,f}'
            y_axis_title = 'Confirmed Cases Per Day'
        else:
            hovert = '%{x}<br>New Deaths - %{y:,f}'
            y_axis_title = 'Deaths Per Day'

        # Add the forcast values
        forcast = sub_df[sub_df['forcast'] == True]
        dates = list(forcast['Date'])
        ys = sub_df[metric].diff().fillna(0)[-len(dates):]
        data_traces.append(
            go.Bar(
                x=dates,
                y=ys,
                showlegend=False,
                offsetgroup=offset_group,
                hovertemplate=hovert.replace('New', 'Predicted'),
                name=name,
                # text='Prediction',
                # textposition='auto',
                marker=dict(
                    color=color_,
                    line=dict(
                        color='white', width=0.5,
                    )
                ),
            ))

        forcast = sub_df[sub_df['forcast'] == False]
        dates = list(forcast['Date'])
        ys = forcast[metric].diff().fillna(0)
        data_traces.append(
            go.Bar(
                x=dates,
                y=ys,
                showlegend=True,
                offsetgroup=offset_group,
                hovertemplate=hovert,
                name=name,
                marker=dict(
                    color=color_,
                    line=dict(
                        color='white', width=0.5
                    )
                ),
            ))
    shapes = []
    forcast_date = JHU_DF_AGG_COUNTRY[JHU_DF_AGG_COUNTRY['forcast'] == True]['Date'].iloc[0]
    start_date = JHU_DF_AGG_COUNTRY['Date'].iloc[0]
    end_date_range = JHU_DF_AGG_COUNTRY['Date'].iloc[-1]
    end_date = JHU_DF_AGG_COUNTRY[JHU_DF_AGG_COUNTRY['forcast'] == True]['Date'].iloc[-1]
    shapes.append(
        dict(
            type='rect',
            xref="x",
            yref='paper',
            x0=forcast_date-timedelta(hours=12),
            y0=0,
            x1=end_date+timedelta(hours=12),
            y1=1,
            line=dict(
                color='white', width=0),
            fillcolor='rgba(255,255,255,0.2)'
        ))
    layout = dict(
        margin=dict(t=70, r=40, l=80, b=80),
        shapes=shapes,
        yaxis=dict(
            title=dict(text=y_axis_title, standoff=2),
            titlefont_size=14,
            tickfont_size=14,
            showgrid=True,
            color='white',
            side='left',
        ),
        xaxis=dict(
            color='white',
            range=[start_date+timedelta(days=1), end_date_range+timedelta(hours=12)]
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
                y = plottable.loc[indexes[indexer-backtrack]: indexes[indexer]].sum()['confirmed_diff']
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


def per_gr(values, JHU_DF_AGG_COUNTRY, JHU_DF_AGG_PROVINCE, CSBS_DF_AGG_STATE, CSBS_DF_AGG_COUNTY, log=False, metric='confirmed'):

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
            s = sub_df['confirmed'].replace(
                to_replace=0, method='ffill').pct_change()*100
            ys = s.replace(np.inf, 1)
            ys = ys.fillna(1)
            # ys = s.diff()
            hovert = '%{x}<br>Growth Factor - %{y:.3f}%'
            y_axis_title = 'Confirmed Cases Growth Factor'
        else:
            s = sub_df['deaths'].replace(
                to_replace=0, method='ffill').pct_change()*100
            ys = s.replace(np.inf, 1)
            ys = ys.fillna(1)
            hovert = '%{x}<br>Death Growth - %{y:.3f}%'
            y_axis_title = 'Deaths Growth Factor'

        data_traces.append(
            go.Scatter(
                x=xs,
                y=ys,
                name=name,
                showlegend=True,
                hovertemplate=hovert,
                mode='lines+markers',
                textfont=dict(size=14, color='white'),
                marker=dict(
                    color=color_,
                    line=dict(
                        color=color_, width=0.5)
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
        plot_bgcolor='rgb(52,51,50)')
    if log:
        layout['yaxis']['type'] = 'log'

    return {'data': data_traces, 'layout': layout}
