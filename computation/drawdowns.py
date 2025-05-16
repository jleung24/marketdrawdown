from computation.drawdown import Drawdown
from database.rds_client import RdsClient

class Drawdowns:

    def __init__(self, drawdown: Drawdown):
        self.drawdown = drawdown
        self.client = RdsClient()
        self.client.create_engine()
        self.stock_data_id_list = []
        self.total = 0

    def get_drawdowns(self):
        self.stock_data_id_list = self.client.get_drawdowns(self.drawdown)
        self.total = len(self.stock_data_id_list)
    



drawdown = Drawdown("SPY", 20, 50, 10, 100)
test = Drawdowns(drawdown)
test.get_drawdowns()
print(test.stock_data_id_list)


