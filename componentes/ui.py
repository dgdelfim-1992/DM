"""Componentes visuais padronizados, independentes das telas."""


def criar_componentes_padrao(ft, paleta):
    """Cria os construtores visuais com a paleta ativa da aplicação."""
    rosa = paleta["rosa"]
    rosa_claro = paleta["rosa_claro"]
    marrom = paleta["marrom"]
    branco = paleta["branco"]
    texto_secundario = paleta["texto_secundario"]

    def criar_campo_padrao(**kwargs):
        kwargs.setdefault(
            "border",
            {
                ft.ControlState.DEFAULT: ft.OutlineInputBorder(
                    border_radius=12,
                    side=ft.BorderSide(width=1, color=rosa_claro),
                ),
                ft.ControlState.FOCUSED: ft.OutlineInputBorder(
                    border_radius=12,
                    side=ft.BorderSide(width=2, color=rosa),
                ),
            },
        )
        kwargs.setdefault("cursor_color", rosa)
        kwargs.setdefault("label_style", ft.TextStyle(color=texto_secundario))
        return ft.TextField(**kwargs)

    def criar_dropdown_padrao(**kwargs):
        kwargs.setdefault(
            "border",
            {
                ft.ControlState.DEFAULT: ft.OutlineInputBorder(
                    border_radius=12,
                    side=ft.BorderSide(width=1, color=rosa_claro),
                ),
                ft.ControlState.FOCUSED: ft.OutlineInputBorder(
                    border_radius=12,
                    side=ft.BorderSide(width=2, color=rosa),
                ),
            },
        )
        kwargs.setdefault("label_style", ft.TextStyle(color=texto_secundario))
        return ft.Dropdown(**kwargs)

    def criar_dialogo_padrao(*args, **kwargs):
        kwargs.setdefault("bgcolor", branco)
        kwargs.setdefault("shape", ft.RoundedRectangleBorder(radius=18))
        return ft.AlertDialog(*args, **kwargs)

    def criar_cabecalho_padrao(titulo, subtitulo, acao_voltar):
        return ft.Container(
            padding=ft.Padding.only(left=18, right=18, top=20, bottom=4),
            content=ft.Row(
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        width=40,
                        height=40,
                        bgcolor=rosa_claro,
                        border_radius=12,
                        alignment=ft.Alignment(0, 0),
                        on_click=acao_voltar,
                        content=ft.Icon(ft.Icons.ARROW_BACK_ROUNDED, color=marrom, size=22),
                    ),
                    ft.Column(
                        expand=True,
                        spacing=3,
                        controls=[
                            ft.Text(titulo, size=22, weight=ft.FontWeight.BOLD, color=marrom),
                            ft.Text(subtitulo, size=12, color=texto_secundario),
                        ],
                    ),
                ],
            ),
        )

    def criar_botao_primario(texto, acao, icone=ft.Icons.ADD):
        return ft.Container(
            height=52,
            padding=ft.Padding.symmetric(horizontal=16),
            bgcolor=rosa,
            border_radius=14,
            on_click=acao,
            alignment=ft.Alignment(0, 0),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=9,
                controls=[
                    ft.Icon(icone, color=branco, size=21),
                    ft.Text(texto, color=branco, weight=ft.FontWeight.BOLD, size=14),
                ],
            ),
        )

    return {
        "campo": criar_campo_padrao,
        "dropdown": criar_dropdown_padrao,
        "dialogo": criar_dialogo_padrao,
        "cabecalho": criar_cabecalho_padrao,
        "botao_primario": criar_botao_primario,
    }
