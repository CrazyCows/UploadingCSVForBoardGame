import json
from flask import Flask, jsonify, request, json
import psycopg2

from psycopg2 import pool



# Database configuration (adjust as needed)
DATABASE_URL = "dbname=school user=firstuser password=Studyhard1234. host=135.181.106.80 port=5432"

# Initialize the database pool
db_pool = psycopg2.pool.SimpleConnectionPool(1, 20, DATABASE_URL)

def get_db_connection():
    if db_pool:
        return db_pool.getconn()
    raise Exception("No database connection pool available")

def put_db_connection(conn):
    if db_pool:
        db_pool.putconn(conn)


def insertIntoRecents(user, id):
     conn = get_db_connection()
     try:
         with conn.cursor() as cur:
             sql_query_check = "SELECT username FROM recents WHERE username=%s"
             sql_query = "INSERT INTO recents (username, id_actual) VALUES (%s, %s)"
             values = (user, id)
             cur.execute(sql_query_check, (user,))
             recents = cur.fetchall()
             print(len(recents))
             if len(recents) >= 10:
                 sql_query_delete = "DELETE FROM recents WHERE timestamp = (SELECT MIN(timestamp) FROM recents);"
                 cur.execute(sql_query_delete, (user,))
                 conn.commit()
             cur.execute(sql_query, values)
             conn.commit()
             return json.dumps({"success": "New Recent Added"}), 200
     except Exception as e:
         conn.rollback()
         return json.dumps({"error": "Failed to insert into recents"}), 500
     finally:
         put_db_connection(conn)



def get_boardgame_items(category,limit, offset):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            if category != "none":
                cur.execute("SELECT * FROM boardgame WHERE LOWER(%s) = ANY(SELECT LOWER(UNNEST(categories))) AND description is not null LIMIT %s OFFSET %s", (category, limit, offset))
            else:
                cur.execute("SELECT * FROM boardgame WHERE description is not null LIMIT %s OFFSET %s", (limit, offset))

            boardgame_data = cur.fetchall()
            if boardgame_data:
                column_names = [desc[0] for desc in cur.description]
                boardgame_dicts = [dict(zip(column_names, row)) for row in boardgame_data]
                print(boardgame_dicts)
                return json.dumps(boardgame_dicts)
            else:
                return jsonify({"error": "Boardgames not found"}), 404
    finally:
        put_db_connection(conn)

if __name__ == '__main__':
    print(insertIntoRecents("static_user", "1"))
    print(insertIntoRecents("static_user", "2"))
    print(insertIntoRecents("static_user", "3"))
    print(insertIntoRecents("static_user", "4"))
    print(insertIntoRecents("static_user", "5"))
    print(insertIntoRecents("static_user", "6"))
    print(insertIntoRecents("static_user", "7"))
    print(insertIntoRecents("static_user", "8"))
    print(insertIntoRecents("static_user", "9"))
    print(insertIntoRecents("static_user", "10"))
    print(insertIntoRecents("static_user", "11"))
    print(insertIntoRecents("static_user", "12"))

