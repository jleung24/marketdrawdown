import statistics
from collections import Counter

from computation.drawdown import Drawdown
from database.rds_client import RdsClient


rds_client = RdsClient()

class Drawdowns:

    def __init__(self, drawdown: Drawdown):
        self.drawdown = drawdown
        self.client = rds_client
        self.drawdown_data = {}
        self.total_drawdowns = 0
        self.avg_recovery_months = 0
        self.median_recovery_months = 0
        self.recovery_graph = {}
        self.recovery_yearly_scatter = []
        self.recovery_list = []
        self.drawdown_period_graph = []
        self.max_drawdown_graph = []

    def get_drawdowns(self):
        self.drawdown_data = self.client.get_drawdowns(self.drawdown)
        self.total_drawdowns = len(self.drawdown_data)
    
    def get_drawdown_info(self, recovery_percentage: int):
        self.reset_data()
        self.get_drawdowns()
        self.drawdown_data = self.client.get_recovery_data(self.drawdown_data, self.drawdown, recovery_percentage)

        for stock_data_id, drawdown_info in self.drawdown_data.items():
            total_recovery_days = (drawdown_info["recovery_date"]- drawdown_info["drawdown_date"]).days
            total_recovery_months = round(total_recovery_days/30)
            drawdown_info["total_recovery_months"] = total_recovery_months
            self.recovery_list.append(total_recovery_months)
            self.push_recovery_months_data(total_recovery_months)
            self.push_recovery_yearly_data(drawdown_info)
            self.push_drawdown_period_data(drawdown_info)
            self.push_max_drawdown_data(drawdown_info)
        
        self.avg_recovery_months = round(statistics.mean(self.recovery_list))
        self.median_recovery_months = round(statistics.median(self.recovery_list))
        self.convert_scatter_to_bubble()

    def push_recovery_months_data(self, total_recovery_months: int):

        if total_recovery_months in self.recovery_graph.keys():
            self.recovery_graph[total_recovery_months] += 1
        else:
            self.recovery_graph[total_recovery_months] = 1

    def push_recovery_yearly_data(self, drawdown_info: dict):
        year = drawdown_info['drawdown_date'].year
        self.recovery_yearly_scatter.append({'x': year, 'y': drawdown_info['total_recovery_months']})

    def push_drawdown_period_data(self, drawdown_info: dict):
        drawdown_period = round(drawdown_info['drawdown_period_days']/30)
        self.drawdown_period_graph.append({'x': drawdown_period, 'y': drawdown_info['total_recovery_months']})
    
    def convert_scatter_to_bubble(self):
        counter = Counter((p["x"], p["y"]) for p in self.drawdown_period_graph)
        bubble_points = [
            {"x": x, "y": y, "r": 3 + 1 * count}
            for (x, y), count in counter.items()
        ]
        self.drawdown_period_graph = bubble_points

        counter = Counter((p["x"], p["y"]) for p in self.recovery_yearly_scatter)
        bubble_points = [
            {"x": x, "y": y, "r": 3 + 0.5 * count}
            for (x, y), count in counter.items()
        ]
        self.recovery_yearly_scatter = bubble_points

        counter = Counter((p["x"], p["y"]) for p in self.max_drawdown_graph)
        bubble_points = [
            {"x": x, "y": y, "r": 3 + 0.5 * count}
            for (x, y), count in counter.items()
        ]
        self.max_drawdown_graph = bubble_points
    
    def push_max_drawdown_data(self, drawdown_info: dict):
        peak = drawdown_info['local_max']
        current = drawdown_info['low']
        max_drawdown = drawdown_info['max_drawdown']
        current_drawdown_percent = round(((peak - current)/peak)*100)
        max_drawdown_percent = round(((peak - max_drawdown)/peak)*100)
        drawdown_diff = abs(max_drawdown_percent - current_drawdown_percent)
        self.max_drawdown_graph.append({'x': current_drawdown_percent, 'y': drawdown_diff})

    def reset_data(self):
        self.drawdown_data = {}
        self.total_drawdowns = 0
        self.avg_recovery_months = 0
        self.median_recovery_months = 0
        self.recovery_graph = {}
        self.recovery_yearly_scatter = []
        self.recovery_list = []
        self.drawdown_period_graph = []
        self.max_drawdown_graph = []
