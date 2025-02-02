import pandas as pd
import plotly.express as px
from dash import html, dcc, Output, callback, Input
from connection import conn

# Function to fetch sales data
def fetch_sales_data(selected_year):
    if selected_year == 'All':
        sql_query = """
        SELECT 
            YEAR(sh.OrderDate) AS year,
            FORMAT(sh.OrderDate, 'MMMM') AS month_name,
            SUM(sd.LineTotal) AS total_sales
        FROM sales.SalesOrderDetail sd
        JOIN sales.SalesOrderHeader sh ON sd.SalesOrderID = sh.SalesOrderID
        GROUP BY YEAR(sh.OrderDate), FORMAT(sh.OrderDate, 'MMMM')
        ORDER BY YEAR(sh.OrderDate), MIN(sh.OrderDate)
        """
        return pd.read_sql(sql_query, conn)
    else:
        sql_query = """
        SELECT 
            YEAR(sh.OrderDate) AS year,
            FORMAT(sh.OrderDate, 'MMMM') AS month_name,
            SUM(sd.LineTotal) AS total_sales
        FROM sales.SalesOrderDetail sd
        JOIN sales.SalesOrderHeader sh ON sd.SalesOrderID = sh.SalesOrderID
        WHERE YEAR(sh.OrderDate) = :selected_year
        GROUP BY YEAR(sh.OrderDate), FORMAT(sh.OrderDate, 'MMMM')
        ORDER BY YEAR(sh.OrderDate), MIN(sh.OrderDate)
        """
        return pd.read_sql(sql_query, conn, params={'selected_year': selected_year})


# Fetch unique years for dropdown options
def fetch_unique_years():
    years = list(range(2011, 2015))
    # Include "All" option
    years.append('All')
    return years

# Initial year selection
initial_year = 'All'

# Fetch initial sales data
df_sales = fetch_sales_data(initial_year)

# Define the layout
sale = html.Div(children=[
    html.H2("Sales Volume Over Time"),
    dcc.Dropdown(
        id='year-dropdown',
        options=[{'label': str(year), 'value': year} for year in fetch_unique_years()],
        value=initial_year,
        style={'width': '50%', 'margin': 'auto', 'margin-bottom': '20px'}
    ),
    dcc.Graph(id='sales-graph'),
])

@callback(
    Output('sales-graph', 'figure'),
    [Input('year-dropdown', 'value')]
)
def update_sales_graph(selected_year):
    df_sales = fetch_sales_data(selected_year)
    if selected_year == 'All':
        fig = px.line(df_sales, x='year', y='total_sales', title='Sales Volume Over Time',
                      hover_data={'month_name': True, 'total_sales': ':.2f'})
        fig.update_xaxes(title_text='Year')
    else:
        fig = px.line(df_sales, x='month_name', y='total_sales', title='Sales Volume Over Time',
                      hover_data={'month_name': True, 'total_sales': ':.2f'})
        fig.update_xaxes(title_text='Month')
    fig.update_traces(line=dict(width=3))
    return fig
