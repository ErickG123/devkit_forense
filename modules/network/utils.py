from scapy.all import ARP, Ether, srp
import socket
import requests

def get_mac(ip):
    pkt = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ip)
    ans, _ = srp(pkt, timeout=2, verbose=0)
    for _, rcv in ans:
        return rcv[Ether].src
    return None

def get_vendor(mac):
    if not mac:
        return "Desconhecido"
    try:
        resp = requests.get(f"https://api.macvendors.com/{mac}", timeout=3)
        if resp.status_code == 200:
            return resp.text
    except:
        return "Desconhecido"
    return "Desconhecido"

def get_hostname(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except:
        return "N/A"
