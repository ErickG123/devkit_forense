//go:build !windows

package browser

import (
	"fmt"
	"os"
	"path/filepath"
)

// ForenseFileCopy para sistemas Unix-like
func ForenseFileCopy(lockedFilePath string, destDir string) (string, error) {
	if destDir == "" {
		destDir = os.TempDir()
	}

	if err := os.MkdirAll(destDir, 0755); err != nil {
		return "", fmt.Errorf("falha ao criar diretorio de destino '%s': %w", destDir, err)
	}

	baseName := filepath.Base(lockedFilePath)
	destPath := filepath.Join(destDir, baseName)

	if err := CopyFileLockBypass(lockedFilePath, destPath); err != nil {
		return "", fmt.Errorf("falha ao copiar arquivo '%s': %w", lockedFilePath, err)
	}

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
