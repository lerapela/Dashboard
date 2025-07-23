import pandas as pd
import dash_bootstrap_components as dbc
from dash import Dash, dcc, html, Input, Output, callback, dash_table
import plotly.express as px
from sqlalchemy import create_engine, text, URL

# Initialize the Dash app with Bootstrap styling
app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])


# Database Connection Setup
def create_db_engine():
    engine_conn_string = (
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=localhost\\SQLEXPRESS;"
        "Database=AdventureWorks2016;"
        "Trusted_Connection=yes;"
    )
    connection_url = URL.create(
        "mssql+pyodbc",
        query={"odbc_connect": engine_conn_string}
    )
    return create_engine(connection_url)


engine = create_db_engine()


# ======================== SALES COMPONENT ========================
def fetch_sales_data(selected_year):
    try:
        if selected_year == 'All':
            sql_query = text("""
                SELECT 
                    YEAR(sh.OrderDate) AS year,
                    FORMAT(sh.OrderDate, 'MMMM') AS month_name,
                    SUM(sd.LineTotal) AS total_sales
                FROM sales.SalesOrderDetail sd
                JOIN sales.SalesOrderHeader sh ON sd.SalesOrderID = sh.SalesOrderID
                GROUP BY YEAR(sh.OrderDate), FORMAT(sh.OrderDate, 'MMMM')
                ORDER BY YEAR(sh.OrderDate), MIN(sh.OrderDate)
                """)
            with engine.connect() as connection:
                return pd.read_sql(sql_query, connection)
        else:
            sql_query = text("""
                SELECT 
                    YEAR(sh.OrderDate) AS year,
                    FORMAT(sh.OrderDate, 'MMMM') AS month_name,
                    SUM(sd.LineTotal) AS total_sales
                FROM sales.SalesOrderDetail sd
                JOIN sales.SalesOrderHeader sh ON sd.SalesOrderID = sh.SalesOrderID
                WHERE YEAR(sh.OrderDate) = :selected_year
                GROUP BY YEAR(sh.OrderDate), FORMAT(sh.OrderDate, 'MMMM')
                ORDER BY YEAR(sh.OrderDate), MIN(sh.OrderDate)
                """)
            with engine.connect() as connection:
                return pd.read_sql(sql_query, connection, params={'selected_year': selected_year})
    except Exception as e:
        print(f"Database error: {e}")
        return pd.DataFrame()


def fetch_unique_years():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("""
                SELECT DISTINCT YEAR(OrderDate) 
                FROM sales.SalesOrderHeader
                ORDER BY YEAR(OrderDate)
                """))
            years = [str(row[0]) for row in result]
            years.append('All')
            return years
    except Exception as e:
        print(f"Error fetching years: {e}")
        return ['2011', '2012', '2013', '2014', 'All']


initial_year = 'All'
df_sales = fetch_sales_data(initial_year)

sale_layout = html.Div(children=[
    html.H2("Sales Volume Over Time"),
    dcc.Dropdown(
        id='year-dropdown',
        options=[{'label': year, 'value': year} for year in fetch_unique_years()],
        value=initial_year,
        style={'width': '50%', 'margin': 'auto', 'margin-bottom': '20px'}
    ),
    dcc.Graph(id='sales-graph'),
])


# ======================== ORDERS COMPONENT ========================
def fetch_order_data():
    sql_query = text("""
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
    """)
    with engine.connect() as connection:
        return pd.read_sql(sql_query, connection)


df_orders = fetch_order_data()
fig_orders = px.scatter(df_orders, x='OrderDate', y='TotalQuantityOrdered', color='ProductName',
                        title="Total Quantity of Orders for Each Product Over Time",
                        labels={'TotalQuantityOrdered': 'Total Quantity Ordered', 'OrderDate': 'Order Date'})
fig_orders.update_layout(xaxis_title="Order Date", yaxis_title="Total Quantity Ordered")

orders_layout = html.Div([
    dcc.Graph(id='order-scatter-plot', figure=fig_orders)
])


# ======================== PRODUCTS COMPONENT ========================
def fetch_popular_products(search_query=None):
    base_query = """
    SELECT p.Name, COUNT(s.ProductID) total_numberOf_orders,
    ROUND(((ListPrice - StandardCost) / NULLIF(ListPrice, 0)), 2) *COUNT(s.ProductID) AS profit_margin
    FROM sales.SalesOrderDetail s
    JOIN Production.Product p ON s.ProductID = p.ProductID
    """
    if search_query:
        base_query += f" WHERE p.Name LIKE '%{search_query}%'"
    base_query += " GROUP BY p.Name,p.ListPrice,p.StandardCost ORDER BY 2 DESC;"

    with engine.connect() as connection:
        return pd.read_sql(text(base_query), connection)


