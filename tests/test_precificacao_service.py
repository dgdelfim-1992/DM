import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

from database import banco

from servicos.precificacao_service import (
    calcular_preco_sugerido,
    calcular_indicadores_preco_praticado,
)


class TestPrecificacaoService(unittest.TestCase):
    def test_calcula_preco_sugerido_com_markup_e_taxas(self):
        resultado = calcular_preco_sugerido(
            custo_total=10,
            markup_pct=100,
            impostos_pct=0,
            taxa_pct=10,
        )
        self.assertAlmostEqual(resultado, 200 / 9, places=7)

    def test_rejeita_soma_de_percentuais_igual_ou_superior_a_cem(self):
        with self.assertRaises(ValueError):
            calcular_preco_sugerido(10, 50, 20, 80)

    def test_rejeita_custos_e_markup_negativos(self):
        casos = [
            (-1, 100, 0, 0),
            (10, -1, 0, 0),
            (10, 100, -1, 0),
            (10, 100, 0, -1),
        ]
        for argumentos in casos:
            with self.subTest(argumentos=argumentos):
                with self.assertRaises(ValueError):
                    calcular_preco_sugerido(*argumentos)

    def test_rejeita_valores_nao_finitos(self):
        for valor in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(valor=valor):
                with self.assertRaises(ValueError):
                    calcular_preco_sugerido(valor, 100)

    def test_calcula_indicadores_do_preco_praticado(self):
        resultado = calcular_indicadores_preco_praticado(
            preco_praticado=20,
            custo_total=12,
            custo_variavel=8,
            impostos_pct=10,
            taxa_pct=5,
        )
        self.assertAlmostEqual(resultado["markup_aplicado_pct"], 200 / 3)
        self.assertAlmostEqual(resultado["imposto_cartao"], 1)
        self.assertAlmostEqual(resultado["imposto_venda"], 2)
        self.assertAlmostEqual(resultado["margem_contribuicao"], 9)
        self.assertAlmostEqual(resultado["resultado_apos_rateio"], 5)
        self.assertAlmostEqual(resultado["margem_real_pct"], 45)

    def test_preco_zero_nao_divide_por_zero(self):
        resultado = calcular_indicadores_preco_praticado(
            preco_praticado=0,
            custo_total=0,
            custo_variavel=0,
            impostos_pct=0,
            taxa_pct=0,
        )
        self.assertEqual(resultado["markup_aplicado_pct"], 0)
        self.assertEqual(resultado["margem_real_pct"], 0)

    def test_indicadores_rejeitam_valores_negativos(self):
        casos = [
            (-1, 10, 5, 0, 0),
            (10, -1, 5, 0, 0),
            (10, 10, -1, 0, 0),
            (10, 10, 5, -1, 0),
            (10, 10, 5, 0, -1),
        ]
        for argumentos in casos:
            with self.subTest(argumentos=argumentos):
                with self.assertRaises(ValueError):
                    calcular_indicadores_preco_praticado(*argumentos)

    def test_indicadores_rejeitam_percentuais_que_anulam_divisor(self):
        with self.assertRaises(ValueError):
            calcular_indicadores_preco_praticado(20, 10, 5, 60, 40)


