import unittest

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


if __name__ == "__main__":
    unittest.main()
