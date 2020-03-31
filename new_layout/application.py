import dash
import functions
import layouts
import callbacks


def get_meta():
    meta_tags = [
        {"name": "viewport",
         "content": "width=device-width, initial-scale=1.0"},
        {"name": "author",
         "content": "Jordan R. Willis PhD"},

        {"name": "description",
         "content": "Hi! My name is Jordan. Here is my COVID-19 tracking application built in Dash and served by Flask and AWS. Timescale Resolution."},
        {"name": "keywords",
         "content": "COVID19,COVID-19,caronavirus,tracking,dash"},
        {'property': 'og:image',
         "content": "https://i.imgur.com/IOSVSbI.png"},
        {'property': 'og:title',
         "content": "Coronavirus 2019 - A tracking application"
         },
        {'property': 'og:description',
         "content": "Hi! My name is Jordan. Here is my COVID-19 tracking application built in Dash and served by Flask and AWS. It is updated with various scraping APIS. Timescale Resolution."
         }

    ]

    return meta_tags


# Initialize APP
app = dash.Dash(__name__,
                meta_tags=get_meta())
app.layout = layouts.serve_dash_layout
callbacks.register_callbacks(app)

# We must expose this for Elastic Bean Stalk to Run
application = app.server


if __name__ == '__main__':
    app.run_server(debug=True, port=8050)
