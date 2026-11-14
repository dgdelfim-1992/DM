import sqlite3
import tempfile
import unittest
from pathlib import Path

from servicos.backup_service import (
    criar_backup_automatico, gerar_backup_bytes, restaurar_banco_bytes, validar_banco,
)


class TestBackupService(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.pasta = Path(self.tempdir.name)
        self.banco = self.pasta / "dm_gulositos.db"
        self._criar_banco(self.banco, "produto original")

    def tearDown(self):
        self.tempdir.cleanup()

    @staticmethod
    def _criar_banco(caminho, nome):
        caminho.parent.mkdir(parents=True, exist_ok=True)
        conexao = sqlite3.connect(caminho)
        try:
            conexao.executescript("""
                CREATE TABLE ingredientes (id INTEGER PRIMARY KEY, nome TEXT);
                CREATE TABLE receitas (id INTEGER PRIMARY KEY, nome TEXT);
                CREATE TABLE configuracoes (chave TEXT PRIMARY KEY, valor TEXT);
            """)
            conexao.execute("INSERT INTO ingredientes (nome) VALUES (?)", (nome,))
            conexao.commit()
        finally:
            conexao.close()

    @staticmethod
    def _nome_ingrediente(caminho):
        conexao = sqlite3.connect(caminho)
        try:
            return conexao.execute(
                "SELECT nome FROM ingredientes ORDER BY id LIMIT 1"
            ).fetchone()[0]
        finally:
            conexao.close()

    def test_validar_banco_reconhece_estrutura_essencial(self):
        self.assertTrue(validar_banco(self.banco))

    def test_rejeita_arquivo_vazio_ou_sqlite_sem_tabelas_da_aplicacao(self):
        vazio = self.pasta / "vazio.db"
        vazio.write_bytes(b"")
        estranho = self.pasta / "estranho.db"
        sqlite3.connect(estranho).close()
        for caminho in (vazio, estranho):
            with self.subTest(caminho=caminho):
                with self.assertRaises(ValueError):
                    validar_banco(caminho)

    def test_exportacao_gera_copia_sqlite_valida(self):
        conteudo = gerar_backup_bytes(self.banco)
        arquivo = self.pasta / "exportado.db"
        arquivo.write_bytes(conteudo)
        self.assertGreater(len(conteudo), 0)
        self.assertTrue(validar_banco(arquivo))
        self.assertEqual(self._nome_ingrediente(arquivo), "produto original")
        self.assertEqual(self._nome_ingrediente(self.banco), "produto original")

    def test_restauracao_preserva_backup_do_banco_anterior(self):
        importado = self.pasta / "backup_importado.db"
        self._criar_banco(importado, "produto restaurado")
        restaurar_banco_bytes(importado.read_bytes(), self.banco)
        self.assertEqual(self._nome_ingrediente(self.banco), "produto restaurado")
        anteriores = list((self.pasta / "backups").glob("antes_restauracao_*.db"))
        self.assertEqual(len(anteriores), 1)
        self.assertEqual(self._nome_ingrediente(anteriores[0]), "produto original")

    def test_restauracao_invalida_nao_altera_banco_atual(self):
        with self.assertRaises(ValueError):
            restaurar_banco_bytes("arquivo inválido".encode("utf-8"), self.banco)
        self.assertEqual(self._nome_ingrediente(self.banco), "produto original")
        self.assertFalse((self.pasta / "backups").exists())

    def test_backup_automatico_cria_copia_e_reaproveita_a_do_dia(self):
        primeiro = criar_backup_automatico(caminho_banco=self.banco)
        segundo = criar_backup_automatico(caminho_banco=self.banco)
        self.assertTrue(primeiro.is_file())
        self.assertEqual(primeiro, segundo)
        self.assertTrue(validar_banco(primeiro))

    def test_backup_automatico_aplica_retencao_mesmo_com_backup_diario_existente(self):
        pasta_backups = self.pasta / "backups"
        pasta_backups.mkdir()
        antigo = pasta_backups / "automatico_20000101_000000.db"
        self._criar_banco(antigo, "backup antigo")

        criado = criar_backup_automatico(limite=10, caminho_banco=self.banco)
        resultado = criar_backup_automatico(limite=1, caminho_banco=self.banco)

        self.assertEqual(resultado, criado)
        self.assertTrue(criado.exists())
        self.assertFalse(antigo.exists())

    def test_backup_automatico_aplica_limite_de_retencao(self):
        pasta_backups = self.pasta / "backups"
        pasta_backups.mkdir()
        antigo = pasta_backups / "automatico_20000101_000000.db"
        self._criar_banco(antigo, "backup antigo")
        criado = criar_backup_automatico(limite=1, caminho_banco=self.banco)
        backups = list(pasta_backups.glob("automatico_*.db"))
        self.assertEqual(backups, [criado])
        self.assertFalse(antigo.exists())


if __name__ == "__main__":
    unittest.main()
