## An example of reduced bandwidth to share when using qBittorrent-auto-superseed

Example below showing a real world seeding session.  

___

Example uses default settings:  
```
POLLING_INTERVAL_SECONDS = 600
QB_SUPER_SEED_SEED_THRESHOLD = 1
QB_SUPER_SEED_LEECH_THRESHOLD = 3
```
## Sample logs from auto-superseed:  
> docker logs qbittorrent-autosuperseed  
```
Successfully logged into qBittorrent (or no authentication required).
Script started. Monitoring active torrents...

Super Seeding will be enabled if Total Seeds = 1 AND Leechers >= 3.
Automatic Choking Algorithm control is DISABLED.
Checking every 600 seconds.

[2026/02/28][09:33:26] (Seeders [1]~[3] Leechers) | Super Seeding ON: 'Family Holiday'
Successfully Enabled Super Seeding for torrent hash: f45628660a...
[2026/02/28][10:53:26] (Seeders [1]~[2] Leechers) | Super Seeding OFF: 'Family Holiday'
Successfully Disabled Super Seeding for torrent hash: f45628660a...
[2026/02/28][11:03:26] (Seeders [1]~[4] Leechers) | Super Seeding ON: 'Family Holiday'
Successfully Enabled Super Seeding for torrent hash: f45628660a...
[2026/02/28][11:53:26] (Seeders [3]~[2] Leechers) | Super Seeding OFF: 'Family Holiday'
Successfully Disabled Super Seeding for torrent hash: f45628660a...
```

Filtering the log for easier reading:  
> docker logs qbittorrent-autosuperseed | grep -i "~"   
```
[2026/02/28][09:33:26] (Seeders [1]~[3] Leechers) | Super Seeding ON: 'Family Holiday'
[2026/02/28][10:53:26] (Seeders [1]~[2] Leechers) | Super Seeding OFF: 'Family Holiday'
[2026/02/28][11:03:26] (Seeders [1]~[4] Leechers) | Super Seeding ON: 'Family Holiday'
[2026/02/28][11:53:26] (Seeders [3]~[2] Leechers) | Super Seeding OFF: 'Family Holiday'
```

In the logs we can see superseed toggle ON automatically for this share and, once the peers reach 100% and complete re-checking, they also seed which toggles superseed OFF.  

___

## UI data used/saved by using superseed

Total Peer percentage: **319.5%**  
Total Seed uploaded: **128%**  (irl less because I was slow to get screenshots)  

Peer #4 only needed 34mb from the seed source and pulled over 45% (6gb) of the torrent from the other peers.  

Sample 12Gb+ Seed  
<img width="975" height="55" alt="image" src="https://github.com/user-attachments/assets/c895f4e1-1e29-46cc-8db3-85f67249d49b" />

Connected Peers  
<img width="835" height="185" alt="image" src="https://github.com/user-attachments/assets/29742364-2c0b-44d7-a3e4-200f78253e7f" />

___

