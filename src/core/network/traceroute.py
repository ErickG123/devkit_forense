import platform
import subprocess
import re

def traceroute_host(ip: str):
    system = platform.system()
    if system == "Windows":
        cmd = ["tracert", "-d", ip]
    else:
        cmd = ["traceroute", "-n", ip]

    result = subprocess.run(cmd, capture_output=True, text=True)
    lines = result.stdout.splitlines()
    hops = []

    for line in lines[1:]:
        if system == "Windows":
            match = re.search(r"^\s*(\d+)\s+([\d<]+ ms)\s+([\d<]+ ms)\s+([\d<]+ ms)\s+([\d.]+)", line)
            if match:
                hop = int(match.group(1))
                rtt_values = []
                for g in match.groups()[1:4]:
                    g_clean = g.replace("ms", "").replace("<", "").strip()
                    try:
                        rtt_values.append(float(g_clean))
                    except:
                        pass
                rtt = sum(rtt_values) / len(rtt_values) if rtt_values else None
                ip_hop = match.group(5)
                hops.append({"hop": hop, "ip": ip_hop, "rtt": rtt})
        else:
            parts = line.split()
            if len(parts) >= 2 and parts[0].isdigit():
                hop = int(parts[0])
                ip_hop = parts[1]
                rtt_values = [float(x) for x in parts[2:] if re.match(r"\d+\.?\d*", x)]
                rtt = sum(rtt_values)/len(rtt_values) if rtt_values else None
                hops.append({"hop": hop, "ip": ip_hop, "rtt": rtt})

    return hops
