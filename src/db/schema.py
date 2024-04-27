import logging
import psycopg2
from psycopg2.errors import SerializationFailure
import psycopg2.extras
from dotenv import load_dotenv
import os
from src.models.datapoint import DataPoint



load_dotenv()
db_url = os.getenv("DATABASE_URL")

def db_conn():
  connection = None

  try:
      connection = psycopg2.connect(db_url, 
                              application_name="Data Logger", 
                              cursor_factory=psycopg2.extras.RealDictCursor)
  except Exception as e:
      logging.fatal("database connection failed")
      logging.fatal(e)
      exit()

  return connection


def cleanup():
  return None


def create_schema():
    connection = db_conn()

    with connection.cursor() as cur:
        cur.execute(
            """CREATE TABLE IF NOT EXISTS stations (
              id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
              region STRING NOT NULL,
              INDEX index_region (region)
              )
              """
        )
        logging.debug("Created stations table: status message: %s", cur.statusmessage)

        cur.execute(
          """CREATE TABLE IF NOT EXISTS datapoints (
            at TIMESTAMP,
            station UUID NOT NULL REFERENCES stations (id) ON DELETE CASCADE,
            param0 INT,
            param1 INT,
            param2 FLOAT,
            param3 FLOAT,
            param4 STRING,
            CONSTRAINT "primary" PRIMARY KEY (at ASC, station ASC)
          )"""
        )
        logging.debug("Created datapoints table: status message: %s", cur.statusmessage)

    connection.commit()
    connection.close()

    return None



def get_stations():
  connection = db_conn()
  stations = []

  with connection.cursor() as cur:
    cur.execute(
      "SELECT id, region FROM stations"
    )
    logging.debug("get_stations(): %s", cur.statusmessage)
    rows = cur.fetchall()
  
  connection.commit()
  
  for r in rows:
    stations.append({
      "id": r['id'],
      "region": r['region']
    })

  connection.close()

  return stations



def add_station(region: str):
  connection = db_conn()
  with connection.cursor() as cur:
    cur.execute(
      f"UPSERT INTO stations (region) VALUES ('{region}')"
    )
    logging.debug("add_station(): %s", cur.statusmessage)
  
  connection.commit()
  connection.close()
  
  return None



def log_data_point(data: DataPoint):
  connection = db_conn()
  with connection.cursor() as cur:
    cur.execute(
      f"""UPSERT INTO datapoints
        (station, at, param0, param1, param2, param3, param4)
        VALUES
        ('{data.station}', '{data.date}',
        {data.param0}, {data.param1}, {data.param2},
        {data.param3}, '{data.param4}')"""
    )
    logging.debug("log_data_point(): %s", cur.statusmessage)
  
  connection.commit()
  connection.close()  
  
  return None