class TestBancoIngredientes(unittest.TestCase):
    def setUp(self):
        self.pasta_temporaria = tempfile.TemporaryDirectory()
        self.caminho_banco = Path(self.pasta_temporaria.name) / "teste_dm.db"
        self.patch_banco = patch.object(banco, "CAMINHO_BANCO", self.caminho_banco)
        self.patch_banco.start()
        banco.criar_tabelas()

    def tearDown(self):
        self.patch_banco.stop()
        self.pasta_temporaria.cleanup()

    def test_converte_unidades_para_base(self):
        self.assertEqual(banco.converter_para_base(1, "kg"), (1000, "g"))
        self.assertEqual(banco.converter_para_base(500, "g"), (500, "g"))
        self.assertEqual(banco.converter_para_base(1, "l"), (1000, "ml"))
        self.assertEqual(banco.converter_para_base(2, "un"), (2, "un"))

    def test_rejeita_quantidades_invalidas(self):
        for quantidade in (0, -1, float("nan"), float("inf"), None, "abc"):
            with self.subTest(quantidade=quantidade):
                with self.assertRaises(ValueError):
                    banco.converter_para_base(quantidade, "g")

    def test_calcula_custo_unitario(self):
        self.assertAlmostEqual(banco.calcular_custo_unitario(699, 500), 0.01398)

    def test_rejeita_preco_ou_quantidade_invalidos(self):
        casos = [
            (-1, 100),
            (100, 0),
            (float("nan"), 100),
            (100, float("inf")),
            (None, 100),
        ]
        for preco, quantidade in casos:
            with self.subTest(preco=preco, quantidade=quantidade):
                with self.assertRaises(ValueError):
                    banco.calcular_custo_unitario(preco, quantidade)

    def test_cadastro_registra_ingrediente_e_historico(self):
        ingrediente_id = banco.cadastrar_ingrediente(
            nome="Ingrediente de teste",
            marca="Marca teste",
            fornecedor="Fornecedor teste",
            quantidade_compra=500,
            unidade_compra="g",
            preco_pago_centavos=699,
        )
        ingrediente = banco.obter_ingrediente(ingrediente_id)
        historico = banco.listar_historico_precos_ingrediente(ingrediente_id)

        self.assertEqual(ingrediente["nome"], "Ingrediente de teste")
        self.assertEqual(len(historico), 1)
        self.assertEqual(historico[0]["preco_pago_centavos"], 699)
        self.assertAlmostEqual(ingrediente["custo_por_unidade_base"], 0.01398)

    def test_cadastro_invalido_nao_cria_registro(self):
        with self.assertRaises(ValueError):
            banco.cadastrar_ingrediente(
                nome="Ingrediente inválido",
                marca="",
                fornecedor="",
                quantidade_compra=float("nan"),
                unidade_compra="g",
                preco_pago_centavos=100,
            )
        self.assertEqual(len(banco.listar_ingredientes()), 0)



