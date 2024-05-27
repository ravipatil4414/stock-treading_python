import mysql.connector

try:
    mydb = mysql.connector.connect(
        host="database-1.cfyqg0kwq7od.ap-south-1.rds.amazonaws.com",
        user="ancit",
        password="Ravi12345",
        database="kite_data"
    )
    print("Connection successful")
except mysql.connector.Error as err:
    print(f"Error: {err}")

