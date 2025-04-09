from datamodel import Listing, Observation, Order, OrderDepth, ProsperityEncoder, Symbol, Trade, TradingState
from typing import List
from typing import Any
import json
import statistics
import pandas as pd
import numpy as np

# Ignore Logger code
class Logger:
    def __init__(self) -> None:
        self.logs = ""
        self.max_log_length = 3750

    def print(self, *objects: Any, sep: str = " ", end: str = "\n") -> None:
        self.logs += sep.join(map(str, objects)) + end

    def flush(self, state: TradingState, orders: dict[Symbol, list[Order]], conversions: int, trader_data: str) -> None:
        base_length = len(
            self.to_json(
                [
                    self.compress_state(state, ""),
                    self.compress_orders(orders),
                    conversions,
                    "",
                    "",
                ]
            )
        )

        # We truncate state.traderData, trader_data, and self.logs to the same max. length to fit the log limit
        max_item_length = (self.max_log_length - base_length) // 3

        print(
            self.to_json(
                [
                    self.compress_state(state, self.truncate(state.traderData, max_item_length)),
                    self.compress_orders(orders),
                    conversions,
                    self.truncate(trader_data, max_item_length),
                    self.truncate(self.logs, max_item_length),
                ]
            )
        )

        self.logs = ""

    def compress_state(self, state: TradingState, trader_data: str) -> list[Any]:
        return [
            state.timestamp,
            trader_data,
            self.compress_listings(state.listings),
            self.compress_order_depths(state.order_depths),
            self.compress_trades(state.own_trades),
            self.compress_trades(state.market_trades),
            state.position,
            self.compress_observations(state.observations),
        ]

    def compress_listings(self, listings: dict[Symbol, Listing]) -> list[list[Any]]:
        compressed = []
        for listing in listings.values():
            compressed.append([listing.symbol, listing.product, listing.denomination])

        return compressed

    def compress_order_depths(self, order_depths: dict[Symbol, OrderDepth]) -> dict[Symbol, list[Any]]:
        compressed = {}
        for symbol, order_depth in order_depths.items():
            compressed[symbol] = [order_depth.buy_orders, order_depth.sell_orders]

        return compressed

    def compress_trades(self, trades: dict[Symbol, list[Trade]]) -> list[list[Any]]:
        compressed = []
        for arr in trades.values():
            for trade in arr:
                compressed.append(
                    [
                        trade.symbol,
                        trade.price,
                        trade.quantity,
                        trade.buyer,
                        trade.seller,
                        trade.timestamp,
                    ]
                )

        return compressed

    def compress_observations(self, observations: Observation) -> list[Any]:
        conversion_observations = {}
        for product, observation in observations.conversionObservations.items():
            conversion_observations[product] = [
                observation.bidPrice,
                observation.askPrice,
                observation.transportFees,
                observation.exportTariff,
                observation.importTariff,
                observation.sugarPrice,
                observation.sunlightIndex,
            ]

        return [observations.plainValueObservations, conversion_observations]

    def compress_orders(self, orders: dict[Symbol, list[Order]]) -> list[list[Any]]:
        compressed = []
        for arr in orders.values():
            for order in arr:
                compressed.append([order.symbol, order.price, order.quantity])

        return compressed

    def to_json(self, value: Any) -> str:
        return json.dumps(value, cls=ProsperityEncoder, separators=(",", ":"))

    def truncate(self, value: str, max_length: int) -> str:
        if len(value) <= max_length:
            return value

        return value[: max_length - 3] + "..."

# Start here

logger = Logger()
class Trader:
    def run(self, state: TradingState):
        # TODO: write the self.trade_ink() function
        product_function_map = {
            "RAINFOREST_RESIN": self.trade_resin,
            "KELP": self.trade_kelp,
            # "SQUID_INK": self.trade_ink
        }

        result = {}
        self.log_state(state)
        for product in state.order_depths:
            if product in product_function_map:
                function = product_function_map[product]
                orders = function(state)
                result[product] = orders

        trader_data = self.get_trader_data(state)
        conversions = 1

        logger.flush(state, result, conversions, trader_data)
        return result, conversions, trader_data

    def get_trader_data(self, state):
        if not state.traderData:
            trader_data = {"KELP": [[], []]}
        else:
            trader_data = json.loads(state.traderData)
        return json.dumps({"KELP": self.get_kelp_trader_data(trader_data, state)})

    # Our kelp trader data allows us to calculate the moving average of the price
    def get_kelp_trader_data(self, trader_data, state):
        kelp_trader_data = trader_data["KELP"]
        kelp_trader_data[0].append(list(state.order_depths["KELP"].buy_orders.items())[0][0])
        kelp_trader_data[1].append(list(state.order_depths["KELP"].sell_orders.items())[0][0])
        if len(kelp_trader_data[0]) > 50:
            kelp_trader_data[0] = kelp_trader_data[0][1:]
            kelp_trader_data[1] = kelp_trader_data[1][1:]
        return kelp_trader_data

    # We buy when the price dips below 10k and sell when it goes above
    def trade_resin(self, state):
        theoretical_price = 10000
        spread = 1

        product = "RAINFOREST_RESIN"
        orders: List[Order] = []
        order_depth = state.order_depths[product]

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

    # We buy when the price dips below the exponential weighted moving average and sell when it goes above
    def trade_kelp(self, state):

        product = "KELP"
        orders: List[Order] = []
        order_depth = state.order_depths[product]
        if state.traderData:
            trader_data = json.loads(state.traderData)["KELP"]
        else:
            return []

        theoretical_price = self.smoothed_price([(a + b) / 2 for a, b in zip(trader_data[0][-10:], trader_data[1][-10:])])
        spread = 1

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

    def smoothed_price(self, data: List[float]) -> float:
        if not data:
            return 0.0
        series = pd.Series(data)
        smoothed = series.ewm(alpha=0.3, adjust=False).mean()
        return smoothed.iloc[-1]

    def smoothed_price_2(self, data: List[float]) -> float:
        if len(data) < 2:
            return data[-1] if data else 0.0
        x = np.arange(len(data))
        y = np.array(data)
        m, b = np.polyfit(x, y, 1)
        next_time = len(data)
        predicted_price = m * next_time + b

        return predicted_price

    def trade_ink(self, order_depths):
        # TODO. We don't have a working algo for ink yet.
        product = "SQUID_INK"
        orders: List[Order] = []
        order_depth = order_depths[product]

        ink_price = (list(order_depths["SQUID_INK"].sell_orders.items())[0][0] + list(order_depths["SQUID_INK"].buy_orders.items())[0][0]) / 2
        kelp_price = (list(order_depths["KELP"].sell_orders.items())[0][0] + list(order_depths["KELP"].buy_orders.items())[0][0]) / 2

        theoretical_price = kelp_price
        spread = 100

        # orders.append(Order(product, int(theoretical_price - spread), 5))
        # orders.append(Order(product, int(theoretical_price + spread), -5))

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

    # Not important
    def log_state(self, state):
        logger.print("traderData: " + state.traderData)
        logger.print("Observations: " + str(state.observations))

        for product in state.order_depths:
            order_depth = state.order_depths[product]
            best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]
            best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
            logger.print(f"{product} best market bid: {best_bid_amount}@{best_bid}")
            logger.print(f"{product} best market ask: {best_ask_amount}@{best_ask}")