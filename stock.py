import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import sqlite3
import csv
import datetime
from selenium import webdriver


class Stock(object):
    """
    Defines a Stock with ticker symbol and name.
    """
    def __init__(self, ticker, name=''):
        self.ticker = ticker
        if name == '':
            self.name = Database.stock_dictionary[self.ticker]
        else:
            self.name = name
        
    def __str__(self):
        return "Stock {}".format(self.ticker)
    
    def __name__(self):
        return self.name
    
    def get_ticker(self):
        return self.ticker
    
    def set_status(self, status):
        self.status = status
        
    def get_status(self):
        if self.status == "":
            return "I haven't buy or sell this stock."
        return self.status
    
    def get_market_detail(self):
        """
        Returns market detail data of a stock.
        """
        self.market_detail = Database.cursor.execute("""
            SELECT *
            FROM market
            WHERE ticker = '{}'
                AND date IN (
                       SELECT MAX(date)
                       FROM market
                           )
        """.format(self.get_ticker())).fetchall()
        return self.market_detail[0]
    
    def Market_Detail(self):
        """
        Call the inner class.
        """
        return self._Market_Detail(market_detail=self.get_market_detail())
    
    class _Market_Detail(object):
        """
        This class stores the functions to call the market detail data for stock.
        """
        def __init__(self, market_detail):
            self.market_detail = market_detail
            
        def get_latest_closed_price(self):
            return self.market_detail[2]
        
        def get_latest_change(self):
            return self.market_detail[3]
    
        def get_latest_volume(self):
            return self.market_detail[4]
        
        def get_latest_opening_price(self):
            return self.market_detail[5]
        
        def get_latest_limit_up(self):
            return self.market_detail[6]
        
        def get_latest_limit_down(self):
            return self.market_detail[7]
    
    
class Order_Stock(Stock):
    """
    This class is an abstract class, which means we will never make an instance of it.
    """
    def __init__(self, ticker, quantity, price, date, fee, tax):
        Stock.__init__(self, ticker)
        self.quantity = quantity
        self.price = price
        self.date = date
        self.fee = fee*(price*quantity)
        self.tax = tax*(price*quantity)
        
    def get_quantity(self):
        return self.quantity
    
    def get_price(self):
        return self.price
    
    def get_date(self):
        return self.date
    
    def get_fee(self):
        return self.fee
    
    def get_tax(self):
        return self.tax
    
    def get_detail(self):
        return (self.ticker, self.name, self.quantity, self.price, self.date, self.status, self.fee, self.tax)
    
    def __str__(self):
        raise NotImplementedError
        

class Buy_Stock(Order_Stock):
    """
    Defines a Stock that was bought by myself.
    """
    def __init__(self, ticker, quantity, price, date, fee=0.1/100, tax=0):
        Order_Stock.__init__(self, ticker, quantity, price, date, fee=0.1/100, tax=0)
        
    def __str__(self):
        return "{} {} shares were bought on {} at {} thousand VND".format(self.quantity, self.ticker, self.date, self.price)


class Sell_Stock(Order_Stock):
    """
    Defines a Stock that was sold by myself.
    """
    def __init__(self, ticker, quantity, price, date, fee=0.1/100, tax=0.1/100):
        Order_Stock.__init__(self, ticker, quantity, price, date, fee=0.1/100, tax=0.1/100)
        
    def __str__(self):
        return "{} {} shares were sold on {} at {} thousand VND".format(self.quantity, self.ticker, self.date, self.price)


