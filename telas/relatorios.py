"""Relatórios, indicadores e painel inicial do DM Gulositos."""


def criar_telas_relatorios(dependencias):
    """Cria callbacks das telas de relatório e do painel inicial."""
    ft = dependencias["ft"]
    page = dependencias["page"]
    datetime = dependencias["datetime"]
    LOGO_DM_BASE64 = dependencias["LOGO_DM_BASE64"]
    BRANCO = dependencias["BRANCO"]
    MARROM = dependencias["MARROM"]
    ROSA = dependencias["ROSA"]
    ROSA_CLARO = dependencias["ROSA_CLARO"]
    TEXTO_SECUNDARIO = dependencias["TEXTO_SECUNDARIO"]
    indice_atual = dependencias["indice_atual"]
    navegacao = dependencias["navegacao"]
    obter_conexao = dependencias["obter_conexao"]
    calcular_custo_receita = dependencias["calcular_custo_receita"]
    calcular_precificacao_produto = dependencias["calcular_precificacao_produto"]
    calcular_custo_fixo_proporcional = dependencias["calcular_custo_fixo_proporcional"]
    obter_dados_painel = dependencias["obter_dados_painel"]
    criar_indicador = dependencias["criar_indicador"]
    criar_atalho = dependencias["criar_atalho"]
    abrir_orcamentos = dependencias["abrir_orcamentos"]
    abrir_precificacao = dependencias["abrir_precificacao"]
    abrir_receitas = dependencias["abrir_receitas"]
    abrir_ingredientes = dependencias["abrir_ingredientes"]

    def abrir_relatorios(e=None):
    
        conexao = obter_conexao()
    
        try:
            receitas = conexao.execute(
                """
                SELECT *
                FROM receitas
                WHERE ativo = 1
                ORDER BY tipo DESC, nome
                """
            ).fetchall()
    
            custos = conexao.execute(
                """
                SELECT *
                FROM custos_fixos
                """
            ).fetchall()
    
            ingredientes = conexao.execute(
                """
                SELECT *
                FROM ingredientes
                WHERE ativo = 1
                """
            ).fetchall()
    
            fat_row = conexao.execute(
                """
                SELECT valor
                FROM configuracoes
                WHERE chave = 'faturamento_mensal'
                """
            ).fetchone()
    
            faturamento_alvo = (
                float(fat_row["valor"])
                if fat_row else 2000.0
            )
    
        finally:
            conexao.close()
    
        total_despesas_fixas = (
            sum(c["valor_centavos"] for c in custos) / 100
        )
    
        produtos_relatorio = []
    
        for receita in receitas:
    
            calculo = calcular_custo_receita(receita["id"])
    
            if not calculo:
                continue
    
            if receita["tipo"] == "PRODUTO":
    
                precificacao = calcular_precificacao_produto(
                    receita["id"]
                )
    
                if precificacao:
    
                    preco_venda = precificacao["preco_venda_sugerido"]
                    lucro = precificacao["lucro_unitario"]
    
                    margem_real = (
                        lucro / preco_venda * 100
                        if preco_venda > 0 else 0
                    )
    
                    produtos_relatorio.append(
                        {
                            "nome": receita["nome"],
                            "tipo": "Produto final",
                            "custo_unitario": precificacao["custo_unitario"],
                            "preco_sugerido": preco_venda,
                            "lucro": lucro,
                            "margem_real": margem_real,
                        }
                    )
    
                else:
    
                    rendimento = receita["rendimento_unidades"] or 0
    
                    custo_fixo_receita = calcular_custo_fixo_proporcional(
                        receita["id"]
                    )
                    custo_total_receita = (
                        calculo["custo_insumos"] + custo_fixo_receita
                    )
                    custo_unitario = (
                        custo_total_receita / rendimento
                        if rendimento > 0 else 0
                    )
    
                    produtos_relatorio.append(
                        {
                            "nome": receita["nome"],
                            "tipo": "Produto final",
                            "custo_unitario": custo_unitario,
                            "preco_sugerido": None,
                            "lucro": None,
                            "margem_real": None,
                        }
                    )
    
            else:
    
                rendimento = receita["rendimento_unidades"] or 0
    
                custo_unitario = (
                    calculo["custo_insumos"] / rendimento
                    if rendimento > 0 else 0
                )
    
                produtos_relatorio.append(
                    {
                        "nome": receita["nome"],
                        "tipo": "Sub-receita",
                        "custo_unitario": custo_unitario,
                        "preco_sugerido": None,
                        "lucro": None,
                        "margem_real": None,
                    }
                )
    
        # --------------------------------------------------
        # CARTÕES DO RELATÓRIO
        # --------------------------------------------------
    
        cartoes_relatorio = []
    
        for item in produtos_relatorio:
    
            if item["tipo"] == "Sub-receita":
    
                conteudo = ft.Column(
                    spacing=6,
                    controls=[
                        ft.Text(
                            item["nome"],
                            weight=ft.FontWeight.BOLD,
                            color=MARROM,
                            size=15,
                        ),
                        ft.Text(
                            "Sub-receita — custo de produção",
                            size=11,
                            color=TEXTO_SECUNDARIO,
                        ),
                        ft.Text(
                            f"Custo por unidade de rendimento: "
                            f"R$ {item['custo_unitario']:.4f}",
                            color=ROSA,
                            weight=ft.FontWeight.BOLD,
                        ),
                    ],
                )
    
            elif item["preco_sugerido"] is None:
    
                conteudo = ft.Column(
                    spacing=6,
                    controls=[
                        ft.Text(
                            item["nome"],
                            weight=ft.FontWeight.BOLD,
                            color=MARROM,
                            size=15,
                        ),
                        ft.Text(
                            "Produto final — ainda não precificado",
                            size=11,
                            color=TEXTO_SECUNDARIO,
                        ),
                        ft.Text(
                            f"Custo por unidade de rendimento: "
                            f"R$ {item['custo_unitario']:.4f}",
                            color=ROSA,
                            weight=ft.FontWeight.BOLD,
                        ),
                    ],
                )
    
            else:
    
                conteudo = ft.Column(
                    spacing=6,
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text(
                                    item["nome"],
                                    weight=ft.FontWeight.BOLD,
                                    color=MARROM,
                                    size=15,
                                ),
                                ft.Text(
                                    f"Lucro: R$ {item['lucro']:.2f}",
                                    color=ROSA,
                                    weight=ft.FontWeight.BOLD,
                                    size=14,
                                ),
                            ],
                        ),
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text(
                                    f"Custo: R$ {item['custo_unitario']:.4f}",
                                    size=12,
                                    color=TEXTO_SECUNDARIO,
                                ),
                                ft.Text(
                                    f"Preço: R$ {item['preco_sugerido']:.2f}",
                                    size=12,
                                    color=MARROM,
                                    weight=ft.FontWeight.BOLD,
                                ),
                            ],
                        ),
                        ft.Text(
                            f"Margem efetiva: {item['margem_real']:.1f}%",
                            size=11,
                            color=ROSA,
                            weight=ft.FontWeight.BOLD,
                        ),
                    ],
                )
    
            cartoes_relatorio.append(
                ft.Container(
                    bgcolor=BRANCO,
                    padding=14,
                    border_radius=12,
                    content=conteudo,
                )
            )
    
        if not cartoes_relatorio:
            cartoes_relatorio.append(
                ft.Container(
                    bgcolor=BRANCO,
                    padding=16,
                    border_radius=12,
                    content=ft.Text(
                        "Ainda não existem dados para exibir.",
                        color=TEXTO_SECUNDARIO,
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
                                "Relatórios & Lucratividade",
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
                                            "INDICADORES GERAIS",
                                            size=11,
                                            weight=ft.FontWeight.BOLD,
                                            color=TEXTO_SECUNDARIO,
                                        ),
                                        ft.Row(
                                            controls=[
                                                criar_indicador(
                                                    str(len(receitas)),
                                                    "Receitas cadastradas",
                                                    MARROM,
                                                ),
                                                criar_indicador(
                                                    str(len(ingredientes)),
                                                    "Insumos cadastrados",
                                                    MARROM,
                                                ),
                                            ],
                                        ),
                                        ft.Divider(color=ROSA),
                                        ft.Row(
                                            controls=[
                                                criar_indicador(
                                                    f"R$ {total_despesas_fixas:.2f}",
                                                    "Despesas fixas",
                                                    MARROM,
                                                ),
                                                criar_indicador(
                                                    f"R$ {faturamento_alvo:.2f}",
                                                    "Faturamento alvo",
                                                    ROSA,
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                            ),
                            ft.Text(
                                "Custos e lucratividade",
                                weight=ft.FontWeight.BOLD,
                                color=MARROM,
                            ),
                            ft.Column(
                                spacing=10,
                                controls=cartoes_relatorio,
                            ),
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
    # PAINEL INICIAL - DM GULOSITOS
    # ==================================================
    
    def criar_card_painel(icone, valor, titulo, descricao, cor, acao):
        return ft.Container(
            expand=True,
            bgcolor=BRANCO,
            padding=14,
            border_radius=16,
            on_click=acao,
            content=ft.Row(
                spacing=10,
                controls=[
                    ft.Container(
                        width=42,
                        height=42,
                        bgcolor=ROSA_CLARO,
                        border_radius=12,
                        alignment=ft.Alignment(0, 0),
                        content=ft.Icon(icone, color=cor, size=22),
                    ),
                    ft.Column(
                        expand=True,
                        spacing=2,
                        controls=[
                            ft.Text(str(valor), size=22, weight=ft.FontWeight.BOLD, color=MARROM),
                            ft.Text(titulo, size=12, weight=ft.FontWeight.BOLD, color=MARROM),
                            ft.Text(descricao, size=10, color=TEXTO_SECUNDARIO),
                        ],
                    ),
                ],
            ),
        )
    
    def montar_painel_inicial():
        painel = obter_dados_painel()
        agora = datetime.now()
        hora = agora.hour
        saudacao = "Bom dia" if hora < 12 else ("Boa tarde" if hora < 18 else "Boa noite")
    
        cabecalho = ft.Container(
            margin=ft.Margin.only(left=18, right=18, top=18),
            padding=16,
            bgcolor=BRANCO,
            border_radius=20,
            content=ft.Row(
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=14,
                controls=[
                    ft.Container(
                        width=82,
                        height=82,
                        padding=4,
                        bgcolor=ROSA_CLARO,
                        border_radius=16,
                        alignment=ft.Alignment(0, 0),
                        content=ft.Image(
                            src=LOGO_DM_BASE64,
                            width=74,
                            height=74,
                            fit=ft.BoxFit.CONTAIN,
                        ),
                    ),
                    ft.Column(
                        expand=True,
                        spacing=4,
                        controls=[
                            ft.Text(f"{saudacao}!", size=21, weight=ft.FontWeight.BOLD, color=MARROM),
                            ft.Text("Painel de gestão da doceria", size=12, color=TEXTO_SECUNDARIO),
                            ft.Text(agora.strftime("%d/%m/%Y"), size=11, color=ROSA, weight=ft.FontWeight.BOLD),
                        ],
                    ),
                ],
            ),
        )
    
        indicadores = ft.Column(
            spacing=10,
            controls=[
                ft.Row(
                    spacing=10,
                    controls=[
                        criar_card_painel(
                            ft.Icons.SEND,
                            painel["aguardando_retorno"],
                            "Enviados",
                            "Orçamentos aguardando retorno",
                            ROSA,
                            lambda ev: abrir_orcamentos(filtro_status="Enviado"),
                        ),
                        criar_card_painel(
                            ft.Icons.CHECK_CIRCLE,
                            painel["aprovados"],
                            "Aprovados",
                            "Encomendas confirmadas",
                            "#2E7D32",
                            lambda ev: abrir_orcamentos(filtro_status="Aprovado"),
                        ),
                    ],
                ),
                ft.Row(
                    spacing=10,
                    controls=[
                        criar_card_painel(
                            ft.Icons.EDIT,
                            painel["em_elaboracao"],
                            "Em elaboração",
                            "Orçamentos não enviados",
                            "#A66A20",
                            lambda ev: abrir_orcamentos(filtro_status="Em elaboração"),
                        ),
                        criar_card_painel(
                            ft.Icons.CANCEL,
                            painel["recusados"],
                            "Recusados",
                            "Orçamentos não aprovados",
                            "#A52D35",
                            lambda ev: abrir_orcamentos(filtro_status="Recusado"),
                        ),
                    ],
                ),
            ],
        )
    
        entregas_controles = []
        for entrega in painel["entregas"]:
            try:
                data_entrega_texto = datetime.strptime(
                    str(entrega["data_entrega"])[:10], "%Y-%m-%d"
                ).strftime("%d/%m")
            except (ValueError, TypeError):
                data_entrega_texto = str(entrega["data_entrega"] or "—")
    
            entregas_controles.append(
                ft.Container(
                    padding=12,
                    bgcolor=ROSA_CLARO,
                    border_radius=12,
                    on_click=lambda ev, oid=entrega["id"]: abrir_orcamentos(orcamento_id=oid),
                    content=ft.Row(
                        spacing=10,
                        controls=[
                            ft.Container(
                                width=48,
                                height=48,
                                bgcolor=BRANCO,
                                border_radius=12,
                                alignment=ft.Alignment(0, 0),
                                content=ft.Column(
                                    spacing=0,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    controls=[
                                        ft.Icon(ft.Icons.CALENDAR_TODAY, size=16, color=ROSA),
                                        ft.Text(data_entrega_texto, size=11, weight=ft.FontWeight.BOLD, color=MARROM),
                                    ],
                                ),
                            ),
                            ft.Column(
                                expand=True,
                                spacing=3,
                                controls=[
                                    ft.Text(
                                        entrega["cliente"] or "Cliente não informado",
                                        weight=ft.FontWeight.BOLD,
                                        color=MARROM,
                                        size=13,
                                    ),
                                    ft.Text(f'Orçamento {entrega["numero"]}', size=10, color=TEXTO_SECUNDARIO),
                                ],
                            ),
                            ft.Text(
                                "R$ " + f'{entrega["total_final_centavos"] / 100:,.2f}'.replace(",", "X").replace(".", ",").replace("X", "."),
                                size=12,
                                weight=ft.FontWeight.BOLD,
                                color=MARROM,
                            ),
                        ],
                    ),
                )
            )
    
        if not entregas_controles:
            entregas_controles.append(
                ft.Container(
                    padding=16,
                    bgcolor=ROSA_CLARO,
                    border_radius=12,
                    content=ft.Row(
                        spacing=10,
                        controls=[
                            ft.Icon(ft.Icons.CALENDAR_TODAY, color=ROSA, size=24),
                            ft.Text(
                                "Nenhuma entrega aprovada nos próximos 7 dias. "
                                "Cadastre a data de entrega nos novos orçamentos.",
                                size=12,
                                color=TEXTO_SECUNDARIO,
                                expand=True,
                            ),
                        ],
                    ),
                )
            )
    
        atividades_controles = []
        for atividade in painel["atividades"]:
            icone = {
                "Orçamento": ft.Icons.DESCRIPTION_OUTLINED,
                "Insumo": ft.Icons.INVENTORY_2_OUTLINED,
                "Precificação": ft.Icons.CALCULATE_OUTLINED,
            }.get(atividade["tipo"], ft.Icons.HISTORY)
    
            data_atividade = str(atividade["data"] or "")
            try:
                data_atividade = datetime.fromisoformat(
                    data_atividade.replace("Z", "+00:00")
                ).strftime("%d/%m %H:%M")
            except (ValueError, TypeError):
                data_atividade = data_atividade[:16].replace("T", " ")
    
            atividades_controles.append(
                ft.Row(
                    spacing=10,
                    controls=[
                        ft.Container(
                            width=34,
                            height=34,
                            bgcolor=ROSA_CLARO,
                            border_radius=10,
                            alignment=ft.Alignment(0, 0),
                            content=ft.Icon(icone, color=ROSA, size=18),
                        ),
                        ft.Column(
                            expand=True,
                            spacing=2,
                            controls=[
                                ft.Text(atividade["descricao"], size=12, weight=ft.FontWeight.BOLD, color=MARROM),
                                ft.Text(
                                    f'{atividade["tipo"]} • {atividade["detalhe"]}',
                                    size=10,
                                    color=TEXTO_SECUNDARIO,
                                ),
                            ],
                        ),
                        ft.Text(data_atividade, size=9, color=TEXTO_SECUNDARIO),
                    ],
                )
            )
    
        if not atividades_controles:
            atividades_controles.append(
                ft.Text(
                    "As movimentações recentes aparecerão aqui.",
                    size=12,
                    color=TEXTO_SECUNDARIO,
                )
            )
    
        atalhos_painel = ft.Column(
            spacing=10,
            controls=[
                ft.Row(
                    spacing=10,
                    controls=[
                        criar_atalho(
                            ft.Icons.ADD_CIRCLE_OUTLINE,
                            "Novo orçamento",
                            "Criar proposta para cliente",
                            ROSA,
                            abrir_orcamentos,
                        ),
                        criar_atalho(
                            ft.Icons.CALCULATE_OUTLINED,
                            "Precificação",
                            "Calcular preço de venda",
                            ROSA,
                            abrir_precificacao,
                        ),
                    ],
                ),
                ft.Row(
                    spacing=10,
                    controls=[
                        criar_atalho(
                            ft.Icons.MENU_BOOK_OUTLINED,
                            "Receitas",
                            "Fichas técnicas",
                            ROSA,
                            abrir_receitas,
                        ),
                        criar_atalho(
                            ft.Icons.INVENTORY_2_OUTLINED,
                            "Insumos",
                            "Cadastro e preços",
                            ROSA,
                            abrir_ingredientes,
                        ),
                    ],
                ),
            ],
        )
    
        return ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=16,
            controls=[
                cabecalho,
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=18),
                    content=ft.Column(
                        spacing=10,
                        controls=[
                            ft.Text("Visão geral", size=18, weight=ft.FontWeight.BOLD, color=MARROM),
                            ft.Text(
                                "Acompanhe os orçamentos e a rotina da doceria.",
                                size=11,
                                color=TEXTO_SECUNDARIO,
                            ),
                            indicadores,
                            ft.Text("Acessos rápidos", size=18, weight=ft.FontWeight.BOLD, color=MARROM),
                            atalhos_painel,
                            ft.Text("Próximas encomendas", size=18, weight=ft.FontWeight.BOLD, color=MARROM),
                            ft.Text(
                                "Entregas aprovadas previstas para os próximos 7 dias.",
                                size=11,
                                color=TEXTO_SECUNDARIO,
                            ),
                            ft.Container(
                                padding=12,
                                bgcolor=BRANCO,
                                border_radius=16,
                                content=ft.Column(spacing=9, controls=entregas_controles),
                            ),
                            ft.Text("Atividades recentes", size=18, weight=ft.FontWeight.BOLD, color=MARROM),
                            ft.Container(
                                padding=14,
                                bgcolor=BRANCO,
                                border_radius=16,
                                content=ft.Column(spacing=12, controls=atividades_controles),
                            ),
                        ],
                    ),
                ),
            ],
        )
    
    # ==================================================

    return abrir_relatorios, montar_painel_inicial
