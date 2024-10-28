import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    return psycopg2.connect(
        dbname="your_db_name",
        user="your_user",
        password="your_password",
        host="your_host",
        port="your_port",
        cursor_factory=RealDictCursor
    )