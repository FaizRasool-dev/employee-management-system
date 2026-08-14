import os

import oracledb
from dotenv import load_dotenv


load_dotenv()

oracledb.init_oracle_client(
    lib_dir=r"D:\app\instantclient_19_31"
)

USERNAME = os.getenv("ORACLE_USERNAME")
PASSWORD = os.getenv("ORACLE_PASSWORD")
DSN = os.getenv("ORACLE_DSN")


try:
    connection = oracledb.connect(
        user=USERNAME,
        password=PASSWORD,
        dsn=DSN
    )

    print("Oracle Database Connected Successfully!")

    connection.close()

except oracledb.Error as error:
    print("Connection failed!")
    print(error)