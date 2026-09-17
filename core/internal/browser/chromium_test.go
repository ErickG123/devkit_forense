package browser

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"io"
	"testing"
)

// Helper para criar ciphertext AES-GCM sintético no padrão v10 do Chromium
func createMockEncryptedPassword(masterKey []byte, plaintext string) []byte {
	block, _ := aes.NewCipher(masterKey)
	gcm, _ := cipher.NewGCM(block)
	nonce := make([]byte, gcm.NonceSize())
	_, _ = io.ReadFull(rand.Reader, nonce)
	ciphertext := gcm.Seal(nil, nonce, []byte(plaintext), nil)

	// Prefixo "v10" (3 bytes) + nonce (12 bytes) + tag/ciphertext
	res := append([]byte("v10"), nonce...)
	return append(res, ciphertext...)
}

func TestDecryptPasswordV10(t *testing.T) {
	mockMasterKey := make([]byte, 32)
	_, _ = rand.Read(mockMasterKey)

	expectedPlaintext := "SenhaSuperSecretaForense123!"
	encryptedBlob := createMockEncryptedPassword(mockMasterKey, expectedPlaintext)

	// Executa a descriptografia da função interna de produção
	decrypted, err := DecryptPassword(encryptedBlob, mockMasterKey)
	if err != nil {
		t.Fatalf("Erro ao descriptografar blob de teste: %v", err)
	}

	if decrypted != expectedPlaintext {
		t.Errorf("Senha descriptografada incorreta: obteve %q, esperava %q", decrypted, expectedPlaintext)
	}
}

func TestDecryptPasswordShortBlob(t *testing.T) {
	mockMasterKey := make([]byte, 32)
	_, _ = rand.Read(mockMasterKey)

	// Menos de 31 bytes no formato v10 deve falhar graciosamente
	shortBlob := []byte("v10short")
	_, err := DecryptPassword(shortBlob, mockMasterKey)
	if err == nil {
		t.Errorf("Esperava erro para blob truncado (<31 bytes), mas obteve nil")
	}
}