def fetch_less_sold_products(search_query=None):
    base_query = """
    SELECT p.Name, COUNT(s.ProductID) AS total_quantity_sold,
    ROUND(((ListPrice - StandardCost) / NULLIF(ListPrice, 0)), 2) * COUNT(s.ProductID) AS profit_margin
    FROM Production.Product p
    LEFT JOIN Sales.SalesOrderDetail s ON p.ProductID = s.ProductID
    GROUP BY p.Name, p.ListPrice, p.StandardCost, s.OrderQty
    HAVING SUM(s.OrderQty) < 3
    ORDER BY total_quantity_sold ASC;
    """
    if search_query:
        base_query = base_query.replace("GROUP BY", f"WHERE p.Name LIKE '%{search_query}%' GROUP BY")

    with engine.connect() as connection:
        return pd.read_sql(text(base_query), connection)


df_popular = fetch_popular_products()
df_less_sold = fetch_less_sold_products()

products_layout = html.Div([
    html.H2("Product Performance Analysis"),
    dcc.Input(id='search-input', type='text', placeholder='Search Product...',
              style={'width': '100%', 'margin-bottom': '20px'}),

    html.Div([
        html.H3("Most Popular Products"),
        dcc.Graph(id='popular-products-graph',
                  figure=px.bar(df_popular, x='total_numberOf_orders', y='Name', orientation='h',
                                title='Most Popular Products').update_layout(height=600))
    ]),

    html.Div([
        html.H3("Less Sold Products"),
        dcc.Graph(id='less-sold-products-graph',
                  figure=px.bar(df_less_sold, x='total_quantity_sold', y='Name', orientation='h',
                                title='Products Sold Less', color_discrete_sequence=['green']).update_layout(
                      height=600))
    ])
])


# ======================== STORES COMPONENT ========================
def fetch_store_performance():
    sql_query = text("""
    WITH StoreProductSales AS (
        SELECT 
            SST.Name AS CountryName,
            SST.CountryRegionCode AS CountryRegionCode,
            SS.BusinessEntityID AS StoreID,
            SS.Name AS StoreName,
            PP.ProductID,
            PP.Name AS ProductName,
            ROUND(((ListPrice - StandardCost) / NULLIF(ListPrice, 0)), 2) * SUM(SD.OrderQty) AS profit_margin,
            SUM(SD.OrderQty) AS TotalQuantitySold,
            ROW_NUMBER() OVER (PARTITION BY PP.ProductID ORDER BY SUM(SD.OrderQty) DESC) AS StoreRank
        FROM 
            Sales.Store AS SS
        JOIN 
            Sales.Customer AS SC ON SS.BusinessEntityID = SC.StoreID
        JOIN [Sales].[SalesTerritory] SST ON SST.TerritoryID = SC.TerritoryID
        JOIN 
            Sales.SalesOrderHeader AS SH ON SC.CustomerID = SH.CustomerID
        JOIN 
            Sales.SalesOrderDetail AS SD ON SH.SalesOrderID = SD.SalesOrderID
        JOIN 
            Production.Product AS PP ON SD.ProductID = PP.ProductID
        GROUP BY 
            SS.BusinessEntityID,
            SS.Name,
            PP.ProductID,
            PP.Name,SST.Name,SST.CountryRegionCode,PP.ListPrice,PP.StandardCost
    )
    SELECT 
        StoreID,
        StoreName,
        CountryName,
        CountryRegionCode,
        ProductID,
        ProductName,
        TotalQuantitySold,
        profit_margin
    FROM 
        StoreProductSales
    WHERE 
        StoreRank = 1
    ORDER BY 
        StoreID,
        ProductID,
        TotalQuantitySold DESC;
    """)
    with engine.connect() as connection:
        return pd.read_sql(sql_query, connection)


def fetch_low_performing_stores():
    sql_query = text("""
    WITH StoreProductSales AS (
        SELECT 
              SST.Name AS CountryName,
            SST.CountryRegionCode AS CountryRegionCode,
            SS.BusinessEntityID AS StoreID,
            SS.Name AS StoreName,
            PP.ProductID,
            PP.Name AS ProductName,
            ROUND(((ListPrice - StandardCost) / NULLIF(ListPrice, 0)), 2) *SUM(SD.OrderQty)  AS profit_margin,
            SUM(SD.OrderQty) AS TotalQuantitySold,
            RANK() OVER (PARTITION BY PP.ProductID ORDER BY SUM(SD.OrderQty) ASC) AS StoreRank
        FROM 
            Sales.Store AS SS
        JOIN 
            Sales.Customer AS SC ON SS.BusinessEntityID = SC.StoreID
        JOIN [Sales].[SalesTerritory] SST ON SST.TerritoryID = SC.TerritoryID
        JOIN 
            Sales.SalesOrderHeader AS SH ON SC.CustomerID = SH.CustomerID
        JOIN 
            Sales.SalesOrderDetail AS SD ON SH.SalesOrderID = SD.SalesOrderID
        JOIN 
            Production.Product AS PP ON SD.ProductID = PP.ProductID
        GROUP BY 
            SS.BusinessEntityID,
            SS.Name,
            PP.ProductID,
            PP.Name,SST.Name,SST.CountryRegionCode,PP.ListPrice,PP.StandardCost
    )
    SELECT 
        StoreID,
        StoreName,
        CountryName,
        CountryRegionCode,
        ProductID,
        ProductName,
        TotalQuantitySold,
        profit_margin
    FROM 
        StoreProductSales
    WHERE 
        StoreRank = 1
    ORDER BY 
        ProductID,
        TotalQuantitySold ASC;
    """)
    with engine.connect() as connection:
        return pd.read_sql(sql_query, connection)


