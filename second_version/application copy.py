import dash_table
import dash
import pandas as pd
from callbacks import serve_data
JHU_RECENT, JHU_TIME, CSBS, DATE_MAPPER = serve_data(True)

app = dash.Dash(__name__)

df = JHU_RECENT
df = df[['Date_text', 'country', 'province', 'county', 'confirmed', 'deaths']]
df = df.groupby(['Date_text', 'country']).sum(
).reset_index().sort_values('confirmed')[::-1]

app.layout = dash_table.DataTable(
    id='table',
    columns=[{"name": i, "id": i} for i in df.columns],
    data=df.to_dict('records'),
)


if __name__ == '__main__':
    app.run_server(debug=True, port=8050)
