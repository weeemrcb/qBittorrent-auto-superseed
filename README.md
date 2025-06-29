# **qBittorrent Super Seeding Automation (Dockerized)**

A lightweight Python script designed to automate qBittorrent's Super Seeding mode based on the number of available seeds on the torrent network.  
If seeds \== 1 and leeches \>= 3, turn super seeding mode on  
else, turn super seeding mode off

## **✨ Features**

* **Automated Super Seeding:** Automatically enable Super Seeding for torrents where you are the sole seed and leechers are >=3  
* **Automated Super Seeding Disablement:** Automatically disables Super Seeding when there are more seeds  
* **Automated Choking Algorithm:** Toggle *Fastest Upload* or *Anti-Leech* when Super Seeding is on or off (may not work. QBT Version specific)
* **Configurable Threshold Values:** Users have the option to define their own trigger values
* **Clean Logging:** Only logs when an action is taken  

## **🚀 Getting Started**

### **Prerequisites**

Before you begin, ensure you have the following installed and configured:

* [**Docker**](https://www.docker.com/get-started): For running the container.  
* [**qBittorrent**](https://www.qbittorrent.org/): With the **Web UI enabled** and accessible.  
  * Go to qBittorrent Tools \> Options (or Preferences on macOS) \> Web UI.  
  * Check Enable Web User Interface (Remote Control) and note down the Listen port (default is often 8080 or 9090).  
  * If you set a Username and Password, you'll need them for the script.
  * Alternatively, if you set "Bypass authentication for clients in whitelisted IP subnets", you won't need any uname/password

### **1\. Run the Docker Container**

You'll likely need `--network=host` to allow the container to access localhost on the docker host.  

### **DockerCLI**:
```sh
docker run -d \
--name=qbittorrent-autosuperseed \
--network=host \
  -e QB_HOST=localhost  \
  -e QB_PORT=8080  \
  -e QB_USERNAME=MySecretUname  \
  -e QB_PASSWORD=MySecretPasswd  \
  -e POLLING_INTERVAL_SECONDS=120  \
  -e QB_SUPER_SEED_SEED_THRESHOLD=1 \
  -e QB_SUPER_SEED_LEECH_THRESHOLD=3 \
  -e QB_ENABLE_CHOKING_ALGORITHM_CONTROL=true \
--restart unless-stopped \
ghcr.io/weeemrcb/qbittorrent-autosuperseed:latest
```

### **Docker-Compose**:
```sh
name: qbittorrent-autosuperseed
services:
    qbittorrent-autosuperseed:
        container_name: qbittorrent-autosuperseed
        network_mode: host
        environment:
            - QB_HOST=localhost
            - QB_PORT=8080
            - QB_USERNAME=MySecretUname
            - QB_PASSWORD=MySecretPasswd
            - POLLING_INTERVAL_SECONDS=120
            - QB_SUPER_SEED_SEED_THRESHOLD=1
            - QB_SUPER_SEED_LEECH_THRESHOLD=3
            - QB_ENABLE_CHOKING_ALGORITHM_CONTROL=true
        restart: unless-stopped
        image: ghcr.io/weeemrcb/qbittorrent-autosuperseed:latest

```

### 2\. Environment Variables:

|  Environment Variable | Default settings that can be overridden in the dockerfile |
| :---- | :---- |
| | |
| QB_HOST  | `localhost` |
| QB_PORT | `8080` |
| QB_USERNAME    |`admin` |
| QB_PASSWORD    |`adminadmin` |
| POLLING_INTERVAL_SECONDS    | `120` [seconds] |
| QB_SUPER_SEED_SEED_THRESHOLD    | `1` |
| QB_SUPER_SEED_LEECH_THRESHOLD    | `3` |
| QB_ENABLE_CHOKING_ALGORITHM_CONTROL    | `false` [true\|false] |
| | |
| | |



## 🧠 **Container Logic**

**Seed Count Logic:**  
The script uses a torrent's \['num\_complete'\] from the qBittorrent API to determine the "seed number".  
This represents the *total number of available seeds on the network*, which is typically what is needed for Super Seeding logic, as opposed to \['num\_seeds'\] which is only the count of connected seeds.

## 📜 **Contributing**

The tool is supplied as-is and without warranty.  
Feel free to fork and update to make it your own.

