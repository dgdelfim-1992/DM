"""Construção independente do menu principal do DM Gulositos."""


def criar_tela_menu(ft, acoes, cores):
    """Monta o menu responsivo usando callbacks e cores da aplicação.

    Args:
        ft: módulo Flet utilizado pela aplicação.
        acoes: callbacks dos módulos disponíveis no menu.
        cores: paleta visual da aplicação.
    """
    marrom = cores["marrom"]
    rosa = cores["rosa"]
    rosa_claro = cores["rosa_claro"]
    branco = cores["branco"]
    texto_secundario = cores["texto_secundario"]

    def criar_card_menu(icone, titulo, descricao, acao):
        return ft.Container(
            col={"xs": 12, "sm": 6, "lg": 4},
            height=148,
            padding=16,
            bgcolor=branco,
            border_radius=18,
            on_click=acao,
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.START,
                spacing=10,
                controls=[
                    ft.Container(
                        width=46,
                        height=46,
                        border_radius=14,
                        bgcolor=rosa_claro,
                        alignment=ft.Alignment(0, 0),
                        content=ft.Icon(icone, color=rosa, size=25),
                    ),
                    ft.Text(
                        titulo,
                        size=14,
                        weight=ft.FontWeight.BOLD,
                        color=marrom,
                    ),
                    ft.Text(
                        descricao,
                        size=11,
                        color=texto_secundario,
                    ),
                ],
            ),
        )

    def criar_secao(titulo, descricao, itens):
        return ft.Column(
            spacing=10,
            controls=[
                ft.Container(
                    padding=ft.Padding.only(left=2, right=2, top=4),
                    content=ft.Column(
                        spacing=3,
                        controls=[
                            ft.Text(
                                titulo,
                                size=15,
                                weight=ft.FontWeight.BOLD,
                                color=marrom,
                            ),
                            ft.Text(
                                descricao,
                                size=11,
                                color=texto_secundario,
                            ),
                        ],
                    ),
                ),
                ft.ResponsiveRow(
                    spacing=12,
                    run_spacing=12,
                    controls=[
                        criar_card_menu(icone, nome, detalhe, acoes[chave])
                        for chave, icone, nome, detalhe in itens
                    ],
                ),
            ],
        )

    return ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        spacing=20,
        controls=[
            ft.Container(
                padding=ft.Padding.only(left=18, right=18, top=22, bottom=2),
                content=ft.Container(
                    padding=20,
                    bgcolor=rosa_claro,
                    border_radius=20,
                    content=ft.Column(
                        spacing=6,
                        controls=[
                            ft.Text(
                                "DM GULOSITOS",
                                size=11,
                                weight=ft.FontWeight.BOLD,
                                color=rosa,
                            ),
                            ft.Text(
                                "Menu Principal",
                                size=24,
                                weight=ft.FontWeight.BOLD,
                                color=marrom,
                            ),
                            ft.Text(
                                "Tudo o que você precisa para organizar e "
                                "administrar sua doceria.",
                                size=12,
                                color=texto_secundario,
                            ),
                        ],
                    ),
                ),
            ),
            ft.Container(
                padding=ft.Padding.symmetric(horizontal=18),
                content=ft.Column(
                    spacing=20,
                    controls=[
                        criar_secao(
                            "Produção e cadastros",
                            "Gerencie os ingredientes, receitas e entregas.",
                            [
                                (
                                    "ingredientes",
                                    ft.Icons.INVENTORY_2_OUTLINED,
                                    "Insumos",
                                    "Estoque, fornecedores e preços",
                                ),
                                (
                                    "receitas",
                                    ft.Icons.MENU_BOOK_OUTLINED,
                                    "Receitas",
                                    "Fichas técnicas e tempos",
                                ),
                                (
                                    "agenda",
                                    ft.Icons.CALENDAR_MONTH_OUTLINED,
                                    "Agenda de Produção",
                                    "Encomendas e entregas",
                                ),
                            ],
                        ),
                        criar_secao(
                            "Gestão do negócio",
                            "Acompanhe os custos, vendas e resultados.",
                            [
                                (
                                    "custos_fixos",
                                    ft.Icons.CALCULATE_OUTLINED,
                                    "Custos Fixos",
                                    "Despesas, mão de obra e taxas",
                                ),
                                (
                                    "orcamentos",
                                    ft.Icons.DESCRIPTION_OUTLINED,
                                    "Orçamentos",
                                    "Propostas e acompanhamento",
                                ),
                                (
                                    "relatorios",
                                    ft.Icons.BAR_CHART_OUTLINED,
                                    "Relatórios",
                                    "Análise de custos e lucratividade",
                                ),
                            ],
                        ),
                        criar_secao(
                            "Segurança dos dados",
                            "Mantenha as informações da doceria protegidas.",
                            [
                                (
                                    "backup",
                                    ft.Icons.SAVE_OUTLINED,
                                    "Backup e Exportação",
                                    "Salvar e restaurar seus dados",
                                ),
                            ],
                        ),
                    ],
                ),
            ),
        ],
    )
