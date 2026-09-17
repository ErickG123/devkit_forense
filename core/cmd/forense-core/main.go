package main

import (
	"fmt"
	"os"
	"time"

	"github.com/ErickG123/devkit_forense/core/internal/browser"
	"github.com/ErickG123/devkit_forense/core/internal/ipc"
	"github.com/ErickG123/devkit_forense/core/internal/network"
)

func main() {
	startTime := time.Now()

	// Filtra as flags globais --debug e --benchmark
	debugEnabled := false
	benchmarkEnabled := false
	filteredArgs := make([]string, 0, len(os.Args))
	for _, arg := range os.Args {
		if arg == "--debug" {
			debugEnabled = true
		} else if arg == "--benchmark" {
			benchmarkEnabled = true
		} else {
			filteredArgs = append(filteredArgs, arg)
		}
	}
	os.Args = filteredArgs
	ipc.BenchmarkEnabled = benchmarkEnabled

	auditLogger := ipc.InitAuditLogger(debugEnabled)
	if auditLogger != nil {
		defer auditLogger.Close()
		defer auditLogger.RecoverWithStackTrace()
	}

	if len(os.Args) < 2 {
		ipc.OutputError(
			"unknown",
			"ERR_MISSING_COMMAND",
			"Nenhum comando fornecido. Uso: forense-core <mock|scan|sweep|browser-logins|browser-history|browser-downloads> [args]",
			0,
			1,
		)
	}

	command := os.Args[1]
	args := os.Args[2:]

	if auditLogger != nil {
		auditLogger.Log("COMMAND_DISPATCH", fmt.Sprintf("Executando subcomando: %s", command))
	}

	switch command {
	case "mock":
		ipc.RunMockTask(command, args, startTime)

	case "scan", "net-scan":
		network.RunScanTask(command, args, startTime)

	case "sweep", "net-sweep":
		network.RunSweepTask(command, args, startTime)

	case "browser-logins":
		browser.RunLoginsTask(command, args, startTime)

	case "browser-history":
		browser.RunHistoryTask(command, args, startTime)

	case "browser-downloads":
		browser.RunDownloadsTask(command, args, startTime)

	default:
		ipc.OutputError(
			command,
			"ERR_UNKNOWN_COMMAND",
			fmt.Sprintf("Comando '%s' não reconhecido pelo núcleo Go.", command),
			time.Since(startTime).Milliseconds(),
			1,
		)
	}
}
