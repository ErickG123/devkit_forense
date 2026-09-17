//go:build !windows

package browser

import (
	"io"
	"os"
)

// OpenFileShareAll para sistemas Unix-like (onde locks compartilhados nativos não bloqueiam leitura padrão)
func OpenFileShareAll(path string) (io.ReadCloser, error) {
	return os.Open(path)
}
