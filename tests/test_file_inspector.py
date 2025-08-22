import unittest
import os
import tempfile

class TestFileInspector(unittest.TestCase):

    def setUp(self):
        self.test_file = tempfile.NamedTemporaryFile(delete=False)
        self.test_file.write(b"Conteudo de teste para hash.")
        self.test_file.close()

    def tearDown(self):
        os.unlink(self.test_file.name)


if __name__ == "__main__":
    unittest.main()
