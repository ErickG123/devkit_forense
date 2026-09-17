package network

import (
	"net"
	"reflect"
	"testing"
	"time"
)

// TestParsePorts valida o parsing de especificações de portas (Table-Driven Test)
func TestParsePorts(t *testing.T) {
	tests := []struct {
		name      string
		input     string
		expected  []int
		expectErr bool
	}{
		{"Porta unica", "80", []int{80}, false},
		{"Multiplas portas e duplicadas", "443, 80, 443, 22", []int{22, 80, 443}, false},
		{"Intervalo valido", "80-83", []int{80, 81, 82, 83}, false},
		{"Misto com espacos", "21, 80-82, 443", []int{21, 80, 81, 82, 443}, false},
		{"Porta invalida (fora do limite)", "70000", nil, true},
		{"Intervalo invertido", "100-50", nil, true},
		{"String nao numerica", "http,ssh", nil, true},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := ParsePorts(tt.input)
			if (err != nil) != tt.expectErr {
				t.Fatalf("ParsePorts(%q) error = %v, expectErr %v", tt.input, err, tt.expectErr)
			}
			if !tt.expectErr && !reflect.DeepEqual(got, tt.expected) {
				t.Errorf("ParsePorts(%q) = %v, esperado %v", tt.input, got, tt.expected)
			}
		})
	}
}

// TestScanPortsWorkerPoolWithLocalListener valida o Worker Pool sem abrir sockets externos
func TestScanPortsWorkerPoolWithLocalListener(t *testing.T) {
	// 1. Cria um servidor TCP local de teste
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("Falha ao criar listener de teste: %v", err)
	}
	defer listener.Close()

	// Obtem a porta real alocada dinamicamente pelo SO
	openPort := listener.Addr().(*net.TCPAddr).Port

	// Goroutine para aceitar probes de conexao
	go func() {
		for {
			conn, err := listener.Accept()
			if err != nil {
				return
			}
			conn.Close()
		}
	}()

	closedPort := openPort + 1
	portsToTest := []int{openPort, closedPort}

	progressCalls := 0
	progressCallback := func(percent float64, msg string, completed, total int) {
		progressCalls++
	}

	// 2. Executa o ScanPorts com pool controlado
	results := ScanPorts("127.0.0.1", portsToTest, 2, 200*time.Millisecond, progressCallback)

	// 3. Assercoes
	if len(results) != 1 {
		t.Fatalf("Esperava exatamente 1 porta aberta, obteve %d", len(results))
	}

	if results[0].Port != openPort {
		t.Errorf("Porta identificada incorreta: obteve %d, esperava %d", results[0].Port, openPort)
	}

	if results[0].State != "open" {
		t.Errorf("Estado incorreto: %s", results[0].State)
	}

	if progressCalls == 0 {
		t.Errorf("Callback de progresso nao foi acionado")
	}
}
