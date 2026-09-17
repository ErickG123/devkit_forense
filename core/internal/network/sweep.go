package network

import (
	"errors"
	"fmt"
	"net"
	"strconv"
	"strings"
	"sync"
	"sync/atomic"
	"time"
)

// HostResult representa um host ativo identificado
type HostResult struct {
	IP        string `json:"ip"`
	Status    string `json:"status"` // "ONLINE"
	Method    string `json:"method"` // "tcp-ack" | "tcp-rst"
	Port      int    `json:"port,omitempty"`
	LatencyMs int64  `json:"latency_ms"`
}

// Portas estratégicas para detecção forense rápida sem privilégios
var discoveryPorts = []int{445, 80, 443, 135, 139, 22, 3389, 53, 8080}

// ParseNetworkRange converte formatos CIDR (192.168.1.0/24) ou faixas (192.168.1.1-254) em lista de IPs
func ParseNetworkRange(networkSpec string) ([]string, error) {
	networkSpec = strings.TrimSpace(networkSpec)

	// Caso 1: CIDR (ex: 192.168.1.0/24)
	if strings.Contains(networkSpec, "/") {
		ip, ipnet, err := net.ParseCIDR(networkSpec)
		if err != nil {
			return nil, fmt.Errorf("formato CIDR inválido: %w", err)
		}

		var ips []string
		for current := cloneIP(ip.Mask(ipnet.Mask)); ipnet.Contains(current); incrementIP(current) {
			ips = append(ips, current.String())
		}

		// Remove endereço de rede e broadcast em redes IPv4 típicas (/24, etc)
		if len(ips) > 2 && ip.To4() != nil {
			return ips[1 : len(ips)-1], nil
		}
		return ips, nil
	}

	// Caso 2: Notação Range (ex: 192.168.1.1-254)
	if strings.Contains(networkSpec, "-") {
		lastDot := strings.LastIndex(networkSpec, ".")
		if lastDot == -1 {
			return nil, fmt.Errorf("formato de range inválido: '%s'", networkSpec)
		}
		baseIP := networkSpec[:lastDot]
		rangePart := networkSpec[lastDot+1:]
		rangeParts := strings.Split(rangePart, "-")
		if len(rangeParts) != 2 {
			return nil, fmt.Errorf("intervalo inválido após o ponto: '%s'", rangePart)
		}

		start, err1 := strconv.Atoi(rangeParts[0])
		end, err2 := strconv.Atoi(rangeParts[1])
		if err1 != nil || err2 != nil || start < 0 || end > 255 || start > end {
			return nil, fmt.Errorf("octeto final fora do limite (0-255): '%s'", rangePart)
		}

		var ips []string
		for i := start; i <= end; i++ {
			ipStr := fmt.Sprintf("%s.%d", baseIP, i)
			if net.ParseIP(ipStr) == nil {
				return nil, fmt.Errorf("IP gerado inválido: %s", ipStr)
			}
			ips = append(ips, ipStr)
		}
		return ips, nil
	}

	// Caso 3: IP individual
	if net.ParseIP(networkSpec) != nil {
		return []string{networkSpec}, nil
	}

	return nil, fmt.Errorf("alvo de rede inválido: '%s'. Use formato CIDR (192.168.1.0/24) ou Range (192.168.1.1-254)", networkSpec)
}

func cloneIP(ip net.IP) net.IP {
	dup := make(net.IP, len(ip))
	copy(dup, ip)
	return dup
}

func incrementIP(ip net.IP) {
	for j := len(ip) - 1; j >= 0; j-- {
		ip[j]++
		if ip[j] > 0 {
			break
		}
	}
}

// probeHost verifica se um host está vivo conectando em portas comuns
// Utiliza o fato de que portas fechadas que respondem com TCP RST comprovam host vivo no nível IP
func probeHost(ip string, timeout time.Duration) *HostResult {
	for _, port := range discoveryPorts {
		addr := net.JoinHostPort(ip, strconv.Itoa(port))
		start := time.Now()
		conn, err := net.DialTimeout("tcp", addr, timeout)
		latency := time.Since(start).Milliseconds()

		if err == nil {
			conn.Close()
			return &HostResult{
				IP:        ip,
				Status:    "ONLINE",
				Method:    "tcp-ack",
				Port:      port,
				LatencyMs: latency,
			}
		}

		// Checa se recebeu conexão recusada (RST packet do alvo)
		var opErr *net.OpError
		if errors.As(err, &opErr) && opErr.Err != nil {
			errStr := strings.ToLower(opErr.Err.Error())
			if strings.Contains(errStr, "refused") || strings.Contains(errStr, "recusada") {
				return &HostResult{
					IP:        ip,
					Status:    "ONLINE",
					Method:    "tcp-rst",
					Port:      port,
					LatencyMs: latency,
				}
			}
		}
	}

	return nil
}

// PingSweep executa a descoberta paralela de hosts vivos sem exigir root/admin
func PingSweep(
	ips []string,
	workers int,
	probeTimeout time.Duration,
	onProgress func(percent float64, msg string, completed, total int),
) []HostResult {
	if workers <= 0 {
		workers = 100
	}
	if workers > len(ips) {
		workers = len(ips)
	}

	total := len(ips)
	jobs := make(chan string, total)
	resultsChan := make(chan *HostResult, total)

	var wg sync.WaitGroup
	var completedCount uint32

	for w := 0; w < workers; w++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for ip := range jobs {
				res := probeHost(ip, probeTimeout)
				if res != nil {
					resultsChan <- res
				}

				done := atomic.AddUint32(&completedCount, 1)
				if onProgress != nil {
					if done%10 == 0 || int(done) == total {
						pct := (float64(done) / float64(total)) * 100.0
						msg := fmt.Sprintf("Verificando host %s (%d/%d)...", ip, done, total)
						onProgress(pct, msg, int(done), total)
					}
				}
			}
		}()
	}

	for _, ip := range ips {
		jobs <- ip
	}
	close(jobs)

	wg.Wait()
	close(resultsChan)

	var activeHosts []HostResult
	for h := range resultsChan {
		if h != nil {
			activeHosts = append(activeHosts, *h)
		}
	}

	return activeHosts
}