class My_Portfolio(object):
    """
    This object works like your wallet, where you know your owned stock, current
    portfolio value and net profit.
    """
    def __init__(self):
        self.orders = {} # a json format recorded all stock trading orders
        self.portfolio = {} # a json format recorded the quantity and value of owned stocks
        self.tax = 0.0 # the money spent on tax when selling
        self.fee= 0.0 # the fee paid to securities company when trading an order
        
    def buy_stock(self, stock):
        """
        Set status 'Buy' and add stock to portfolio.
        """
        # set status for stock
        stock.set_status('Buy')
        
        # add stock to orders
        if stock.get_date() not in self.orders:
            self.orders[stock.get_date()] = {}
        if self.orders[stock.get_date()].get('buy') == None:
            self.orders[stock.get_date()]['buy'] = []
        self.orders[stock.get_date()]['buy'].append(stock)
        
        # add stock to portfolio
        if stock.get_ticker() not in self.portfolio:
            self.portfolio[stock.get_ticker()] = {
                'quantity': 0,
                'value': 0.0,
                'object': Stock(stock.get_ticker())
                }
        self.portfolio[stock.get_ticker()] = self.change_stock_state(self.portfolio[stock.get_ticker()], stock)
        
        # add fee
        self.fee += stock.get_fee()
        
    def sell_stock(self, stock):
        """
        Set status 'Sell' and minus stock in portfolio.
        """
        # minus stock in portfolio
        if stock.get_ticker() not in self.portfolio:
            raise ValueError('Stock {} not in Portfolio'.format(stock.get_ticker()))
        if stock.get_quantity() > self.portfolio[stock.get_ticker()]['quantity']:
            raise ValueError('Not enough quantity of stock {} in Portfolio'.format(stock.get_ticker()))
        ## set status for stock
        stock.set_status('Sell')
        ## change in portfolio
        self.portfolio[stock.get_ticker()] = self.change_stock_state(self.portfolio[stock.get_ticker()], stock)
        ## remove from portfolio if stock quant = 0
        if self.portfolio[stock.get_ticker()]['quantity'] == 0:
            del self.portfolio[stock.get_ticker()]
        
        # add stock to orders
        if stock.get_date() not in self.orders:
            self.orders[stock.get_date()] = {}
        if self.orders[stock.get_date()].get('sell') == None:
            self.orders[stock.get_date()]['sell'] = []
        self.orders[stock.get_date()]['sell'].append(stock)
        
        # add tax
        self.tax += stock.get_tax()
        
        # add fee
        self.fee += stock.get_fee()
        
    def add_stock(self, stock):
        """
        Add stock to order and portfolio without setting status.
        This method maybe used when importing all data from database.
        
        IMPORTANT NOTE:
        Make sure your date is sorted from oldest to latest or the instantaneous price will be false.
        """
        if stock.get_status() == '':
            print("{} on {} has no status.".format(stock.get_ticker(), stock.get_date()))
            return
        if stock.get_date() not in self.orders:
            self.orders[stock.get_date()] = {
                'buy': [],
                'sell': []
                }
        if stock.get_status() == 'Buy':
            self.orders[stock.get_date()]['buy'].append(stock)
        else:
            self.orders[stock.get_date()]['sell'].append(stock)
            
    def change_stock_state(self, adict, stock):
        """
        This method changes the state of stock in portfolio.
        Args:
            adict: a dictionary saving the current quantity and value of an owned stock
            stock: a Stock object that needs to be added to portfolio
        Returns:
            a dictionary with updated quantity and value of an owned stock
        """
        cur_quant = adict['quantity']
        cur_value = adict['value']
        if stock.get_status() == 'Buy':  
            updated_quantity = cur_quant + stock.get_quantity()
            updated_value = (cur_value*cur_quant + stock.get_quantity()*stock.get_price())/updated_quantity
        elif stock.get_status() == 'Sell':
            updated_quantity = cur_quant - stock.get_quantity()
            updated_value = cur_value
        return {
            'quantity': updated_quantity,
            'value': updated_value,
            'object': adict['object']
            }
        
    def get_orders(self):
        return self.orders
    
    def get_portfolio(self):
        return self.portfolio    
    
    def print_orders(self):
        """
        Returns all trading orders in json format.
        """
        return json.dumps(self.orders, default=lambda o: o.__dict__, indent=4)
    
    def print_portfolio(self):
        """
        Returns current portfolio in json format.
        """
        return json.dumps(self.portfolio, default=lambda o: o.__dict__, indent=4)
    
    def get_stock_ticker(self):
        """
        Returns the current owned stock.
        """
        return self.portfolio.keys()
    
    def get_investment(self):
        """
        Return the total money put in Stock in total.
        """
        investment = 0.0
        stocks = self.portfolio
        for stock in stocks:
            investment += stocks[stock]['quantity']*stocks[stock]['value']
        return investment
    
    def get_net_profit(self):
        """
        Returns the total estimated profit AS MONEY in Stock till today.
        """
        return self.get_portfolio_value() - self.get_investment() - self.get_tax() - self.get_fee()
    
    def get_profit(self):
        """
        Returns the total estimated profit in Stock IN PERCENTAGE till today.
        """
        profit_percent = self.get_net_profit()/self.get_investment()
        return "{} %".format(round(profit_percent*100,2))
    
    def get_portfolio_value(self):
        """
        Returns the value as money of all the stock in portfolio till today.
        Value is in thousand VND.
        """
        value = 0.0
        portfolio = self.portfolio
        for stock in portfolio:
            value += portfolio[stock]['quantity']*portfolio[stock]['object'].Market_Detail().get_latest_closed_price()
        return value
    
    def get_tax(self):
        """
        Returns the total tax paid so far.
        Value is in thousand VND.
        """
        return self.tax
        
    def get_fee(self):
        """
        Returns the total fee paid for Stock Company so far.
        Value is in thousand VND.
        """
        return self.fee
    
    def export_json(self, order=False, portfolio=False):
        """
        Export data into json files.
        """
        if order:
            with open("Stock_Orders.json", "w") as order_file:
                json.dump(self.orders, order_file, default= lambda o: o.__dict__, indent=4)
        
        if portfolio:
            with open("My_portfolio.json", "w") as portfolio_file:
                json.dump(self.portfolio, portfolio_file, default= lambda o: o.__dict__, indent=4)


