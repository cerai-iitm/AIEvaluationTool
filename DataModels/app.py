from sqlalchemy.orm import sessionmaker
from models import Metric, engine
import pandas as pd

data = pd.read_csv("sample.csv")

# print(data.head())
Session = sessionmaker(bind=engine)

session = Session()


for i in range(len(data)):
    metric = Metric(
        type=data['Type'][i],
        mapped_benchmark=data['Benchmark'][i],
        source=data['Source'][i],
        metric=data['Metric'][i]
    )
    session.add(metric)
    if i %1000 == 0:
        session.flush()
session.commit()
print("Data inserted successfully")

