package browser

import (
	"database/sql"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"

	_ "modernc.org/sqlite"
)

// HistoryRecord representa uma entrada do historico de navegacao
type HistoryRecord struct {
	Browser      string `json:"browser"`
	Profile      string `json:"profile"`
	URL          string `json:"url"`
	Title        string `json:"title"`
	VisitCount   int    `json:"visit_count"`
	TypedCount   int    `json:"typed_count"`
	LastVisitUTC string `json:"last_visit_utc"`
}

// DownloadRecord representa um registro de download forense
type DownloadRecord struct {
	Browser       string `json:"browser"`
	Profile       string `json:"profile"`
	TargetFile    string `json:"target_file"`
	URL           string `json:"url"`
	ReceivedBytes int64  `json:"received_bytes"`
	TotalBytes    int64  `json:"total_bytes"`
	State         string `json:"state"` // "COMPLETE", "CANCELLED", "INTERRUPTED"
	StartTimeUTC  string `json:"start_time_utc"`
	EndTimeUTC    string `json:"end_time_utc,omitempty"`
}

// webkitTimeToUTC converte timestamp de microssegundos desde 01/01/1601 para RFC3339
func webkitTimeToUTC(webkitTime int64) string {
	if webkitTime <= 0 {
		return ""
	}
	// Diferenca em microssegundos entre 1601-01-01 e 1970-01-01
	unixEpochMicro := (webkitTime - 11644473600000000)
	if unixEpochMicro < 0 {
		return ""
	}
	t := time.Unix(unixEpochMicro/1000000, (unixEpochMicro%1000000)*1000)
	return t.UTC().Format(time.RFC3339)
}

// ExtractChromiumHistory extrai o historico de URLs e visitas contornando locks e transmitindo via callback
func ExtractChromiumHistory(
	browserName string,
	userDataPath string,
	onRecord func(record HistoryRecord),
) (int, error) {
	tempDir, err := os.MkdirTemp("", "forenselab_history_*")
	if err != nil {
		return 0, fmt.Errorf("falha ao criar pasta temporaria: %w", err)
	}
	defer os.RemoveAll(tempDir)

	entries, err := os.ReadDir(userDataPath)
	if err != nil {
		return 0, fmt.Errorf("falha ao ler User Data: %w", err)
	}

	totalExtracted := 0

	for _, entry := range entries {
		if !entry.IsDir() {
			continue
		}
		profileName := entry.Name()
		if profileName != "Default" && !strings.HasPrefix(profileName, "Profile") {
			continue
		}

		historyPath := filepath.Join(userDataPath, profileName, "History")
		if _, err := os.Stat(historyPath); os.IsNotExist(err) {
			continue
		}

		// Copia arquivo de Historico contornando locks de navegadores ativos
		copiedDB, err := ForenseFileCopy(historyPath, tempDir)
		if err != nil {
			continue
		}

		db, err := sql.Open("sqlite", copiedDB)
		if err != nil {
			_ = os.Remove(copiedDB)
			continue
		}

		query := `
			SELECT url, title, visit_count, typed_count, last_visit_time
			FROM urls
			ORDER BY last_visit_time DESC
		`
		rows, err := db.Query(query)
		if err != nil {
			db.Close()
			_ = os.Remove(copiedDB)
			continue
		}

		for rows.Next() {
			var (
				url           string
				title         string
				visitCount    int
				typedCount    int
				lastVisitTime int64
			)
			if err := rows.Scan(&url, &title, &visitCount, &typedCount, &lastVisitTime); err == nil {
				rec := HistoryRecord{
					Browser:      browserName,
					Profile:      profileName,
					URL:          url,
					Title:        title,
					VisitCount:   visitCount,
					TypedCount:   typedCount,
					LastVisitUTC: webkitTimeToUTC(lastVisitTime),
				}
				totalExtracted++
				if onRecord != nil {
					onRecord(rec)
				}
			}
		}

		rows.Close()
		db.Close()
		_ = os.Remove(copiedDB)
	}

	return totalExtracted, nil
}

// ExtractChromiumDownloads extrai o registro de downloads com lock bypass emitindo os itens via callback
func ExtractChromiumDownloads(
	browserName string,
	userDataPath string,
	onRecord func(record DownloadRecord),
) (int, error) {
	tempDir, err := os.MkdirTemp("", "forenselab_downloads_*")
	if err != nil {
		return 0, fmt.Errorf("falha ao criar pasta temporaria: %w", err)
	}
	defer os.RemoveAll(tempDir)

	entries, err := os.ReadDir(userDataPath)
	if err != nil {
		return 0, fmt.Errorf("falha ao ler User Data: %w", err)
	}

	totalExtracted := 0

	for _, entry := range entries {
		if !entry.IsDir() {
			continue
		}
		profileName := entry.Name()
		if profileName != "Default" && !strings.HasPrefix(profileName, "Profile") {
			continue
		}

		historyPath := filepath.Join(userDataPath, profileName, "History")
		if _, err := os.Stat(historyPath); os.IsNotExist(err) {
			continue
		}

		copiedDB, err := ForenseFileCopy(historyPath, tempDir)
		if err != nil {
			continue
		}

		db, err := sql.Open("sqlite", copiedDB)
		if err != nil {
			_ = os.Remove(copiedDB)
			continue
		}

		// A tabela downloads do Chromium mapeia status: 1=COMPLETE, 2=CANCELLED, 3=INTERRUPTED
		query := `
			SELECT target_path, tab_url, received_bytes, total_bytes, state, start_time, end_time
			FROM downloads
			ORDER BY start_time DESC
		`
		rows, err := db.Query(query)
		if err != nil {
			db.Close()
			_ = os.Remove(copiedDB)
			continue
		}

		for rows.Next() {
			var (
				targetPath    string
				tabURL        string
				receivedBytes int64
				totalBytes    int64
				stateInt      int
				startTime     int64
				endTime       int64
			)
			if err := rows.Scan(&targetPath, &tabURL, &receivedBytes, &totalBytes, &stateInt, &startTime, &endTime); err == nil {
				stateStr := "UNKNOWN"
				switch stateInt {
				case 1:
					stateStr = "COMPLETE"
				case 2:
					stateStr = "CANCELLED"
				case 3:
					stateStr = "INTERRUPTED"
				}

				rec := DownloadRecord{
					Browser:       browserName,
					Profile:       profileName,
					TargetFile:    targetPath,
					URL:           tabURL,
					ReceivedBytes: receivedBytes,
					TotalBytes:    totalBytes,
					State:         stateStr,
					StartTimeUTC:  webkitTimeToUTC(startTime),
					EndTimeUTC:    webkitTimeToUTC(endTime),
				}
				totalExtracted++
				if onRecord != nil {
					onRecord(rec)
				}
			}
		}

		rows.Close()
		db.Close()
		_ = os.Remove(copiedDB)
	}

	return totalExtracted, nil
}
