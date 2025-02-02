import pandas as pd
from connection import conn


# Function to fetch data for products sold less
def fetch_less_sold_products(search_query=None):
    sql_query = """
    --Products which are sold less.
    SELECT p.Name, COUNT(s.ProductID) AS total_quantity_sold,
    ROUND(((ListPrice - StandardCost) / NULLIF(ListPrice, 0)), 2) * COUNT(s.ProductID) AS profit_margin
    FROM Production.Product p
    LEFT JOIN Sales.SalesOrderDetail s ON p.ProductID = s.ProductID
    GROUP BY p.Name, p.ListPrice, p.StandardCost, s.OrderQty
    HAVING SUM(s.OrderQty) < 3 -- Adjust the threshold as needed
    ORDER BY total_quantity_sold ASC;
    """
    return pd.read_sql(sql_query, conn)


# Fetching data for products sold less
df = fetch_less_sold_products()



