package ipc

import (
	"flag"
	"fmt"
	"time"
)

// RunMockTask simula um processo pericial pesado com progresso NDJSON
func RunMockTask(command string, args []string, startTime time.Time) {
	mockFlags := flag.NewFlagSet("mock", flag.ContinueOnError)
	target := mockFlags.String("target", "localhost", "Alvo do teste mock")
	_ = mockFlags.Parse(args)

	steps := []struct {
		msg     string
		percent float64
		sleepMs int
	}{
		{msg: "Inicializando subsistema forense e alocando buffers...", percent: 10.0, sleepMs: 600},
		{msg: "Carregando módulos de análise e regras de extração...", percent: 30.0, sleepMs: 600},
		{msg: fmt.Sprintf("Iniciando varredura e coleta no alvo: %s...", *target), percent: 60.0, sleepMs: 600},
		{msg: "Processando artefatos e calculando integridade de hashes...", percent: 85.0, sleepMs: 600},
		{msg: "Finalizando extração e consolidando evidências...", percent: 100.0, sleepMs: 600},
	}

	totalSteps := len(steps)
	for i, s := range steps {
		EmitProgress(s.msg, s.percent, i+1, totalSteps)
		time.Sleep(time.Duration(s.sleepMs) * time.Millisecond)
	}

	duration := time.Since(startTime).Milliseconds()

	OutputSuccess(command, map[string]interface{}{
		"task":            "mock_simulation",
		"target":          *target,
		"items_processed": 150,
		"hash_sha256":     "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
		"status":          "COMPLETED_OK",
	}, duration)
}
