# alternator-demo

This will provision a 5 node ScyllaDB cluster with the Alternator port `8000` enabled. It will also install ScyllaDB monitoring and a python node to run the test scripts.

## Deploy

To deploy the cluster, use 

```
❯ docker compose up -d
[+] Running 12/12
 ✔ Network alternator-demo_public  Cre...                                  0.0s
 ✔ Container promtail              Started                                 0.3s
 ✔ Container pyhost                Started                                 0.4s
 ✔ Container aprom                 Started                                 0.3s
 ✔ Container loki                  Started                                 0.3s
 ✔ Container agraf                 Started                                 0.4s
 ✔ Container aalert                Started                                 0.2s
 ✔ Container node1                 Started                                 0.2s
 ✔ Container node5                 Started                                 0.4s
 ✔ Container node2                 Started                                 0.4s
 ✔ Container node4                 Started                                 0.3s
 ✔ Container node3                 Started                                 0.3s
 ```

 ### Verify

 ```
 ❯ docker container  ls
CONTAINER ID   IMAGE                       COMMAND                  CREATED              STATUS                        PORTS                                                            NAMES
688585e09979   scylladb/scylla:latest      "/docker-entrypoint.…"   About a minute ago   Up About a minute (healthy)   22/tcp, 7000-7001/tcp, 9042/tcp, 9160/tcp, 9180/tcp, 10000/tcp   node5
0d9f542398c3   scylladb/scylla:latest      "/docker-entrypoint.…"   About a minute ago   Up About a minute (healthy)   22/tcp, 7000-7001/tcp, 9042/tcp, 9160/tcp, 9180/tcp, 10000/tcp   node2
e92618db5d79   scylladb/scylla:latest      "/docker-entrypoint.…"   About a minute ago   Up About a minute (healthy)   22/tcp, 7000-7001/tcp, 9042/tcp, 9160/tcp, 9180/tcp, 10000/tcp   node3
58465ea36d22   scylladb/scylla:latest      "/docker-entrypoint.…"   About a minute ago   Up About a minute (healthy)   22/tcp, 7000-7001/tcp, 9042/tcp, 9160/tcp, 9180/tcp, 10000/tcp   node4
d4c9c5b5801f   prom/prometheus:v2.51.1     "/bin/prometheus --c…"   About a minute ago   Up About a minute             0.0.0.0:9090->9090/tcp                                           aprom
eb93ae25d16e   grafana/grafana:10.4.1      "/run.sh"                About a minute ago   Up About a minute             0.0.0.0:3000->3000/tcp                                           agraf
31899e591b3c   grafana/promtail:2.7.3      "/usr/bin/promtail -…"   About a minute ago   Up About a minute             0.0.0.0:1514->1514/tcp, 0.0.0.0:9080->9080/tcp                   promtail
2be52a205981   prom/alertmanager:v0.26.0   "/bin/alertmanager -…"   About a minute ago   Up About a minute             0.0.0.0:9093->9093/tcp                                           aalert
483c48755230   alternator-demo-python      "tail -f /dev/null"      About a minute ago   Up About a minute                                                                              pyhost
d542c387d875   scylladb/scylla:latest      "/docker-entrypoint.…"   About a minute ago   Up About a minute (healthy)   22/tcp, 7000-7001/tcp, 9042/tcp, 9160/tcp, 9180/tcp, 10000/tcp   node1
```

Verify the cluster status

```
❯ docker container exec -it node1 nodetool status
Datacenter: datacenter1
=======================
Status=Up/Down
|/ State=Normal/Leaving/Joining/Moving
-- Address         Load      Tokens Owns Host ID                              Rack
UN 192.168.100.101 766.76 KB 256    ?    cc972040-7456-45e3-9b6d-6bbf2a767a66 rack1
UN 192.168.100.102 766.36 KB 256    ?    311a5b24-7cc4-4862-ab75-f37b1297c95d rack1
UN 192.168.100.103 733.16 KB 256    ?    cb7b9fcc-bece-48c6-baff-2aa4492b00e5 rack1
UN 192.168.100.104 768.19 KB 256    ?    e728fb34-cf28-4f9a-a788-eafedbe47432 rack1
UN 192.168.100.105 759.92 KB 256    ?    18b02533-7fa0-4623-8430-ea10da29b3ef rack1

Note: Non-system keyspaces don't have the same replication settings, effective ownership information is meaningless
```

### Monitoring

Access the monitoring page by `http://localhost:3000` and then go to the dashboard from the left `hamburger` menu.

### Testing

Connect to the python container node

```
❯ docker container exec -it pyhost bash
root@pyhost:/scripts# ls -lrt
total 36
-rw-r--r-- 1 root root 8213 Oct 27 13:10 boto3_alternator.py
-rw-r--r-- 1 root root 6869 Oct 27 20:40 stress.py
-rw-r--r-- 1 root root 6341 Oct 28 10:26 ttl_test.py
-rw-r--r-- 1 root root 7925 Oct 28 10:28 alternator_crud.py
```

Python and dependencies are already installed and ready. Execute the `python alternator_crud.py` To execute the put_item workload. Modify the code to use the `boto3_alternator` wrapper that provides the high availability and load balancing. 

## Decommission

Once done testing, destroy the setup

```
❯ docker compose down
[+] Running 12/11
 ✔ Container node5                 Removed                                                                   2.6s
 ✔ Container promtail              Removed                                                                   0.2s
 ✔ Container node3                 Removed                                                                   2.6s
 ✔ Container aalert                Removed                                                                   0.2s
 ✔ Container agraf                 Removed                                                                   0.2s
 ✔ Container node2                 Removed                                                                   2.6s
 ✔ Container loki                  Removed                                                                   0.0s
 ✔ Container node4                 Removed                                                                   2.5s
 ✔ Container aprom                 Removed                                                                   0.3s
 ✔ Container pyhost                Removed                                                                  10.1s
 ✔ Container node1                 Removed                                                                  10.1s
 ✔ Network alternator-demo_public  Removed                                                                   0.0s
 ```

### Thank You!