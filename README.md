This is a fork of https://github.com/peterhoneder/pynetfilter_conntrack and works with the
latest Python 3 versions.

## Usage on Ubuntu
```bash
sudo modprobe nf_conntrack
sudo iptables -A INPUT -m conntrack --ctstate NEW,RELATED,ESTABLISHED -j ACCEPT
/bin/echo "1" | sudo tee /proc/sys/net/netfilter/nf_conntrack_acct
/bin/echo "1" | sudo tee /proc/sys/net/netfilter/nf_conntrack_timestamp
sudo apt install conntrack
```

### For non-root users
```bash
sudo setcap CAP_NET_ADMIN=ep /usr/sbin/conntrack
sudo setcap CAP_NET_ADMIN=ep $HOME/.pyenv/versions/3.11.1/bin/python3.11
```

## Links
https://stackoverflow.com/questions/27860646/how-to-use-pynetfilter-conntrack-library-of-python
https://github.com/sam-github/netfilter-lua
https://levelup.gitconnected.com/linux-kernel-tuning-for-high-performance-networking-5999a13b3fb4
