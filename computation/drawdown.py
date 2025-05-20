class Drawdown:

    def __init__(self, stock_symbol: str, min: int, max: int, duration_days_min: int, duration_days_max: int):
        self.stock_symbol = stock_symbol
        self.min = min
        self.max = max
        self.duration_days_min = duration_days_min
        self.duration_days_max = duration_days_max


