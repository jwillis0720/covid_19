## COVID-19 Bored

COVID-19 Bored is a web application that uses Country, US state and US county wide data to plot, track and predict confirmed cases and deaths. COVID-19 Bored, is a DashBoard I created while bored, hence COVID-19 *Bored*.

## Country Data
Like most COIVD-19 trackers, it was inspired from the Johns Hopkins University (JHU) tracking application found [here](https://www.arcgis.com/apps/opsdashboard/index.html#/bda7594740fd40299423467b48e9ecf6). JHU has compiled an updating list of countries and reports a timeline of deaths, confirmed cases, and recoveries.

## State and County data
JHU does not track state and county granularity. For that, I use the New York Times which [has published](https://github.com/nytimes/covid-19-data) county wide data for the United States. I then joined that data with county wide population and location statistics.

## Development
 I used a publicly available map at [mapbox](https://www.mapbox.com). The app is written with [Dash and Plot.ly](https://plotly.com/) with my own CSS. I am not an epidemiologist nor a front-end developer. I wanted to learn how to make a publicly facing web application. Dash allows me to abstract all the React.js code into python. 

 ## Predictions
 
 Confirmed cases and deaths are forecasted for 14 days. I used the [ARIMA model](https://www.machinelearningplus.com/time-series/arima-model-time-series-forecasting-python/) inspired from a [Kaggle](https://www.kaggle.com/) notebook I cant find anymore. If you have information on this notebook, please reach out. 

## How to use:
Confirmed cases and deaths are available at the Region/Country, State, or County level. All can be compared by clicking the hover icon on the map. They can be manually added to the list for comparison. The date slider can be used to show the disease progression across time. Four types of graphs are available. The cumulative cases graph, the new cases per day graph, the exponential graph, and the growth rate graph. The exponential plot was inspired by [MinutePhysics](https://www.youtube.com/watch?v=54XLXg4fYsc) on youtube. It's a great way to see exponential growth.

===

The code is available at my [github](https://github.com/jwillis0720/covid_19). You can find me on [LinkedIn](https://www.linkedin.com/in/jwillis0720) or my [website](https://www.jordanrwillis.com).
