import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
import asyncio
import sqlalchemy

import mysecrets

import binance
from binance import AsyncClient, BinanceSocketManager
from binance.client import Client

import sys
import time
import os
import logging
import signal
import argparse

db_engine = sqlalchemy.create_engine("sqlite:///cTracker.db")
client = Client(mysecrets.API_KEY, mysecrets.SECRET_KEY)


def create_parser() -> argparse.ArgumentParser:
    """Returns an instance Parser"""
    parser = argparse.ArgumentParser(
        description="""Will connect to crypto socket
        from binance using symbol passed in
        """
    )

    parser.add_argument(
        "-f", "--feed", help="feed database with data", action="store_true"
    )
    parser.add_argument("symbol", help="symbol of crypto to look up")
    parser.add_argument("pulls", help="how many entries to pull")

    return parser


async def main(args) -> None:

    parser = create_parser()
    ns = parser.parse_args(args)

    feed = ns.feed
    symbol = ns.symbol.upper()
    pulls = int(ns.pulls)

    if not ns:
        parser.print_usage()

    if feed:
        await feed_data(symbol, pulls)


async def feed_data(sym: str, pulls: int) -> None:
    bsm = BinanceSocketManager(client)
    bin_sym = f"{sym}USDT"
    socket = bsm.trade_socket(bin_sym)
    async with socket as bsm_socket:
        print("Generating data...")
        while True:
            for _ in range(pulls):
                response = await bsm_socket.recv()
                # print(response)
                df = create_data_frame(response)
                df.to_sql(f"cT_{sym}", db_engine, if_exists="append", index=False)
                sql_df = pd.read_sql(f"cT_{sym}", db_engine)
                print(sql_df)
                print("downloading...")

                client.close_connection()
            # os.system('clear')
            time.sleep(1)
            strategy(0.0001, pulls, 0.001, sym)


def create_data_frame(rs: dict) -> pd.core.frame.DataFrame:
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


def strategy(
    entry: float, lookback: int, qty: float, sym: str, open_pos: bool = False
) -> None:
    """
    Trend-following
    if the crypto was rising by x % --> Buy
    exit when profit is above 0.15% or loss is crossing -0.15%
    """
    bin_sym = f"{sym}USDT"
    # while True:

    print("Developing strategy...")
    time.sleep(1)

    sql_df = pd.read_sql(f"cT_{sym}", db_engine)
    # looking back at the last 60 valid entries in db
    lookbackperiod = sql_df.iloc[-lookback:]
    # print(lookbackperiod.Price.pct_change())
    print("Accumilating returns...")
    time.sleep(1)
    # accumilating the returns from the lookbackperiod
    cum_ret = (lookbackperiod.Price.pct_change() + 1).cumprod() - 1
    print("Returns completed")
    time.sleep(1)
    print(f"Accumilated Returns:\n{cum_ret}")
    # print("Done")
    time.sleep(1)

    if not open_pos:
        if cum_ret[cum_ret.last_valid_index()] > entry:
            try:
                order = client.create_order(
                    symbol=bin_sym, side="BUY", TYPE="market", quantity=qty
                )
                print(order)
                open_pos = True
            except binance.exceptions.BinanceAPIException:
                print("You do not have permission to BUY")

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
