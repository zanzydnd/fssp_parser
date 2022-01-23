import os

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())


class Config:
    DB_USER = os.environ.get('DATABASE_USER')
    DB_PASSWORD = os.environ.get('DATABASE_PASSWORD')
    DB_HOST = os.environ.get('DATABASE_HOST')
    DB_PORT = os.environ.get('PORT')
    DB_NAME = os.environ.get('DATABASE_NAME')
    DB_DRIVER = os.environ.get('DB_DRIVER')

    def DATABASE_URL(self) -> str:
        return f'postgres://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'