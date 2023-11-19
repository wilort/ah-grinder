from money import Money
import statistics

class ItemStat:
    def __init__(self):
        self.item_id: int = None
        self.auctions: dict = {} # time_stamp -> {unit_prices: [], quantities: []}

        self.time_stamps: list[str] = []
        self.min_unit_prices: list[int] = []
        self.median_unit_prices: list[int] = []
        self.max_unit_prices: list[int] = []
        self.quantities: list[int] = []

        self.min_min_unit_price: int = None
        self.median_min_unit_price: int = None
        self.max_min_unit_price: int = None
        self.min_quantity: int = None
        self.median_quantity: int = None
        self.max_quantity: int = None
        self.latest_min_unit_price: int = None
        self.latest_time_stamp: str = None
        self.score: int = None
        self.score2: int = None

        self.name: str = None
        self.sell_price: int = None # the price at which the item is sold to a vendor
        self.quality: str = None
        self.class_name: str = None

    def calculate_statistics(self):
        for time_stamp in self.auctions:

            unit_prices = self.auctions[time_stamp]['unit_prices']
            quantities = self.auctions[time_stamp]['quantities']
            min_unit_price = min(unit_prices)
            max_unit_price = max(unit_prices)
            median_unit_price = statistics.median(unit_prices)
            quantity = sum(quantities)

            self.time_stamps.append(time_stamp)
            self.min_unit_prices.append(min_unit_price)
            self.max_unit_prices.append(max_unit_price)
            self.median_unit_prices.append(median_unit_price)
            self.quantities.append(quantity)

        self.min_min_unit_price = min(self.min_unit_prices)
        self.median_min_unit_price = statistics.median(self.min_unit_prices)
        self.max_min_unit_price = max(self.min_unit_prices)
        self.min_quantity = min(self.quantities)
        self.median_quantity = round(statistics.median(self.quantities))
        self.max_quantity = max(self.quantities)
        self.latest_time_stamp = max(self.time_stamps)
        self.latest_min_unit_price = self.min_unit_prices[-1]
        self.calculate_score()
        #self.calculate_score2()

    def calculate_score(self):
        """
        The score is the potential profit you can make if you buy the item at the latest min price and sell it at the
        median min price and it includes the auction house cut.
        """
        # calculate the score
        potential_sell_price = self.median_min_unit_price
        auction_house_cut = potential_sell_price * 0.05
        buyout_price = self.latest_min_unit_price
        potential_profit = potential_sell_price - auction_house_cut - buyout_price
        self.score = potential_profit

    def calculate_score2(self):
        """
        This score is the potential profit if you buy all items below the median min price and sell them all for the median min price.
        This also includes the auction house cut.
        """

        unit_prices = self.auctions[self.latest_time_stamp]['unit_prices']
        quantities = self.auctions[self.latest_time_stamp]['quantities']
        total_potential_profit = 0
        for unit_price, quantity in zip(unit_prices, quantities):

                potential_sell_price = self.median_min_unit_price * quantity
                auction_house_cut = potential_sell_price * 0.05
                buyout_price = unit_price * quantity
                potential_profit = potential_sell_price - auction_house_cut - buyout_price

                if potential_profit > 0:
                    total_potential_profit += potential_profit

        self.score2 = total_potential_profit

    def print_statistics(self):

        header_format = "{:<25} {:<15} {:<20} {:<20} {:<20} {:<20} {:<20}"
        item_name = self.name
        min_min_price = str(Money(self.min_min_unit_price))
        median_min_price = str(Money(self.median_min_unit_price))
        max_min_price = str(Money(self.max_min_unit_price))
        latest_min_price = str(Money(self.latest_min_unit_price))
        score = str(Money(self.score))
        min_quantity = str(self.min_quantity)
        median_quantity = str(self.median_quantity)
        max_quantity = str(self.max_quantity)
        quantity_summary = f"{min_quantity} / {median_quantity} / {max_quantity}"
        print(header_format.format(item_name, score, latest_min_price, min_min_price, median_min_price, max_min_price, quantity_summary))
