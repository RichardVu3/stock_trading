from stock import *


def test():
    # Create an instance of the object
    my_portfolio = My_Portfolio()
    
    # Add trading orders to portfolio
    my_portfolio.buy_stock(Buy_Stock('SBT', 300, 23.4, '2021-11-08'))
    my_portfolio.buy_stock(Buy_Stock('MBB', 100, 28.6, '2021-11-24'))
    my_portfolio.buy_stock(Buy_Stock('STB', 100, 29.0, '2021-12-01'))
    my_portfolio.buy_stock(Buy_Stock('VHM', 100, 80.0, '2021-12-01'))
    my_portfolio.buy_stock(Buy_Stock('SBT', 100, 22.9, '2021-12-03'))
    my_portfolio.buy_stock(Buy_Stock('VHM', 200, 80.0, '2021-12-05'))
    my_portfolio.buy_stock(Buy_Stock('VIC', 100, 97.0, '2021-12-06'))
    my_portfolio.buy_stock(Buy_Stock('MBB', 100, 30.4, '2021-12-07'))
    my_portfolio.sell_stock(Sell_Stock('VHM', 100, 85.2, '2021-12-09'))
    my_portfolio.buy_stock(Buy_Stock('SBT', 200, 24.0, '2021-12-09'))
    my_portfolio.buy_stock(Buy_Stock('VIC', 400, 93.7, '2021-12-10'))
    my_portfolio.sell_stock(Sell_Stock('SBT', 400, 27.6, '2021-12-12'))
    my_portfolio.buy_stock(Buy_Stock('VHM', 300, 79.5, '2021-12-12'))
    
    # Print stats
    print("My orders: ", my_portfolio.print_orders())
    print("")
    
    print("My portfolio: ", my_portfolio.print_portfolio())
    print("")
    
    print("Money invested: ", my_portfolio.get_investment())
    print("")
    
    print("Current portfolio value: ", my_portfolio.get_portfolio_value())
    print("")
    
    print("Current profit: ", my_portfolio.get_net_profit())
    print("")
    
    print("Profit percentage: ", my_portfolio.get_profit())
    print("")
    
    print("Tax paid: ", my_portfolio.get_tax())
    print("")
    
    print("Fee paid :", my_portfolio.get_fee())
    print("")
    
    # Save trading orders and portfolio into json files
    my_portfolio.export_json(order=True, portfolio=True)
    
    # Visualize stock trend
    Visualize.visualize_stock_trend('VHM', my_portfolio)
    

if __name__ == "__main__":
    test()