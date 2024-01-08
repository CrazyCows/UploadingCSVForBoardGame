import requests
from PIL import Image
import io


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


async def get_picture():
    db_pool = PoolUsersData()
    await db_pool.initialize_pool()
    async with db_pool.acquire() as conn:
        asyncpg_list = await conn.fetch("SELECT image_data FROM boardgame where id_actual = '340677'")
        return asyncpg_list[0][0]

image_byte_array = asyncio.run(get_picture())





# Convert bytearray to BytesIO object
image_stream = io.BytesIO(image_byte_array)

# Open the image
image = Image.open(image_stream)

# Display the image
image.show()