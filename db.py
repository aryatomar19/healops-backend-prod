import psycopg2
from psycopg2.extras import RealDictCursor

from config import (
    DB_HOST,
    DB_NAME,
    DB_USER,
    DB_PASSWORD
)


db = psycopg2.connect(
    host=DB_HOST,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)


def get_cursor(dict_cursor=False):

    if dict_cursor:

        return db.cursor(
            cursor_factory=RealDictCursor
        )

    return db.cursor()
