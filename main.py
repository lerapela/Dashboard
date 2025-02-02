import pandas as pd
import dash_bootstrap_components as dbc
from dash import Input, Output, html, callback, Dash
from dash import Dash, dcc, html
import plotly.express as px
from sqlalchemy import URL, create_engine
from connection import conn
from Sales import sale
from product import products  #50 from product
from storeInfo import  stores #70 from storeInfo

app = Dash(external_stylesheets=[dbc.themes.FLATLY])



# Function to fetch data for the scatter plot
def fetch_order_data():
    sql_query = """
    ---how many orders they're getting and when they're happening most frequently of the products
    SELECT 
        CONCAT(DATEPART(YEAR, soh.OrderDate), '-', DATEPART(MONTH, soh.OrderDate)) AS OrderDate,
        p.Name AS ProductName,
        SUM(sod.OrderQty) AS TotalQuantityOrdered
    FROM 
        Sales.SalesOrderHeader AS soh
    JOIN 
        Sales.SalesOrderDetail AS sod ON soh.SalesOrderID = sod.SalesOrderID
    JOIN 
        Production.Product AS p ON sod.ProductID = p.ProductID
    GROUP BY 
        CONCAT(DATEPART(YEAR, soh.OrderDate), '-', DATEPART(MONTH, soh.OrderDate)),
        p.Name
    ORDER BY 
        OrderDate,
        TotalQuantityOrdered DESC;
    """
    df1 = pd.read_sql(sql_query, conn)
    return df1


# Fetching data for the scatter plot
df = fetch_order_data()

# Creating the scatter plot
fig = px.scatter(df, x='OrderDate', y='TotalQuantityOrdered', color='ProductName',
                 title="Total Quantity of Orders for Each Product Over Time",
                 labels={'TotalQuantityOrdered': 'Total Quantity Ordered', 'OrderDate': 'Order Date'})

# Adjusting the layout of the scatter plot
fig.update_layout(xaxis_title="Order Date", yaxis_title="Total Quantity Ordered")

# Displaying the scatter plot
orders = html.Div([
    dcc.Graph(id='order-scatter-plot', figure=fig)
])

app.layout = html.Div(
    [
        dbc.Navbar(
            dbc.Container(
                [
                    html.A(
                        dbc.Col(dbc.NavbarBrand("AdventureWorks2016 Dashboard", className="ms-2")),
                        href="/",
                        style={"textDecoration": "none"},
                    ),

                ]
            ),
            color="dark",
            dark=True,
        ),
        dbc.Tabs(
            [
                dbc.Tab(label="Sales", tab_id="sales"),
                dbc.Tab(label="Orders", tab_id="orders"),
                dbc.Tab(label="Products", tab_id="products"),
                dbc.Tab(label="Stores", tab_id="stores"),

            ],
            id="tabs",
            active_tab="home",
        ),
        html.Div(id="content"),
    ]
)


@callback(Output("content", "children"),
          [Input("tabs", "active_tab")])
def switch_tab(at):

    if at == "home":
        return html.Div([
            html.A(
                dbc.Col(dbc.NavbarBrand("Home", className="ms-2")),
                href="/",
                style={"textDecoration": "none"},
            ),
        ])
    elif at == "orders":
        return orders
    elif at == "products":
        return products
    elif at == "stores":
        return stores
    elif at == "sales":
        return sale
    return html.P("Error 404: Page not found.")


if __name__ == '__main__':
    app.run_server(debug=True)
