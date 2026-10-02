import os
import pandas as pd
import snowflake.connector
import torch
from chronos import BaseChronosPipeline
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
cur.execute("SELECT WEEK_START, CASES FROM ANOMALY_RESULTS WHERE CITY = 'BANGKOK' ORDER BY WEEK_START")
df = pd.DataFrame(cur.fetchall(), columns=["WEEK_START", "CASES"])
conn.close()

pipeline = BaseChronosPipeline.from_pretrained("amazon/chronos-bolt-small", device_map="cpu")
quantiles, mean = pipeline.predict_quantiles(
    inputs=torch.tensor(df["CASES"].values, dtype=torch.float32),
    prediction_length=8,
    quantile_levels=[0.1, 0.5, 0.9],
)
print("Next 8 weeks for BANGKOK (low, median, high):")
print(quantiles[0])