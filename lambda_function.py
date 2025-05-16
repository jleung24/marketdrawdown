from pipeline.stock_data_pipeline import StockDataPipeline

def lambda_handler(event, context):
    pipeline = StockDataPipeline("rds")
    pipeline.update_database("SPY")
