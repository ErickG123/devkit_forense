# utils/converter.py
import json
import ipaddress
import html

def is_ip(addr: str) -> bool:
    try:
        ipaddress.ip_address(addr)
        return True
    except Exception:
        return False

def convert_hosts_to_graph(hosts):
    nodes = []
    edges = []
    nodes_map = {}

    def add_node(node_id, label=None, title=None, group="unknown", value=15, raw=None):
        node_id = str(node_id)
        if node_id in nodes_map:
            return
        node = {"id": node_id, "label": label or node_id, "title": title or "", "group": group, "value": value}
        if raw:
            node["raw"] = raw
        nodes.append(node)
        nodes_map[node_id] = node

    for item in hosts:
        ip = item.get("host") or item.get("ip") or item.get("address") or item.get("ipv4") or item.get("ip_address")
        if not ip:
            tr = item.get("traceroute") or item.get("trace") or item.get("hops")
            if isinstance(tr, list) and tr:
                for hop in reversed(tr):
                    if isinstance(hop, dict):
                        hopip = hop.get("ip") or hop.get("addr") or hop.get("address")
                        if hopip and is_ip(str(hopip)):
                            ip = hopip
                            break
                    elif isinstance(hop, str) and is_ip(hop):
                        ip = hop
                        break
        if not ip:
            continue
        ip = str(ip)

        hostname = item.get("hostname") or item.get("host_name") or item.get("name") or ""
        mac = item.get("mac") or item.get("mac_address") or ""
        vendor = item.get("vendor") or item.get("oui") or ""
        open_ports = item.get("open_ports") or item.get("ports") or []
        os_info = item.get("os_info") or {}
        os_name = os_info.get("os") if isinstance(os_info, dict) else ""
        ip_info = item.get("ip_info") or {}

        details = [f"IP: {html.escape(ip)}"]
        if hostname: details.append(f"Hostname: {html.escape(str(hostname))}")
        if mac: details.append(f"MAC: {html.escape(str(mac))}")
        if vendor: details.append(f"Vendor: {html.escape(str(vendor))}")
        if os_name: details.append(f"OS: {html.escape(str(os_name))}")
        if isinstance(open_ports, list) and open_ports:
            ports_summary = ", ".join(str(p) for p in open_ports[:8])
            details.append(f"Open ports: {html.escape(ports_summary)} ({len(open_ports)})")
        if isinstance(ip_info, dict) and ip_info:
            geo = ip_info.get("geo") or ip_info.get("country") or ip_info.get("region")
            if geo:
                details.append(f"IP info: {html.escape(str(geo))}")

        pretty_json = json.dumps(item, indent=2, ensure_ascii=False)
        html_title = "\n".join(details)

        size = 15 + min(30, int(len(open_ports)) * 2) if open_ports else 15

        group = "unknown"
        if os_name:
            on = os_name.lower()
            if "win" in on:
                group = "windows"
            elif "linux" in on:
                group = "linux"
            elif "android" in on:
                group = "android"
            elif "embedded" in on or "router" in on:
                group = "embedded"
            else:
                group = "other"

        add_node(ip, label=hostname or ip, title=html_title, group=group, value=size, raw=pretty_json)

        traceroute = item.get("traceroute") or item.get("trace") or []
        if isinstance(traceroute, list) and traceroute:
            prev = None
            for hop in traceroute:
                hop_ip = None
                if isinstance(hop, dict):
                    hop_ip = hop.get("ip") or hop.get("addr") or hop.get("address") or hop.get("host")
                elif isinstance(hop, str):
                    hop_ip = hop
                if not hop_ip:
                    continue
                hop_ip = str(hop_ip)
                if is_ip(hop_ip):
                    add_node(hop_ip, label=hop_ip, title=f"Hop: {html.escape(hop_ip)}", group="hop", value=10)
                    if prev and is_ip(prev):
                        edges.append({"from": prev, "to": hop_ip})
                    prev = hop_ip
            if prev and prev != ip:
                edges.append({"from": prev, "to": ip})

    if not edges and nodes:
        hub_candidates = ["192.168.0.1", "192.168.1.1", "10.0.0.1"]
        hub = next((c for c in hub_candidates if c in nodes_map), None)
        if not hub:
            hub = next(iter(nodes_map.keys()))
        for nid in nodes_map:
            if nid != hub:
                edges.append({"from": hub, "to": nid})

    return nodes, edges
