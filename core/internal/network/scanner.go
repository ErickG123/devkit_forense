package network

import (
	"context"
	"time"
)

// ScannerAPI consolida a interface de varredura forense de rede (Port Scan e Ping Sweep)
type ScannerAPI struct{}

// NewScanner cria uma nova instância de ScannerAPI
func NewScanner() *ScannerAPI {
	return &ScannerAPI{}
}

// ScanPorts executa o TCP Connect Scan sem privilégios administrativos
func (s *ScannerAPI) ScanPorts(
	target string,
	ports []int,
	workers int,
	timeout time.Duration,
	onProgress func(percent float64, msg string, completed, total int),
) []PortResult {
	return ScanPorts(target, ports, workers, timeout, onProgress)
}

// PingSweep executa o ping sweep concorrente em range de rede
func (s *ScannerAPI) PingSweep(
	ips []string,
	workers int,
	timeout time.Duration,
	onProgress func(percent float64, msg string, completed, total int),
) []HostResult {
	return PingSweep(ips, workers, timeout, onProgress)
}

// ScanPortsWithContext permite cancelamento gracioso via contexto
func (s *ScannerAPI) ScanPortsWithContext(
	ctx context.Context,
	target string,
	ports []int,
	workers int,
	timeout time.Duration,
	onProgress func(percent float64, msg string, completed, total int),
) ([]PortResult, error) {
	// Wrapper resiliente utilizando ScanPorts
	doneChan := make(chan []PortResult, 1)
	go func() {
		doneChan <- ScanPorts(target, ports, workers, timeout, onProgress)
	}()

	select {
	case <-ctx.Done():
		return nil, ctx.Err()
	case res := <-doneChan:
		return res, nil
	}
}
