
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL

engine_conn_string = ("Driver={SQL Server};"
                      "Server=serverName\\SQLEXPRESS;"
                      "Database=AdventureWorks2016;"
                      "Trusted_Connection=yes;")
connection_url = URL.create("mssql+pyodbc", query={"odbc_connect": engine_conn_string})
conn = create_engine(connection_url)