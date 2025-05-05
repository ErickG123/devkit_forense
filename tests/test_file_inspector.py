import unittest
import os
import tempfile
from modules import file_inspector

class TestFileInspector(unittest.TestCase):

    def setUp(self):
        # Criar um arquivo temporário para testes
        self.test_file = tempfile.NamedTemporaryFile(delete=False)
        self.test_file.write(b"Conteudo de teste para hash.")
        self.test_file.close()

    def tearDown(self):
        # Apagar o arquivo após os testes
        os.unlink(self.test_file.name)

    def test_calculate_sha256(self):
        # Calcula o hash e verifica se tem 64 caracteres hexadecimais
        hash_result = file_inspector.calculate_sha256(self.test_file.name)
        self.assertEqual(len(hash_result), 64)
        self.assertTrue(all(c in "0123456789abcdef" for c in hash_result.lower()))

    def test_get_file_metadata(self):
        metadata = file_inspector.get_file_metadata(self.test_file.name)
        self.assertIn("hash_sha256", metadata)
        self.assertEqual(metadata["caminho"], self.test_file.name)
        self.assertGreater(metadata["tamanho_bytes"], 0)

    def test_arquivo_inexistente(self):
        with self.assertRaises(FileNotFoundError):
            file_inspector.get_file_metadata("arquivo_inexistente.txt")


if __name__ == "__main__":
    unittest.main()
