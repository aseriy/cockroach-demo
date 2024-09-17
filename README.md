- [Cluster Setup](#cluster-setup)
  - [HAProxy configuration](#haproxy-configuration)
  - [Create 3-node CockroachDB cluster](#create-3-node-cockroachdb-cluster)
  - [Grafana](#grafana)
- [Generating Workload](#generating-workload)
- [Node Removal Exercises](#node-removal-exercises)
  - [Graceful Shutdown](#graceful-shutdown)
  - [Dirty Shutdown](#dirty-shutdown)
- [Remove all but one node](#remove-all-but-one-node)
- [Alternative Workload Generation](#alternative-workload-generation)
- [Data Collection Application](#data-collection-application)
  - [Multi-Region Cluster](#multi-region-cluster)

## Cluster Setup

AWS EC2 instance running Ubuntu 22.04, 4 CPU Cores, 16GB RAM.

### HAProxy configuration

Copy file `setup/haproxy.cf` to `/etc/haproxy` directory and start HAProxy service:

```bash
systemctl restart haproxy
```

Verify that port 8080 and 26257 are up:

```bash
ss -antpl | grep 8080
LISTEN 0      4096         0.0.0.0:8080       0.0.0.0:*
```

```bash
ss -antpl | grep 26257
LISTEN 0      4096         0.0.0.0:26257      0.0.0.0:* 
```

A helpful video HAProxy tutorial: https://youtu.be/RxrdC9l7yKk?si=60mVQjt3ZoRq9Vn6

### Create 3-node CockroachDB cluster

The nodes in the cluster should be serving on ports `26258`, `26259`, etc. and the admin console on ports `8081`, `8082`, etc. Nodes use directories names `cockroach-data-1`, `cockroach-data-2`, etc. respectively.

```bash
cockroach start --insecure --listen-addr=localhost:26258 --join=localhost:26258,localhost:26259,localhost:26260 --http-addr=localhost:8081 --store=cockroach-data-1 --background
```

```bash
cockroach start --insecure --listen-addr=localhost:26259 --join=localhost:26258,localhost:26259,localhost:26260 --http-addr=localhost:8082 --store=cockroach-data-2 --background
```

```bash
cockroach start --insecure --listen-addr=localhost:26260 --join=localhost:26258,localhost:26259,localhost:26260 --http-addr=localhost:8083 --store=cockroach-data-3 --background
```

```bash
cockroach init --host localhost:26258 --insecure
```

Verify that the proxy is routing the traffic as expected:

```bash
ss -antpl | grep 808
LISTEN 0      4096       127.0.0.1:8081       0.0.0.0:*    users:(("cockroach",pid=1105,fd=33))
LISTEN 0      4096       127.0.0.1:8083       0.0.0.0:*    users:(("cockroach",pid=1141,fd=66))
LISTEN 0      4096       127.0.0.1:8082       0.0.0.0:*    users:(("cockroach",pid=1123,fd=69))
LISTEN 0      4096         0.0.0.0:8080       0.0.0.0:*
```

```bash
ss -antpl | grep 26
LISTEN 0      4096       127.0.0.1:26259      0.0.0.0:*    users:(("cockroach",pid=1123,fd=70))
LISTEN 0      4096       127.0.0.1:26258      0.0.0.0:*    users:(("cockroach",pid=1105,fd=43))
LISTEN 0      4096       127.0.0.1:26260      0.0.0.0:*    users:(("cockroach",pid=1141,fd=67))
LISTEN 0      4096         0.0.0.0:26257      0.0.0.0:*
```

```bash
tail -f /var/log/haproxy.log
Apr 26 13:31:45 ip-172-31-89-156 haproxy[987]: Server cockroach/east1 is UP, reason: Layer4 check passed, check duration: 0ms. 2 active and 0 backup servers online. 0 sessions requeued, 0 total in queue.
Apr 26 13:31:45 ip-172-31-89-156 haproxy[987]: Server cockroach/east1 is UP, reason: Layer4 check passed, check duration: 0ms. 2 active and 0 backup servers online. 0 sessions requeued, 0 total in queue.
Apr 26 13:31:46 ip-172-31-89-156 haproxy[987]: Server admin/east1 is UP, reason: Layer4 check passed, check duration: 0ms. 2 active and 0 backup servers online. 0 sessions requeued, 0 total in queue.
Apr 26 13:31:46 ip-172-31-89-156 haproxy[987]: [WARNING]  (987) : Server admin/east1 is UP, reason: Layer4 check passed, check duration: 0ms. 2 active and 0 backup servers online. 0 sessions requeued, 0 total in queue.
Apr 26 13:31:46 ip-172-31-89-156 haproxy[987]: Server admin/east1 is UP, reason: Layer4 check passed, check duration: 0ms. 2 active and 0 backup servers online. 0 sessions requeued, 0 total in queue.
Apr 26 13:31:55 ip-172-31-89-156 haproxy[987]: Server admin/east2 is UP, reason: Layer4 check passed, check duration: 0ms. 3 active and 0 backup servers online. 0 sessions requeued, 0 total in queue.
Apr 26 13:31:55 ip-172-31-89-156 haproxy[987]: [WARNING]  (987) : Server admin/east2 is UP, reason: Layer4 check passed, check duration: 0ms. 3 active and 0 backup servers online. 0 sessions requeued, 0 total in queue.
Apr 26 13:31:56 ip-172-31-89-156 haproxy[987]: [WARNING]  (987) : Server cockroach/east2 is UP, reason: Layer4 check passed, check duration: 0ms. 3 active and 0 backup servers online. 0 sessions requeued, 0 total in queue.
Apr 26 13:31:55 ip-172-31-89-156 haproxy[987]: Server admin/east2 is UP, reason: Layer4 check passed, check duration: 0ms. 3 active and 0 backup servers online. 0 sessions requeued, 0 total in queue.
Apr 26 13:31:56 ip-172-31-89-156 haproxy[987]: Server cockroach/east2 is UP, reason: Layer4 check passed, check duration: 0ms. 3 active and 0 backup servers online. 0 sessions requeued, 0 total in queue.
```

Open the admin console in a browser:

```bash
http://localhost:8080
```

In my case, local port 8080 on my laptop is forwarded to the EC2 via the SSH tunnel. If the traffic from public Internet is allowed through a Security Group policy, then use the public URL:

```bash
http://ec2-44-203-176-182.compute-1.amazonaws.com:8080
```

or similar.

### Grafana

Grafana is available at http://ec2-44-204-48-26.compute-1.amazonaws.com:3000/dashboards

Grafana works in concert with Prometheus, an open source tool for storing, aggregating, and querying time series data. CockroachDB emits various runtime status parameters at http://localhost:8080/_status/vars. Prometheus poll the output, parses it and serves to Grafana.
In addition, Prometheus Alertmanager is a rules based engine that generates alerts when the cluster experiences problems that need attention. CockroachDB emits alert info at http://localhost:8080/api/v2/rules which gets processes by the Alertmanager and makes them available to Gafana to visualize as well.

## Generating Workload

```bash
cockroach workload init bank
I240430 08:56:24.268360 1 workload/cli/run.go:639  [-] 1  random seed: 8684093597599225673
I240430 08:56:24.293048 1 ccl/workloadccl/fixture.go:315  [-] 2  starting import of 1 tables
I240430 08:56:24.805379 24 ccl/workloadccl/fixture.go:492  [-] 3  imported 112 KiB in bank table (1000 rows, 0 index entries, took 455.587693ms, 0.24 MiB/s)
I240430 08:56:24.806233 1 ccl/workloadccl/fixture.go:323  [-] 4  imported 112 KiB bytes in 1 tables (took 513.10111ms, 0.21 MiB/s)
I240430 08:56:24.886276 1 workload/workloadsql/workloadsql.go:148  [-] 5  starting 9 splits
```

```bash
nohup cockroach workload run bank > workload_bank.log 2>&1 &
```

```bash
tail -f workload_bank.log
```

Add the fourth node:

```bash
cockroach start --insecure --listen-addr=localhost:26261 --join=localhost:26258,localhost:26259,localhost:26260 --http-addr=localhost:8084 --store=cockroach-data-4 --background
```

The 65 ranges get re-distributed between 4 nodes, resulting in 48 to 50 ranges per node.


```bash
cockroach start --insecure --listen-addr=localhost:26262 --join=localhost:26258,localhost:26259,localhost:26260 --http-addr=localhost:8085 --store=cockroach-data-5 --background
```

## Node Removal Exercises

### Graceful Shutdown

```bash
ps auxwww| grep cockroach-data-4 | grep -v grep
```

```bash
kill <pid>
```

1. Node 4 is DRAINING
2. Becomes SUSPECT
3. 48 ranges become under-replicated

Restore the node within 5 minutes:

```bash
cockroach start --insecure --listen-addr=localhost:26261 --join=localhost:26258,localhost:26259,localhost:26260 --http-addr=localhost:8084 --store=cockroach-data-4 --background
```

1. When node 4 isn't back up for 5 minutes, the system considered the node DEAD.
2. Within a few minutes, the 48 under-replicated ranges are redistributed about the remaining 3 nodes, resulting in 65 ranges per node.

Restore the node:

```bash
cockroach start --insecure --listen-addr=localhost:26261 --join=localhost:26258,localhost:26259,localhost:26260 --http-addr=localhost:8084 --store=cockroach-data-4 --background
```

### Dirty Shutdown

```bash
ps auxwww| grep cockroach-data-4 | grep -v grep
```

```bash
kill -9 <pid>
```

1. Under-replicated ranges (49) detected before the node is classified as SUSPECT. No draining.
2. Five minutes later, the system declares the node DEAD and redistributes the under-replicated ranges among the remaining 3 nodes.

## Remove all but one node

```bash
ps auxwww| grep cockroach-data-3 | grep -v grep
```

```bash
kill <pid>
```

1. Node 3 becomes a SUSPECT
2. Five minutes later, is declared DEAD.
3. There are 65 ranges total, all are still available but under-replicated.

```bash
ps auxwww| grep cockroach-data-2 | grep -v grep
```

```bash
kill <pid>
```

The single remaining node process is still up but the cluster as a whole dies.

```bash
ps auxwww| grep cockroach-data | grep -v grep
ubuntu       951 22.9  8.1 2260776 661884 ?      Sl   07:49  29:37 cockroach start --insecure --listen-addr=localhost:26258 --join=localhost:26258,localhost:26259,localhost:26260 --http-addr=localhost:8081 --store=cockroach-data-1
```

```bash
 2254.0s        0          113.9          120.9     31.5     71.3     92.3    109.1 transfer
 2255.0s        0          116.1          120.9     33.6     60.8     71.3     75.5 transfer
 2256.0s        0           24.0          120.8     28.3     54.5     75.5     75.5 transfer
 2257.0s        0            0.0          120.8      0.0      0.0      0.0      0.0 transfer
 2258.0s        0            0.0          120.7      0.0      0.0      0.0      0.0 transfer
 2259.0s        0            0.0          120.7      0.0      0.0      0.0      0.0 transfer
 2260.0s        0            0.0          120.6      0.0      0.0      0.0      0.0 transfer
_elapsed___errors__ops/sec(inst)___ops/sec(cum)__p50(ms)__p95(ms)__p99(ms)_pMax(ms)
 2261.0s        0            5.0          120.6     10.5   5905.6   5905.6   5905.6 transfer
Error: pq: result is ambiguous: error=ba: Put [/Table/106/1/790/0], [txn: 857cd75d], [protect-ambiguous-replay] RPC error: grpc: grpc: the client connection is closing [code 1/Canceled] [exhausted] (last error: failed to connect to n4 at localhost:26261: initial connection heartbeat failed: grpc: connection error: desc = "transport: error while dialing: dial tcp 127.0.0.1:26261: connect: connection refused" [code 14/Unavailable])
```

Bringing up Node 2 revives the cluster:

```bash
cockroach start --insecure --listen-addr=localhost:26259 --join=localhost:26258,localhost:26259,localhost:26260 --http-addr=localhost:8082 --store=cockroach-data-2 --background
```

Bringing Node 3 back up restores full replication:

```bash
cockroach start --insecure --listen-addr=localhost:26260 --join=localhost:26258,localhost:26259,localhost:26260 --http-addr=localhost:8083 --store=cockroach-data-3 --background
```

The workload generator appears to have died once it lost connection to the cluster.

Cleanup:

```bash
cockroach sql --insecure
```

```sql
DROP DATABASE bank CASCADE;
```

## Alternative Workload Generation

```bash
pgbench
```

On Ubuntu 20.04, it can be installed (without the Postgres server):

```bash
sudo apt-get install postgresql-contrib
```

```bash
pgbench --version
pgbench (PostgreSQL) 14.11 (Ubuntu 14.11-0ubuntu0.22.04.1)
```

Some helpful references:

- https://medium.com/@c.ucanefe/pgbench-load-test-166bdfb5c75a
- https://dzone.com/articles/using-pgbench-with-cockroachdb-serverless


First, create a new database from the SQL shell:

```sql
CREATE DATABASE example;
```

Then initialize the new database. `pgbench` will create new table(s). Below, the scale factor tells `pgbench` to create 50 times as many rows.

```bash
pgbench --host=localhost --port=26257 --user=root --initialize --no-vacuum example
```

Output:

```bash
dropping old tables...
creating tables...
NOTICE:  storage parameter "fillfactor" is ignored
NOTICE:  storage parameter "fillfactor" is ignored
NOTICE:  storage parameter "fillfactor" is ignored
generating data (client-side)...
100000 of 100000 tuples (100%) done (elapsed 0.10 s, remaining 0.00 s)
creating primary keys...
done in 18.80 s (drop tables 0.50 s, create tables 0.15 s, client-side generate 5.76 s, primary keys 12.39 s).
```

The database can be scaled to have more rows in the tables:

```bash
pgbench --host=localhost --port=26257 --user=root --initialize --no-vacuum --scale=5 example
```

```bash
pgbench --host=localhost --port=26257 --user=root --log --client=2 --jobs=5 --transactions=1000 example
```

Output:

```bash
pgbench (14.11 (Ubuntu 14.11-0ubuntu0.22.04.1), server 13.0.0)
transaction type: <builtin: TPC-B (sort of)>
scaling factor: 5
query mode: simple
number of clients: 2
number of threads: 2
number of transactions per client: 1000
number of transactions actually processed: 2000/2000
latency average = 83.161 ms
initial connection time = 1.959 ms
tps = 24.049677 (without initial connection time)
```

Cleanup:

```sql
DROP DATABASE example CASCADE;
```

## Data Collection Application

```sql
CREATE DATABASE takehome;
```

```bash
uvicorn main:app --host 0.0.0.0 --port 9000 --reload
INFO:     Will watch for changes in these directories: ['/Users/31aas586/git/cockroach-demo']
INFO:     Uvicorn running on http://0.0.0.0:9000 (Press CTRL+C to quit)
INFO:     Started reloader process [84911] using StatReload
INFO:     Started server process [84913]
INFO:     Waiting for application startup.
DEBUG     Created stations table: status message: CREATE TABLE
DEBUG     Created datapoints table: status message: CREATE TABLE
INFO:     Application startup complete.
```

Verify that the tables have been created:

```sql
USE takehome;
SHOW TABLES;
```

```bash
schema_name | table_name | type  | owner | estimated_row_count | locality
--------------+------------+-------+-------+---------------------+-----------
  public      | datapoints | table | root  |                   0 | NULL
  public      | stations   | table | root  |                   0 | NULL
(2 rows)
```

```sql
SHOW COLUMNS FROM stations;
```

```bash
  column_name | data_type | is_nullable |  column_default   | generation_expression |           indices            | is_hidden
--------------+-----------+-------------+-------------------+-----------------------+------------------------------+------------
  id          | UUID      |      f      | gen_random_uuid() |                       | {index_region,stations_pkey} |     f
  region      | STRING    |      f      | NULL              |                       | {index_region,stations_pkey} |     f
(2 rows)
```

```sql
SHOW COLUMNS FROM datapoints;
```

```bash
  column_name | data_type | is_nullable | column_default | generation_expression |  indices  | is_hidden
--------------+-----------+-------------+----------------+-----------------------+-----------+------------
  at          | TIMESTAMP |      f      | NULL           |                       | {primary} |     f
  station     | UUID      |      f      | NULL           |                       | {primary} |     f
  param0      | INT8      |      t      | NULL           |                       | {primary} |     f
  param1      | INT8      |      t      | NULL           |                       | {primary} |     f
  param2      | FLOAT8    |      t      | NULL           |                       | {primary} |     f
  param3      | FLOAT8    |      t      | NULL           |                       | {primary} |     f
  param4      | STRING    |      t      | NULL           |                       | {primary} |     f
(7 rows)
```

In a browser, open the following URL:

```bash
http://localhost:9000/docs
```

From this OpenAPI screen, we can run some basic operations, such as adding data stations and logging data points.


List all registered stations:

```bash
python3 src/client/station.py --url http://localhost:9000 list
```

Simulate data points sent from the stations in a given region:

```bash
python3 src/client/station.py --url http://localhost:9000 generate --region US-East
```

### Multi-Region Cluster
This application has been designed to experiment with multi-region clusters. The Enterprise Edition is required for such as setup. The following SQL would be used to enable multiple regions (to be tested):

```sql
ALTER DATABASE takehome PRIMARY REGION "US-East";
ALTER DATABASE takehome ADD REGION "US-West";
ALTER DATABASE takehome ADD REGION "EU-Central";
ALTER DATABASE takehome ADD REGION "US-Mountain";
```

```sql
ALTER TABLE stations SET locality GLOBAL;
```

```sql
ALTER TABLE datapoints SET LOCALITY REGIONAL BY ROW AS "region";
```


## Running the API with Docker Compose

Build the Docker images:

```bash
docker build -t datapoint-haproxy -f Dockerfile.haproxy .
```

```bash
docker build -t datapoint-api -f Dockerfile.api .
```
