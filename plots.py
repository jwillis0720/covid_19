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


def plot_map(dataframe, metrics, zoom, center):
    data_traces = []
    if not metrics or dataframe.empty:
        data_traces.append(go.Scattermapbox(
            lon=[],
            lat=[]
        ))
    if 'confirmed' in metrics and not dataframe.empty:
        # First Do Confirmed
        gb_confirmed = dataframe.groupby('CSize')

        # Do this so we can sort them if need be
        for group in gb_confirmed:
            plotting_df = group[1]
            sizes = plotting_df['confirmed']
            # This should be so, but okay
            sizes[sizes < 1] = 1
            name = "{}-{}".format(get_closest_inerval(int(plotting_df['confirmed'].min()), 'min'),
                                  get_closest_inerval(int(plotting_df['confirmed'].max()), 'max'))
            data = go.Scattermapbox(
                lon=plotting_df['lon'],
                lat=plotting_df['lat'],
                customdata=plotting_df['pid'],
                text=plotting_df['Text_Confirmed'],
                hoverinfo='text',
                name=name,
                mode='markers',
                marker=dict(
                    opacity=0.85,
                    sizemin=3,
                    size=plotting_df['CSize'],
                    color=plotting_df['CColor'],
                    sizemode='area'
                )
            )
            data_traces.append(data)
    if 'deaths' in metrics and not dataframe.empty:
        # Second Do Confirmed
        dataframe = dataframe[dataframe['deaths'] > 1]
        gb_deaths = dataframe.groupby('DSize')

        # Do this so we can sort them if need be
        for group in gb_deaths:
            plotting_df = group[1]
            # This should be so, but okay
            name = "{}-{}".format(get_closest_inerval(int(plotting_df['deaths'].min()), 'min'),
                                  get_closest_inerval(int(plotting_df['deaths'].max()), 'max'))
            data = go.Scattermapbox(
                lon=plotting_df['lon'],
                lat=plotting_df['lat'],
                customdata=plotting_df['pid'],
                text=plotting_df['Text_Deaths'],
                hoverinfo='text',
                name=name,
                mode='markers',
                marker=dict(
                    opacity=0.85,
                    sizemin=3,
                    size=plotting_df['DSize'],
                    color=plotting_df['DColor'],
                    sizemode='area'
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
            x=0.00,
            y=0.00,
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


def total_confirmed_graph(values, MASTER_DF, KEY_VALUE,log=False, metric='confirmed'):
    data_traces = []
    MASTER_DF = MASTER_DF.reset_index()
    forcast_date = MASTER_DF.groupby('forcast').tail(1)['Date'].iloc[0]
    start_date = MASTER_DF['Date'].iloc[0]
    end_date = MASTER_DF['Date'].iloc[-1]
    for enum_, item in enumerate(values):
        color_ = colors[enum_]
        color_rgba = get_rgb_with_opacity(color_, opacity=0.2)
        sub_df = MASTER_DF[MASTER_DF['pid'] == item]
        sub_df = sub_df.set_index('Date')
        name = KEY_VALUE.loc[item,'name']
        if metric == 'confirmed':
            hovert = '%{x}<br>Confirmed Cases - %{y:,f}'
            y_axis_title = 'Total Cases'
        else:
            hovert = '%{x}<br>Confirmed Deaths - %{y:,f}'
            y_axis_title = 'Total Deaths'

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


        #Add solid marker at end of confirmed
        forcast = sub_df.loc[forcast_date]
        ys = [forcast[metric]]
        data_traces.append(
            go.Scatter(
                x=[forcast_date],
                y=ys,
                showlegend=False,
                mode='markers',
                hoverinfo='none',
                marker=dict(
                    color=color_,
                    size=12,
                ),
                ))
        # Add a connecting line between prediction and confirmed
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
            title=dict(text=y_axis_title, standoff=2),
            titlefont_size=16,
            tickfont_size=16,
            showgrid=True,
            color='white',
            side='left',
        ),
        xaxis=dict(
            color='white',
            tickfont_size=16,
            range=[start_date-timedelta(days=1), end_date+timedelta(days=1)]
        ),
        autosize=True,
        showlegend=True,
        legend=dict(x=0, y=1, font=dict(color='white')),
        paper_bgcolor='#1f2630',
        plot_bgcolor='rgb(52,51,50)')
    if log:
        layout['yaxis']['type'] = 'log'
    return {'data': data_traces, 'layout': layout}


def per_day_confirmed(values,MASTER_DF, KEY_VALUE, log=True, metric='confirmed'):
    data_traces = []
    if not values:
        data_traces.append(go.Bar(x=[],y=[]))
        y_axis_title = "Select a value"
    MASTER_DF = MASTER_DF.reset_index()
    forcast_date = MASTER_DF.reset_index().groupby('forcast').tail(1)['Date'].iloc[0]
    start_date = MASTER_DF.reset_index()['Date'].iloc[0]
    end_date = MASTER_DF.reset_index()['Date'].iloc[-1] 
    sorted_values = list(MASTER_DF[(MASTER_DF['pid'].isin(values)) & (MASTER_DF['Date']==end_date)].sort_values('confirmed')[::-1]['pid'])
    
    print(sorted_values)
    offset_group = 0

    for enum_, item in enumerate(sorted_values):
        color_ = colors[enum_]
        color_rgba = get_rgb_with_opacity(color_, opacity=0.2)
        sub_df = MASTER_DF[MASTER_DF['pid'] == item].reset_index()
        sub_df = sub_df.set_index('Date')[['confirmed','deaths']].diff().fillna(0)
        name = KEY_VALUE.loc[item,'name']
        if metric == 'confirmed':
            hovert = '%{x}<br>Confirmed Cases - %{y:,f}'
            y_axis_title = 'Total Cases'
        else:
            hovert = '%{x}<br>Confirmed Deaths - %{y:,f}'
            y_axis_title = 'Total Deaths' 
        # Add the forcast values
        # forcast = sub_df[sub_df['forcast'] == True]
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
    shapes.append(
        dict(
            type='rect',
            xref="x",
            yref='paper',
            x0=forcast_date+timedelta(hours=12),
            y0=0,
            x1=end_date+timedelta(days=365),
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
            range=[start_date+timedelta(days=1), end_date+timedelta(hours=12)]
        ),
        showlegend=True,
        legend=dict(x=0, y=1, font=dict(color='white')),
        paper_bgcolor='#1f2630',
        plot_bgcolor='rgb(52,51,50)',
        barmode='grouped',
        bargap=0.1)
    if log:
        layout['yaxis']['type'] = 'log'

    return {'data': data_traces, 'layout': layout}


