import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
import asyncio
import sqlalchemy

import mysecrets

from binance import AsyncClient, BinanceSocketManager
from binance.client import Client

import sys
import os
import logging
import signal
import argparse

db_engine = sqlalchemy.create_engine("sqlite:///cTracker.db")
client = Client(mysecrets.API_KEY, mysecrets.SECRET_KEY)


def create_parser():
    """Returns an instance Parser"""
    parser = argparse.ArgumentParser(
        description="""Will connect to crypto socket
        from binance using symbol passed in
        """
    )

    parser.add_argument("-f", "--feed", help="feed database with data", action='store_true')
    parser.add_argument("-s", "--strat", help="buy or sell", action='store_true')
    parser.add_argument("symbol", help="symbol of crypto to look up")

    return parser


async def main(args):

    parser = create_parser()
    ns = parser.parse_args(args)

    feed = ns.feed
    strat = ns.strat
    symbol = ns.symbol

    if not ns:
        parser.print_usage()

    if feed:
        await feed_data(symbol)

    if strat:
        strategy(0.001, 60, 0.001, symbol)


async def feed_data(sym):
    bsm = BinanceSocketManager(client)
    bin_sym = f"{sym}USDT"
    socket = bsm.trade_socket(bin_sym)
    async with socket as bsm_socket:
        while True:
            response = await bsm_socket.recv()
            # print(response)
            df = create_data_frame(response)
            df.to_sql(f"cT_{sym}", db_engine, if_exists="append", index=False)
            sql_df = pd.read_sql(f"cT_{sym}", db_engine)
            print(sql_df)

            client.close_connection()


def create_data_frame(rs):
    """
    Takes in a dictionary and returns
    a pandas data frame
    """
    df = pd.DataFrame([rs])
    df = df.loc[:, ["s", "E", "p"]]
    df.columns = ["symbol", "Time", "Price"]
    df.Price = df.Price.astype(float)
    df.Time = pd.to_datetime(df.Time, unit="ms")
    return df


def strategy(entry, lookback, qty, sym, open_pos=False):
    """
    Trend-following
    if the crypto was rising by x % --> Buy
    exit when profit is above 0.15% or loss is crossing -0.15%
    strategy(<entry>, <lookback>, client, bin_sym)
    """
    bin_sym = f"{sym}USDT"
    while True:
        sql_df = pd.read_sql("cT_ETH", db_engine)
        lookbackperiod = sql_df.iloc[-lookback:]
        cumilitive_return = (lookbackperiod.Price.pct_change() + 1).cumprod() - 1
        if not open_pos:
            if cumilitive_return[cumilitive_return.last_valid_index()] > entry:
                # loop getting stuck on this line ^^^
                order = client.create_order(
                    symbol=bin_sym, side="BUY", TYPE="market", quantity=qty
                )
                print(order)
                open_pos = True
                break
    if open_pos:
        while True:
            sql_df = pd.read_sql("cT_ETH", db_engine)
            sincebuy = sql_df.loc[
                sql_df.Time > pd.to_datetime(order["transactTime"], unit="ms")
            ]

            if len(sincebuy) > 1:
                sincebuy_return = (sincebuy.Price.pct_change() + 1).cumprod() - 1
                last_entry = sincebuy_return[sincebuy_return.last_valid_index()]
                if last_entry > 0.0015 or last_entry < -0.0015:
                    order = client.create_order(
                        symbol=bin_sym, side="SELL", TYPE="market", quantity=qty
                    )
                    print(order)
                    break


if __name__ == "__main__":

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(sys.argv[1:]))