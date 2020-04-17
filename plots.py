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


AXIS_FONT_SIZE = 18
AXIS_TITLE_FONT_SIZE = 18
LEGEND_FONT_SIZE = 18
FONT_FAMILY = 'Fira Sans'


def get_closest_inerval(n, s='max'):
    import math
    d = math.floor(math.log(abs(n)) / math.log(10))
    scale = 10**d
    if s == 'max':
        return math.ceil(n/scale) * scale
    return math.floor(n/scale) * scale


def get_rgb_with_opacity(hex_color, opacity=0.5):
    h = hex_color.lstrip('#')
    return 'rgba'+'{}'.format(tuple(list(int(h[i:i+2], 16) for i in (0, 2, 4))+[opacity]))


def plot_map(dataframe, metrics, zoom, center, relative_check):
    data_traces = []
    if not metrics or dataframe.empty:
        data_traces.append(go.Scattermapbox(
            lon=[],
            lat=[]
        ))
    if 'confirmed' in metrics and not dataframe.empty:
        # First Do Confirmed
        dataframe = dataframe[dataframe['CSize'] > 0]
        plotting_df = dataframe
        if relative_check:
            sizes = plotting_df['per_capita_confirmed'].to_numpy()
            name = 'Relative Cases'
            text = plotting_df['Text_Confirmed'].str.split(':').str.get(
                0).str.replace('Total Cases', 'Relative Cases') + ": 1 in " + (1/plotting_df['per_capita_confirmed']).replace(
                    np.inf, 0).astype(int).apply(lambda x: "{:,}".format(x))
            colors = list(plotting_df['per_capita_confirmed'])
            size_max = max(plotting_df[plotting_df['per_capita_confirmed'] < 0.1]['per_capita_confirmed'])
            size_max = 0.01
            np.place(sizes, sizes > 0.01, [0.01])
            cmax = np.percentile(sizes, 99)
            cmid = np.percentile(sizes, 50)
            cmin = np.percentile(sizes, 25)
            sizeref = 2. * size_max / (40 ** 2)
        else:
            sizes = plotting_df['confirmed']
            name = "Confirmed Cases"
            text = plotting_df['Text_Confirmed']
            colors = plotting_df['confirmed']
            size_max = max(plotting_df['confirmed'])
            cmax = np.percentile(sizes, 99)
            cmid = np.percentile(sizes, 50)
            cmin = np.percentile(sizes, 25)
            sizeref = 2. * size_max / (100 ** 2)

        colorscale = 'YlOrBr'
        sizemin = 2

        data = go.Scattermapbox(
            lon=plotting_df['lon'],
            lat=plotting_df['lat'],
            customdata=plotting_df['PID'],
            text=text,
            hoverinfo='text',
            name=name,
            mode='markers',
            marker=dict(
                opacity=0.95,
                sizemin=sizemin,
                sizeref=sizeref,
                reversescale=False,
                colorscale=colorscale,
                size=sizes,
                color=colors,
                cmax=cmax,
                cmin=cmin,
                cmid=cmid,
                sizemode='area'
            ),
        )
        data_traces.append(data)
    if 'deaths' in metrics and not dataframe.empty:
         # First Do Confirmed
        dataframe = dataframe[dataframe['deaths'] > 0]
        plotting_df = dataframe
        if relative_check:
            sizes = plotting_df['per_capita_deaths'].to_numpy()
            name = 'Relative Deaths'
            text = plotting_df['Text_Deaths'].str.split(':').str.get(
                0).str.replace('Total Deaths', 'Relative Deaths') + ": 1 in " + (1/plotting_df['per_capita_deaths']).replace(
                    np.inf, 0).astype(int).apply(lambda x: "{:,}".format(x))
            colors = list(plotting_df['per_capita_deaths'])
            np.place(sizes, sizes > 0.003, [0.003])
            size_max = max(sizes)
            cmax = np.percentile(sizes, 99)
            cmid = np.percentile(sizes, 30)
            cmin = np.percentile(sizes, 10)
            sizeref = 2. * size_max / (40 ** 2)
        else:
            sizes = plotting_df['deaths']
            name = "Confirmed Deaths"
            text = plotting_df['Text_Deaths']
            colors = plotting_df['deaths']
            size_max = max(plotting_df['deaths'])
            cmax = np.percentile(sizes, 99)
            cmid = np.percentile(sizes, 20)
            cmin = np.percentile(sizes, 10)
            sizeref = 2. * size_max / (100 ** 2)

        colorscale = 'Reds'
        sizemin = 2

        data = go.Scattermapbox(
            lon=plotting_df['lon'],
            lat=plotting_df['lat'],
            customdata=plotting_df['PID'],
            text=text,
            hoverinfo='text',
            name=name,
            mode='markers',
            marker=dict(
                opacity=0.95,
                sizemin=sizemin,
                sizeref=sizeref,
                reversescale=False,
                colorscale=colorscale,
                size=sizes,
                color=colors,
                cmax=cmax,
                cmin=cmin,
                cmid=cmid,
                sizemode='area'
            ),
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
            x=0.00,
            y=0.00,
            itemsizing='constant',
            orientation='v',
            traceorder="normal",
            font=dict(
                family="Montserrat",
                color="white",
                size=14
            ),
            bgcolor='rgba(0,0,0,0.6)'
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    return {'data': data_traces, 'layout': layout}


def total_confirmed_graph(values, MASTER_DF, KEY_VALUE, log, metric, predict, gs):
    data_traces = []
    MASTER_DF = MASTER_DF.reset_index()
    forcast_date = MASTER_DF.groupby('forcast').tail(1)['Date'].iloc[0]
    start_date = MASTER_DF['Date'].iloc[0]
    end_date = MASTER_DF['Date'].iloc[-1]
    if gs:
        x_axis_range = [gs['xaxis.range[0]'], gs['xaxis.range[1]']]
        if 'yaxis.range[1]' in gs:
            y_axis_range = [gs['yaxis.range[0]'], gs['yaxis.range[1]']]
        else:
            y_axis_range = 'auto'
    else:
        if predict:
            x_axis_range = [start_date-timedelta(days=1), end_date+timedelta(days=1)]
        else:
            x_axis_range = [start_date-timedelta(days=1), forcast_date + timedelta(days=1)]
        y_axis_range = 'auto'
    for enum_, item in enumerate(values):
        color_ = colors[enum_]
        color_rgba = get_rgb_with_opacity(color_, opacity=0.2)
        sub_df = MASTER_DF[MASTER_DF['PID'] == item]
        sub_df = sub_df.set_index('Date')
        name = KEY_VALUE.loc[item, 'name']
        if metric == 'confirmed':
            hovert = '%{x}<br>Confirmed Cases - %{y:,f}'
            y_axis_title = 'Total Cases'
        else:
            hovert = '%{x}<br>Confirmed Deaths - %{y:,f}'
            y_axis_title = 'Total Deaths'

        if predict:
            # First add the confidence interval
            forcast = sub_df.loc[:forcast_date]
            dates = list(forcast.reset_index()['Date'])
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

            # Then add the prediction lineA
            forcast = sub_df.loc[forcast_date+timedelta(days=1):].reset_index()
            dates = list(forcast['Date'])
            ys = forcast[metric]
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

        # Add the confirmed line
        forcast = sub_df.loc[:forcast_date].reset_index()
        dates = list(forcast['Date'])
        ys = forcast[metric]
        data_traces.append(
            go.Scatter(
                x=dates,
                y=ys,
                showlegend=True,
                mode='lines',
                name=name,
                hovertemplate=hovert,
                marker=dict(
                    color=color_,
                    size=9,
                ),
                line=dict(
                    color=color_,
                    width=5,
                    dash='solid'
                )))
        # Add solid marker at end of confirmed
        if predict:
            hoverinfo = 'none'
        else:
            hoverinfo = 'all'
        forcast = sub_df.loc[forcast_date]
        ys = [forcast[metric]]
        data_traces.append(
            go.Scatter(
                x=[forcast_date],
                y=ys,
                showlegend=False,
                mode='markers',
                name=name,
                hovertemplate=hovert,
                hoverinfo=hoverinfo,
                marker=dict(
                    color=color_,
                    size=12,
                ),
            ))
        # Add a connecting line between prediction and confirmed
        if predict:
            forcast = sub_df.loc[forcast_date:forcast_date+timedelta(days=1)].reset_index()
            dates = list(forcast['Date'])
            ys = forcast[metric]
            data_traces.append(
                go.Scatter(
                    x=dates,
                    y=ys,
                    showlegend=False,
                    mode='lines',
                    name=name,
                    hoverinfo='none',
                    marker=dict(
                        color=color_,
                        size=9,
                    ),
                    line=dict(
                        color=color_,
                        width=2,
                        dash='dashdot'
                    )))
    shapes = []
    if predict:
        shapes.append(
            dict(
                type='rect',
                xref="x",
                yref='paper',
                x0=forcast_date+timedelta(days=1),
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
            title=dict(
                text=y_axis_title,
                standoff=2,
                font=dict(
                    size=AXIS_TITLE_FONT_SIZE,
                    family=FONT_FAMILY,
                )),
            tickfont=dict(
                family=FONT_FAMILY,
                size=AXIS_FONT_SIZE),
            showgrid=True,
            color='white',
            side='left',
            range=y_axis_range
        ),
        xaxis=dict(
            color='white',
            tickfont=dict(
                size=AXIS_FONT_SIZE,
                family=FONT_FAMILY,
            ),
            range=x_axis_range
        ),
        autosize=True,
        showlegend=True,
        hovermode='closest',
        legend=dict(x=0, y=1, font=dict(
            color='white',
            size=LEGEND_FONT_SIZE)),
        paper_bgcolor='#1f2630',
        plot_bgcolor='rgb(52,51,50)')
    if log:
        layout['yaxis']['type'] = 'log'
    return {'data': data_traces, 'layout': layout}


def per_day_confirmed(values, MASTER_DF, KEY_VALUE, log, metric, predict, gs):
    data_traces = []
    if not values:
        data_traces.append(go.Bar(x=[], y=[]))
        y_axis_title = "Select a value"
    MASTER_DF = MASTER_DF.reset_index()
    forcast_date = MASTER_DF.reset_index().groupby('forcast').tail(1)['Date'].iloc[0]
    start_date = MASTER_DF.reset_index()['Date'].iloc[0]
    end_date = MASTER_DF.reset_index()['Date'].iloc[-1]
    sorted_values = list(MASTER_DF[(MASTER_DF['PID'].isin(values)) & (
        MASTER_DF['Date'] == forcast_date)].sort_values('confirmed')[::-1]['PID'])

    x_axis_range = 'auto'
    y_axis_range = 'auto'
    if gs:
        if 'xaxis.range[0]' in gs:
            x_axis_range = [gs['xaxis.range[0]'], gs['xaxis.range[1]']]
        if 'yaxis.range[0]' in gs:
            y_axis_range = [gs['yaxis.range[0]'], gs['yaxis.range[1]']]

    else:
        if predict:
            x_axis_range = [start_date-timedelta(days=1), end_date+timedelta(days=1)]
        else:
            x_axis_range = [start_date-timedelta(days=1), forcast_date+timedelta(days=1)]

        y_axis_range = 'auto'
    # t(sorted_values)
    offset_group = 0

    for enum_, item in enumerate(sorted_values):
        color_ = colors[enum_]
        color_rgba = get_rgb_with_opacity(color_, opacity=0.2)
        sub_df = MASTER_DF[MASTER_DF['PID'] == item].reset_index()
        sub_df = sub_df.set_index('Date')[['confirmed', 'deaths']].diff().fillna(0)
        name = KEY_VALUE.loc[item, 'name']
        if metric == 'confirmed':
            hovert = '%{x}<br>Confirmed Cases - %{y:,f}'
            y_axis_title = 'Total Cases'
        else:
            hovert = '%{x}<br>Confirmed Deaths - %{y:,f}'
            y_axis_title = 'Total Deaths'
        # Add the forcast values
        # forcast = sub_df[sub_df['forcast'] == True]
        if predict:
            forcast = sub_df.loc[forcast_date+timedelta(days=1):]
            dates = list(forcast.reset_index()['Date'])
            ys = forcast[metric]
            data_traces.append(
                go.Bar(
                    x=dates,
                    y=ys,
                    showlegend=False,
                    offsetgroup=offset_group,
                    hovertemplate=hovert.replace('Confirmed', 'Predicted'),
                    name=name,
                    marker=dict(
                        color=color_,
                        line=dict(
                            color='white', width=0.5,
                        )
                    ),
                ))

        forcast = sub_df.loc[:forcast_date]
        dates = list(forcast.reset_index()['Date'])
        ys = forcast[metric]
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
    if predict:
        shapes.append(
            dict(
                type='rect',
                xref="x",
                yref='paper',
                x0=forcast_date+timedelta(hours=12),
                y0=0,
                x1=end_date+timedelta(days=1),
                y1=1,
                line=dict(
                    color='white', width=0),
                fillcolor='rgba(255,255,255,0.2)'
            ))
    layout = dict(
        margin=dict(t=70, r=40, l=80, b=80),
        shapes=shapes,
        yaxis=dict(
            title=dict(
                text=y_axis_title,
                standoff=2,
                font=dict(
                    size=AXIS_TITLE_FONT_SIZE,
                    family=FONT_FAMILY,
                )),
            tickfont=dict(
                family=FONT_FAMILY,
                size=AXIS_FONT_SIZE),
            showgrid=True,
            color='white',
            side='left',
            y_axis_title=y_axis_range,
        ),
        xaxis=dict(
            color='white',
            tickfont=dict(
                size=AXIS_FONT_SIZE,
                family=FONT_FAMILY,
            ),
            range=x_axis_range
        ),
        showlegend=True,
        legend=dict(
            x=0,
            y=1,
            font=dict(color='white',
                      family=FONT_FAMILY,
                      size=LEGEND_FONT_SIZE)),
        paper_bgcolor='#1f2630',
        plot_bgcolor='rgb(52,51,50)',
        barmode='grouped',
        bargap=0.1)
    if log:
        layout['yaxis']['type'] = 'log'

    return {'data': data_traces, 'layout': layout}


def plot_exponential(values, MASTER_DF, KEY_VALUE, log, predict, gs):
    backtrack = 7
    fig = go.Figure()
    max_number = 0
    annotations = []
    MASTER_DF = MASTER_DF.reset_index()
    if gs:
        x_axis_range = [gs['xaxis.range[0]'], gs['xaxis.range[1]']]
        if 'yaxis.range[0]' in gs:
            y_axis_range = [gs['yaxis.range[0]'], gs['yaxis.range[1]']]
        else:
            y_axis_range = ['auto', 'auto']
    else:
        x_axis_range = ['auto', 'auto']
        y_axis_range = ['auto', 'auto']

    for enum_, item in enumerate(values):
        name = KEY_VALUE.loc[item, 'name']
        full_report = MASTER_DF[MASTER_DF['PID'] == item].set_index(['Date', 'forcast'])[['confirmed', 'deaths']]
        per_day = full_report.diff()
        plottable = full_report.join(
            per_day, lsuffix='_cum', rsuffix='_diff')
        plottable = plottable.fillna(0)
        plottable = plottable.reset_index().set_index('Date')
        # print(plottable)
        # print(item, plottable)

        xs = []
        ys = []
        xs_predict = []
        ys_predict = []
        dates = []
        dates_predict = []
        indexes = plottable.index
        # print(plottable)
        for indexer in range(1, len(indexes)):
            date = indexes[indexer]
            x = plottable.loc[date]['confirmed_cum']
            forcast_bool = plottable.loc[date]['forcast']
            # print(forcast_bool)
            if indexer > backtrack:
                y = plottable.loc[date - timedelta(days=backtrack): date].sum()['confirmed_diff']
            else:
                y = plottable.loc[: indexes[indexer]].sum()['confirmed_diff']
            if x > max_number:
                max_number = x
            if y > max_number:
                max_number = y
            if forcast_bool:
                xs_predict.append(x)
                ys_predict.append(y)
                dates_predict.append(date.strftime('%m/%d/%Y'))
            else:
                xs.append(x)
                ys.append(y)
                dates.append(date.strftime('%m/%d/%Y'))
        if not predict:
            sl = True
            circle = 'circle'
        else:
            sl = False
            circle = 'circle-open'

        fig.add_trace(
            go.Scatter(
                x=xs,
                y=ys,
                mode='lines',
                name=name,
                text=dates,
                showlegend=False,
                legendgroup=item,
                line=dict(shape='linear', color=colors[enum_], width=4),
                hovertemplate="On %{text} <br> Total Cases: %{x}<br> Cummulative Cases Last Week %{y}"
            )
        )
        fig.add_trace(
            go.Scatter(
                x=[xs[-1]],
                y=[ys[-1]],
                mode='markers',
                name=name,
                text=[dates[-1]],
                showlegend=sl,
                legendgroup=name,
                hoverlabel=dict(align='left'),
                marker=dict(
                    symbol=circle,
                    size=8,
                    color=colors[enum_]
                ),
                hovertemplate="On %{text} <br> Total Cases: %{x}<br> Cummulative Cases Last Week %{y}"
            )
        )
        if predict:
            fig.add_trace(
                go.Scatter(
                    x=xs_predict,
                    y=ys_predict,
                    mode='lines',
                    name=name,
                    text=dates_predict,
                    showlegend=False,
                    legendgroup=item,
                    line=dict(dash='dash', shape='linear', color=colors[enum_], width=4),
                    hovertemplate="On %{text} <br> Predicted Total Cases: %{x}<br> Predicted Cummulative Cases Last Week %{y}"
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=[xs_predict[-1]],
                    y=[ys_predict[-1]],
                    mode='markers',
                    name=name,
                    text=[dates_predict[-1]],
                    hoverlabel=dict(align='left'),
                    marker=dict(
                        symbol='circle',
                        size=8,
                        color=colors[enum_]
                    ),
                    hovertemplate="On %{text} <br> Predicted Total Cases: %{x}<br> Predicted Cummulative Cases Last Week %{y}"
                )
            )
        if not predict:
            x_annt = xs[-1]
            y_annt = ys[-1]
        else:
            x_annt = xs_predict[-1]
            y_annt = ys_predict[-1]

        annotation = dict(
            xref='x',
            yref='y',
            x=x_annt,
            yanchor='top',
            yshift=-35,
            xanchor='left',
            valign='bottom',
            y=y_annt,
            showarrow=True,
            align='right',
            text=name,
            bgcolor='rgb(52,52,50)',
            font=dict(
                size=12, color='white'))

        if log:
            annotation['x'] = np.log10(annotation['x'])
            annotation['y'] = np.log10(annotation['y'])

        annotations.append(annotation)
    fig.add_trace(
        go.Scatter(
            x=[0, max_number],
            y=[0, max_number],
            hoverinfo='none',
            mode='lines',
            name='Exponential',
            showlegend=True,
            line=dict(color='white', width=3, dash='dash')
        )
    )
    fig.update_layout(annotations=annotations)
    if log:
        fig.update_xaxes(type="log", dtick=1)
        fig.update_yaxes(type="log", dtick=1)

    fig.update_layout(
        yaxis=dict(
            title=dict(
                text='New Cases Previous {} Days'.format(backtrack),
                standoff=2,
                font=dict(
                    size=AXIS_TITLE_FONT_SIZE,
                    family=FONT_FAMILY,
                )),
            tickfont=dict(
                family=FONT_FAMILY,
                size=AXIS_FONT_SIZE),
            showgrid=True,
            color='white',
            side='left',
            range=y_axis_range,
        ),
        margin=dict(t=70, r=40, l=80, b=80),
        xaxis=dict(
            title=dict(
                text='Total Cases',
                standoff=2,
                font=dict(
                    size=AXIS_TITLE_FONT_SIZE,
                    family=FONT_FAMILY,
                )),
            color='white',
            tickfont=dict(
                size=AXIS_FONT_SIZE,
                family=FONT_FAMILY,
            ),
            range=x_axis_range,
            showgrid=False
        ),
        autosize=True,
        showlegend=True,
        paper_bgcolor='#1f2630',
        plot_bgcolor='rgb(52,51,50)',
        legend=dict(x=0.01,
                      y=0.99,
                      font=dict(
                          color='white',
                          family=FONT_FAMILY,
                          size=LEGEND_FONT_SIZE)))
    return fig


def per_gr(values, MASTER_DF, KEY_VALUE, log, metric, predict, gs):
    shapes = []
    data_traces = []
    MASTER_DF = MASTER_DF.reset_index()
    if gs:
        x_axis_range = [gs['xaxis.range[0]'], gs['xaxis.range[1]']]
        if 'yaxis.range[0]' in gs:
            y_axis_range = [gs['yaxis.range[0]'], gs['yaxis.range[1]']]
        else:
            y_axis_range = ['auto', 'auto']
    else:
        if predict:
            x_axis_range = [MASTER_DF['Date'].iloc[0], MASTER_DF['Date'].iloc[-1]]
        else:
            x_axis_range = [MASTER_DF['Date'].iloc[0], MASTER_DF.set_index('forcast').loc[False].iloc[-1]['Date']]

        y_axis_range = ['auto', 'auto']
    for enum_, item in enumerate(values):
        color_ = colors[enum_]
        sub_df = MASTER_DF[MASTER_DF['PID'] == item]
        sub_df = sub_df.set_index('Date')
        xs = sub_df[sub_df['forcast'] == False].index
        xs_predict = sub_df[sub_df['forcast'] == True].index
        name = KEY_VALUE.loc[item, 'name']
        if metric == 'confirmed':
            sub_df = sub_df.reset_index().set_index(['Date', 'forcast'])
            sub_df['gr'] = sub_df['confirmed'].replace(
                to_replace=0, method='ffill').pct_change()*100
            sub_df['gr'] = sub_df['gr'].replace(np.inf, 1)
            sub_df['gr'] = sub_df['gr'].fillna(1)
            sub_df = sub_df.reset_index()
            ys = sub_df[sub_df['forcast'] == False]['gr']
            ys_predict = sub_df[sub_df['forcast'] == True]['gr']
            hovert = '%{x}<br>Growth Rate - %{y:.3f}%'
            y_axis_title = 'Confirmed Cases Growth Rate'
        else:
            sub_df = sub_df.reset_index().set_index(['Date', 'forcast'])
            sub_df['gr'] = sub_df['deaths'].replace(
                to_replace=0, method='ffill').pct_change()*100
            sub_df['gr'] = sub_df['gr'].replace(np.inf, 1)
            sub_df['gr'] = sub_df['gr'].fillna(1)
            sub_df = sub_df.reset_index()
            ys = sub_df[sub_df['forcast'] == False]['gr']
            ys_predict = sub_df[sub_df['forcast'] == True]['gr']
            hovert = '%{x}<br>Death Rate - %{y:.3f}%'
            y_axis_title = 'Confirmed Deaths Growth Rate'

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
        if predict:
            data_traces.append(
                go.Scatter(
                    x=[xs[-1], xs_predict[0]],
                    y=[ys.iloc[-1], ys_predict.iloc[0]],
                    name=name,
                    showlegend=False,
                    hoverinfo='skip',
                    hovertemplate="",
                    mode='lines+markers',
                    textfont=dict(size=14, color='white'),
                    marker=dict(color=color_, symbol='circle-open'),
                    line=dict(dash='dashdot')
                ))
            data_traces.append(
                go.Scatter(
                    x=xs_predict,
                    y=ys_predict,
                    name=name,
                    showlegend=False,
                    hovertemplate=hovert.replace("<br>", "<br> Predicted "),
                    mode='lines+markers',
                    textfont=dict(size=14, color='white'),
                    marker=dict(color=color_, symbol='circle-open'),
                    line=dict(dash='dashdot')
                ))
    if predict:
        shapes.append(
            dict(
                type='rect',
                xref="x",
                yref='paper',
                x0=xs_predict[0],
                y0=0,
                x1=xs_predict[-1],
                y1=1,
                line=dict(
                    color='white', width=0),
                fillcolor='rgba(255,255,255,0.2)'
            ))
    layout = dict(
        margin=dict(t=70, r=40, l=80, b=80),
        shapes=shapes,
        yaxis=dict(
            title=dict(
                text=y_axis_title,
                standoff=2,
                font=dict(
                    size=AXIS_TITLE_FONT_SIZE,
                    family=FONT_FAMILY,
                )),
            tickfont=dict(
                family=FONT_FAMILY,
                size=AXIS_FONT_SIZE),
            showgrid=True,
            color='white',
            side='left',
            range=y_axis_range,
            y_axis_title=y_axis_range,
        ),
        xaxis=dict(
            color='white',
            tickfont=dict(
                size=AXIS_FONT_SIZE,
                family=FONT_FAMILY,
            ),
            range=x_axis_range
        ),
        showlegend=True,
        legend=dict(x=0.01,
                    y=0.99,
                    font=dict(
                        color='white',
                        family=FONT_FAMILY,
                        size=LEGEND_FONT_SIZE)),
        paper_bgcolor='#1f2630',
        hovermode='closest',
        plot_bgcolor='rgb(52,51,50)')
    if log:
        layout['yaxis']['type'] = 'log'

    return {'data': data_traces, 'layout': layout}
