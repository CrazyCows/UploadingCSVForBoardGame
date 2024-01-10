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


def incrementUser(user, category, increment):
    if (increment == "True"):
        incrementVar = 1
    elif(increment == "False"):
        incrementVar = -1
    else:
        return json.dumps({"error": "Failed to increment userdata"}), 400
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            sql_query = "SELECT * FROM users WHERE username=%s"
            cur.execute(sql_query, (user,))
            result = cur.fetchall()
            match category:
                case "played_games":
                    catint = result[0][2] + incrementVar
                    sql_query = "UPDATE users SET played_games=%s WHERE username=%s"
                case "rated_games":
                    catint = result[0][3] + incrementVar
                    sql_query = "UPDATE users SET rated_games=%s WHERE username=%s"
                case "streak":
                    catint = result[0][4] + incrementVar
                    sql_query = "UPDATE users SET streak=%s WHERE username=%s"
            cur.execute(sql_query, (catint, user))
            conn.commit()
            return json.dumps({"Success": "user data successfully updated"}), 200
    except Exception as e:
        conn.rollback()
        return json.dumps({"error": "Failed to increment userdata"}), 500
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

def update_played_count(username, game_id):
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Check if the game exists for the user
            sql_query = "SELECT * FROM user_played WHERE username= %s AND id_actual= %s"
            cur.execute(sql_query, (username, game_id))
            existing_game = cur.fetchone()
            if existing_game:
                # If the game exists, increment the played_count
                played_count = existing_game[2] + 1
                update_query = "UPDATE user_played SET played_count = %s WHERE username = %s AND id_actual = %s"
                cur.execute(update_query, (played_count, username, game_id))
            else:
                # If the game doesn't exist, insert a new record
                insert_query = "INSERT INTO user_played (username, id_actual, played_count) VALUES (%s, %s, %s)"
                cur.execute(insert_query, (username, game_id, 1))
            conn.commit()

    except Exception as e:
        conn.rollback()
        return json.dumps({"error": "Failed to update played count"}), 500
    finally:
        put_db_connection(conn)

def getUserData(username, category):
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            match category:
                case "played_games":
                    sql_query = "SELECT played_games FROM users WHERE username=%s"
                    cur.execute(sql_query, (username,))
                    result = cur.fetchone()
                case "rated_games":
                    sql_query = "SELECT rated_games FROM users WHERE username=%s"
                    cur.execute(sql_query, (username,))
                    result = cur.fetchone()
                case "streak":
                    sql_query = "SELECT streak FROM users WHERE username=%s"
                    cur.execute(sql_query, (username,))
                    result = cur.fetchone()
        return json.dumps(result), 200
    except Exception as e:
        return json.dumps({"error":"Unable to fetch userdata"}), 500
    finally:
        put_db_connection(conn)

def insertIntoRecents(user, id):
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            #statement check for when a user already has 10 recents
            sql_query_check1 = "SELECT username FROM recents WHERE username=%s"
            #statement check for when an touple needs to be updated
            sql_query_check2 = "SELECT id_actual FROM recents WHERE id_actual=%s"
            #the insert that gets executed no matter what
            sql_query = "INSERT INTO recents (username, id_actual) VALUES (%s, %s)"
            cur.execute(sql_query_check2, (id, ))
            alreadyexcisting = cur.fetchone()
            values = (user, id)
            cur.execute(sql_query_check1, (user,))
            recents = cur.fetchall()
            print(len(recents))
            if len(recents) >= 10:
                if alreadyexcisting:
                    sql_query_delete = "DELETE FROM recents WHERE id_actual = %s;"
                    cur.execute(sql_query_delete, (id,))
                    conn.commit()
                else:
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

if __name__ == '__main__':
    print(insertIntoRecents("static_user", "12"))

