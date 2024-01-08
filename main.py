# This is a sample Python script.
import asyncio
import csv
from contextlib import asynccontextmanager
import xml.etree.ElementTree as ET

import requests
import time

import asyncpg

from PIL import Image
import requests
from io import BytesIO


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonMeta, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class BasePool:
    _pools = {}

    def __init__(self, database_name, user, host, password, min_size, max_size):
        self.database_name = database_name
        self.user = user
        self.host = host
        self.password = password
        self.min_size = min_size
        self.max_size = max_size

    async def initialize_pool(self):
        pool_key = f"{self.host}_{self.database_name}"
        if pool_key not in BasePool._pools:
            BasePool._pools[pool_key] = await asyncpg.create_pool(
                database=self.database_name,
                user=self.user,
                host=self.host,
                password=self.password,
                min_size=self.min_size,
                max_size=self.max_size
            )
        return BasePool._pools[pool_key]

    # Contextmanagers is awesome <3
    @asynccontextmanager
    async def acquire(self):
        pool_key = f"{self.host}_{self.database_name}"
        pool = BasePool._pools[pool_key]
        # pool = await self.initialize_pool()
        conn = await pool.acquire()
        try:
            yield conn
        finally:
            await pool.release(conn)

    async def close(self):
        pool_key = f"{self.host}_{self.database_name}"
        pool = BasePool._pools[pool_key]
        await pool.close()

class PoolUsersData(BasePool, metaclass=SingletonMeta):
    def __init__(self):
        super().__init__(database_name="school",
                         user="firstuser",
                         host="135.181.106.80",
                         password="Studyhard1234.",
                         min_size=1,
                         max_size=20)

async def insert_data_from_csv(file_path, batch_size=100):
    # Initialize the connection pool
    db_pool = PoolUsersData()
    await db_pool.initialize_pool()

    async with db_pool.acquire() as conn:
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Skip header row

            batch = []
            for row in reader:
                batch.append(row)
                if len(batch) >= batch_size:
                    await conn.executemany("""
                        INSERT INTO boardgame (id_actual, name, year, rank, average, bayes_average, users_rated, URL, thumbnail)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    """, batch)
                    batch = []

            # Insert any remaining rows
            if batch:
                await conn.executemany("""
                    INSERT INTO boardgame (id_actual, name, year, rank, average, bayes_average, users_rated, URL, thumbnail)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """, batch)

async def search_and_insert_remaining_data_from_bgg():
    db_pool = PoolUsersData()
    await db_pool.initialize_pool()
    async with db_pool.acquire() as conn:
        asyncpg_list = await conn.fetch("SELECT id_actual FROM boardgame")
        for id_actual in asyncpg_list:
            test = await conn.fetch("SELECT description FROM boardgame WHERE id_actual = $1", id_actual.get('id_actual'))

            if test[0].get('description') is not None:
                print("skip")
                continue

            print(id_actual.get('id_actual'))

            xml_data = fetch_bgg_data(id_actual.get('id_actual'))
            data = parse_xml(xml_data)

            await conn.execute(
                '''
                UPDATE boardgame
                SET description = $1,
                    min_players = $2,
                    max_players = $3,
                    play_time = $4,
                    age = $5,
                    mechanisms = $6,
                    categories = $7,
                    publishers = $8,
                    artists = $9,
                    designers = $10,
                    families = $11,
                    image = $12,
                    category_rank = $13,
                    overall_rank = $14,
                    weight = $15
                    
                WHERE id_actual = $16
                ''',
                data.get('description'),
                data.get('min_players'),
                data.get('max_players'),
                data.get('play_time'),
                data.get('age'),
                data.get('mechanics'),
                data.get('categories'),
                data.get('publishers'),
                data.get('artists'),
                data.get('designers'),
                data.get('families'),
                data.get('image'),
                data.get('overall_rank'),
                data.get('category_rank'),
                data.get('weight'),
                id_actual.get('id_actual')
            )
            await conn.execute(
                """INSERT INTO image_data (id_actual, image_data) VALUES ($1, $2)""", data.get('id_actual'), data.get('image_data')
            )
# Function to parse the XML and extract the required data

def parse_xml(xml_data):
    root = ET.fromstring(xml_data)
    item = root.find('boardgame')



    if item is None:
        return None  # Or handle the absence of <item> as needed

    img_bytes = ''
    try:
        response = requests.get(item.find('image').text)
        img_bytes = response.content
    except:
        print("Error")

    def extract_data(tag_name):
        return [element.text for element in item.findall(tag_name)]

    data = {
        'year_published': item.find('yearpublished').text if item.find('yearpublished') is not None else '',
        'min_players': item.find('minplayers').text if item.find('minplayers') is not None else '',
        'max_players': item.find('maxplayers').text if item.find('maxplayers') is not None else '',
        'play_time': item.find('playingtime').text if item.find('playingtime') is not None else '',
        'min_play_time': item.find('minplaytime').text if item.find('minplaytime') is not None else '',
        'max_play_time': item.find('maxplaytime').text if item.find('maxplaytime') is not None else '',
        'age': item.find('age').text if item.find('age') is not None else '',
        'name': item.find("name[@primary='true']").text if item.find("name[@primary='true']") is not None else '',
        'description': item.find('description').text if item.find('description') is not None else '',
        'thumbnail': item.find('thumbnail').text if item.find('thumbnail') is not None else '',
        'image': item.find('image').text if item.find('image') is not None else '',
        'publishers': extract_data('boardgamepublisher'),
        'podcast_episodes': extract_data('boardgamepodcastepisode'),
        'honors': extract_data('boardgamehonor'),
        'mechanics': extract_data('boardgamemechanic'),
        'versions': extract_data('boardgameversion'),
        'families': extract_data('boardgamefamily'),
        'artists': extract_data('boardgameartist'),
        'designers': extract_data('boardgamedesigner'),
        'categories': extract_data('boardgamecategory'),
        'subdomains': extract_data('boardgamesubdomain'),
        'accessories': extract_data('boardgameaccessory'),
        'overall_rank': '',
        'category_rank': '',
        'weight': '',
        'image_data': img_bytes
    }



    # Parse ratings and ranks
    try:
        statistics = item.find('statistics')
        ratings = statistics.find('ratings')
        if ratings is not None:
            data['weight'] = ratings.find('averageweight').text if ratings.find('averageweight') is not None else ''
            ranks = ratings.find('ranks')
            if ranks is not None:
                for rank in ranks.findall('rank'):
                    # Use the friendlyname attribute to identify the rank type
                    if rank.get('friendlyname') == 'Board Game Rank':
                        data['overall_rank'] = rank.get('value')
                    elif rank.get('friendlyname') == 'Strategy Game Rank':
                        data['category_rank'] = rank.get('value')
    except:
        print("Error parsing ratings and ranks")

    # print(data)
    return data

def fetch_bgg_data(id_actual):
    xml_data = ''
    while True:
        url = f'https://boardgamegeek.com/xmlapi/boardgame/{id_actual}?stats=1'
        re = requests.get(url)
        if re.status_code != 200:
            print("Rate limit exceeded")
            time.sleep(10)
            continue
        xml_data = re.text
        break
    return xml_data

async def runstuff():
    try:
        print("Just tricking the thingy")
        # await insert_data_from_csv('2023-10-24T15-10-00.csv')
    except:
        print("Error")
    await search_and_insert_remaining_data_from_bgg()

# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    asyncio.run(runstuff())



# See PyCharm help at https://www.jetbrains.com/help/pycharm/
