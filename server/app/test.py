from models import PivotModel


pivot = PivotModel.load_data(filepath=data['filepath'], encoding='utf8')
pivot.json()