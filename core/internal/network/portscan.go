package network

import (
	"bufio"
	"fmt"
	"net"
	"sort"
	"strconv"
	"strings"
	"sync"
	"sync/atomic"
	"time"
)

// PortResult representa o resultado de uma porta escaneada
type PortResult struct {
	Port      int    `json:"port"`
	Protocol  string `json:"protocol"`
	State     string `json:"state"` // "open"
	Service   string `json:"service"`
	Banner    string `json:"banner,omitempty"`
	LatencyMs int64  `json:"latency_ms"`
}

// Mapa de serviços conhecidos
var commonServices = map[int]string{
	21:    "ftp",
	22:    "ssh",
	23:    "telnet",
	25:    "smtp",
	53:    "dns",
	80:    "http",
	110:   "pop3",
	111:   "rpcbind",
	135:   "msrpc",
	139:   "netbios-ssn",
	143:   "imap",
	443:   "https",
	445:   "microsoft-ds",
	993:   "imaps",
	995:   "pop3s",
	1433:  "ms-sql-s",
	1521:  "oracle",
	3306:  "mysql",
	3389:  "ms-wbt-server",
	5432:  "postgresql",
	5900:  "vnc",
	6379:  "redis",
	8080:  "http-proxy",
	8443:  "https-alt",
	27017: "mongodb",
}

// ParsePorts converte formatos como '80', '22,80,443' ou '1-1024' em uma slice ordenada
func ParsePorts(portSpec string) ([]int, error) {
	portMap := make(map[int]bool)
	parts := strings.Split(portSpec, ",")

	for _, part := range parts {
		part = strings.TrimSpace(part)
		if part == "" {
			continue
		}

		if strings.Contains(part, "-") {
			rangeParts := strings.Split(part, "-")
			if len(rangeParts) != 2 {
				return nil, fmt.Errorf("intervalo de portas inválido: '%s'", part)
			}
			start, err1 := strconv.Atoi(strings.TrimSpace(rangeParts[0]))
			end, err2 := strconv.Atoi(strings.TrimSpace(rangeParts[1]))
			if err1 != nil || err2 != nil || start < 1 || end > 65535 || start > end {
				return nil, fmt.Errorf("faixa de portas fora do limite (1-65535): '%s'", part)
			}
			for p := start; p <= end; p++ {
				portMap[p] = true
			}
		} else {
			p, err := strconv.Atoi(part)
			if err != nil || p < 1 || p > 65535 {
				return nil, fmt.Errorf("porta inválida (1-65535): '%s'", part)
			}
			portMap[p] = true
		}
	}

	if len(portMap) == 0 {
		return nil, fmt.Errorf("nenhuma porta especificada")
	}

	ports := make([]int, 0, len(portMap))
	for p := range portMap {
		ports = append(ports, p)
	}
	sort.Ints(ports)
	return ports, nil
}

// grabBanner tenta ler um cabeçalho ou banner inicial com timeout curto
func grabBanner(target string, port int, timeout time.Duration) string {
	addr := net.JoinHostPort(target, strconv.Itoa(port))
	conn, err := net.DialTimeout("tcp", addr, timeout)
	if err != nil {
		return ""
	}
	defer conn.Close()

	_ = conn.SetDeadline(time.Now().Add(timeout))

	// Para HTTP/HTTPS enviamos probe simples
	if port == 80 || port == 8080 {
		_, _ = fmt.Fprintf(conn, "HEAD / HTTP/1.0\r\nHost: %s\r\n\r\n", target)
	} else if port == 21 || port == 25 || port == 110 {
		// Serviços com banner inicial imediato
	}

	reader := bufio.NewReader(conn)
	line, err := reader.ReadString('\n')
	if err == nil {
		clean := strings.TrimSpace(line)
		if len(clean) > 80 {
			clean = clean[:77] + "..."
		}
		return clean
	}
	return ""
}

// ScanPorts executa o TCP Connect Scan orquestrado por um worker pool
func ScanPorts(
	target string,
	ports []int,
	workers int,
	timeout time.Duration,
	onProgress func(percent float64, msg string, completed, total int),
) []PortResult {
	if workers <= 0 {
		workers = 500
	}
	if workers > len(ports) {
		workers = len(ports)
	}
	if workers > 1000 {
		workers = 1000 // Limite seguro para não estourar File Descriptors
	}

	total := len(ports)
	jobs := make(chan int, total)
	resultsChan := make(chan PortResult, total)

	var wg sync.WaitGroup
	var completedCount uint32

	// Inicializa os workers
	for w := 0; w < workers; w++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for port := range jobs {
				addr := net.JoinHostPort(target, strconv.Itoa(port))
				start := time.Now()

				// TCP Connect sem privilégios
				conn, err := net.DialTimeout("tcp", addr, timeout)
				latency := time.Since(start).Milliseconds()

				if err == nil {
					conn.Close()

					service, ok := commonServices[port]
					if !ok {
						service = "unknown"
					}

					// Banner grabbing rápido (max 400ms)
					banner := grabBanner(target, port, 400*time.Millisecond)

					resultsChan <- PortResult{
						Port:      port,
						Protocol:  "tcp",
						State:     "open",
						Service:   service,
						Banner:    banner,
						LatencyMs: latency,
					}
				}

				done := atomic.AddUint32(&completedCount, 1)
				if onProgress != nil {
					// Emite progresso a cada lote ou no final
					if done%25 == 0 || int(done) == total {
						pct := (float64(done) / float64(total)) * 100.0
						msg := fmt.Sprintf("Escaneando porta %d (%d/%d)...", port, done, total)
						onProgress(pct, msg, int(done), total)
					}
				}
			}
		}()
	}

	// Enfileira todas as portas
	for _, p := range ports {
		jobs <- p
	}
	close(jobs)

	// Aguarda os workers e fecha os resultados
	wg.Wait()
	close(resultsChan)

	var openPorts []PortResult
	for r := range resultsChan {
		openPorts = append(openPorts, r)
	}

	// Ordena portas abertas
	sort.Slice(openPorts, func(i, j int) bool {
		return openPorts[i].Port < openPorts[j].Port
	})

	return openPorts
}
