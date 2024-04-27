# Cockroach DB Demo

## Cluster Setup

AWS EC2 instance running Ubuntu 22.04

### HAProxy configuration

Copy file `setup/haproxy.cf` to `/etc/haproxy` directory and start HAProxy service:

```bash
$ systemctl restart haproxy
```

Verify that port 8080 and 26257 are up:

```bash
$ ss -antpl | grep 8080
LISTEN 0      4096         0.0.0.0:8080       0.0.0.0:*
```

```bash
$ ss -antpl | grep 26257
LISTEN 0      4096         0.0.0.0:26257      0.0.0.0:* 
```

### Create 3-node CockroachDB cluster

The nodes in the cluster should be serving on ports `26258`, `26259`, etc. and the admin console on ports `8081`, `8082`, etc. Nodes use directories names `cockroach-data-1`, `cockroach-data-2`, etc. respectively.

```bash
$ cockroach start --insecure --listen-addr=localhost:26258 --join=localhost:26258,localhost:26259,localhost:26260 --http-addr=localhost:8081 --store=cockroach-data-1 --background
```

```bash
$ cockroach start --insecure --listen-addr=localhost:26259 --join=localhost:26258,localhost:26259,localhost:26260 --http-addr=localhost:8082 --store=cockroach-data-2 --background
```

```bash
$ cockroach start --insecure --listen-addr=localhost:26260 --join=localhost:26258,localhost:26259,localhost:26260 --http-addr=localhost:8083 --store=cockroach-data-3 --background
```

```bash
$ cockroach start --insecure --listen-addr=localhost:26261 --join=localhost:26258,localhost:26259,localhost:26260 --http-addr=localhost:8084 --store=cockroach-data-4 --background
```

```bash
$ cockroach start --insecure --listen-addr=localhost:26262 --join=localhost:26258,localhost:26259,localhost:26260 --http-addr=localhost:8085 --store=cockroach-data-5 --background
```

Verify that the proxy is routing the traffic as expected:

```bash
$ ss -antpl | grep 808
LISTEN 0      4096       127.0.0.1:8081       0.0.0.0:*    users:(("cockroach",pid=1105,fd=33))
LISTEN 0      4096       127.0.0.1:8083       0.0.0.0:*    users:(("cockroach",pid=1141,fd=66))
LISTEN 0      4096       127.0.0.1:8082       0.0.0.0:*    users:(("cockroach",pid=1123,fd=69))
LISTEN 0      4096         0.0.0.0:8080       0.0.0.0:*
```

```bash
$ ss -antpl | grep 26
LISTEN 0      4096       127.0.0.1:26259      0.0.0.0:*    users:(("cockroach",pid=1123,fd=70))
LISTEN 0      4096       127.0.0.1:26258      0.0.0.0:*    users:(("cockroach",pid=1105,fd=43))
LISTEN 0      4096       127.0.0.1:26260      0.0.0.0:*    users:(("cockroach",pid=1141,fd=67))
LISTEN 0      4096         0.0.0.0:26257      0.0.0.0:*
```

```bash
$ tail -f /var/log/haproxy.log
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

## Graceful Shutdown



```bash
$ cockroach node decomission 5 --insecure
```

```bash
cockroach node recommission 5 --insecure
```


```bash
$ ps auxwww|grep cockroach
$ kill <pid>
```

```bash
$ cockroach start --insecure --listen-addr=localhost:26262 --join=localhost:26258,localhost:26259,localhost:26260 --http-addr=localhost:8085 --store=cockroach-data-5 --background
```


```bash
$ uvicorn main:app --host 0.0.0.0 --port 9000 --reload
```
