import argparse
import os
import requests
import json
from datetime import datetime
import random
import string
from apscheduler.schedulers.blocking import BlockingScheduler


def get_stations(args):
  url = f"{args.url}/api/stations"
  r = requests.get(url)

  result = None

  if r.status_code == 200:
    result = json.loads(r.text)

  return result



def list(args):
  stations = get_stations(args)
  stations.sort(key=lambda s: (s['region'], s['id']))

  # Header
  output = [
    "REGION                             ID",
    "--------------------------------------------------------------------------"
  ]

  # Data
  for s in stations:
    output.append(
      f"{s['region'].ljust(35)}{s['id']}"
    )

  for row in output:
    print(row)

  print()

  return None


# TODO: Seed random generator ranges.
#       In the future, we may be receiving calibrations for the
#       ranges from the API on the fly.

init_random_ranges = {
  "interval": {
    "low": 1,
    "high": 10
  },
  "param0": {
    "low": 0,
    "high": 1000
  },
  "param1": {
    "low": -1000,
    "high": 1000
  },
  "param2": {
    "low": -1000,
    "high": 1000,
    "precision": 3
  },
  "param3": {
    "low": -1000,
    "high": 1000,
    "precision": 2
  },
  "param4": {
    "low": 8,
    "high": 32
  }
}



scheduler = BlockingScheduler()
scheduler.add_executor('processpool')


def update_stations(args):
  stations = get_stations(args)

  stations = [station['id'] for station in stations if station['region'] in args.region[0]]
  print(json.dumps(stations, indent=2))
  
  random_ranges = init_random_ranges
  url = f"{args.url}/api/datapoint"

  for station in stations:
    interval = random.randint(
                      random_ranges['interval']['low'],
                      random_ranges['interval']['high']
                    )

    if scheduler.get_job(station) is None:
      print(f"{station}\t{interval} sec(s)")
      scheduler.add_job(
        single_data_point,
        'interval',
        [url, station],
        seconds = interval,
        id = station
      )

  return None


def generate(args):
  update_stations(args)

  scheduler.add_job(
    update_stations,
    'interval',
    [args],
    seconds = 60
  )

  print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))

  try:
    scheduler.start()
  except (KeyboardInterrupt, SystemExit):
    scheduler.shutdown()
    pass

  return None


  
def single_data_point(url, station_id):
  random_ranges = init_random_ranges

  datapoint = {
    "station":  station_id,
    "date":     str(datetime.now()),
    "param0":   random.randint(
                  random_ranges['param0']['low'],
                  random_ranges['param0']['high']
                ),
    "param1":   random.randint(
                  random_ranges['param1']['low'],
                  random_ranges['param1']['high']
                ),
    "param2":   round(random.uniform(
                  random_ranges['param2']['low'],
                  random_ranges['param2']['high']
                ), random_ranges['param2']['precision']),
    "param3":   round(random.uniform(
                  random_ranges['param3']['low'],
                  random_ranges['param3']['high']
                ), random_ranges['param3']['precision']),
    "param4":   ''.join(random.choices(
                    string.ascii_uppercase + string.digits,
                    k = random.randint(
                      random_ranges['param4']['low'],
                      random_ranges['param4']['high']
                    )))
  }

  print(json.dumps(datapoint, indent=2))

  r = requests.post(url, json=datapoint)
  print(r.status_code)

  result = None

  return None



#
# Main
#
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
            prog = os.path.basename(__file__),
            description = "Simulates multiple stations sending data points"
        )

    parser.add_argument("-u", "--url", type=str, required=True,
                        help="REST API URL"
                      )

    subparsers = parser.add_subparsers(required=True, title='subcommands', dest="cmd")

    # create the parser for the "list" command
    sub_list = subparsers.add_parser('list', aliases=['ls'], help='List available stations')
    sub_list.set_defaults(func=list)

    # create the parser for the "generate" command
    sub_gen = subparsers.add_parser('generate', aliases=['gen'], help='Generate data points')
    sub_gen.set_defaults(func=generate)
    sub_gen.add_argument("-r", "--region", type=str, required=True, action='append', nargs='+',
                        help="The region from which the stations will be sending data."
                    )

    args, unknown = parser.parse_known_args()
    args.func(args)

    exit(0)


