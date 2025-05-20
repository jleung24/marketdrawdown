from computation.drawdown import Drawdown
from database.rds_client import RdsClient

class Drawdowns:

    def __init__(self, drawdown: Drawdown):
        self.drawdown = drawdown
        self.client = RdsClient()
        self.client.create_engine()
        self.drawdown_data = {}
        self.total_drawdowns = 0

    def get_drawdowns(self):
        self.drawdown_data = self.client.get_drawdowns(self.drawdown)
        self.total_drawdowns = len(self.drawdown_data)
    
    def get_drawdown_info(self, recovery_percentage: int):
        self.drawdown_data = self.client.get_recovery_data(self.drawdown_data, self.drawdown, recovery_percentage)


drawdown = Drawdown("SPY", 20, 50, 10, 1000)
test = Drawdowns(drawdown)
test.get_drawdowns()
test.get_drawdown_info(100)
print(test.drawdown_data)