df_high_performing = fetch_store_performance()
df_low_performing = fetch_low_performing_stores()

stores_layout = html.Div([
    html.H2("Store Performance Analysis"),

    html.Div([
        html.H3("High Performing Stores"),
        dash_table.DataTable(
            id='high-performing-table',
            columns=[{"name": i, "id": i} for i in df_high_performing.columns],
            data=df_high_performing.to_dict('records'),
            sort_action="native",
            filter_action="native",
            page_size=10,
            style_table={'overflowX': 'auto'},
            style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
            style_cell={'textAlign': 'left', 'minWidth': '100px'},
        )
    ]),

    html.Div([
        html.H3("Low Performing Stores"),
        dash_table.DataTable(
            id='low-performing-table',
            columns=[{"name": i, "id": i} for i in df_low_performing.columns],
            data=df_low_performing.to_dict('records'),
            sort_action="native",
            filter_action="native",
            page_size=10,
            style_table={'overflowX': 'auto'},
            style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
            style_cell={'textAlign': 'left', 'minWidth': '100px'},
        )
    ])
])

# ======================== MAIN APP LAYOUT ========================
app.layout = html.Div([
    dbc.Navbar(
        dbc.Container([
            html.A(
                dbc.Col(dbc.NavbarBrand("AdventureWorks2016 Dashboard", className="ms-2")),
                href="/",
                style={"textDecoration": "none"},
            ),
        ]),
        color="dark",
        dark=True,
    ),

    dbc.Tabs([
        dbc.Tab(label="Sales", tab_id="sales"),
        dbc.Tab(label="Orders", tab_id="orders"),
        dbc.Tab(label="Products", tab_id="products"),
        dbc.Tab(label="Stores", tab_id="stores"),
    ], id="tabs", active_tab="sales"),

    html.Div(id="content")
])


# ======================== CALLBACKS ========================
@app.callback(
    Output("content", "children"),
    [Input("tabs", "active_tab")]
)
def switch_tab(active_tab):
    if active_tab == "sales":
        return sale_layout
    elif active_tab == "orders":
        return orders_layout
    elif active_tab == "products":
        return products_layout
    elif active_tab == "stores":
        return stores_layout
    return html.P("Please select a tab")


@app.callback(
    Output('sales-graph', 'figure'),
    [Input('year-dropdown', 'value')]
)
def update_sales_graph(selected_year):
    df_sales = fetch_sales_data(selected_year)

    if df_sales.empty:
        return px.scatter(title="No data available")

    if selected_year == 'All':
        fig = px.line(df_sales, x='year', y='total_sales',
                      title='Sales Volume Over Time',
                      hover_data={'month_name': True, 'total_sales': ':.2f'})
        fig.update_xaxes(title_text='Year')
    else:
        fig = px.line(df_sales, x='month_name', y='total_sales',
                      title=f'Sales Volume for {selected_year}',
                      hover_data={'month_name': True, 'total_sales': ':.2f'})
        fig.update_xaxes(title_text='Month', categoryorder='array',
                         categoryarray=['January', 'February', 'March', 'April',
                                        'May', 'June', 'July', 'August',
                                        'September', 'October', 'November', 'December'])

    fig.update_layout(
        hovermode='x unified',
        yaxis_title="Total Sales",
        plot_bgcolor='rgba(0,0,0,0)'
    )
    fig.update_traces(line=dict(width=3))
    return fig


@app.callback(
    [Output('popular-products-graph', 'figure'),
     Output('less-sold-products-graph', 'figure')],
    [Input('search-input', 'value')]
)
def update_products_graph(search_query):
    df_popular = fetch_popular_products(search_query)
    df_less_sold = fetch_less_sold_products(search_query)

    fig_popular = px.bar(df_popular, x='total_numberOf_orders', y='Name', orientation='h',
                         title='Most Popular Products').update_layout(height=600)
    fig_popular.update_traces(
        hovertemplate='Product: %{y}<br>Total Orders: %{x}<br>Profit Margin: %{text}',
        text=df_popular['profit_margin']
    )

    fig_less_sold = px.bar(df_less_sold, x='total_quantity_sold', y='Name', orientation='h',
                           title='Products Sold Less', color_discrete_sequence=['green']).update_layout(height=600)
    fig_less_sold.update_traces(
        hovertemplate='Product: %{y}<br>Total Quantity Sold: %{x}<br>Profit Margin: %{text}',
        text=df_less_sold['profit_margin']
    )

    return fig_popular, fig_less_sold


if __name__ == '__main__':
    app.run_server(debug=True)