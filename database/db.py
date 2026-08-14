import os

import oracledb
from dotenv import load_dotenv

load_dotenv()

oracledb.init_oracle_client(
    lib_dir=r"D:\app\instantclient_19_31"
)


def get_connection():
    return oracledb.connect(
        user=os.getenv("ORACLE_USERNAME"),
        password=os.getenv("ORACLE_PASSWORD"),
        dsn=os.getenv("ORACLE_DSN")
    )