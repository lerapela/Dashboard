import pandas as pd
import plotly.express as px
from dash import Input, Output, callback
from dash import dcc, html

from connection import conn
from productLess import fetch_less_sold_products


# Function to fetch data for the horizontal bar graph
def fetch_popular_products(search_query=None):
    sql_query = """
    --most popular products among customers
    --products their customers like the most.

    SELECT p.Name, COUNT(s.ProductID ) total_numberOf_orders,
    ROUND(((ListPrice - StandardCost) / NULLIF(ListPrice, 0)), 2) *COUNT(s.ProductID )   AS profit_margin

    FROM sales.SalesOrderDetail s

    JOIN Production.Product p ON s.ProductID =p.ProductID
    """

    if search_query:
        sql_query += f" WHERE p.Name LIKE '%{search_query}%'"

    sql_query += """
    GROUP BY p.Name,p.ListPrice,p.StandardCost

    ORDER BY 2 DESC;
    """

    return pd.read_sql(sql_query, conn)


# Fetching data for the horizontal bar graph
df = fetch_popular_products()

# Creating the horizontal bar graph
fig = px.bar(df, x='total_numberOf_orders', y='Name', orientation='h', title='Most Popular Products')

# Adjusting the width of the bars and adding space between them
fig.update_layout(width=1000, height=900, margin=dict(l=100, r=100, t=50, b=50), bargap=0.2)

# Update hover information
fig.update_traces(hovertemplate='Product: %{y}<br>Total Orders: %{x}<br>Profit Margin: %{text}',
                  text=df['profit_margin'])

# Displaying the horizontal bar graph
products = html.Div([
    dcc.Input(id='search-input', type='text', placeholder='Search Product'),
    dcc.Graph(id='popular-products-graph', figure=fig),
    dcc.Input(id='search-input', type='text', placeholder='Search Product'),
    dcc.Graph(id='less-sold-products-graph', figure=fig)
])


# Callback to update the graph based on search input
@callback(
    Output('popular-products-graph', 'figure'),
    [Input('search-input', 'value')]
)
def update_graph(search_query):
    df_filtered = fetch_popular_products(search_query)
    fig = px.bar(df_filtered, x='total_numberOf_orders', y='Name', orientation='h', title='Most Popular Products')
    fig.update_layout(width=1500, height=900, margin=dict(l=100, r=100, t=50, b=50), bargap=0.2)
    fig.update_traces(hovertemplate='Product: %{y}<br>Total Orders: %{x}<br>Profit Margin: %{text}',
                      text=df_filtered['profit_margin'])
    return fig


@callback(
    Output('less-sold-products-graph', 'figure'),
    [Input('search-input', 'value')]
)
def update_graph(search_query):
    df_filtered = fetch_less_sold_products(search_query)
    fig = px.bar(df_filtered, x='total_quantity_sold', y='Name', orientation='h', title='Products Sold Less',
                 labels={'total_quantity_sold': 'Total Quantity Sold'})
    fig.update_layout(width=1000, height=900, margin=dict(l=100, r=100, t=50, b=50), bargap=0.2)
    fig.update_traces(hovertemplate='Product: %{y}<br>Total Quantity Sold: %{x}<br>Profit Margin: %{text}',
                      text=df_filtered['profit_margin'], marker_color='green')
    return fig