
import os
import snowflake.connector
from dotenv import load_dotenv

load_dotenv()

conn = snowflake.connector.connect(
    account=os.environ["SNOWFLAKE_ACCOUNT"],
    user=os.environ["SNOWFLAKE_USER"],
    password=os.environ["SNOWFLAKE_PASSWORD"],
    role="SYSADMIN",
    warehouse="COMPUTE_WH",
)

cur = conn.cursor()
cur.execute("SELECT CURRENT_ROLE(), CURRENT_ACCOUNT(), CURRENT_WAREHOUSE()")
print(cur.fetchone())
cur.execute("SHOW DATABASES")
print([row[1] for row in cur.fetchall()])
conn.close()

