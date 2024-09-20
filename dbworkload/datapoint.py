import datetime as dt
import psycopg
import random
import time
import uuid


class Datapoint:
    def __init__(self, args: dict):
        # args is a dict of string passed with the --args flag
        # user passed a yaml/json, in python that's a dict object

        self.read_pct: float = float(args.get("read_pct", 50) / 100)

        self.lane: str = (
            random.choice(["ACH", "DEPO", "WIRE"])
            if not args.get("lane", "")
            else args["lane"]
        )

        # you can arbitrarely add any variables you want
        self.uuid: uuid.UUID = uuid.uuid4()
        self.ts: dt.datetime = ""
        self.event: str = ""

    # the setup() function is executed only once
    # when a new executing thread is started.
    # Also, the function is a vector to receive the excuting threads's unique id and the total thread count
    def setup(self, conn: psycopg.Connection, id: int, total_thread_count: int):
        with conn.cursor() as cur:
            print(
                f"My thread ID is {id}. The total count of threads is {total_thread_count}"
            )
            print(cur.execute(f"select version()").fetchone()[0])

    # the run() function returns a list of functions
    # that dbworkload will execute, sequentially.
    # Once every func has been executed, run() is re-evaluated.
    # This process continues until dbworkload exits.
    def loop(self):
        return [
                self.sql_count_datapoints,
                self.sql_stats_by_region
            ]


    def sql_count_datapoints(self, conn: psycopg.Connection):
        with conn.transaction() as tx:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT region, COUNT(*) AS s_count FROM stations
                    AS OF SYSTEM TIME follower_read_timestamp()
                    GROUP BY region ORDER BY region
                    """
                )
                cur.fetchone()


    def sql_stats_by_region(self, conn: psycopg.Connection):
        with conn.transaction() as tx:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT s.region, count(dp.at), min(dp.at), max(dp.at), sum(dp.param0), avg(dp.param2)
                    FROM datapoints AS dp JOIN stations AS s ON s.id=dp.station
                    AS OF SYSTEM TIME follower_read_timestamp()
                    GROUP BY s.region ORDER BY s.region
                    """
                )
                cur.fetchone()
