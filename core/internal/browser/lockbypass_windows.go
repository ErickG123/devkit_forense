//go:build windows

package browser

import (
	"fmt"
	"io"
	"os"

	"golang.org/x/sys/windows"
)

// OpenFileShareAll abre um arquivo no Windows permitindo leitura mesmo que outro processo
// (como o Google Chrome ou Microsoft Edge) mantenha um lock exclusivo ativo.
//
// Utiliza a flag Win32:
// FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE (0x1 | 0x2 | 0x4 = 0x7)
func OpenFileShareAll(path string) (io.ReadCloser, error) {
	pathPtr, err := windows.UTF16PtrFromString(path)
	if err != nil {
		return nil, fmt.Errorf("caminho UTF16 inválido '%s': %w", path, err)
	}

	handle, err := windows.CreateFile(
		pathPtr,
		windows.GENERIC_READ,
		windows.FILE_SHARE_READ|windows.FILE_SHARE_WRITE|windows.FILE_SHARE_DELETE,
		nil,
		windows.OPEN_EXISTING,
		windows.FILE_ATTRIBUTE_NORMAL,
		0,
	)
	if err != nil {
		return nil, fmt.Errorf("falha ao abrir arquivo com lock bypass via CreateFileW: %w", err)
	}

	// Converte o Windows Handle em um *os.File padrão gerenciado pelo runtime do Go
	file := os.NewFile(uintptr(handle), path)
	if file == nil {
		_ = windows.CloseHandle(handle)
		return nil, fmt.Errorf("impossível criar os.File a partir do handle do Windows")
	}

	return file, nil
}
