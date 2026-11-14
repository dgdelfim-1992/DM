import sqlite3
import tempfile
import unittest
from pathlib import Path

from database.caminhos import migrar_banco_legado_se_necessario


class TestMigracaoBancoLegado(unittest.TestCase):
    def test_copia_banco_para_novo_diretorio_sem_apagar_origem(self):
        with tempfile.TemporaryDirectory() as pasta:
            raiz = Path(pasta)
            legado = raiz / "antigo" / "dm_gulositos.db"
            destino = raiz / "dados" / "database" / "dm_gulositos.db"
            legado.parent.mkdir(parents=True)
            conexao = sqlite3.connect(legado)
            try:
                conexao.execute("CREATE TABLE exemplo (valor TEXT)")
                conexao.execute("INSERT INTO exemplo VALUES ('dados preservados')")
                conexao.commit()
            finally:
                conexao.close()

            resultado = migrar_banco_legado_se_necessario(legado, destino)

            self.assertEqual(resultado, destino)
            self.assertTrue(legado.exists())
            leitura = sqlite3.connect(destino)
            try:
                valor = leitura.execute("SELECT valor FROM exemplo").fetchone()[0]
                integridade = leitura.execute("PRAGMA integrity_check").fetchone()[0]
            finally:
                leitura.close()
            self.assertEqual(valor, "dados preservados")
            self.assertEqual(integridade, "ok")

    def test_nao_sobrescreve_destino_ja_existente(self):
        with tempfile.TemporaryDirectory() as pasta:
            raiz = Path(pasta)
            legado = raiz / "antigo.db"
            destino = raiz / "novo.db"
            sqlite3.connect(legado).close()
            destino.write_bytes(b"destino existente")

            resultado = migrar_banco_legado_se_necessario(legado, destino)

            self.assertEqual(resultado, destino)
            self.assertEqual(destino.read_bytes(), b"destino existente")


if __name__ == "__main__":
    unittest.main()
