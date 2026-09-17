package ipc

import (
	"fmt"
	"os"
	"runtime/debug"
	"time"
)

// AuditLogger grava trilhas de troubleshooting e latência em arquivo oculto
type AuditLogger struct {
	file *os.File
}

// InitAuditLogger inicializa o logger forense se enabled for true
func InitAuditLogger(enabled bool) *AuditLogger {
	if !enabled {
		return nil
	}

	logFile, err := os.OpenFile("forense_debug.log", os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0600)
	if err != nil {
		return nil
	}

	logger := &AuditLogger{file: logFile}
	logger.Log("DEBUG_INIT", fmt.Sprintf("Sessao de auditoria iniciada (PID: %d)", os.Getpid()))
	return logger
}

func (l *AuditLogger) Log(event string, detail string) {
	if l == nil || l.file == nil {
		return
	}
	ts := time.Now().UTC().Format(time.RFC3339Nano)
	fmt.Fprintf(l.file, "[%s] [%s] %s\n", ts, event, detail)
	_ = l.file.Sync()
}

func (l *AuditLogger) LogLatency(operation string, start time.Time) {
	if l == nil || l.file == nil {
		return
	}
	elapsed := time.Since(start)
	l.Log("LATENCY", fmt.Sprintf("Operacao '%s' durou %v (%d ms)", operation, elapsed, elapsed.Milliseconds()))
}

func (l *AuditLogger) RecoverWithStackTrace() {
	if r := recover(); r != nil {
		if l != nil && l.file != nil {
			stack := debug.Stack()
			l.Log("CRITICAL_PANIC", fmt.Sprintf("Panic recuperado: %v\nStack Trace:\n%s", r, string(stack)))
			_ = l.file.Sync()
		}
		OutputError("panic", "ERR_INTERNAL_PANIC", fmt.Sprintf("Falha critica interna no Go Core: %v. Consulte 'forense_debug.log'.", r), 0, 2)
	}
}

func (l *AuditLogger) Close() {
	if l != nil && l.file != nil {
		l.Log("DEBUG_END", "Sessao de auditoria encerrada com sucesso.")
		_ = l.file.Close()
	}
}
