from pydantic import BaseModel, Field

class StockData(BaseModel):
    stock_data_id: str = Field(pattern=r'^\d{8}_.*')
    date: str = Field(pattern=r'^\d{4}-\d{2}-\d{2}$')
    stock_symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    local_max_id: str = Field(pattern=r'^\d{8}_.*')
