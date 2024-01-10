import io
from pprint import pprint

from flask import Flask, jsonify, request, json, send_file
import psycopg2
from psycopg2 import pool


app = Flask(__name__)

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

@app.route('/boardgame/<string:id_actual>/', methods=['GET'])
def get_boardgame(id_actual):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM boardgame WHERE id_actual = %s", (id_actual,))
            cur.execute("""
            SELECT
                boardgame.*,
                CASE
                    WHEN liked_games.id_actual IS NOT NULL THEN 'True'
                    ELSE 'False'
                END as is_liked,
                CASE
                    WHEN user_ratings.id_actual IS NOT NULL THEN user_ratings.liked
                    ELSE '0'
                END as user_rating
            FROM
                boardgame
            LEFT JOIN
                liked_games ON boardgame.id_actual = liked_games.id_actual
            LEFT JOIN
                user_ratings ON boardgame.id_actual = user_ratings.id_actual 
            WHERE boardgame.id_actual = %s""",
                        (id_actual,))


            boardgame_data = cur.fetchone()
            if boardgame_data:
                column_names = [desc[0] for desc in cur.description]
                boardgame_dict = dict(zip(column_names, boardgame_data))
                print(json.dumps(boardgame_dict))
                return json.dumps(boardgame_dict)
            else:
                return jsonify({"error": "Boardgame not found"}), 404
    finally:
        put_db_connection(conn)

@app.route('/boardgameitems/<string:category>/<int:limit>/<int:offset>/', methods=['GET'])
def get_boardgame_items(category,limit, offset):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            if category != "none":
                cur.execute(
                    "SELECT * FROM boardgame WHERE LOWER(%s) = ANY(SELECT LOWER(UNNEST(categories))) AND description is not null LIMIT %s OFFSET %s",
                    (category, limit, offset))
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


@app.route('/boardgamesearch/<string:user_search>/', methods=['GET'])
def get_boardgame_search(user_search):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM boardgame WHERE lower(name) LIKE lower(%s)", (user_search,))
            boardgame_data = cur.fetchone()
            if boardgame_data:
                return jsonify(dict(boardgame_data))
            else:
                return jsonify({"error": "Boardgame not found"}), 404
    finally:
        put_db_connection(conn)

@app.route('/favoritetoggle/<string:id_actual>/<string:username>/', methods=['GET'])
def toggle_favorite(id_actual, username):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            try:
                cur.execute("INSERT INTO liked_games(username, id_actual) VALUES (%s, %s)", (username, id_actual))
                conn.commit()
                return jsonify({"created": True})
            except Exception as e:
                conn.rollback()
                cur.execute("DELETE FROM liked_games WHERE username = %s AND id_actual = %s", (username, id_actual))
                conn.commit()
                return jsonify({"created": False})
    finally:
        put_db_connection(conn)

@app.route('/favorite-gameboard-all/<string:username>/<int:offset>/<int:limit>', methods=['GET'])
def get_all_favorites(username, offset, limit):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM boardgame WHERE id_actual IN (SELECT id_actual FROM liked_games WHERE username = %s) LIMIT %s OFFSET %s", (username, limit, offset))
            boardgame_data = cur.fetchall()
            if boardgame_data:

                column_names = [desc[0] for desc in cur.description]
                boardgame_dicts = [dict(zip(column_names, row)) for row in boardgame_data]
                return json.dumps(boardgame_dicts)
            else:
                return None
    finally:
        put_db_connection(conn)

@app.route('/ratingstoggle/<string:id_actual>/<string:username>/<string:rating>/', methods=['GET'])
def toggle_ratings(id_actual, username, rating):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT liked FROM user_ratings WHERE username = %s AND id_actual = %s", (username, id_actual))
            result = cur.fetchone()

            if result:
                result = result[0]
                if result == rating:
                    cur.execute("DELETE FROM user_ratings WHERE username = %s AND id_actual = %s", (username, id_actual))
                    conn.commit()
                    return json.dumps({"Deleted": True, "user_rating": 0})
                else:
                    cur.execute("UPDATE user_ratings SET liked = %s WHERE username = %s AND id_actual = %s", (rating, username, id_actual))
                    conn.commit()

                    return json.dumps({"Updated": True, "user_rating": rating})

            cur.execute("INSERT INTO user_ratings(username, id_actual, liked) VALUES (%s, %s, %s)", (username, id_actual, rating))
            conn.commit()
            return json.dumps({"Created": True, "user_rating": rating})
    finally:
        put_db_connection(conn)

@app.route('/getratings/<string:id_actual>/<string:username>/', methods=['GET'])
def get_rating(id_actual, username):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT liked FROM user_ratings WHERE username = %s AND id_actual = %s", (username, id_actual))
            rating = cur.fetchone()
            if rating:
                return json.dumps({"user_rating": rating[0]})
            else:
                return jsonify({"user_rating": None})
    finally:
        put_db_connection(conn)



@app.route('/images/<string:id_actual>', methods=['GET'])
def get_image_data(id_actual):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT image_data FROM image_data WHERE id_actual = %s", (id_actual,))
            image_data = cur.fetchone()
            if image_data:
                image_data = image_data[0]
                # Assuming image_data is in a binary format (e.g., BLOB)
                return send_file(
                    io.BytesIO(image_data),
                    mimetype='image/png',
                    as_attachment=False
                )
            else:
                return jsonify({"error": "Image data not found"}), 404
    finally:
        put_db_connection(conn)




