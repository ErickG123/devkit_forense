//go:build !windows

package browser

import "fmt"

// CryptUnprotectData stub para compilação em plataformas não-Windows (Linux / macOS)
func CryptUnprotectData(data []byte) ([]byte, error) {
	return nil, fmt.Errorf("DPAPI CryptUnprotectData está disponível exclusivamente no sistema Windows")
}
