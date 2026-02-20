import pymysql

# Connect to the database
connection = pymysql.connect(
    host='localhost',
    user='root',
    password='',
    database='reservation_db',
    cursorclass=pymysql.cursors.DictCursor
)

try:
    with connection.cursor() as cursor:
        print("Dropping reservation_seats table...")
        cursor.execute("DROP TABLE IF EXISTS reservation_seats")
        print("Table dropped.")
        
        print("Recreating reservation_seats table with Correct PK...")
        sql = """
        CREATE TABLE reservation_seats (
            reservation_id INT NOT NULL,
            seat_id INT NOT NULL,
            showtime_id INT NOT NULL,
            PRIMARY KEY (reservation_id, seat_id),
            FOREIGN KEY (reservation_id) REFERENCES reservations(reservation_id) ON DELETE CASCADE,
            UNIQUE KEY unique_seat_booking_per_showtime (showtime_id, seat_id)
        )
        """
        cursor.execute(sql)
        print("Table recreated successfully.")
    
    connection.commit()
finally:
    connection.close()
