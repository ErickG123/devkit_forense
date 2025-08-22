from scapy.all import ARP, Ether, srp, conf

def ping_sweep(network):
    conf.verb = 0
    pkt = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=network)
    ans, _ = srp(pkt, timeout=2)
    ativos = [rcv[ARP].psrc for _, rcv in ans]
    return ativos
