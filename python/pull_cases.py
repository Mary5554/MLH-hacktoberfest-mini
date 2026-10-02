import os
import pandas as pd
import snowflake.connector
from dotenv import load_dotenv

load_dotenv()

conn = snowflake.connector.connect(
    account=os.environ["SNOWFLAKE_ACCOUNT"],
    user=os.environ["SNOWFLAKE_USER"],
    password=os.environ["SNOWFLAKE_PASSWORD"],
    role="SYSADMIN",
    warehouse="COMPUTE_WH",
    database="OUTBREAK_DB",
    schema="EARLY_WARNING",
)

cur = conn.cursor()
cur.execute("SELECT CITY, WEEK_START, CASES FROM ANOMALY_RESULTS ORDER BY CITY, WEEK_START")
df = pd.DataFrame(cur.fetchall(), columns=["CITY", "WEEK_START", "CASES"])
conn.close()

print(df.head())
print(df.groupby("CITY").size())