class TestBancoReceitas(unittest.TestCase):
    def setUp(self):
        self.pasta_temporaria = tempfile.TemporaryDirectory()
        self.caminho_banco = Path(self.pasta_temporaria.name) / "teste_receitas.db"
        self.patch_banco = patch.object(banco, "CAMINHO_BANCO", self.caminho_banco)
        self.patch_banco.start()
        banco.criar_tabelas()
        self.ingrediente_id = banco.cadastrar_ingrediente(
            nome="Farinha de teste",
            marca="Marca",
            fornecedor="Fornecedor",
            quantidade_compra=1000,
            unidade_compra="g",
            preco_pago_centavos=500,
        )

    def tearDown(self):
        self.patch_banco.stop()
        self.pasta_temporaria.cleanup()

    def item_ingrediente(self, quantidade=100, ingrediente_id=None):
        return {
            "ingrediente_id": ingrediente_id or self.ingrediente_id,
            "quantidade_usada": quantidade,
        }

    def cadastrar(self, nome="Receita teste", tipo="PRODUTO", itens=None):
        return banco.cadastrar_receita(
            nome=nome,
            tipo=tipo,
            rendimento_unidades=10,
            custo_embalagem_centavos=0,
            margem_lucro_pct=0,
            taxa_cartao_pct=0,
            lista_itens=itens if itens is not None else [self.item_ingrediente()],
        )

    def test_cadastra_receita_e_calcula_custo(self):
        receita_id = self.cadastrar()
        resultado = banco.calcular_custo_receita(receita_id)
        self.assertAlmostEqual(resultado["custo_insumos"], 0.5)
        self.assertAlmostEqual(resultado["custo_unitario"], 0.05)

    def test_rejeita_rendimento_e_tempos_nao_finitos(self):
        base = {
            "nome": "Receita inválida",
            "tipo": "PRODUTO",
            "rendimento_unidades": 10,
            "custo_embalagem_centavos": 0,
            "margem_lucro_pct": 0,
            "taxa_cartao_pct": 0,
            "lista_itens": [self.item_ingrediente()],
        }
        casos = [
            {"rendimento_unidades": float("nan")},
            {"rendimento_unidades": float("inf")},
            {"tempo_preparo_min": float("nan")},
            {"tempo_batedeira_min": float("inf")},
            {"tempo_forno_min": -1},
        ]
        for alteracao in casos:
            with self.subTest(alteracao=alteracao):
                parametros = {**base, **alteracao}
                with self.assertRaises(ValueError):
                    banco.cadastrar_receita(**parametros)
        conexao = banco.obter_conexao()
        try:
            total = conexao.execute("SELECT COUNT(*) FROM receitas").fetchone()[0]
        finally:
            conexao.close()
        self.assertEqual(total, 0)

    def test_rejeita_item_sem_ou_com_dois_vinculos(self):
        casos = [
            {"quantidade_usada": 10},
            {
                "ingrediente_id": self.ingrediente_id,
                "sub_receita_id": 999,
                "quantidade_usada": 10,
            },
        ]
        for item in casos:
            with self.subTest(item=item):
                with self.assertRaises(ValueError):
                    self.cadastrar(itens=[item])

    def test_rejeita_quantidade_de_item_invalida(self):
        for quantidade in (0, -1, float("nan"), float("inf"), "abc", None):
            with self.subTest(quantidade=quantidade):
                with self.assertRaises(ValueError):
                    self.cadastrar(itens=[self.item_ingrediente(quantidade)])

    def test_rejeita_ingrediente_inexistente(self):
        with self.assertRaises(ValueError):
            self.cadastrar(itens=[self.item_ingrediente(100, ingrediente_id=9999)])

    def test_rejeita_produto_como_sub_receita(self):
        produto_id = self.cadastrar(nome="Produto existente")
        with self.assertRaises(ValueError):
            self.cadastrar(
                nome="Receita que tenta usar produto",
                itens=[{
                    "sub_receita_id": produto_id,
                    "quantidade_usada": 1,
                }],
            )

    def test_impede_ciclo_ao_atualizar_sub_receita(self):
        sub_a = self.cadastrar(nome="Sub A", tipo="SUB_RECEITA")
        sub_b = self.cadastrar(
            nome="Sub B",
            tipo="SUB_RECEITA",
            itens=[{"sub_receita_id": sub_a, "quantidade_usada": 1}],
        )
        with self.assertRaisesRegex(ValueError, "ciclo"):
            banco.atualizar_receita(
                receita_id=sub_a,
                nome="Sub A",
                tipo="SUB_RECEITA",
                rendimento_unidades=10,
                custo_embalagem_centavos=0,
                margem_lucro_pct=0,
                taxa_cartao_pct=0,
                lista_itens=[{"sub_receita_id": sub_b, "quantidade_usada": 1}],
            )

        dados = banco.obter_receita(sub_a)
        self.assertEqual(len(dados["itens"]), 1)
        self.assertEqual(dados["itens"][0]["ingrediente_id"], self.ingrediente_id)

    def test_edicao_invalida_nao_apaga_itens_existentes(self):
        receita_id = self.cadastrar()
        with self.assertRaises(ValueError):
            banco.atualizar_receita(
                receita_id=receita_id,
                nome="Receita alterada",
                tipo="PRODUTO",
                rendimento_unidades=10,
                custo_embalagem_centavos=0,
                margem_lucro_pct=0,
                taxa_cartao_pct=0,
                lista_itens=[self.item_ingrediente(0)],
            )
        dados = banco.obter_receita(receita_id)
        self.assertEqual(len(dados["itens"]), 1)
        self.assertEqual(dados["receita"]["nome"], "Receita teste")

    def test_edicao_rejeita_receita_inexistente(self):
        with self.assertRaisesRegex(ValueError, "não encontrada"):
            banco.atualizar_receita(
                receita_id=9999,
                nome="Não existe",
                tipo="PRODUTO",
                rendimento_unidades=1,
                custo_embalagem_centavos=0,
                margem_lucro_pct=0,
                taxa_cartao_pct=0,
                lista_itens=[self.item_ingrediente()],
            )


if __name__ == "__main__":
    unittest.main()