class Database(object):
    """
    This object is used to manipulate database, including web_scrape, create table, update table,
    delete table, etc. This class works mainly with sqlite commands.
    """
    # Connect to stock.db and create cursor object
    connect = sqlite3.connect("stock.db")
    cursor = connect.cursor()
    connect.text_factory = str
    
    # Create a dictionary to store ticker symbol and name of each stock
    stock_dictionary = {'VHM':'Vinhomes', 'SBT':'Bien Hoa Sugar','VNM':'Vinamilk',
                        'FPT':'FPT','MWG':'Thegioididong','VIC':'Vingroup',
                        'MBB':'MBBank', 'VRE':'Vincom Retail', 'SSI':'Chung khoan SSI',
                        'STB':'Ngan hang Saigonthuongtin', 'POW':'Dien luc Dau khi',
                        'VPB':'VPBank', 'CTG':'Ngan hang Cong thuong', 'ACB':'A Chau Bank',
                        'HPG':'Tap doan Hoa Phat', 'TCB':'Techcombank', 'TPB':'TPBank',
                        'VCB':'Vietcombank'}
    
    # Create some datetime variables
    today = datetime.date.today()
    yesterday = (today - datetime.timedelta(days=1))
    today_string = today.strftime('%Y-%m-%d')
    yesterday_string = yesterday.strftime('%Y-%m-%d')
    
    # Check if today's data have been imported yet
    today_data = cursor.execute("""SELECT date FROM market WHERE date='{}'""".format(today_string)).fetchall()
    
    @staticmethod
    def create_table(portfolio=False, market=False):
        if portfolio:
            Database.cursor.execute("""CREATE TABLE IF NOT EXISTS portfolio (ticker TEXT, name TEXT, quantity INTEGER, price REAL, date TEXT, status TEXT, fee REAL, tax REAL)""")
            Database.connect.commit()
        if market:
            Database.cursor.execute("""CREATE TABLE IF NOT EXISTS market (ticker TEXT, date TEXT, closed_price REAL, change REAL, volume REAL, open_price REAL, highest_price REAL, lowest_price REAL)""")
            Database.connect.commit()

    @staticmethod    
    def drop_table(table):
        while True:
            action = input("Confirm DROP TABLE '{}': [y/n] ".format(table))
            if  action in ['y','n']:
                break
        if action == 'y':
            Database.cursor.execute("""DROP TABLE IF EXISTS {}""".format(table))
            Database.connect.commit()
            Database.cursor.execute("""VACUUM""")
            Database.connect.commit()
            print("Table '{}' dropped successfully.".format(table))
        else:
            print("Table '{}' has NOT been dropped.".format(table))
        
    @staticmethod
    def update_database(table, data):
        """
        Insert one row for each function call.
        table is type string.
        """
        Database.cursor.execute("""INSERT INTO {} VALUES {}""".format(table, data))
        Database.connect.commit()
        
    @staticmethod
    def clear_table(table):
        while True:
            action = input("Confirm DISCARD ALL DATA in table '{}': [y/n] ".format(table))
            if  action in ['y','n']:
                break
        if action == 'y':
            Database.cursor.execute("""DELETE FROM {}""".format(table))
            Database.connect.commit()
            Database.cursor.execute("""VACUUM""")
            Database.connect.commit()
            print("Data from table '{}' have been discarded successfully.".format(table))
        else:
            print("Data from table '{}' have NOT been discarded.".format(table))
        
    @staticmethod
    def web_scrape_market_data(ticker, today_string=datetime.date.today().strftime('%Y-%m-%d')):
        """
        Returns market detail of a stock by web sraping from MB Securities website.
        This method is called by import_from_web() and therefore, should not be used directly.
        """
        url = "https://dulieu.mbs.com.vn/vi/Enterprise/Overview?StockCode={}".format(ticker)
        driver_path = "./chromedriver.exe" # Enter your path to ChromDriver
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        driver = webdriver.Chrome(driver_path, options=options)
        try:
            driver.get(url)
        except Exception:
            raise RuntimeError("Access failed for {}".format(ticker))
        else:
            print("Access website successfully for {}.".format(ticker))
            closed_price = Database.Helper.str_to_float(driver.find_element_by_xpath('//*[@id="box1ClosePriceOverview"]').text)
            change = Database.Helper.str_to_float(driver.find_element_by_xpath('//*[@id="box1Change"]').text)
            volume = Database.Helper.str_to_float(driver.find_element_by_xpath('//*[@id="box1TotalVol"]').text)*1000
            open_price = Database.Helper.str_to_float(driver.find_element_by_xpath('//*[@id="box1OpenPrice"]').text)
            highest_price = Database.Helper.str_to_float(driver.find_element_by_xpath('//*[@id="box1HighestPrice"]').text)
            lowest_price = Database.Helper.str_to_float(driver.find_element_by_xpath('//*[@id="box1LowestPrice"]').text)
            return (ticker, today_string, closed_price, change, volume, open_price, highest_price, lowest_price)

    @staticmethod
    def import_from_web():
        """
        This method scrape web stock data and import into table 'market' in database.
        But first, it checks if today's data have been imported.
        """
        if len(Database.today_data) > 0:
            print("Today's data have been imported into the database.")
            action = input("Do you still want to import data? [y/n] ")
            if action != "y":
                return
        for ticker in Database.stock_dictionary.keys():
            try:
                data = Database.web_scrape_market_data(ticker, today_string=Database.today_string)
            except RuntimeError:
                print("Access failed for {}".format(ticker))
                continue
            else:
                Database.update_database('market', data)
    
    @staticmethod
    def collect_stock_data(ticker):
        """
        This method is used to get all history price of a stock from website.
        Data is downloaded from website https://finance.vietstock.vn/VHM/thong-ke-giao-dich.htm.
        After downloading, copy only the data from the excel file and save as csv file.
        """
        ### get data
        with open('{}.csv'.format(ticker),'r',encoding="utf8") as stock_file:
            data = pd.read_csv(stock_file)
            
        ### clean data
        data['date'] = pd.to_datetime(data['Ngày'], dayfirst=True).dt.strftime('%Y-%m-%d')
        for column in data.columns:
            if data[column].isnull().any() == True:
                print('{} has null value'.format(column))
        # Null data typically result from no transaction in the day or no change in price.
        # Therefore, the null value is replace with 0.
        data = data.fillna(0)
        
        # Rename and change value of other columns
        data['closed_price'] = data['Đóng cửa']/1000
        data['change'] = data['+/- giá']/1000
        data['volume'] = data['Khớp lệnh']
        data['open_price'] = data['Mở cửa']/1000
        data['highest_price'] = data['Cao nhất']/1000
        data['lowest_price'] = data['Thấp nhất']/1000
        data['ticker'] = 'VHM'
        clean = pd.DataFrame(data, columns = ['ticker','date','closed_price','change','volume','open_price','highest_price','lowest_price'])

        ### Append data into database table.
        clean.to_sql('market', Database.connect, if_exists='append', index=False)
        return
    
    
    class Helper(object):
        """
        This class contains all the helper functions needed for class Database.
        """
        @staticmethod
        def str_to_float(string):
            """
            When scraping the web, the stock's metrics are strings.
            This method converts those strings as integer for further calculation.
            """
            if string == "":
                return float(0)
            if " " in string:
                string = string[:string.find(" ")]
            string = string.replace(".","")
            return float(string)/1000
      
         
