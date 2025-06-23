# **qBittorrent Super Seeding Automation (Dockerized)**

A lightweight Python script designed to automate qBittorrent's Super Seeding mode based on the number of available seeds on the torrent network.  
If seeds \== 1 , turn super seeding mode on  
If seeds \=> 2 , turn super seeding mode off

## **✨ Features**

* **Automated Super Seeding:** Automatically enables Super Seeding for torrents where you are the sole seed (total seeds \= 1).  
* **Automated Super Seeding Disablement:** Automatically disables Super Seeding when more seeds (total seeds 2 or more) become available on the network.  
* **Dockerized:** Runs in a Docker container for easy deployment, portability, and isolation.  
* **Configurable:** All parameters (qBittorrent host, port, credentials, polling interval) are set via environment variables.  
* **Clean Logging:** Only logs when an action is taken (enabling/disabling Super Seeding).

## **🚀 Getting Started**

### **Prerequisites**

Before you begin, ensure you have the following installed and configured:

* [**Docker**](https://www.docker.com/get-started): For running the container.  
* [**qBittorrent**](https://www.qbittorrent.org/): With the **Web UI enabled** and accessible.  
  * Go to qBittorrent Tools \> Options (or Preferences on macOS) \> Web UI.  
  * Check Enable Web User Interface (Remote Control).  
  * Note down the Listen port (default is often 8080 or 9090).  
  * If you set a Username and Password, you'll need them for the script.

### **1\. Run the Docker Container**

#### **For Linux Hosts (assuming qBittorrent is on the same host):**

You'll likely need `--network=host` to allow the container to access localhost on the docker host.  

### **DockerCLI**:
```sh
docker run -d \
--name=qbittorrent-autosuperseed \
--network=host \
  -e QB_HOST=localhost  \
  -e QB_PORT=8080  \
  -e QB_USERNAME=admin  \
  -e QB_PASSWORD=adminadmin  \
  -e POLLING_INTERVAL_SECONDS=120  \
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
            - QB_USERNAME=admin
            - QB_PASSWORD=adminadmin
            - POLLING_INTERVAL_SECONDS=120
        restart: unless-stopped
        image: ghcr.io/weeemrcb/qbittorrent-autosuperseed:latest

```

### 2\. Environment Variables:

|  Environment Variable | Default settings that can be overridden in the dockerfile |
| :---- | :---- |
| | |
| QB_HOST  | `localhost` |
| QB_PORT | `8080` |
| QB_USERNAME    |` ` |
| QB_PASSWORD    |` ` |
| POLLING_INTERVAL_SECONDS    | `120` [seconds] |
| | |
| | |



## **⚠️ Important Notes**

* **Seed Count Logic:** The script uses torrent\['num\_complete'\] from the qBittorrent API to determine the "seed number." This represents the *total number of available seeds on the network*, which is typically what we need for Super Seeding logic, as opposed to num\_seeds which is only the count of connected seeds.  
* **Credentials Security:** Always keep your qBittorrent username and password secure.

## **Contributing**

The tool is supplied as-is. Feel free to fork, open issues or submit pull requests if you have suggestions for improvements or encounter any bugs.

