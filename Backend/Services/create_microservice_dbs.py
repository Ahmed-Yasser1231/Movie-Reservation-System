import pymysql

# XAMPP Default credentials
host = "localhost"
user = "root"
password = "" 

databases = [
    "auth_db",
    "user_db",
    "movie_db",
    "reservation_db"
]

try:
    connection = pymysql.connect(host=host, user=user, password=password)
    with connection.cursor() as cursor:
        for db_name in databases:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
            print(f"Database '{db_name}' created or already exists.")
    connection.commit()
    connection.close()
except Exception as e:
    print(f"Error creating databases: {e}")
