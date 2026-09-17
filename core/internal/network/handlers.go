package network

import (
	"flag"
	"fmt"
	"time"

	"github.com/ErickG123/devkit_forense/core/internal/ipc"
)

// RunScanTask gerencia argumentos e execucao do TCP Port Scan
func RunScanTask(command string, args []string, startTime time.Time) {
	scanFlags := flag.NewFlagSet("scan", flag.ContinueOnError)
	target := scanFlags.String("target", "", "Alvo (IP ou hostname)")
	portSpec := scanFlags.String("ports", "21,22,53,80,443,445,3306,8080", "Portas para escanear")
	workers := scanFlags.Int("workers", 500, "Numero de workers paralelos")
	timeoutMs := scanFlags.Int("timeout", 1000, "Timeout por porta em milissegundos")

	if err := scanFlags.Parse(args); err != nil || *target == "" {
		ipc.OutputError(
			command,
			"ERR_INVALID_ARGS",
			"Parametro --target obrigatorio. Exemplo: forense-core scan --target 192.168.1.1 --ports 80,443",
			time.Since(startTime).Milliseconds(),
			1,
		)
	}

	ports, err := ParsePorts(*portSpec)
	if err != nil {
		ipc.OutputError(
			command,
			"ERR_INVALID_PORTS",
			fmt.Sprintf("Erro ao processar portas: %v", err),
			time.Since(startTime).Milliseconds(),
			1,
		)
	}

	ipc.EmitProgress(fmt.Sprintf("Iniciando varredura em %s (%d portas)...", *target, len(ports)), 0.0, 0, len(ports))

	openPorts := ScanPorts(
		*target,
		ports,
		*workers,
		time.Duration(*timeoutMs)*time.Millisecond,
		func(percent float64, msg string, completed, total int) {
			ipc.EmitProgress(msg, percent, completed, total)
		},
	)

	duration := time.Since(startTime).Milliseconds()

	ipc.OutputSuccess(command, map[string]interface{}{
		"target":        *target,
		"scanned_ports": len(ports),
		"open_ports":    openPorts,
		"total_open":    len(openPorts),
	}, duration)
}

// RunSweepTask gerencia argumentos e execucao do Ping Sweep unprivileged
func RunSweepTask(command string, args []string, startTime time.Time) {
	sweepFlags := flag.NewFlagSet("sweep", flag.ContinueOnError)
	netSpec := sweepFlags.String("network", "", "Range de rede (CIDR ou intervalo: 192.168.1.1-254)")
	workers := sweepFlags.Int("workers", 100, "Numero de workers paralelos")
	timeoutMs := sweepFlags.Int("timeout", 400, "Timeout de probe por host em milissegundos")

	if err := sweepFlags.Parse(args); err != nil || *netSpec == "" {
		ipc.OutputError(
			command,
			"ERR_INVALID_ARGS",
			"Parametro --network obrigatorio. Exemplo: forense-core sweep --network 192.168.1.0/24",
			time.Since(startTime).Milliseconds(),
			1,
		)
	}

	ips, err := ParseNetworkRange(*netSpec)
	if err != nil {
		ipc.OutputError(
			command,
			"ERR_INVALID_NETWORK",
			fmt.Sprintf("Erro ao interpretar rede: %v", err),
			time.Since(startTime).Milliseconds(),
			1,
		)
	}

	ipc.EmitProgress(fmt.Sprintf("Iniciando descoberta em %d hosts...", len(ips)), 0.0, 0, len(ips))

	activeHosts := PingSweep(
		ips,
		*workers,
		time.Duration(*timeoutMs)*time.Millisecond,
		func(percent float64, msg string, completed, total int) {
			ipc.EmitProgress(msg, percent, completed, total)
		},
	)

	duration := time.Since(startTime).Milliseconds()

	ipc.OutputSuccess(command, map[string]interface{}{
		"network":       *netSpec,
		"total_scanned": len(ips),
		"active_hosts":  activeHosts,
		"total_active":  len(activeHosts),
	}, duration)
}