class Visualize(object):
    """
    This class contains methods to visualize for multiple purposes.
    """
    @staticmethod
    def visualize_stock_trend(ticker, portfolio=None):
        """
        This method uses seaborn to draw trendline (closed price, volume) of each stock so far.
        Arg: ticker is the ticker symbol of stock.
        """
        data = pd.read_sql("SELECT * FROM market WHERE ticker='{}' ORDER BY date".format(ticker), Database.connect)
        data['date'] = pd.to_datetime(data['date'])
        
        plt.figure()
        sns.set(rc={'figure.figsize': (25,10)})
        plot = sns.lineplot(x='date', y='closed_price', data=data, label='{} trend'.format(ticker))
        plot.set_title('{} price trendline'.format(ticker), fontsize=40)
        plot.set_xlabel('Date', fontsize=25)
        plot.set_ylabel('Price (thousand VND)', fontsize=25)
        plot.set_ylim(0,np.max(data['closed_price'])+5)
        plt.xticks(fontsize=20)
        plt.yticks(fontsize=20)
        
        # Draw owned-stock's price
        if portfolio:
            price = portfolio.get_portfolio()[ticker]['value']
            plot = sns.lineplot(x=data['date'], y=np.ones(np.count_nonzero(data['date']))*price, label="My {}'s price".format(ticker))
        
        
    @staticmethod
    def stock_profit(stock):
        """
        This method draws the relationship between stock price and profit percentage
        to assisst stock-selling decision.
        """
        # There is a horizontal line representing current profit based on current market price
        raise NotImplementedError


def export_csv(filename="my_portfolio.csv", write=False, append=False, data=()):
    """
    write = True (or append = False) when intending to discard old file and create a new one
    write = False (or append = True) when intending to append new line (new stock) into the file
    data is the detail of stock stored in a tuple.
    """
    if write == append:
        return "write & append arguments cannot be the same."
    if write == True or append == False:
        mode, header = "w", True
    else:
        mode, header = "a", False
    with open(filename, mode, newline='') as csv_file:
        writer = csv.writer(csv_file)
        if header:
            header = ['Ticker','Name','Quantity','Price','Date','Status','Fee','Tax']
            writer.writerow(header)
        writer.writerow(data)
