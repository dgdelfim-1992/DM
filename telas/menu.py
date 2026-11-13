"""Construção independente do menu principal do DM Gulositos."""


def criar_tela_menu(ft, acoes, cores):
    """Monta o menu usando callbacks e cores fornecidos pela aplicação.

    Args:
        ft: módulo Flet utilizado pela aplicação.
        acoes: callbacks para ingredientes, receitas, custos, orçamentos,
            agenda, relatórios e backup.
        cores: paleta visual da aplicação.
    """
    marrom = cores["marrom"]
    rosa = cores["rosa"]
    rosa_claro = cores["rosa_claro"]
    branco = cores["branco"]
    texto_secundario = cores["texto_secundario"]

    def criar_card_menu(icone, titulo, descricao, acao):
        return ft.Container(
            expand=True,
            height=142,
            padding=14,
            bgcolor=branco,
            border_radius=18,
            on_click=acao,
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.START,
                spacing=9,
                controls=[
                    ft.Container(
                        width=42,
                        height=42,
                        border_radius=12,
                        bgcolor=rosa_claro,
                        alignment=ft.Alignment(0, 0),
                        content=ft.Icon(icone, color=rosa, size=23),
                    ),
                    ft.Text(titulo, size=14, weight=ft.FontWeight.BOLD, color=marrom),
                    ft.Text(descricao, size=10, color=texto_secundario),
                ],
            ),
        )

    return ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        spacing=16,
        controls=[
            ft.Container(
                padding=ft.Padding.only(left=18, right=18, top=22, bottom=2),
                content=ft.Column(
                    spacing=4,
                    controls=[
                        ft.Text("Menu Principal", size=24, weight=ft.FontWeight.BOLD, color=marrom),
                        ft.Text("Acesse as ferramentas da sua doceria.", size=12, color=texto_secundario),
                    ],
                ),
            ),
            ft.Container(
                padding=ft.Padding.symmetric(horizontal=18),
                content=ft.Column(
                    spacing=12,
                    controls=[
                        ft.Row(
                            spacing=12,
                            controls=[
                                criar_card_menu(ft.Icons.INVENTORY_2_OUTLINED, "Insumos", "Gerenciar estoque e preços", acoes["ingredientes"]),
                                criar_card_menu(ft.Icons.MENU_BOOK_OUTLINED, "Receitas", "Fichas técnicas e tempos", acoes["receitas"]),
                            ],
                        ),
                        ft.Row(
                            spacing=12,
                            controls=[
                                criar_card_menu(ft.Icons.CALCULATE_OUTLINED, "Custos Fixos", "Despesas, rateio e taxas", acoes["custos_fixos"]),
                                criar_card_menu(ft.Icons.DESCRIPTION_OUTLINED, "Orçamentos", "Montar e enviar propostas", acoes["orcamentos"]),
                            ],
                        ),
                        ft.Row(
                            spacing=12,
                            controls=[
                                criar_card_menu(ft.Icons.CALENDAR_MONTH_OUTLINED, "Agenda de Produção", "Organizar encomendas e entregas", acoes["agenda"]),
                                criar_card_menu(ft.Icons.BAR_CHART_OUTLINED, "Relatórios", "Análise de lucratividade", acoes["relatorios"]),
                            ],
                        ),
                        ft.Row(
                            spacing=12,
                            controls=[
                                criar_card_menu(ft.Icons.SAVE_OUTLINED, "Backup / Exportar", "Salvar e restaurar dados", acoes["backup"]),
                            ],
                        ),
                    ],
                ),
            ),
        ],
    )
