from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List

from logger import Logger

logger = Logger()
class Trader:
    def run(self, state: TradingState):
        product_function_map = {
            "RAINFOREST_RESIN": self.trade_resin,
            # "KELP": self.trade_kelp,
            # "SQUID_INK": self.trade_ink
        }

        result = {}
        self.log_state(state)
        for product in state.order_depths:
            if product in product_function_map:
                function = product_function_map[product]
                orders = function(state.order_depths[product])
                result[product] = orders

        trader_data = "SAMPLE"
        conversions = 1
        logger.flush(state, result, conversions, trader_data)
        return result, conversions, trader_data

    def trade_resin(self, order_depth):
        theoretical_price = 10000
        spread = 1

        product = "RAINFOREST_RESIN"
        orders: List[Order] = []
        logger.print("Acceptable price : " + str(theoretical_price))

        # orders.append(Order(product, 10000 - spread, 10))
        # orders.append(Order(product, 10000 + spread, -10))

        if len(order_depth.sell_orders) != 0:
            best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
            if int(best_ask) < theoretical_price - spread:
                logger.print("BUY", str(-best_ask_amount) + "x", best_ask)
                orders.append(Order(product, best_ask, -best_ask_amount))

        if len(order_depth.buy_orders) != 0:
            best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]
            if int(best_bid) > theoretical_price + spread:
                logger.print("SELL", str(best_bid_amount) + "x", best_bid)
                orders.append(Order(product, best_bid, -best_bid_amount))
        return orders

    def trade_kelp(self, order_depth):
        theoretical_price = 10000
        spread = 1

        product = "KELP"
        orders: List[Order] = []
        logger.print("Acceptable price : " + str(theoretical_price))

        if len(order_depth.sell_orders) != 0:
            best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
            if int(best_ask) < theoretical_price - spread:
                logger.print("BUY", str(-best_ask_amount) + "x", best_ask)
                orders.append(Order(product, best_ask, -best_ask_amount))

        if len(order_depth.buy_orders) != 0:
            best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]
            if int(best_bid) > theoretical_price + spread:
                logger.print("SELL", str(best_bid_amount) + "x", best_bid)
                orders.append(Order(product, best_bid, -best_bid_amount))
        return orders

    def trade_ink(self, order_depth):
        theoretical_price = 10000
        spread = 1

        product = "SQUID_INK"
        orders: List[Order] = []
        logger.print("Acceptable price : " + str(theoretical_price))

        if len(order_depth.sell_orders) != 0:
            best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
            if int(best_ask) < theoretical_price - spread:
                logger.print("BUY", str(-best_ask_amount) + "x", best_ask)
                orders.append(Order(product, best_ask, -best_ask_amount))

        if len(order_depth.buy_orders) != 0:
            best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]
            if int(best_bid) > theoretical_price + spread:
                logger.print("SELL", str(best_bid_amount) + "x", best_bid)
                orders.append(Order(product, best_bid, -best_bid_amount))
        return orders

    def log_state(self, state):
        logger.print("traderData: " + state.traderData)
        logger.print("Observations: " + str(state.observations))

        for product in state.order_depths:
            order_depth = state.order_depths[product]
            best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]
            best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
            logger.print(f"{product} best market bid: {best_bid_amount}@{best_bid}")
            logger.print(f"{product} best market ask: {best_ask_amount}@{best_ask}")
