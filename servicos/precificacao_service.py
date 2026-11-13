"""Regras puras de cálculo usadas pela camada de precificação.

Este módulo não acessa SQLite nem depende da interface Flet.
Os valores monetários são recebidos em reais e os percentuais em pontos percentuais.
"""


def calcular_preco_sugerido(custo_total, markup_pct, impostos_pct=0, taxa_pct=0):
    """Calcula o preço necessário para cobrir custos, markup e percentuais da venda."""
    custo_total = float(custo_total)
    markup_pct = float(markup_pct)
    impostos_pct = float(impostos_pct)
    taxa_pct = float(taxa_pct)

    percentual_total = impostos_pct + taxa_pct
    if percentual_total < 0 or percentual_total >= 100:
        raise ValueError("A soma de impostos e taxas deve ser inferior a 100%.")

    divisor = 1 - (percentual_total / 100.0)
    return custo_total * (1 + (markup_pct / 100.0)) / divisor


def calcular_indicadores_preco_praticado(
    preco_praticado,
    custo_total,
    custo_variavel,
    impostos_pct,
    taxa_pct,
):
    """Calcula markup aplicado, margem de contribuição e resultado após rateio."""
    preco_praticado = float(preco_praticado)
    custo_total = float(custo_total)
    custo_variavel = float(custo_variavel)
    impostos_pct = float(impostos_pct)
    taxa_pct = float(taxa_pct)

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
