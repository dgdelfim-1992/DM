import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from database import banco


class TestConsultasCentralizadas(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.caminho = Path(self.tempdir.name) / "teste.db"
        self.patch_caminho = patch("database.banco.CAMINHO_BANCO", self.caminho)
        self.patch_caminho.start()

        conexao = banco.obter_conexao()
        try:
            conexao.executescript("""
                CREATE TABLE configuracoes (chave TEXT PRIMARY KEY, valor TEXT);
                CREATE TABLE receitas (
                    id INTEGER PRIMARY KEY,
                    nome TEXT NOT NULL,
                    tipo TEXT NOT NULL,
                    ativo INTEGER NOT NULL DEFAULT 1
                );
                CREATE TABLE custos_fixos (
                    id INTEGER PRIMARY KEY,
                    descricao TEXT NOT NULL,
                    valor_centavos INTEGER NOT NULL
                );
                CREATE TABLE ingredientes (
                    id INTEGER PRIMARY KEY,
                    nome TEXT NOT NULL,
                    ativo INTEGER NOT NULL DEFAULT 1
                );
                INSERT INTO receitas (nome, tipo, ativo) VALUES
                    ('Bolo final', 'PRODUTO', 1),
                    ('Massa base', 'SUB_RECEITA', 1),
                    ('Receita arquivada', 'PRODUTO', 0);
                INSERT INTO custos_fixos (descricao, valor_centavos)
                    VALUES ('Energia', 15000);
                INSERT INTO ingredientes (nome, ativo)
                    VALUES ('Farinha', 1), ('Ingrediente arquivado', 0);
            """)
            conexao.commit()
        finally:
            conexao.close()

    def tearDown(self):
        self.patch_caminho.stop()
        self.tempdir.cleanup()

    def test_faturamento_mensal_tem_padrao_e_pode_ser_atualizado(self):
        self.assertEqual(banco.obter_faturamento_mensal(), "2000.00")
        banco.salvar_faturamento_mensal("3500,50")
        self.assertEqual(banco.obter_faturamento_mensal(), "3500,50")

    def test_faturamento_mensal_rejeita_valores_invalidos(self):
        for valor in ("0", "-10", "nan", "texto"):
            with self.subTest(valor=valor):
                with self.assertRaises(ValueError):
                    banco.salvar_faturamento_mensal(valor)

    def test_listagens_de_receitas_filtram_tipo_e_status(self):
        todas = banco.listar_receitas_ativas()
        produtos = banco.listar_produtos_finais()
        sub_receitas = banco.listar_sub_receitas_ativas()

        self.assertEqual({r["nome"] for r in todas}, {"Bolo final", "Massa base"})
        self.assertEqual([r["nome"] for r in produtos], ["Bolo final"])
        self.assertEqual([r["nome"] for r in sub_receitas], ["Massa base"])

    def test_dados_do_relatorio_geral_sao_carregados_em_conjunto(self):
        dados = banco.obter_dados_relatorio_geral()

        self.assertEqual(len(dados["receitas"]), 2)
        self.assertEqual(len(dados["custos"]), 1)
        self.assertEqual([i["nome"] for i in dados["ingredientes"]], ["Farinha"])
        self.assertEqual(dados["faturamento_alvo"], 2000.0)


if __name__ == "__main__":
    unittest.main()
