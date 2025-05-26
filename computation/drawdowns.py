import statistics

from computation.drawdown import Drawdown
from database.rds_client import RdsClient


class Drawdowns:

    def __init__(self, drawdown: Drawdown):
        self.drawdown = drawdown
        self.client = RdsClient()
        self.drawdown_data = {}
        self.total_drawdowns = 0
        self.avg_recovery_days = 0
        self.median_recovery_days = 0
        self.recovery_graph = {}
        self.recovery_yearly_scatter = []
        self.recovery_list = []

    def get_drawdowns(self):
        self.drawdown_data = self.client.get_drawdowns(self.drawdown)
        self.total_drawdowns = len(self.drawdown_data)
    
    def get_drawdown_info(self, recovery_percentage: int):
        self.reset_data()
        self.get_drawdowns()
        self.drawdown_data = self.client.get_recovery_data(self.drawdown_data, self.drawdown, recovery_percentage)

        for stock_data_id, drawdown_info in self.drawdown_data.items():
            total_recovery_days = (drawdown_info["recovery_date"]- drawdown_info["drawdown_date"]).days
            drawdown_info["total_recovery_days"] = total_recovery_days
            self.recovery_list.append(total_recovery_days)
            self.push_recovery_months_data(total_recovery_days)
            self.push_recovery_yearly_data(drawdown_info)
        
        self.avg_recovery_days = round(statistics.mean(self.recovery_list))
        self.median_recovery_days = round(statistics.median(self.recovery_list))

    def push_recovery_months_data(self, total_recovery_days: int):
        total_recovery_months = round(total_recovery_days/30)

        if total_recovery_months in self.recovery_graph.keys():
            self.recovery_graph[total_recovery_months] += 1
        else:
            self.recovery_graph[total_recovery_months] = 1

    def push_recovery_yearly_data(self, drawdown_info: dict):
        year = drawdown_info['drawdown_date'].year
        self.recovery_yearly_scatter.append({'x': year, 'y': drawdown_info['total_recovery_days']})

    def cleanup(self):
        for attr in list(self.__dict__):
            setattr(self, attr, None)
    
    def reset_data(self):
        self.drawdown_data = {}
        self.total_drawdowns = 0
        self.avg_recovery_days = 0
        self.median_recovery_days = 0
        self.recovery_graph = {}
        self.recovery_yearly_scatter = []
        self.recovery_list = []
