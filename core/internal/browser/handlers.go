package browser

import (
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"runtime"
	"time"

	"github.com/ErickG123/devkit_forense/core/internal/ipc"
)

type browserSpec struct {
	Name     string
	UserData string
}

func resolveTargets(browserTarget string) []browserSpec {
	localAppData := os.Getenv("LOCALAPPDATA")
	if localAppData == "" {
		localAppData = filepath.Join(os.Getenv("USERPROFILE"), "AppData", "Local")
	}

	chromePath := filepath.Join(localAppData, "Google", "Chrome", "User Data")
	edgePath := filepath.Join(localAppData, "Microsoft", "Edge", "User Data")

	var targets []browserSpec
	switch browserTarget {
	case "chrome":
		targets = append(targets, browserSpec{Name: "Google Chrome", UserData: chromePath})
	case "edge":
		targets = append(targets, browserSpec{Name: "Microsoft Edge", UserData: edgePath})
	default:
		targets = append(targets,
			browserSpec{Name: "Google Chrome", UserData: chromePath},
			browserSpec{Name: "Microsoft Edge", UserData: edgePath},
		)
	}
	return targets
}

// RunLoginsTask extrai credenciais de navegadores Chromium emitindo JSON ou NDJSON
func RunLoginsTask(command string, args []string, startTime time.Time) {
	loginFlags := flag.NewFlagSet("browser-logins", flag.ContinueOnError)
	browserTarget := loginFlags.String("browser", "all", "Navegador alvo: 'chrome', 'edge' ou 'all'")
	streamJSONL := loginFlags.Bool("jsonl", false, "Emitir credenciais como streaming JSONL no stdout")
	streamNDJSON := loginFlags.Bool("ndjson", false, "Emitir credenciais como streaming NDJSON no stdout")

	if err := loginFlags.Parse(args); err != nil {
		ipc.OutputError(command, "ERR_INVALID_ARGS", fmt.Sprintf("Parametros invalidos: %v", err), time.Since(startTime).Milliseconds(), 1)
	}

	if runtime.GOOS != "windows" {
		ipc.OutputError(command, "ERR_UNSUPPORTED_OS", "Extracao DPAPI de Chromium disponivel apenas no Windows.", time.Since(startTime).Milliseconds(), 1)
	}

	targets := resolveTargets(*browserTarget)
	var allCreds []LoginCredential
	totalTargets := len(targets)
	isStream := *streamJSONL || *streamNDJSON

	for i, t := range targets {
		ipc.EmitProgress(
			fmt.Sprintf("Extraindo credenciais de %s...", t.Name),
			(float64(i)/float64(totalTargets))*100.0,
			i+1,
			totalTargets,
		)

		if _, err := os.Stat(t.UserData); os.IsNotExist(err) {
			continue
		}

		creds, err := ExtractChromiumLogins(t.Name, t.UserData, func(cred LoginCredential) {
			if isStream {
				_ = ipc.EmitNDJSON(cred)
			}
		})
		if err == nil {
			allCreds = append(allCreds, creds...)
		}
	}

	duration := time.Since(startTime).Milliseconds()
	ipc.EmitProgress("Extracao de credenciais concluida.", 100.0, totalTargets, totalTargets)

	if !isStream {
		ipc.OutputSuccess(command, map[string]interface{}{
			"total_credentials": len(allCreds),
			"credentials":       allCreds,
		}, duration)
	}
}

// RunHistoryTask extrai historico com lock-bypass
func RunHistoryTask(command string, args []string, startTime time.Time) {
	histFlags := flag.NewFlagSet("browser-history", flag.ContinueOnError)
	browserTarget := histFlags.String("browser", "all", "Navegador alvo: 'chrome', 'edge' ou 'all'")
	streamNDJSON := histFlags.Bool("ndjson", true, "Emitir historico em streaming NDJSON no stdout")

	_ = histFlags.Parse(args)

	targets := resolveTargets(*browserTarget)
	totalTargets := len(targets)
	var allRecords []HistoryRecord

	for i, t := range targets {
		ipc.EmitProgress(
			fmt.Sprintf("Extraindo historico de %s...", t.Name),
			(float64(i)/float64(totalTargets))*100.0,
			i+1,
			totalTargets,
		)

		if _, err := os.Stat(t.UserData); os.IsNotExist(err) {
			continue
		}

		_, _ = ExtractChromiumHistory(t.Name, t.UserData, func(rec HistoryRecord) {
			if *streamNDJSON {
				_ = ipc.EmitNDJSON(rec)
			} else {
				allRecords = append(allRecords, rec)
			}
		})
	}

	ipc.EmitProgress("Extracao de historico finalizada.", 100.0, totalTargets, totalTargets)

	if !*streamNDJSON {
		ipc.OutputSuccess(command, map[string]interface{}{
			"total_history": len(allRecords),
			"records":       allRecords,
		}, time.Since(startTime).Milliseconds())
	}
}

// RunDownloadsTask extrai downloads com lock-bypass
func RunDownloadsTask(command string, args []string, startTime time.Time) {
	dlFlags := flag.NewFlagSet("browser-downloads", flag.ContinueOnError)
	browserTarget := dlFlags.String("browser", "all", "Navegador alvo: 'chrome', 'edge' ou 'all'")
	streamNDJSON := dlFlags.Bool("ndjson", true, "Emitir downloads em streaming NDJSON no stdout")

	_ = dlFlags.Parse(args)

	targets := resolveTargets(*browserTarget)
	totalTargets := len(targets)
	var allRecords []DownloadRecord

	for i, t := range targets {
		ipc.EmitProgress(
			fmt.Sprintf("Extraindo downloads de %s...", t.Name),
			(float64(i)/float64(totalTargets))*100.0,
			i+1,
			totalTargets,
		)

		if _, err := os.Stat(t.UserData); os.IsNotExist(err) {
			continue
		}

		_, _ = ExtractChromiumDownloads(t.Name, t.UserData, func(rec DownloadRecord) {
			if *streamNDJSON {
				_ = ipc.EmitNDJSON(rec)
			} else {
				allRecords = append(allRecords, rec)
			}
		})
	}

	ipc.EmitProgress("Extracao de downloads finalizada.", 100.0, totalTargets, totalTargets)

	if !*streamNDJSON {
		ipc.OutputSuccess(command, map[string]interface{}{
			"total_downloads": len(allRecords),
			"records":         allRecords,
		}, time.Since(startTime).Milliseconds())
	}
}
