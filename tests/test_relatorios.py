import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from database import banco


class TestRelatorioPrecificacaoV2(unittest.TestCase):
    def setUp(self):
        self.pasta_temporaria = tempfile.TemporaryDirectory()
        self.caminho_banco = Path(self.pasta_temporaria.name) / "teste_relatorios.db"
        self.patch_banco = patch.object(banco, "CAMINHO_BANCO", self.caminho_banco)
        self.patch_banco.start()
        banco.criar_tabelas()

        conexao = banco.obter_conexao()
        try:
            cursor = conexao.execute(
                """
                INSERT INTO receitas (nome, criado_em, atualizado_em)
                VALUES (?, ?, ?)
                """,
                ("Produto de teste", "2026-01-01T10:00:00", "2026-01-01T10:00:00"),
            )
            self.receita_id = cursor.lastrowid
            conexao.commit()
        finally:
            conexao.close()

    def tearDown(self):
        self.patch_banco.stop()
        self.pasta_temporaria.cleanup()

    def inserir_precificacao(self, receita_id=None):
        conexao = banco.obter_conexao()
        try:
            cursor = conexao.execute(
                """
                INSERT INTO precificacao_v2 (
                    receita_id, quantidade_embalagem, custo_embalagem_centavos,
                    markup_ideal_pct, preco_praticado_centavos
                )
                VALUES (?, 1, 0, 100, 1500)
                """,
                (receita_id or self.receita_id,),
            )
            conexao.commit()
            return cursor.lastrowid
        finally:
            conexao.close()

    def inserir_historico(
        self,
        precificacao_id,
        registrado_em,
        nome_receita="Produto histórico",
        custo_total_centavos=800,
        preco_sugerido_centavos=1600,
        preco_praticado_centavos=1500,
        margem_contribuicao_centavos=500,
    ):
        conexao = banco.obter_conexao()
        try:
            cursor = conexao.execute(
                """
                INSERT INTO historico_precificacao_v2 (
                    precificacao_id, receita_id, nome_receita,
                    quantidade_embalagem, custo_embalagem_centavos,
                    taxa_cartao_pct, markup_ideal_pct, custo_insumo_centavos,
                    custo_fixo_centavos, custo_mao_obra_centavos, impostos_pct,
                    custo_total_centavos, preco_sugerido_centavos,
                    preco_praticado_centavos, markup_aplicado_pct,
                    margem_contribuicao_centavos, status, registrado_em
                )
                VALUES (?, ?, ?, 1, 0, 5, 100, 300, 200, 100, 10, ?, ?, ?, 50, ?, 'Dentro da Margem', ?)
                """,
                (
                    precificacao_id,
                    self.receita_id,
                    nome_receita,
                    custo_total_centavos,
                    preco_sugerido_centavos,
                    preco_praticado_centavos,
                    margem_contribuicao_centavos,
                    registrado_em,
                ),
            )
            conexao.commit()
            return cursor.lastrowid
        finally:
            conexao.close()

    def test_retorna_apenas_o_historico_mais_recente_de_cada_precificacao(self):
        precificacao_id = self.inserir_precificacao()
        self.inserir_historico(
            precificacao_id,
            "2026-11-01T10:00:00",
            custo_total_centavos=700,
            preco_praticado_centavos=1200,
        )
        id_mais_recente = self.inserir_historico(
            precificacao_id,
            "2026-11-02T10:00:00",
            custo_total_centavos=900,
            preco_praticado_centavos=1800,
        )

        resultado = banco.listar_relatorio_precificacao_v2()

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["historico_id"], id_mais_recente)
        self.assertEqual(resultado[0]["custo_total_centavos"], 900)
        self.assertEqual(resultado[0]["preco_praticado_centavos"], 1800)

    def test_retorna_precificacoes_separadas_para_a_mesma_receita(self):
        primeira = self.inserir_precificacao()
        segunda = self.inserir_precificacao()
        self.inserir_historico(primeira, "2026-11-01T10:00:00", preco_praticado_centavos=1200)
        self.inserir_historico(segunda, "2026-11-02T10:00:00", preco_praticado_centavos=1900)

        resultado = banco.listar_relatorio_precificacao_v2()

        self.assertEqual(len(resultado), 2)
        self.assertEqual(
            {linha["precificacao_id"] for linha in resultado},
            {primeira, segunda},
        )
        self.assertEqual(
            {linha["preco_praticado_centavos"] for linha in resultado},
            {1200, 1900},
        )

    def test_inclui_precificacao_sem_historico_com_campos_nulos(self):
        self.inserir_precificacao()

        resultado = banco.listar_relatorio_precificacao_v2()

        self.assertEqual(len(resultado), 1)
        self.assertIsNone(resultado[0]["historico_id"])
        self.assertIsNone(resultado[0]["custo_total_centavos"])
        self.assertIsNone(resultado[0]["status"])

    def test_em_empate_de_data_usa_o_maior_id_do_historico(self):
        precificacao_id = self.inserir_precificacao()
        self.inserir_historico(
            precificacao_id,
            "2026-11-03T10:00:00",
            preco_praticado_centavos=1300,
        )
        id_mais_recente = self.inserir_historico(
            precificacao_id,
            "2026-11-03T10:00:00",
            preco_praticado_centavos=1700,
        )

        resultado = banco.listar_relatorio_precificacao_v2()

        self.assertEqual(resultado[0]["historico_id"], id_mais_recente)
        self.assertEqual(resultado[0]["preco_praticado_centavos"], 1700)

    def test_mantem_valores_do_snapshot_historico_sem_recalcular_custos_atuais(self):
        precificacao_id = self.inserir_precificacao()
        self.inserir_historico(
            precificacao_id,
            "2026-11-04T10:00:00",
            nome_receita="Nome registrado na época",
            custo_total_centavos=875,
            preco_sugerido_centavos=1750,
            preco_praticado_centavos=1600,
            margem_contribuicao_centavos=600,
        )

        conexao = banco.obter_conexao()
        try:
            conexao.execute(
                "UPDATE receitas SET nome = ? WHERE id = ?",
                ("Nome atual da receita", self.receita_id),
            )
            conexao.commit()
        finally:
            conexao.close()

        resultado = banco.listar_relatorio_precificacao_v2()[0]

        self.assertEqual(resultado["nome_receita"], "Nome registrado na época")
        self.assertEqual(resultado["nome_receita_atual"], "Nome atual da receita")
        self.assertEqual(resultado["custo_total_centavos"], 875)
        self.assertEqual(resultado["preco_sugerido_centavos"], 1750)
        self.assertEqual(resultado["preco_praticado_centavos"], 1600)
        self.assertEqual(resultado["margem_contribuicao_centavos"], 600)

    def test_ignora_precificacoes_de_receitas_inativas(self):
        self.inserir_precificacao()
        conexao = banco.obter_conexao()
        try:
            conexao.execute(
                "UPDATE receitas SET ativo = 0 WHERE id = ?",
                (self.receita_id,),
            )
            conexao.commit()
        finally:
            conexao.close()

        self.assertEqual(banco.listar_relatorio_precificacao_v2(), [])


if __name__ == "__main__":
    unittest.main()
