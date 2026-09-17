//go:build windows

package browser

import (
	"fmt"
	"syscall"
	"unsafe"

	"golang.org/x/sys/windows"
)

var (
	modCrypt32             = syscall.NewLazyDLL("crypt32.dll")
	procCryptUnprotectData = modCrypt32.NewProc("CryptUnprotectData")
)

// CryptUnprotectData executa a chamada nativa à API DPAPI do Windows
// sem recorrer a CGO ou wrappers externos.
//
// O Windows DPAPI (Data Protection API) utiliza chaves derivadas das credenciais
// do usuário logado (passadas por hash e salvas no LSASS/SAM) para proteger segredos locais.
//
// Assinatura Win32 original:
// BOOL WINAPI CryptUnprotectData(
//
//	[in]            DATA_BLOB*      pDataIn,
//	[out, optional] LPWSTR*         ppszDataDescr,
//	[in, optional]  DATA_BLOB*      pOptionalEntropy,
//	[in]            PVOID           pvReserved,
//	[in, optional]  CRYPTPROTECT_PROMPTSTRUCT* pPromptStruct,
//	[in]            DWORD           dwFlags,
//	[out]           DATA_BLOB*      pDataOut
//
// );
func CryptUnprotectData(data []byte) ([]byte, error) {
	if len(data) == 0 {
		return nil, fmt.Errorf("dados criptografados vazios fornecidos ao DPAPI")
	}

	var inBlob windows.DataBlob
	inBlob.Size = uint32(len(data))
	inBlob.Data = &data[0]

	var outBlob windows.DataBlob

	// dwFlags: 0 (CRYPTPROTECT_UI_FORBIDDEN = 0x1 pode ser usado para suprimir diálogos de UI)
	r, _, err := procCryptUnprotectData.Call(
		uintptr(unsafe.Pointer(&inBlob)),
		0,                                // ppszDataDescr (não necessário)
		0,                                // pOptionalEntropy (null para Master Key do Chromium)
		0,                                // pvReserved
		0,                                // pPromptStruct
		0x1,                              // dwFlags: CRYPTPROTECT_UI_FORBIDDEN (evita qualquer prompt de UI ao usuário)
		uintptr(unsafe.Pointer(&outBlob)), // pDataOut
	)

	if r == 0 {
		return nil, fmt.Errorf("falha ao chamar CryptUnprotectData (Win32 r=0): %w", err)
	}

	// Alocação de memória de saída pelo Windows LocalAlloc exige liberação via LocalFree
	defer windows.LocalFree(windows.Handle(unsafe.Pointer(outBlob.Data)))

	// Converte os bytes descriptografados em uma slice Go gerenciada
	decrypted := make([]byte, outBlob.Size)
	copy(decrypted, unsafe.Slice(outBlob.Data, outBlob.Size))

	return decrypted, nil
}