@app.route('/recents/<string:username>/<string:id_actual>/', methods=['GET'])
def insertIntoRecents(username, id_actual):
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            #statement check for when a user already has 10 recents
            sql_query_check1 = "SELECT username FROM recents WHERE username=%s"
            #statement check for when an touple needs to be updated
            sql_query_check2 = "SELECT id_actual FROM recents WHERE id_actual=%s"
            #the insert that gets executed no matter what
            sql_query = "INSERT INTO recents (username, id_actual) VALUES (%s, %s)"
            cur.execute(sql_query_check2, (id_actual, ))
            alreadyexcisting = cur.fetchone()
            values = (username, id_actual)
            cur.execute(sql_query_check1, (username,))
            recents = cur.fetchall()
            print(len(recents))
            if len(recents) >= 10:
                if alreadyexcisting:
                    sql_query_delete = "DELETE FROM recents WHERE id_actual = %s;"
                    cur.execute(sql_query_delete, (id_actual,))
                    conn.commit()
                else:
                    sql_query_delete = "DELETE FROM recents WHERE timestamp = (SELECT MIN(timestamp) FROM recents);"
                    cur.execute(sql_query_delete, (username,))
                    conn.commit()
            try:
                cur.execute(sql_query, values)
                conn.commit()
            except Exception as e:
                print(1)
            return json.dumps({"success": "New Recent Added"}), 200
    except Exception as e:
        conn.rollback()
        return json.dumps({"error": "Failed to insert into recents"}), 500
    finally:
        put_db_connection(conn)

@app.route('/recents/<string:username>/', methods=["GET"])
def getRecents(username):
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            sql_query = "SELECT * FROM boardgame LEFT JOIN recents on boardgame.id_actual = recents.id_actual WHERE username=%s"

            cur.execute(sql_query, (username,))
            sql_query = "SELECT id_actual FROM recents WHERE username=%s ORDER BY timestamp DESC;"
            cur.execute(sql_query, (username,))
            recents = cur.fetchall()
            column_names = [desc[0] for desc in cur.description]
            boardgame_dicts = [dict(zip(column_names, row)) for row in recents]
            json.dumps({"Success":"Recents successfully fetched"}), 200
            return json.dumps(boardgame_dicts)
    except Exception as e:
        conn.rollback()
        return json.dumps({"error": "Failed to get recents"}), 500
    finally:
        put_db_connection(conn)

@app.route('/users/<string:username>/<string:category>/<string:id_actual>/<string:boolean>/' , methods=["GET"])
def incrementUser(user, category, id_actual, increment):
    if (increment == "True"):
        incrementVar = 1
    elif(increment == "False"):
        incrementVar = -1
    else:
        return json.dumps({"error": "Failed to increment userdata"}), 400
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            sql_query = "SELECT * FROM users WHERE username= %s"
            cur.execute(sql_query, (user,))
            result = cur.fetchall()
            match category:
                case "played_games":
                    update_played_games(user, id_actual)
                    catint = result[0][2] + incrementVar
                    sql_query = "UPDATE users SET played_games= %s WHERE username=%s"
                case "rated_games":
                    catint = result[0][3] + incrementVar
                    sql_query = "UPDATE users SET rated_games= %s WHERE username=%s"
                case "streak":
                    catint = result[0][4] + incrementVar
                    sql_query = "UPDATE users SET streak= %s WHERE username=%s"
            cur.execute(sql_query, (catint, user))
            conn.commit()
            return json.dumps({"Success": "user data successfully updated"}), 200
    except Exception as e:
        conn.rollback()
        return json.dumps({"error": "Failed to increment userdata"}), 500
    finally:
        put_db_connection(conn)



@app.route('/users/<string:username>/<string:category>/', methods=['GET'])
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
                    sql_query = "SELECT played_games FROM users WHERE username=%s"
                    cur.execute(sql_query, (username,))
                    result = cur.fetchone()
                case "streak":
                    sql_query = "SELECT played_games FROM users WHERE username=%s"
                    cur.execute(sql_query, (username,))
                    result = cur.fetchone()
        return json.dumps(result), 200
    except Exception as e:
        return json.dumps({"error":"Unable to fetch userdata"}), 500
    finally:
        put_db_connection(conn)



@app.route('/user_played/<string:username>/<string:game_id>', methods=["GET"])
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

def update_played_games(username, id_actual):
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            sql_query = "SELECT username, id_actual FROM user_played where id_actual=%s"
            cur.execute(sql_query, (id_actual,))
            result = cur.fetchone()
            if(result):
                sql_query = "UPDATE user_played SET played_count=played_count+1 WHERE username=%s AND id_actual=%s"
                cur.execute(sql_query, (username, id_actual))
                conn.commit()
            else:
                sql_query = "INSERT INTO user_played (username, id_actual, played_count) VALUES (%s, %s, 1)"
                cur.execute(sql_query, (username, id_actual))
                conn.commit()
            return json.dumps({"Success": "successfully updated table "}), 200
    except Exception as e:
        return json.dumps({"error": "Unable to update user_played list"}), 500
    finally:
        put_db_connection(conn)


if __name__ == '__main__':
    app.run(host='135.181.106.80', port=5000, debug=True)