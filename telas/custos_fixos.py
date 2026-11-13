"""Tela de custos fixos, remuneração e parâmetros gerais."""


def criar_abrir_custos_fixos(dependencias):
    """Monta a tela de custos e configurações com dependências injetadas."""
    ft = dependencias["ft"]
    page = dependencias["page"]
    BRANCO = dependencias["BRANCO"]
    MARROM = dependencias["MARROM"]
    ROSA = dependencias["ROSA"]
    ROSA_CLARO = dependencias["ROSA_CLARO"]
    TEXTO_SECUNDARIO = dependencias["TEXTO_SECUNDARIO"]
    indice_atual = dependencias["indice_atual"]
    navegacao = dependencias["navegacao"]
    obter_conexao = dependencias["obter_conexao"]
    obter_remuneracao_mensal_desejada = dependencias["obter_remuneracao_mensal_desejada"]
    obter_horas_produtivas_mensais = dependencias["obter_horas_produtivas_mensais"]
    obter_impostos_pct = dependencias["obter_impostos_pct"]
    obter_taxas_pagamento = dependencias["obter_taxas_pagamento"]
    obter_markup_ideal = dependencias["obter_markup_ideal"]
    obter_margem_minima = dependencias["obter_margem_minima"]
    criar_campo_padrao = dependencias["criar_campo_padrao"]
    salvar_remuneracao_mensal_desejada = dependencias["salvar_remuneracao_mensal_desejada"]
    salvar_horas_produtivas_mensais = dependencias["salvar_horas_produtivas_mensais"]
    salvar_impostos_pct = dependencias["salvar_impostos_pct"]
    salvar_taxas_pagamento = dependencias["salvar_taxas_pagamento"]
    salvar_markup_ideal = dependencias["salvar_markup_ideal"]
    salvar_margem_minima = dependencias["salvar_margem_minima"]
    atualizar_custo_fixo = dependencias["atualizar_custo_fixo"]
    cadastrar_custo_fixo = dependencias["cadastrar_custo_fixo"]
    excluir_custo_fixo = dependencias["excluir_custo_fixo"]

    def abrir_custos_fixos(e=None):
    
        conexao = obter_conexao()
    
        try:
            custos = conexao.execute(
                "SELECT * FROM custos_fixos ORDER BY descricao"
            ).fetchall()
    
            faturamento_row = conexao.execute("SELECT valor FROM configuracoes WHERE chave = 'faturamento_mensal'").fetchone()
            faturamento_atual = faturamento_row["valor"] if faturamento_row else "2000.00"
            remuneracao_atual = obter_remuneracao_mensal_desejada()
            horas_produtivas_atual = obter_horas_produtivas_mensais()
            impostos_atual = obter_impostos_pct()
    
            taxas_atuais = obter_taxas_pagamento()
            markup_ideal_atual = obter_markup_ideal()
            margem_minima_atual = obter_margem_minima()
    
        finally:
            conexao.close()
    
        total_custos = sum(
            c["valor_centavos"] for c in custos
        ) / 100
    
        faturamento_numero = float(
            str(faturamento_atual).replace(",", ".")
        )
    
        fator_percentual = (
            (total_custos / faturamento_numero) * 100
            if faturamento_numero > 0 else 0
        )
    
        campo_faturamento = criar_campo_padrao(
            label="Faturamento Médio Mensal Alvo (R$)",
            value=str(faturamento_atual),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12, expand=True
        )
        campo_remuneracao = criar_campo_padrao(
            label="Remuneração mensal desejada (R$)",
            value=f"{remuneracao_atual:.2f}".replace(".", ","),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12, expand=True
        )
        campo_horas_produtivas = criar_campo_padrao(
            label="Horas produtivas mensais",
            value=str(horas_produtivas_atual).replace(".", ","),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12, expand=True
        )
        campo_impostos = criar_campo_padrao(
            label="Impostos sobre venda (%)",
            value=f"{impostos_atual:.2f}".replace(".", ","),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12, expand=True
        )
        
        campo_markup_ideal = criar_campo_padrao(
            label="Markup Ideal Padrão (%)",
            value=str(markup_ideal_atual).replace(".", ","),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12, expand=True
        )
        campo_margem_minima = criar_campo_padrao(
            label="Margem Mínima (%)",
            value=str(margem_minima_atual).replace(".", ","),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12, expand=True
        )
    
        campo_taxa_pix = criar_campo_padrao(
            label="Taxa Pix (%)",
            value=str(taxas_atuais["pix"]).replace(".", ","),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12, expand=True
        )
        campo_taxa_dinheiro = criar_campo_padrao(
            label="Taxa Dinheiro (%)",
            value=str(taxas_atuais["dinheiro"]).replace(".", ","),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12, expand=True
        )
        campo_taxa_debito = criar_campo_padrao(
            label="Taxa Débito (%)",
            value=str(taxas_atuais["debito"]).replace(".", ","),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12, expand=True
        )
        campo_taxa_credito = criar_campo_padrao(
            label="Crédito à vista (%)",
            value=str(taxas_atuais["credito_avista"]).replace(".", ","),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12, expand=True
        )
        campo_taxa_parcelado = criar_campo_padrao(
            label="Crédito parcelado (%)",
            value=str(taxas_atuais["credito_parcelado"]).replace(".", ","),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12, expand=True
        )
    
        mensagem_custos = ft.Text("", size=12, color=ROSA)
    
        def salvar_configuracoes_acao(e):
            try:
                val_fat = (campo_faturamento.value or "0").replace(",", ".").strip()
                val_remuneracao = (campo_remuneracao.value or "0").replace(",", ".").strip()
                val_horas = (campo_horas_produtivas.value or "0").replace(",", ".").strip()
                val_impostos = (campo_impostos.value or "0").replace(",", ".").strip()
                markup_ideal_valor = (campo_markup_ideal.value or "0").replace(",", ".").strip()
                margem_minima_valor = (campo_margem_minima.value or "0").replace(",", ".").strip()
                taxas = {
                    "pix": (campo_taxa_pix.value or "0").replace(",", ".").strip(),
                    "dinheiro": (campo_taxa_dinheiro.value or "0").replace(",", ".").strip(),
                    "debito": (campo_taxa_debito.value or "0").replace(",", ".").strip(),
                    "credito_avista": (campo_taxa_credito.value or "0").replace(",", ".").strip(),
                    "credito_parcelado": (campo_taxa_parcelado.value or "0").replace(",", ".").strip(),
                }
    
                if float(val_fat) <= 0:
                    mensagem_custos.value = "Informe um faturamento maior que zero."
                    page.update()
                    return
                if float(val_remuneracao) < 0:
                    raise ValueError("A remuneração mensal não pode ser negativa.")
                if float(val_horas) <= 0:
                    raise ValueError("As horas produtivas devem ser maiores que zero.")
                if float(val_impostos) < 0 or float(val_impostos) >= 100:
                    raise ValueError("Os impostos devem estar entre 0% e 99,99%.")
    
                if float(markup_ideal_valor) < 0 or float(markup_ideal_valor) >= 10000:
                    raise ValueError("O markup ideal deve estar entre 0% e 9999,99%.")
                if float(margem_minima_valor) < 0 or float(margem_minima_valor) >= 100:
                    raise ValueError("A margem mínima deve estar entre 0% e 99,99%.")
    
                conexao = obter_conexao()
                try:
                    conexao.execute("INSERT OR REPLACE INTO configuracoes (chave, valor) VALUES ('faturamento_mensal', ?)", (val_fat,))
                    conexao.commit()
                finally:
                    conexao.close()
    
                salvar_remuneracao_mensal_desejada(float(val_remuneracao))
                salvar_horas_produtivas_mensais(float(val_horas))
                salvar_impostos_pct(float(val_impostos))
                salvar_taxas_pagamento(taxas)
                salvar_markup_ideal(float(markup_ideal_valor))
                salvar_margem_minima(float(margem_minima_valor))
                abrir_custos_fixos()
            except Exception as err:
                mensagem_custos.value = f"Erro ao atualizar: {err}"
                page.update()
    
        # --------------------------------------------------
        # FORMULÁRIO DE CUSTO FIXO
        # --------------------------------------------------
    
        def abrir_form_custo_fixo(custo=None):
    
            em_ed = custo is not None
    
            c_desc = criar_campo_padrao(
                label="Descrição do Custo Fixo *",
                value=custo["descricao"] if em_ed else "",
                border_radius=12,
            )
    
            c_val = criar_campo_padrao(
                label="Valor (R$) *",
                value=(
                    f"{custo['valor_centavos'] / 100:.2f}".replace(".", ",")
                    if em_ed else ""
                ),
                keyboard_type=ft.KeyboardType.NUMBER,
                border_radius=12,
            )
    
            c_msg = ft.Text(
                "",
                size=12,
                color="#B00020",
            )
    
            def salvar_cf(e):
    
                try:
                    desc = (c_desc.value or "").strip()
    
                    v = float(
                        (c_val.value or "").replace(",", ".")
                    )
    
                    if not desc or v < 0:
                        c_msg.value = (
                            "Preencha a descrição e valor válido."
                        )
                        page.update()
                        return
    
                    val_centavos = round(v * 100)
    
                    if em_ed:
                        atualizar_custo_fixo(
                            custo["id"],
                            desc,
                            val_centavos,
                        )
                    else:
                        cadastrar_custo_fixo(
                            desc,
                            val_centavos,
                        )
    
                    abrir_custos_fixos()
    
                except Exception as err:
                    c_msg.value = f"Erro: {err}"
                    page.update()
    
            def deletar_cf(e):
    
                if em_ed:
                    excluir_custo_fixo(custo["id"])
                    abrir_custos_fixos()
    
            ctrls = [
                c_desc,
                c_val,
                c_msg,
                ft.Container(
                    width=380,
                    padding=12,
                    bgcolor=ROSA,
                    border_radius=12,
                    on_click=salvar_cf,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        controls=[
                            ft.Text(
                                "Salvar Custo Fixo",
                                color=BRANCO,
                                weight=ft.FontWeight.BOLD,
                            )
                        ],
                    ),
                ),
            ]
    
            if em_ed:
                ctrls.append(
                    ft.Container(
                        width=380,
                        padding=12,
                        bgcolor="#B00020",
                        border_radius=12,
                        on_click=deletar_cf,
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            controls=[
                                ft.Text(
                                    "Excluir Despesa",
                                    color=BRANCO,
                                    weight=ft.FontWeight.BOLD,
                                )
                            ],
                        ),
                    )
                )
    
            tela_modal = ft.Column(
                expand=True,
                scroll=ft.ScrollMode.AUTO,
                spacing=14,
                controls=[
                    ft.Container(
                        padding=ft.Padding.only(
                            left=15,
                            right=20,
                            top=20,
                            bottom=5,
                        ),
                        content=ft.Row(
                            controls=[
                                ft.Container(
                                    padding=8,
                                    border_radius=10,
                                    on_click=abrir_custos_fixos,
                                    content=ft.Icon(
                                        ft.Icons.ARROW_BACK,
                                        color=MARROM,
                                        size=24,
                                    ),
                                ),
                                ft.Text(
                                    "Editar Custo Fixo"
                                    if em_ed else "Novo Custo Fixo",
                                    size=20,
                                    weight=ft.FontWeight.BOLD,
                                    color=MARROM,
                                ),
                            ]
                        ),
                    ),
                    ft.Container(
                        padding=ft.Padding.symmetric(horizontal=18),
                        content=ft.Column(
                            spacing=12,
                            controls=ctrls,
                        ),
                    ),
                ],
            )
    
            page.controls.clear()
            page.add(tela_modal)
            page.update()
    
        # --------------------------------------------------
        # LISTA DE CUSTOS
        # --------------------------------------------------
    
        lista_custos = ft.Column(spacing=10)
    
        for c in custos:
    
            c_item = c
    
            lista_custos.controls.append(
                ft.Container(
                    bgcolor=BRANCO,
                    padding=14,
                    border_radius=12,
                    on_click=lambda e, item=c_item:
                        abrir_form_custo_fixo(item),
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Text(
                                        c["descricao"],
                                        weight=ft.FontWeight.BOLD,
                                        color=MARROM,
                                        size=15,
                                    ),
                                    ft.Text(
                                        "Toque para editar ou excluir",
                                        size=10,
                                        color=TEXTO_SECUNDARIO,
                                    ),
                                ],
                            ),
                            ft.Text(
                                f"R$ {c['valor_centavos'] / 100:.2f}",
                                color=ROSA,
                                weight=ft.FontWeight.BOLD,
                                size=16,
                            ),
                        ],
                    ),
                )
            )
    
        tela = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=16,
            controls=[
                ft.Container(
                    padding=ft.Padding.only(
                        left=15,
                        right=20,
                        top=20,
                        bottom=10,
                    ),
                    content=ft.Row(
                        controls=[
                            ft.Container(
                                padding=8,
                                border_radius=10,
                                on_click=voltar_inicio,
                                content=ft.Icon(
                                    ft.Icons.ARROW_BACK,
                                    color=MARROM,
                                    size=24,
                                ),
                            ),
                            ft.Text(
                                "Custos Fixos & Rateio",
                                size=22,
                                weight=ft.FontWeight.BOLD,
                                color=MARROM,
                            ),
                        ],
                    ),
                ),
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=18),
                    content=ft.Column(
                        spacing=14,
                        controls=[
                            ft.Container(
                                bgcolor=ROSA_CLARO,
                                padding=16,
                                border_radius=14,
                                content=ft.Column(
                                    controls=[
                                        ft.Text(
                                            "RESUMO DO RATEIO DE CUSTO FIXO",
                                            size=11,
                                            weight=ft.FontWeight.BOLD,
                                            color=TEXTO_SECUNDARIO,
                                        ),
                                        ft.Text(
                                            f"Total Despesas: R$ {total_custos:.2f}",
                                            size=18,
                                            weight=ft.FontWeight.BOLD,
                                            color=MARROM,
                                        ),
                                        ft.Text(
                                            f"Taxa de Rateio: {fator_percentual:.1f}% "
                                            "sobre o custo de insumos",
                                            size=13,
                                            color=ROSA,
                                            weight=ft.FontWeight.BOLD,
                                        ),
                                    ]
                                ),
                            ),
                            campo_faturamento,
                            ft.Text("REMUNERAÇÃO E TEMPO PRODUTIVO", weight=ft.FontWeight.BOLD, color=MARROM, size=13),
                            ft.Row(controls=[campo_remuneracao, campo_horas_produtivas]),
                            ft.Text("PARÂMETROS GERAIS DE PRECIFICAÇÃO", weight=ft.FontWeight.BOLD, color=MARROM, size=13),
                            ft.Row(controls=[campo_markup_ideal, campo_margem_minima]),
                            campo_impostos,
                            ft.Divider(color=ROSA_CLARO),
                            ft.Text("TAXAS POR FORMA DE PAGAMENTO", weight=ft.FontWeight.BOLD, color=MARROM, size=13),
                            ft.Row(controls=[campo_taxa_pix, campo_taxa_dinheiro]),
                            ft.Row(controls=[campo_taxa_debito, campo_taxa_credito]),
                            campo_taxa_parcelado,
                            mensagem_custos,
                            ft.Container(
                                width=380, padding=12, bgcolor=ROSA, border_radius=12, on_click=salvar_configuracoes_acao,
                                content=ft.Row(alignment=ft.MainAxisAlignment.CENTER, controls=[ft.Text("Atualizar Configurações", color=BRANCO, weight=ft.FontWeight.BOLD)])
                            ),
                            ft.Divider(color=ROSA_CLARO),
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text(
                                        "Despesas Fixas Cadastradas:",
                                        weight=ft.FontWeight.BOLD,
                                        color=MARROM,
                                    ),
                                    ft.IconButton(
                                        ft.Icons.ADD_CIRCLE,
                                        icon_color=ROSA,
                                        on_click=lambda e:
                                            abrir_form_custo_fixo(),
                                    ),
                                ],
                            ),
                            lista_custos,
                        ],
                    ),
                ),
            ],
        )
    
        indice_atual["valor"] = 2
        navegacao.selected_index = 2
        page.controls.clear()
        page.add(tela)
        page.update()
    
    # ==================================================
    # RELATÓRIOS
    # ==================================================
    

    return abrir_custos_fixos
