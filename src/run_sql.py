
import duckdb

# Connect to DuckDB
con = duckdb.connect()

# Read our SQL query from the file
with open("sql/experiment_analysis.sql", "r") as file:
    query = file.read()

# Execute the SQL query
result = con.execute(query).df()

# Display the results
print(result)
