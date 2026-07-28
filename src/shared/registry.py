"""
Registro central de funcionalidades do ForenseLab.
Migrado de src/core/registry.py → src/shared/registry.py
"""

from network.network_map import run as run_network_map


def run_port_scanner_placeholder(*args, **kwargs):
    return {}


def run_chrome_history_placeholder(usuario=None, output_dir=None):
    return {}


def run_firefox_history_placeholder(usuario=None, output_dir=None):
    return {}


def run_edge_history_placeholder(usuario=None, output_dir=None):
    return {}


FUNCTIONALITIES = {
    "network_map": run_network_map,
    "port_scanner": run_port_scanner_placeholder,
    "chrome_history": run_chrome_history_placeholder,
    "firefox_history": run_firefox_history_placeholder,
    "edge_history": run_edge_history_placeholder,
}
