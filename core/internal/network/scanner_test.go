package network

import (
	"net"
	"testing"
	"time"
)

// TestScannerWithLocalTCPListener valida a detecção com listener local sem internet
func TestScannerWithLocalTCPListener(t *testing.T) {
	// Listener TCP efêmero local
	l, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("Erro ao iniciar listener de teste: %v", err)
	}
	defer l.Close()

	openPort := l.Addr().(*net.TCPAddr).Port

	go func() {
		for {
			conn, err := l.Accept()
			if err != nil {
				return
			}
			conn.Close()
		}
	}()

	scanner := NewScanner()
	closedPort := openPort + 1
	ports := []int{openPort, closedPort}

	results := scanner.ScanPorts("127.0.0.1", ports, 2, 200*time.Millisecond, nil)

	if len(results) != 1 {
		t.Fatalf("Esperava 1 porta aberta, obteve %d", len(results))
	}

	if results[0].Port != openPort {
		t.Errorf("Porta detectada incorreta: %d (esperada: %d)", results[0].Port, openPort)
	}
}
