import random

import pandas as pd
import plotly.express as px
import pyodbc
from dash import Input, Output, callback, dash_table
from dash import dcc, html

from connection import conn

# Function to fetch data for low-performing stores
def fetch_low_performing_stores():
    sql_query = """
    -- Separate script for low-performing stores
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
        StoreRank = 1  -- Select the store with the lowest sales for each product
    ORDER BY 
        ProductID,
        TotalQuantitySold ASC;
    """


    df = pd.read_sql(sql_query, conn)
    return df

# function to Fetch data for low-performing stores
df = fetch_low_performing_stores()



# Displaying the data in a DataTable with conditional formatting
stores2 = html.Div([
    html.H1("Low Performing Stores"),

    dash_table.DataTable(
        id='table',
        columns=[{"name": i, "id": i} for i in df.columns],
        data=df.to_dict('records'),
        sort_action="native",
        style_table={'overflowX': 'scroll'},
        style_header={'fontWeight': 'bold'},
        style_data={'whiteSpace': 'normal', 'height': 'auto'},
        page_size=10,

    )
])

# Callback to update the table based on the search input
@callback(
    Output('table', 'data'),
    [Input('store-input', 'value')]
)
def update_table(search_value):
    if search_value:
        filtered_data = df[df['StoreName'].str.contains(search_value, case=False)]
        return filtered_data.to_dict('records')
    else:
        return df.to_dict('records')