"""Tela de agenda de produção do DM Gulositos."""

def criar_abrir_agenda_producao(dependencias):
    ft = dependencias["ft"]
    datetime = dependencias["datetime"]
    timedelta = dependencias["timedelta"]
    json = dependencias["json"]
    listar_agenda_producao = dependencias["listar_agenda_producao"]
    atualizar_status_producao = dependencias["atualizar_status_producao"]
    mostrar_aviso = dependencias["mostrar_aviso"]
    BRANCO = dependencias["BRANCO"]
    ROSA = dependencias["ROSA"]
    ROSA_CLARO = dependencias["ROSA_CLARO"]
    MARROM = dependencias["MARROM"]
    TEXTO_SECUNDARIO = dependencias["TEXTO_SECUNDARIO"]
    page = dependencias["page"]
    abrir_menu_opcoes = dependencias["abrir_menu_opcoes"]
    indice_atual = dependencias["indice_atual"]
    navegacao_ref = dependencias["navegacao_ref"]

    def abrir_agenda_producao(e=None):
        filtro = {"valor": "Todos"}
        filtro_data = {"valor": "Todas"}

        def formatar_reais(valor):
            return ("R$ {:,.2f}".format(valor)).replace(",", "X").replace(".", ",").replace("X", ".")

        def obter_data_entrega(valor):
            try:
                return datetime.strptime(valor[:10], "%Y-%m-%d").date()
            except (ValueError, TypeError):
                return None

        def formatar_data(valor):
            data = obter_data_entrega(valor)
            return data.strftime("%d/%m/%Y") if data else (valor or "Sem data")

        conteudo = ft.Column(spacing=10)

        def aplicar_filtro(valor):
            filtro["valor"] = valor
            montar_agenda()

        def aplicar_filtro_data(valor):
            filtro_data["valor"] = valor
            montar_agenda()

        def montar_agenda():
            registros = listar_agenda_producao()
            hoje = datetime.now().date()
            limite_proximos_dias = hoje + timedelta(days=7)

            if filtro["valor"] != "Todos":
                registros = [
                    registro for registro in registros
                    if (registro["status_producao"] or "Pendente") == filtro["valor"]
                ]

            if filtro_data["valor"] == "Hoje":
                registros = [
                    registro for registro in registros
                    if obter_data_entrega(registro["data_entrega"]) == hoje
                ]
            elif filtro_data["valor"] == "Próximos 7 dias":
                registros = [
                    registro for registro in registros
                    if (obter_data_entrega(registro["data_entrega"]) is not None
                        and hoje < obter_data_entrega(registro["data_entrega"]) <= limite_proximos_dias)
                ]
            elif filtro_data["valor"] == "Atrasadas":
                registros = [
                    registro for registro in registros
                    if (obter_data_entrega(registro["data_entrega"]) is not None
                        and obter_data_entrega(registro["data_entrega"]) < hoje
                        and (registro["status_producao"] or "Pendente") != "Concluída")
                ]

            # Entregas mais próximas aparecem primeiro; registros sem data ficam no final.
            registros.sort(
                key=lambda registro: (
                    obter_data_entrega(registro["data_entrega"]) is None,
                    obter_data_entrega(registro["data_entrega"]) or hoje,
                )
            )

            cartoes = []
            for registro in registros:
                data_texto = formatar_data(registro["data_entrega"])
                data_entrega_obj = obter_data_entrega(registro["data_entrega"])
                status_atual = registro["status_producao"] or "Pendente"
                atrasada = (
                    data_entrega_obj is not None
                    and data_entrega_obj < hoje
                    and status_atual != "Concluída"
                )
                entrega_hoje = (
                    data_entrega_obj == hoje
                    and status_atual != "Concluída"
                )
                cor_cartao = "#FDECEC" if atrasada else ("#FFF4E5" if entrega_hoje else BRANCO)
                texto_data = "ATRASADA" if atrasada else ("ENTREGA HOJE" if entrega_hoje else data_texto)
                cor_data = "#C62828" if atrasada else ( "#A65F00" if entrega_hoje else ROSA)

                try:
                    itens = json.loads(registro["itens_json"] or "[]")
                    nomes_itens = [
                        f'{item.get("quantidade", 1):g} {item.get("unidade", "un")} - {item.get("nome", "Produto")}'
                        for item in itens
                    ]
                except (ValueError, TypeError):
                    nomes_itens = []

                def alterar_status(ev, oid=registro["id"]):
                    try:
                        atualizar_status_producao(oid, ev.control.value)
                        montar_agenda()
                        mostrar_aviso("Status da produção atualizado.")
                    except Exception as erro:
                        mostrar_aviso(f"Não foi possível atualizar: {erro}", "#C62828")

                cartoes.append(
                    ft.Container(
                        bgcolor=cor_cartao,
                        padding=15,
                        border_radius=16,
                        content=ft.Column(spacing=8, controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text(f'Encomenda {registro["numero"]}', weight=ft.FontWeight.BOLD, color=MARROM),
                                    ft.Text(
                                        texto_data,
                                        color=cor_data,
                                        weight=ft.FontWeight.BOLD,
                                        size=12,
                                    ),
                                ],
                            ),
                            ft.Text(registro["cliente"] or "Cliente não informado", color=TEXTO_SECUNDARIO, size=12),
                            ft.Text("Produtos: " + (", ".join(nomes_itens) if nomes_itens else "Consulte os detalhes do orçamento"), color=MARROM, size=12),
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text(
                                        "Total: " + formatar_reais(registro["total_final_centavos"] / 100),
                                        color=MARROM,
                                        weight=ft.FontWeight.BOLD,
                                        size=12,
                                    ),
                                    ft.Dropdown(
                                        width=155,
                                        dense=True,
                                        value=registro["status_producao"] or "Pendente",
                                        options=[
                                            ft.dropdown.Option("Pendente"),
                                            ft.dropdown.Option("Em produção"),
                                            ft.dropdown.Option("Concluída"),
                                        ],
                                        on_select=alterar_status,
                                    ),
                                ],
                            ),
                        ]),
                    )
                )

            if not cartoes:
                cartoes.append(
                    ft.Container(
                        bgcolor=BRANCO,
                        padding=22,
                        border_radius=16,
                        content=ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=8,
                            controls=[
                                ft.Icon(ft.Icons.CALENDAR_MONTH_OUTLINED, size=38, color=ROSA),
                                ft.Text("Nenhuma encomenda encontrada.", color=MARROM, weight=ft.FontWeight.BOLD),
                                ft.Text(
                                    "A agenda mostra orçamentos aprovados que tenham data de entrega.",
                                    color=TEXTO_SECUNDARIO,
                                    size=12,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                            ],
                        ),
                    )
                )

            conteudo.controls = [
                ft.Text("Filtrar por status", color=MARROM, weight=ft.FontWeight.BOLD, size=13),
                ft.Row(
                    wrap=True,
                    spacing=8,
                    controls=[
                        ft.Button(
                            nome,
                            on_click=lambda ev, valor=nome: aplicar_filtro(valor),
                            bgcolor=ROSA if filtro["valor"] == nome else ROSA_CLARO,
                            color=BRANCO if filtro["valor"] == nome else MARROM,
                        )
                        for nome in ["Todos", "Pendente", "Em produção", "Concluída"]
                    ],
                ),
                ft.Text("Filtrar por data de entrega", color=MARROM, weight=ft.FontWeight.BOLD, size=13),
                ft.Row(
                    wrap=True,
                    spacing=8,
                    controls=[
                        ft.Button(
                            nome,
                            on_click=lambda ev, valor=nome: aplicar_filtro_data(valor),
                            bgcolor=ROSA if filtro_data["valor"] == nome else ROSA_CLARO,
                            color=BRANCO if filtro_data["valor"] == nome else MARROM,
                        )
                        for nome in ["Todas", "Hoje", "Próximos 7 dias", "Atrasadas"]
                    ],
                ),
                *cartoes,
            ]
            page.update()

        tela = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=14,
            controls=[
                ft.Container(
                    padding=ft.Padding.only(left=15, right=18, top=18, bottom=6),
                    content=ft.Row(controls=[
                        ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=MARROM, on_click=abrir_menu_opcoes),
                        ft.Text("Agenda de Produção", size=22, weight=ft.FontWeight.BOLD, color=MARROM),
                    ]),
                ),
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=18),
                    content=conteudo,
                ),
            ],
        )
        indice_atual["valor"] = 2
        navegacao_ref["controle"].selected_index = 2
        page.controls.clear()
        page.add(tela)
        montar_agenda()


    return abrir_agenda_producao
