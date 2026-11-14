"""Regras puras de cálculo usadas pela camada de precificação.

Este módulo não acessa SQLite nem depende da interface Flet.
Os valores monetários são recebidos em reais e os percentuais em pontos percentuais.
"""
import math


def _converter_validar_valores(**valores):
    """Converte entradas numéricas e rejeita valores inválidos ou não finitos."""
    convertidos = {}
    for nome, valor in valores.items():
        try:
            numero = float(valor)
        except (TypeError, ValueError) as erro:
            raise ValueError(f"O valor de {nome} deve ser numérico.") from erro
        if not math.isfinite(numero):
            raise ValueError(f"O valor de {nome} deve ser finito.")
        convertidos[nome] = numero
    return convertidos


def _validar_percentuais(impostos_pct, taxa_pct):
    if impostos_pct < 0 or taxa_pct < 0:
        raise ValueError("Impostos e taxas não podem ser negativos.")
    if impostos_pct >= 100 or taxa_pct >= 100:
        raise ValueError("Cada percentual deve ser inferior a 100%.")
    if impostos_pct + taxa_pct >= 100:
        raise ValueError("A soma de impostos e taxas deve ser inferior a 100%.")


def calcular_preco_sugerido(custo_total, markup_pct, impostos_pct=0, taxa_pct=0):
    """Calcula o preço necessário para cobrir custos, markup e percentuais da venda."""
    valores = _converter_validar_valores(
        custo_total=custo_total,
        markup_pct=markup_pct,
        impostos_pct=impostos_pct,
        taxa_pct=taxa_pct,
    )
    custo_total = valores["custo_total"]
    markup_pct = valores["markup_pct"]
    impostos_pct = valores["impostos_pct"]
    taxa_pct = valores["taxa_pct"]

    if custo_total < 0:
        raise ValueError("O custo total não pode ser negativo.")
    if markup_pct < 0:
        raise ValueError("O markup não pode ser negativo.")
    _validar_percentuais(impostos_pct, taxa_pct)

    divisor = 1 - ((impostos_pct + taxa_pct) / 100.0)
    return custo_total * (1 + (markup_pct / 100.0)) / divisor


def calcular_indicadores_preco_praticado(
    preco_praticado,
    custo_total,
    custo_variavel,
    impostos_pct,
    taxa_pct,
):
    """Calcula markup aplicado, margem de contribuição e resultado após rateio."""
    valores = _converter_validar_valores(
        preco_praticado=preco_praticado,
        custo_total=custo_total,
        custo_variavel=custo_variavel,
        impostos_pct=impostos_pct,
        taxa_pct=taxa_pct,
    )
    preco_praticado = valores["preco_praticado"]
    custo_total = valores["custo_total"]
    custo_variavel = valores["custo_variavel"]
    impostos_pct = valores["impostos_pct"]
    taxa_pct = valores["taxa_pct"]

    if preco_praticado < 0:
        raise ValueError("O preço praticado não pode ser negativo.")
    if custo_total < 0 or custo_variavel < 0:
        raise ValueError("Os custos não podem ser negativos.")
    _validar_percentuais(impostos_pct, taxa_pct)

    markup_aplicado_pct = (
        (preco_praticado - custo_total) / custo_total * 100.0
        if custo_total > 0 else 0.0
    )
    imposto_cartao = preco_praticado * (taxa_pct / 100.0)
    imposto_venda = preco_praticado * (impostos_pct / 100.0)
    margem_contribuicao = (
        preco_praticado - custo_variavel - imposto_cartao - imposto_venda
    )
    resultado_apos_rateio = (
        preco_praticado - custo_total - imposto_cartao - imposto_venda
    )
    margem_real_pct = (
        margem_contribuicao / preco_praticado * 100.0
        if preco_praticado > 0 else 0.0
    )

    return {
        "markup_aplicado_pct": markup_aplicado_pct,
        "imposto_cartao": imposto_cartao,
        "imposto_venda": imposto_venda,
        "margem_contribuicao": margem_contribuicao,
        "resultado_apos_rateio": resultado_apos_rateio,
        "margem_real_pct": margem_real_pct,
    }
