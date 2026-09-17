package ipc

import (
	"encoding/json"
	"fmt"
	"os"
	"runtime"
	"time"
)

// BenchmarkEnabled indica se a coleta de métricas de memória/GC do runtime Go está ativa
var BenchmarkEnabled = false

// ProgressEvent define a estrutura estrita de NDJSON emitida no stderr
type ProgressEvent struct {
	Type        string  `json:"type"`                   // "progress" | "log"
	Msg         string  `json:"msg"`                    // Descricao textual amigavel
	Percent     float64 `json:"percent"`                // Percentual de 0 a 100
	PercentDone float64 `json:"percent_done,omitempty"` // Alias compativel
	Step        int     `json:"step,omitempty"`         // Passo atual
	Total       int     `json:"total,omitempty"`        // Total de passos
}

// ErrorDetail detalha erros ocorridos na execucao do Go core
type ErrorDetail struct {
	Code    string `json:"code"`
	Message string `json:"message"`
}

// ExecutionMetrics armazena metricas de uso de memoria e runtime para fins de benchmark (TCC/Pericia)
type ExecutionMetrics struct {
	AllocBytes      uint64 `json:"alloc_bytes"`
	TotalAllocBytes uint64 `json:"total_alloc_bytes"`
	SysBytes        uint64 `json:"sys_bytes"`
	NumGC           uint32 `json:"num_gc"`
}

// ResponseEnvelope define o contrato padrao retornado exclusivamente via stdout
type ResponseEnvelope struct {
	SchemaVersion string            `json:"schema_version"`
	Status        string            `json:"status"` // "success" | "error"
	Command       string            `json:"command"`
	Timestamp     string            `json:"timestamp"`
	DurationMs    int64             `json:"duration_ms"`
	Data          interface{}       `json:"data,omitempty"`
	Error         *ErrorDetail      `json:"error,omitempty"`
	Metrics       *ExecutionMetrics `json:"metrics,omitempty"`
}

// EmitProgress escreve um evento NDJSON no stderr garantindo flush de linha
func EmitProgress(msg string, percent float64, step, total int) {
	evt := ProgressEvent{
		Type:        "progress",
		Msg:         msg,
		Percent:     percent,
		PercentDone: percent,
		Step:        step,
		Total:       total,
	}

	payload, err := json.Marshal(evt)
	if err == nil {
		fmt.Fprintln(os.Stderr, string(payload))
	}
}

// EmitNDJSON escreve um registro de streaming no stdout seguido de quebra de linha
func EmitNDJSON(record interface{}) error {
	payload, err := json.Marshal(record)
	if err != nil {
		return err
	}
	_, err = fmt.Fprintln(os.Stdout, string(payload))
	return err
}

// OutputSuccess emite um envelope de sucesso com dados no stdout e encerra o processo com código 0
func OutputSuccess(command string, data interface{}, durationMs int64) {
	resp := ResponseEnvelope{
		SchemaVersion: "1.0",
		Status:        "success",
		Command:       command,
		Timestamp:     time.Now().UTC().Format(time.RFC3339),
		DurationMs:    durationMs,
		Data:          data,
	}
	OutputJSON(resp, 0)
}

// OutputError emite um envelope de erro estruturado no stdout e encerra com o codigo especificado
func OutputError(command string, code string, message string, durationMs int64, exitCode int) {
	resp := ResponseEnvelope{
		SchemaVersion: "1.0",
		Status:        "error",
		Command:       command,
		Timestamp:     time.Now().UTC().Format(time.RFC3339),
		DurationMs:    durationMs,
		Error: &ErrorDetail{
			Code:    code,
			Message: message,
		},
	}
	OutputJSON(resp, exitCode)
}

// OutputJSON serializa o envelope no stdout com indentacao e encerra a aplicacao
func OutputJSON(resp ResponseEnvelope, exitCode int) {
	if BenchmarkEnabled {
		var m runtime.MemStats
		runtime.ReadMemStats(&m)
		resp.Metrics = &ExecutionMetrics{
			AllocBytes:      m.Alloc,
			TotalAllocBytes: m.TotalAlloc,
			SysBytes:        m.Sys,
			NumGC:           m.NumGC,
		}
	}
	encoder := json.NewEncoder(os.Stdout)
	encoder.SetIndent("", "  ")
	_ = encoder.Encode(resp)
	os.Exit(exitCode)
}
