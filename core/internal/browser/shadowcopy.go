//go:build windows

package browser

import (
	"fmt"
	"os"
	"path/filepath"
)

// ForenseFileCopy contorna o lock exclusivo do Windows e copia arquivos SQLite e WALs para pasta temporária
func ForenseFileCopy(lockedFilePath string, destDir string) (string, error) {
	if destDir == "" {
		destDir = os.TempDir()
	}

	if err := os.MkdirAll(destDir, 0755); err != nil {
		return "", fmt.Errorf("falha ao criar diretorio de destino '%s': %w", destDir, err)
	}

	baseName := filepath.Base(lockedFilePath)
	destPath := filepath.Join(destDir, baseName)

	// Copia o arquivo principal contornando lock de compartilhamento
	if err := CopyFileLockBypass(lockedFilePath, destPath); err != nil {
		return "", fmt.Errorf("falha ao copiar arquivo travado '%s': %w", lockedFilePath, err)
	}

	// Copia arquivos Write-Ahead Log (WAL) e Shared Memory (SHM) se existirem
	walPath := lockedFilePath + "-wal"
	if _, err := os.Stat(walPath); err == nil {
		_ = CopyFileLockBypass(walPath, destPath+"-wal")
	}

	shmPath := lockedFilePath + "-shm"
	if _, err := os.Stat(shmPath); err == nil {
		_ = CopyFileLockBypass(shmPath, destPath+"-shm")
	}

	return destPath, nil
}
