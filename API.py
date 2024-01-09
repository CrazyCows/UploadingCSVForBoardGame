from flask import Flask, jsonify, request, json
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
            boardgame_data = cur.fetchone()
            if boardgame_data:
                column_names = [desc[0] for desc in cur.description]
                boardgame_dicts = dict(zip(column_names, boardgame_data))
                print(boardgame_dicts)
                return json.dumps(boardgame_dicts)
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


@app.route('/boardgamesearch/<int:id_actual>', methods=['GET'])
def get_boardgame_search(id_actual):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM boardgame WHERE id_actual = %s", (id_actual,))
            boardgame_data = cur.fetchone()
            if boardgame_data:
                return jsonify(dict(boardgame_data))
            else:
                return jsonify({"error": "Boardgame not found"}), 404
    finally:
        put_db_connection(conn)

@app.route('/favoritetoggle/<string:id_actual>/<string:username>', methods=['GET'])
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
                return jsonify({"created": False}), 404
    finally:
        put_db_connection(conn)

@app.route('/favoritetoggle/<string:id_actual>/<string:username>/<string:rating>', methods=['GET'])
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

@app.route('/favorite-gameboard/<string:id_actual>/<string:username>/', methods=['GET'])
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

@app.route('/images/<string:id_actual>', methods=['GET'])
def get_image_data(id_actual):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT image_data FROM image_data WHERE id_actual = %s", (id_actual,))
            image_data = cur.fetchone()
            if image_data:
                return jsonify(dict(image_data))
            else:
                return jsonify({"error": "Image data not found"}), 404
    finally:
        put_db_connection(conn)




@app.route('/recents/<string:username>/<string:id_actual>/', methods=['GET'])
def insertIntoRecents(user, id):
    json_data = request.get_json()
    if json_data:
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                sql_query_check = "DELETE FROM recents WHERE timestamp = (SELECT MIN(timestamp) FROM recents);"
                sql_query = "INSERT INTO recents (username, id_actual) VALUES (%s, %s)"
                values = (user, id)
                recents = cur.fetchall
                if len(recents) > 10:
                    cur.execute(sql_query_check, (user,))
                    conn.commit()
                cur.execute(sql_query, values)
                conn.commit()
                return jsonify({"success": True})
        except Exception as e:
            conn.rollback()
            return jsonify({"error": "Failed to insert into recents"}), 500
        finally:
            put_db_connection(conn)

@app.route('/recents/<string:username>/>', methods=["GET"])
def getRecents(user):
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            sql_query = "SELECT id_actual FROM recents WHERE username=%s"
            cur.execute(sql_query, (user,))
            recents = cur.fetchall()
            column_names = [desc[0] for desc in cur.description]
            boardgame_dicts = [dict(zip(column_names, row)) for row in recents]
            return json.dumps(boardgame_dicts)
    except Exception as e:
        conn.rollback()
        return json.dumps({"error": "Failed to get recents"}), 500
    finally:
        put_db_connection(conn)




if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)