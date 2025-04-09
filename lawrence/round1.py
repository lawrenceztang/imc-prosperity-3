from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List
import string

class Trader:

    def run(self, state: TradingState):
        product_function_map = {"RAINFOREST_RESIN": self.trade_resin}

        print("traderData: " + state.traderData)
        print("Observations: " + str(state.observations))

        # Orders to be placed on exchange matching engine
        result = {}
        for product in state.order_depths:
            if product in product_function_map:
                function = product_function_map[product]
                orders = function(state.order_depths[product])
                result[product] = orders

        # String value holding Trader state data required.
        # It will be delivered as TradingState.traderData on next execution.
        traderData = "SAMPLE"

        # Sample conversion request. Check more details below.
        conversions = 1
        return result, conversions, traderData

    def trade_resin(self, order_depth):
        theoretical_price = 10000
        spread = 1

        product = "RAINFOREST_RESIN"
        orders: List[Order] = []
        print("Acceptable price : " + str(theoretical_price))

        if len(order_depth.sell_orders) != 0:
            best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
            print(f"Best market ask: {best_ask_amount}@{best_ask}")
            if int(best_ask) < theoretical_price - spread:
                print("BUY", str(-best_ask_amount) + "x", best_ask)
                orders.append(Order(product, best_ask, -best_ask_amount))

        if len(order_depth.buy_orders) != 0:
            best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]
            print(f"Best market bid: {best_bid_amount}@{best_bid}")
            if int(best_bid) > theoretical_price + spread:
                print("SELL", str(best_bid_amount) + "x", best_bid)
                orders.append(Order(product, best_bid, -best_bid_amount))
        return orders
