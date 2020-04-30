import pandas as pd
from flask_restful import Resource, reqparse
from models import PivotModel


class Pivot(Resource):
  parser = reqparse.RequestParser()
  #必須キー項目の指定。オプション
  parser.add_argument(
    'filepath',
    type=str,
    required=True,
    help="This field cannot be left brank."
  )
  def get(self):
      return {'response':'test'}

  def post(self):
    data = Pivot.parser.parse_args()
    print(data)

    # pivot = PivotModel.getpivot(data)
    pivot = PivotModel.load_data(filepath=data['filepath'], encoding='utf8')
    return pivot.json()

    
