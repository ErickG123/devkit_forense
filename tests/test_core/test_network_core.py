from network.port_scanner import parse_ports


def test_parse_ports():
    ports = parse_ports("22,80,100-102")
    assert 22 in ports
    assert 80 in ports
    assert 100 in ports
    assert 101 in ports
    assert 102 in ports
    assert len(ports) == 5
