from flask import Flask, jsonify
from asyncpg import create_pool
import DatabasePool

app = Flask(__name__)

# Database configuration (adjust as needed)
DATABASE_URL = "postgres://youruser:yourpassword@yourhost:yourport/yourdbname"

# Initialize the database pool

# API Endpoint to fetch boardgame data
@app.route('/boardgames/<int:id_actual>', methods=['GET'])
async def get_boardgame(id_actual):
    db_pool = await create_pool(DATABASE_URL)
    async with db_pool.acquire() as conn:
        boardgame_data = await conn.fetchrow(
            "SELECT * FROM boardgame WHERE id_actual = $1", id_actual)
        if boardgame_data:
            return jsonify(dict(boardgame_data))
        else:
            return jsonify({"error": "Boardgame not found"}), 404

# API Endpoint to fetch image data
@app.route('/images/<int:id_actual>', methods=['GET'])
async def get_image_data(id_actual):
    db_pool = await create_pool(DATABASE_URL)
    async with db_pool.acquire() as conn:
        image_data = await conn.fetchrow(
            "SELECT image_data FROM image_data WHERE id_actual = $1", id_actual)
        if image_data:
            return jsonify(dict(image_data))
        else:
            return jsonify({"error": "Image data not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)