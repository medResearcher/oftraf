[![Build Status](https://travis-ci.org/intracom-telecom-sdn/oftraf.svg)](https://travis-ci.org/intracom-telecom-sdn/oftraf)
[![Code Health](https://landscape.io/github/intracom-telecom-sdn/oftraf/master/landscape.svg?style=flat)](https://landscape.io/github/intracom-telecom-sdn/oftraf/master)
[![Docker Automated build](https://img.shields.io/docker/automated/jrottenberg/ffmpeg.svg?maxAge=2592000)](https://hub.docker.com/r/intracom/oftraf/)
[![Code Issues](https://www.quantifiedcode.com/api/v1/project/8e2065e3b1854903895c4745f7a3b829/badge.svg)](https://www.quantifiedcode.com/app/project/8e2065e3b1854903895c4745f7a3b829)



# oftraf

pcap-based, RESTful OpenFlow traffic monitor

Filters OpenFlow packets from a network interface and reports statistics.

Features:

- **Summary and detailed OF statistics in real-time**: summary statistics refer to
  total incoming and outgoing OF traffic (from the viewpoint of the SDN
  controller). Detailed statistics offer a finer-grain breakdown based on the OF
  message type. Both classes are being updated and displayed in real-time.
- Support for **OF1.0 and OF1.3 protocols**
- **REST interface** for accessing statistics. This enables remote online
  monitoring of a controller's incoming and outgoing OF traffic.
- Non-intrusive to the controller

# Requirements

- Python 2
- `pypcap`, `dpkt` and `bottle` Python packages

On an Ubuntu-based machine, install the required packages as follows:

```bash
sudo apt-get install python-pypcap python-dpkt python-bottle
```

# Usage

```bash
sudo python oftraf.py --rest-host <host> --rest-port <port> --of-port <ofport> --ifname <interface> [--server]
```

Command line arguments:

- `--rest-host`: the IP or hostname of the interface the REST server should listen to
- `--rest-port`: the port the REST server should listen to
- `--of-port`: the OpenFlow port number based on which packet filtering will take place
- `--ifname`: the network interface to sniff packets from
- `--server`: run `oftraf` as server only without printing stats

Example:

1. Launch an SDN controller and a Mininet topology on the same machine
2. Launch `oftraf`:
  ```bash
  sudo python oftraf.py --rest-host localhost --rest-port 5555 --of-port 6653 --ifname lo
  ```
  This starts sniffing and counting OF packets on the `lo` interface. The statistics are
  being displayed in real-time in a curses-based console which refreshes every 1 second.
  Sample output:

```
Elapsed seconds:89.1658
OF in pps:                49.0
OF in Bps:             27532.0
OF out pps:               29.0
OF out Bps:            16000.0

Packet Type                           Count          Bytes
--------------------------------------------------------------
Total OF in:                          9807           4275930
Total OF out:                         5282           3328935

Incoming
----------------
OF13_OFPT_ECHO_REQUEST:               6              360
OF13_OFPT_ERROR:                      10             800
OF13_OFPT_FEATURES_REPLY:             10             840
OF13_OFPT_HELLO:                      10             680
OF13_OFPT_MULTIPART_REPLY:            6424           2061320
OF13_OFPT_PACKET_IN:                  508            89560
OF13_OFPT_PORT_STATUS:                26             3432
OF10_OFPT_ECHO_REQUEST:               9              540
OF10_OFPT_ERROR:                      4              288
OF10_OFPT_FEATURES_REPLY:             10             1512
OF10_OFPT_HELLO:                      10             600
OF10_OFPT_PACKET_IN:                  284            43054
OF10_OFPT_PORT_STATUS:                81             9396
OF10_OFPT_STATS_REPLY:                648            200048

Outgoing
----------------
OF13_OFPT_ECHO_REPLY:                 6              360
OF13_OFPT_FEATURES_REQUEST:           7              420
OF13_OFPT_HELLO:                      14             1024
OF13_OFPT_MULTIPART_REQUEST:          1301           1159444
OF13_OFPT_PACKET_OUT:                 153            57012
OF13_OFPT_SET_CONFIG:                 11             992
OF10_OFPT_ECHO_REPLY:                 9              540
OF10_OFPT_FEATURES_REQUEST:           6              360
OF10_OFPT_HELLO:                      7              428
OF10_OFPT_PACKET_OUT:                 47             11515
OF10_OFPT_SET_CONFIG:                 11             704
OF10_OFPT_STATS_REQUEST:              100            92344
```

  **OF in** and **OF out** refer to OF traffic traveling into and out of the SDN controller,
  respectively. **pps** and **Bps** are packets-per-second and bytes-per-second.

3. The REST server starts together with `oftraf`. Let's try to send some statistics requests.

  On another console, issue the following REST request to access summary statistics:
  ```bash
  curl  http://localhost:5555/get_of_counts
  ```
  Response:

  ```json
  {
    "OF_out_counts": [366417, 114676077],
    "OF_in_counts": [700581, 212923343]
  }
  ```
  In each statistic returned, the first number (e.g. 366417) is the packet count, and the
  second (114676077) is the byte count.

  `OF_out_counts` refers to the packets travelling from the controller to the
  switches, `OF_in_counts` refers to the packets travelling at the opposite
  direction.

  To access detailed OF13 statistics, issue the following REST request:

  ```bash
  curl http://localhost:5555/get_of13_counts
  ```

  Response:

  ```json
  {
    "OF13_in_counts":
    {
      "OFPT_ERROR": [10, 800],
      "OFPT_PORT_STATUS": [82, 10824],
      "OFPT_MULTIPART_REPLY": [107, 28276],
      "OFPT_FEATURES_REPLY": [10, 840],
      "OFPT_HELLO": [10, 680],
      "OFPT_PACKET_IN": [216, 38324],
      "OFPT_ECHO_REQUEST": [10, 600]
    },
    "OF13_out_counts":
    {
      "OFPT_PACKET_OUT": [35, 7201],
      "OFPT_FEATURES_REQUEST": [7, 420],
      "OFPT_MULTIPART_REQUEST": [17, 8240],
      "OFPT_SET_CONFIG": [9, 1332],
      "OFPT_HELLO": [11, 788],
      "OFPT_ECHO_REPLY": [10, 600]
    }
}
  ```

  Similarly, use the following REST request for OF10 statistics:

  ```bash
  curl http://localhost:5555/get_of10_counts
  ```

4. To stop `oftraf`, hit Ctrl-C in the console where it runs, or issue a
   REST request as follows:

   ```bash
   $ curl  http://localhost:5555/stop
   ```

# Deployment of Docker containers

This project provides two options for deployment with the use of Docker
Containers

- Deploy locally, using a `Dockerfile`
- Deploy using a prebuild image from [Docker Hub](https://hub.docker.com/u/intracom/)

In both cases, the [docker](https://www.docker.com/) platform must be installed
on the host side.

- essential tool: [docker](https://docs.docker.com/engine/installation/) (v.1.12.1 or later)

and the actions below have to be followed

- Give non-root access to docker daemon
    * Add the docker group if it doesn't already exist sudo groupadd docker
    * Add the connected user "${USER}" to the docker group. Change the user name to
match your preferred user
    ```bash
    sudo gpasswd -a ${USER} docker
    ```
    * Restart the Docker daemon:
    ```bash
    sudo service docker restart
    ```
## Deploy using Dockerfile

There are 2 different folders, containing `Dockerfiles`,
under the path `<PROJECT_DIR>/deploy`. The one `Dockerfile`
is for a `proxy` environment and one is for a `no_proxy` environment. The
names of the folders containing these `Dockerfiles` are `proxy` and `no_proxy`
respectively.

in order to deploy the `proxy` `Dockerfile` (`<PROJECT_DIR>/deploy/proxy/Dockerfile`),
edit the proxy settings in the file. These settings are in the following lines.

```bash
ENV http_proxy="http://<proxy_ip>:<port>/"
ENV https_proxy="http://<proxy_ip>:<port>/"

RUN echo 'Acquire::http::Proxy "http://<proxy_ip>:<port>/";' | tee -a /etc/apt/apt.conf
RUN echo 'Acquire::https::Proxy "http://<proxy_ip>:<port>/";'| tee -a /etc/apt/apt.conf

RUN echo "http_proxy=http://<proxy_ip>:<port>/" | tee -a /etc/environment
RUN echo "https_proxy=http://<proxy_ip>:<port>/" | tee -a /etc/environment
RUN echo "no_proxy=127.0.0.1,localhost" | tee -a /etc/environment
RUN echo "HTTP_PROXY=http://<proxy_ip>:<port>/" | tee -a /etc/environment
RUN echo "HTTPS_PROXY=http://<proxy_ip>:<port>/" | tee -a /etc/environment
RUN echo "NO_PROXY=127.0.0.1,localhost" | tee -a /etc/environment

```

After configuring the proxy settings, from the path of `Dockerfile`, run the command

```bash
docker build -t oftraf_base .
```

The above command would be the first step in case we deploy a `no_proxy` docker
environment.

Verify that the image has been built successfully by running the command

```bash
  docker images
  ```

the output of this command should look like the following sample

```bash
REPOSITORY         TAG             IMAGE ID          CREATED           SIZE
<repo_name>        oftraf_base     c2c3152907b5      4 minutes ago     275.1 MB
```

to run the environment and start the `Docker container`, execute the following line

```bash
docker run -it <repo_name>:oftraf_base /bin/bash
```

and enter the password

```bash
password: root123
```

After the above step we get a console inside the docker environment and `oftraf`
can be executed with the following command

```bash
/opt/oftraf/start.sh <host_ip> <rest_server_port> <port_to_monitor_for_OpenFlow_messages>
```

or alternatively, activate the virtual environment

```bash
source /opt/venv_oftraf/bin/activate
```

and follow the [Usage](https://github.com/intracom-telecom-sdn/oftraf#usage)
section.

## Deploy using prebuild image

The first step is to get the image from [Docker Hub](https://hub.docker.com/u/intracom/)

```bash
docker pull intracom/nstat-sdn-controllers
```
Once the image pull operation is complete, check locally the existence of the
image

```bash
docker images
```
which should list the ``intracom/nstat-sdn-controllers:latest`` image.  For
running a container out of the ```intracom/nstat-sdn-controllers:latest``` image

```
docker run -it intracom/nstat-sdn-controllers /bin/bash
```

``password: root123``

Run `oftraf` as described in the previous section after starting the `Docker container`.

# Future Extensions

- more efficient OF packet filtering utilizing BPF filters
- breakdown of certain OF message types to finer-grain subtypes (e.g. multipart replies)
- graphical client dashboard