def plot_exponential(values, MASTER_DF, KEY_VALUE, log):
    backtrack = 7
    fig = go.Figure()
    max_number = 0
    annotations = []
    MASTER_DF = MASTER_DF.reset_index()
    for enum_, item in enumerate(values):
        name = KEY_VALUE.loc[item,'name']
        full_report = MASTER_DF[MASTER_DF['pid'] == item].set_index(['Date','forcast'])[['confirmed','deaths']]
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
            print(forcast_bool)
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
                showlegend=False,
                legendgroup=name,
                hoverlabel=dict(align='left'),
                marker=dict(
                    symbol='circle-open',
                    size=8,
                    color=colors[enum_]
                ),
                hovertemplate="On %{text} <br> Total Cases: %{x}<br> Cummulative Cases Last Week %{y}"
            )
       )
        fig.add_trace(
            go.Scatter(
                x=xs_predict,
                y=ys_predict,
                mode='lines',
                name=name,
                text=dates_predict,
                showlegend=False,
                legendgroup=item,
                line=dict(dash='dash', shape='linear',color=colors[enum_], width=4),
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
        if not log:
            annotations.append(
                dict(xref='x',yref='y',x=xs_predict[-1],yanchor='top',yshift=-35, xanchor='left',valign='bottom', y=ys_predict[-1],showarrow=True, align='right',text=name,font=dict(size=12,color='white'))
            )
        else:
             annotations.append(
                dict(xref='x',yref='y',x=np.log10(xs_predict[-1]),yanchor='top',yshift=-35, xanchor='left',valign='bottom', y=np.log10(ys_predict[-1]),showarrow=True, align='right',text=name,font=dict(size=12,color='white'))
              )
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
        legend=dict(x=0.01, y=0.99, font=dict(color='white')))

    if log:
        x_ref = 5
        y_ref = 5.4
    else:
        x_ref = 8 * 10 ** 5
        y_ref = 8 * 10 ** 5
    # annotations.append(dict(xref='x', x=x_ref, yref='y', y=y_ref,
    #                         text="Exponential Growth",
    #                         font=dict(family='Montserrat',
    #                                   color='white',size=12),
    #                         showarrow=True,
    #                         startarrowsize=10,
    #                         arrowwidth=2,
    #                         arrowcolor='white',
    #                         arrowhead=2,
    #                         ))

    # fig.update_layout(legend=dict(title='Click to Toggle'),
    #                   annotations=[])

    fig.update_layout(
        margin=dict(t=50, b=20, r=30, l=20, pad=0))
    print(fig.layout)
    return fig


def per_gr(values, MASTER_DF, KEY_VALUE, log=False, metric='confirmed'):

    data_traces = []
    MASTER_DF = MASTER_DF.reset_index()
    for enum_, item in enumerate(values):
        color_ = colors[enum_]
        sub_df = MASTER_DF[MASTER_DF['pid'] == item]
        sub_df = sub_df.set_index('Date')
        xs = sub_df[sub_df['forcast'] == False].index
        xs_predict = sub_df[sub_df['forcast'] == True].index
        name = KEY_VALUE.loc[item,'name']
        if metric == 'confirmed':
            sub_df = sub_df.reset_index().set_index(['Date','forcast'])
            sub_df['gr'] = sub_df['confirmed'].replace(
                to_replace=0, method='ffill').pct_change()*100
            sub_df['gr'] = sub_df['gr'].replace(np.inf,1)
            sub_df['gr'] = sub_df['gr'].fillna(1)
            sub_df = sub_df.reset_index()
            ys = sub_df[sub_df['forcast'] == False]['gr']
            ys_predict = sub_df[sub_df['forcast'] == True]['gr']
            hovert = '%{x}<br>Growth Rate - %{y:.3f}%'
            y_axis_title = 'Confirmed Cases Growth Factor'
        else:
            s = sub_df['deaths'].replace(
                to_replace=0, method='ffill').pct_change()*100
            ys = s.replace(np.inf, 1)
            ys = ys.fillna(1)
            hovert = '%{x}<br>Death Growth - %{y:.3f}%'
            y_axis_title = 'Deaths Growth Rate'

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
        data_traces.append(
            go.Scatter(
                x=xs_predict,
                y=ys_predict,
                name=name,
                showlegend=False,
                hovertemplate=hovert,
                mode='lines+markers',
                textfont=dict(size=14, color='white'),
                marker=dict(color=color_, symbol='circle-open'),
                line=dict(dash='dashdot')
                ))

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
