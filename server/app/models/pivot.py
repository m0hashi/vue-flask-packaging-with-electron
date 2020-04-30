import pandas as pd
import json

class PivotModel():
  def __init__(self, df):
    self.pivot = df

  def json(self):
      js = self.pivot.to_json(orient='table') #type: str
      js = json.loads(js) #type: dict
      return js #type: dict

  @classmethod
  def load_data(cls, filepath: str, encoding='utf8'):
    df = pd.read_csv(filepath, encoding=encoding)
    return cls(df)
