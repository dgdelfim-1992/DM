import flet as ft
from database.banco import (
    cadastrar_ingrediente,
    listar_ingredientes,
    obter_ingrediente,
    atualizar_ingrediente,
    cadastrar_receita,
    calcular_custo_receita,
    obter_conexao,
)


def main(page: ft.Page):

    # CONFIGURAÇÕES DA JANELA
    page.title = "DM Gulositos"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "#F8F1EF"
    page.padding = 0
    page.window.width = 420
    page.window.height = 850

    # PALETA DE CORES
    MARROM = "#603D3B"
    ROSA = "#A65F72"
    ROSA_CLARO = "#F8EDEB"
    TEXTO_SECUNDARIO = "#876A65"
    BRANCO = "#FFFFFF"

    indice_atual = {"valor": 0}

    # ==================================================
    # NAVEGAÇÃO
    # ==================================================

    def voltar_inicio(e=None):
        indice_atual["valor"] = 0
        navegacao.selected_index = 0
        page.controls.clear()
        page.add(conteudo)
        page.update()

    def navegar(e):
        indice = e.control.selected_index

        if indice == 0:
            voltar_inicio()
        elif indice == 1:
            abrir_ingredientes()
        elif indice == 2 or indice == 3:
            abrir_receitas()
        else:
            navegacao.selected_index = indice_atual["valor"]
            page.update()

    # ==================================================
    # LISTA DE INGREDIENTES
    # ==================================================

    def abrir_ingredientes(e=None):

        ingredientes = listar_ingredientes()
        cartoes = []

        for ingrediente in ingredientes:
            preco = ingrediente["preco_pago_centavos"] / 100
            marca = ingrediente["marca"] or "Sem marca informada"
            ingrediente_id = ingrediente["id"]

            cartoes.append(
                ft.Container(
                    bgcolor=BRANCO,
                    padding=16,
                    border_radius=16,
                    on_click=lambda e, item_id=ingrediente_id: abrir_edicao_ingrediente(item_id),
                    content=ft.Column(
                        spacing=9,
                        controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text(
                                        ingrediente["nome"],
                                        size=17,
                                        weight=ft.FontWeight.BOLD,
                                        color=MARROM,
                                    ),
                                    ft.Icon(
                                        ft.Icons.EDIT_OUTLINED,
                                        color=ROSA,
                                    ),
                                ],
                            ),
                            ft.Text(
                                f"Marca: {marca}",
                                size=12,
                                color=TEXTO_SECUNDARIO,
                            ),
                            ft.Divider(color=ROSA_CLARO),
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text(
                                        f"{ingrediente['quantidade_compra']:g} "
                                        f"{ingrediente['unidade_compra']}",
                                        color=MARROM,
                                        size=13,
                                    ),
                                    ft.Text(
                                        f"R$ {preco:.2f}",
                                        color=MARROM,
                                        weight=ft.FontWeight.BOLD,
                                        size=16,
                                    ),
                                ],
                            ),
                            ft.Text(
                                f"Custo por {ingrediente['unidade_base']}: "
                                f"R$ {ingrediente['custo_por_unidade_base']:.5f}",
                                size=12,
                                color=ROSA,
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Text(
                                "Toque para editar",
                                size=10,
                                color=TEXTO_SECUNDARIO,
                            ),
                        ],
                    ),
                )
            )

        if not cartoes:
            cartoes.append(
                ft.Container(
                    padding=25,
                    bgcolor=BRANCO,
                    border_radius=16,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(
                                ft.Icons.INVENTORY_2_OUTLINED,
                                size=40,
                                color=ROSA,
                            ),
                            ft.Text(
                                "Nenhum ingrediente cadastrado.",
                                color=MARROM,
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
                        left=15, right=20, top=20, bottom=10
                    ),
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.START,
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
                            ft.Column(
                                spacing=3,
                                controls=[
                                    ft.Text(
                                        "Ingredientes",
                                        size=23,
                                        weight=ft.FontWeight.BOLD,
                                        color=MARROM,
                                    ),
                                    ft.Text(
                                        f"{len(ingredientes)} ingrediente(s) cadastrado(s)",
                                        size=12,
                                        color=TEXTO_SECUNDARIO,
                                    ),
                                ],
                            ),
                        ],
                    ),
                ),
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=18),
                    content=ft.Container(
                        width=380,
                        padding=14,
                        bgcolor=ROSA,
                        border_radius=12,
                        on_click=abrir_cadastro_ingrediente,
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            controls=[
                                ft.Icon(ft.Icons.ADD, color=BRANCO),
                                ft.Text(
                                    "Adicionar ingrediente",
                                    color=BRANCO,
                                    weight=ft.FontWeight.BOLD,
                                ),
                            ],
                        ),
                    ),
                ),
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=18),
                    content=ft.Column(spacing=12, controls=cartoes),
                ),
            ],
        )

        indice_atual["valor"] = 1
        navegacao.selected_index = 1
        page.controls.clear()
        page.add(tela)
        page.update()

    # ==================================================
    # FORMULÁRIO DE INGREDIENTES
    # ==================================================

    def abrir_cadastro_ingrediente(e=None):
        abrir_formulario_ingrediente()

    def abrir_edicao_ingrediente(ingrediente_id):
        ingrediente = obter_ingrediente(ingrediente_id)
        if ingrediente is None:
            abrir_ingredientes()
            return
        abrir_formulario_ingrediente(ingrediente)

    def abrir_formulario_ingrediente(ingrediente=None):
        em_edicao = ingrediente is not None

        campo_nome = ft.TextField(
            label="Nome do ingrediente *",
            hint_text="Ex.: Farinha de trigo",
            value=ingrediente["nome"] if em_edicao else "",
            border_radius=12,
            border_color=ROSA_CLARO,
        )

        campo_marca = ft.TextField(
            label="Marca",
            hint_text="Ex.: Qualy",
            value=(ingrediente["marca"] or "") if em_edicao else "",
            border_radius=12,
            border_color=ROSA_CLARO,
        )

        campo_fornecedor = ft.TextField(
            label="Fornecedor ou estabelecimento",
            hint_text="Onde foi comprado?",
            value=(ingrediente["fornecedor"] or "") if em_edicao else "",
            border_radius=12,
            border_color=ROSA_CLARO,
        )

        campo_quantidade = ft.TextField(
            label="Quantidade da embalagem *",
            hint_text="Ex.: 500",
            value=str(ingrediente["quantidade_compra"]) if em_edicao else "",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12,
            border_color=ROSA_CLARO,
        )

        campo_unidade = ft.TextField(
            label="Unidade de compra *",
            value=ingrediente["unidade_compra"] if em_edicao else "g",
            hint_text="g, kg, ml, l ou un",
            border_radius=12,
            border_color=ROSA_CLARO,
        )

        campo_preco = ft.TextField(
            label="Preço pago (R$) *",
            hint_text="Ex.: 6,99",
            value=(
                f"{ingrediente['preco_pago_centavos'] / 100:.2f}".replace(".", ",")
                if em_edicao else ""
            ),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12,
            border_color=ROSA_CLARO,
        )

        campo_observacoes = ft.TextField(
            label="Observações",
            hint_text="Informações adicionais...",
            value=(ingrediente["observacoes"] or "") if em_edicao else "",
            multiline=True,
            min_lines=2,
            max_lines=4,
            border_radius=12,
            border_color=ROSA_CLARO,
        )

        previa_custo = ft.Text(
            "Informe quantidade, unidade e preço para calcular.",
            size=13,
            color=TEXTO_SECUNDARIO,
        )

        mensagem = ft.Text("", size=12, color="#B00020")

        unidades = {
            "kg": (1000, "g"),
            "g": (1, "g"),
            "l": (1000, "ml"),
            "litro": (1000, "ml"),
            "litros": (1000, "ml"),
            "ml": (1, "ml"),
            "un": (1, "un"),
            "unidade": (1, "un"),
            "unidades": (1, "un"),
        }

        def atualizar_previa(e=None):
            try:
                quantidade = float((campo_quantidade.value or "").replace(",", "."))
                preco = float((campo_preco.value or "").replace(",", "."))
                unidade = (campo_unidade.value or "").strip().lower()

                if quantidade <= 0 or preco < 0:
                    raise ValueError

                if unidade not in unidades:
                    previa_custo.value = "Unidade inválida. Use g, kg, ml, l ou un."
                    previa_custo.color = "#B00020"
                    page.update()
                    return

                fator, unidade_base = unidades[unidade]
                custo = preco / (quantidade * fator)

                previa_custo.value = f"Custo calculado: R$ {custo:.5f} por {unidade_base}"
                previa_custo.color = ROSA

            except (ValueError, AttributeError):
                previa_custo.value = "Informe quantidade, unidade e preço para calcular."
                previa_custo.color = TEXTO_SECUNDARIO

            page.update()

        campo_quantidade.on_change = atualizar_previa
        campo_unidade.on_change = atualizar_previa
        campo_preco.on_change = atualizar_previa

        if em_edicao:
            atualizar_previa()

        def salvar_ingrediente(e=None):
            try:
                nome = (campo_nome.value or "").strip()
                marca = (campo_marca.value or "").strip()
                fornecedor = (campo_fornecedor.value or "").strip()
                observacoes = (campo_observacoes.value or "").strip()

                if not nome:
                    mensagem.value = "Informe o nome do ingrediente."
                    page.update()
                    return

                quantidade = float((campo_quantidade.value or "").replace(",", "."))
                preco = float((campo_preco.value or "").replace(",", "."))
                unidade = (campo_unidade.value or "").strip().lower()

                if quantidade <= 0:
                    mensagem.value = "A quantidade deve ser maior que zero."
                    page.update()
                    return

                if preco < 0:
                    mensagem.value = "O preço não pode ser negativo."
                    page.update()
                    return

                if unidade not in unidades:
                    mensagem.value = "Unidade inválida. Use g, kg, ml, l ou un."
                    page.update()
                    return

                preco_centavos = round(preco * 100)

                if em_edicao:
                    atualizar_ingrediente(
                        ingrediente_id=ingrediente["id"],
                        nome=nome,
                        marca=marca,
                        fornecedor=fornecedor,
                        quantidade_compra=quantidade,
                        unidade_compra=unidade,
                        preco_pago_centavos=preco_centavos,
                        observacoes=observacoes,
                    )
                else:
                    cadastrar_ingrediente(
                        nome=nome,
                        marca=marca,
                        fornecedor=fornecedor,
                        quantidade_compra=quantidade,
                        unidade_compra=unidade,
                        preco_pago_centavos=preco_centavos,
                        observacoes=observacoes,
                    )

                abrir_ingredientes()

            except ValueError as erro:
                mensagem.value = f"Verifique os dados: {erro}"
                page.update()
            except Exception as erro:
                mensagem.value = f"Não foi possível salvar: {erro}"
                page.update()

        titulo_formulario = "Editar ingrediente" if em_edicao else "Novo ingrediente"
        texto_botao = "Salvar alterações" if em_edicao else "Salvar ingrediente"

        tela = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=14,
            controls=[
                ft.Container(
                    padding=ft.Padding.only(left=15, right=20, top=20, bottom=5),
                    content=ft.Row(
                        controls=[
                            ft.Container(
                                padding=8,
                                border_radius=10,
                                on_click=abrir_ingredientes,
                                content=ft.Icon(ft.Icons.ARROW_BACK, color=MARROM, size=24),
                            ),
                            ft.Text(
                                titulo_formulario,
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
                        spacing=13,
                        controls=[
                            campo_nome,
                            campo_marca,
                            campo_fornecedor,
                            ft.Row(
                                controls=[
                                    ft.Container(expand=2, content=campo_quantidade),
                                    ft.Container(expand=1, content=campo_unidade),
                                ],
                            ),
                            campo_preco,
                            ft.Container(
                                bgcolor=ROSA_CLARO,
                                padding=15,
                                border_radius=12,
                                content=ft.Column(
                                    spacing=7,
                                    controls=[
                                        ft.Text(
                                            "CÁLCULO DO CUSTO UNITÁRIO",
                                            size=11,
                                            weight=ft.FontWeight.BOLD,
                                            color=MARROM,
                                        ),
                                        previa_custo,
                                    ],
                                ),
                            ),
                            campo_observacoes,
                            mensagem,
                            ft.Container(
                                width=380,
                                padding=14,
                                bgcolor=ROSA,
                                border_radius=12,
                                on_click=salvar_ingrediente,
                                content=ft.Row(
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    controls=[
                                        ft.Icon(ft.Icons.SAVE_OUTLINED, color=BRANCO),
                                        ft.Text(texto_botao, color=BRANCO, weight=ft.FontWeight.BOLD),
                                    ],
                                ),
                            ),
                        ],
                    ),
                ),
            ],
        )

        indice_atual["valor"] = 1
        navegacao.selected_index = 1
        page.controls.clear()
        page.add(tela)
        page.update()

    # ==================================================
    # LISTA DE RECEITAS
    # ==================================================

    def abrir_receitas(e=None):
        conexao = obter_conexao()
        receitas = []
        try:
            receitas = conexao.execute("SELECT * FROM receitas WHERE ativo = 1 ORDER BY nome").fetchall()
        finally:
            conexao.close()

        cartoes = []

        for rec in receitas:
            calculo = calcular_custo_receita(rec["id"])
            if not calculo:
                continue

            cartoes.append(
                ft.Container(
                    bgcolor=BRANCO,
                    padding=16,
                    border_radius=16,
                    content=ft.Column(
                        spacing=8,
                        controls=[
                            ft.Text(rec["nome"], size=18, weight=ft.FontWeight.BOLD, color=MARROM),
                            ft.Text(
                                f"Rendimento: {rec['rendimento_unidades']:g} porção(ões)",
                                size=12,
                                color=TEXTO_SECUNDARIO,
                            ),
                            ft.Divider(color=ROSA_CLARO),
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text("Custo Unitário:", color=MARROM, size=13),
                                    ft.Text(
                                        f"R$ {calculo['custo_unitario']:.2f}",
                                        color=MARROM,
                                        weight=ft.FontWeight.BOLD,
                                        size=14,
                                    ),
                                ],
                            ),
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text(f"Preço Venda Sugerido (+{rec['margem_lucro_pct']}%):", color=ROSA, size=13, weight=ft.FontWeight.BOLD),
                                    ft.Text(
                                        f"R$ {calculo['preco_venda_sugerido']:.2f}",
                                        color=ROSA,
                                        weight=ft.FontWeight.BOLD,
                                        size=16,
                                    ),
                                ],
                            ),
                        ],
                    ),
                )
            )

        if not cartoes:
            cartoes.append(
                ft.Container(
                    padding=25,
                    bgcolor=BRANCO,
                    border_radius=16,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(ft.Icons.MENU_BOOK_OUTLINED, size=40, color=ROSA),
                            ft.Text("Nenhuma receita cadastrada.", color=MARROM),
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
                    padding=ft.Padding.only(left=15, right=20, top=20, bottom=10),
                    content=ft.Row(
                        controls=[
                            ft.Container(
                                padding=8,
                                border_radius=10,
                                on_click=voltar_inicio,
                                content=ft.Icon(ft.Icons.ARROW_BACK, color=MARROM, size=24),
                            ),
                            ft.Column(
                                spacing=3,
                                controls=[
                                    ft.Text("Receitas / Fichas Técnicas", size=22, weight=ft.FontWeight.BOLD, color=MARROM),
                                    ft.Text(f"{len(receitas)} receita(s) cadastrada(s)", size=12, color=TEXTO_SECUNDARIO),
                                ],
                            ),
                        ],
                    ),
                ),
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=18),
                    content=ft.Container(
                        width=380,
                        padding=14,
                        bgcolor=ROSA,
                        border_radius=12,
                        on_click=abrir_cadastro_receita,
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            controls=[
                                ft.Icon(ft.Icons.ADD, color=BRANCO),
                                ft.Text("Nova Receita / Ficha Técnica", color=BRANCO, weight=ft.FontWeight.BOLD),
                            ],
                        ),
                    ),
                ),
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=18),
                    content=ft.Column(spacing=12, controls=cartoes),
                ),
            ],
        )

        indice_atual["valor"] = 2
        navegacao.selected_index = 2
        page.controls.clear()
        page.add(tela)
        page.update()

    # ==================================================
    # CADASTRO DE RECEITA
    # ==================================================

    def abrir_cadastro_receita(e=None):
        ingredientes_disponiveis = listar_ingredientes()
        if not ingredientes_disponiveis:
            page.snack_bar = ft.SnackBar(ft.Text("Cadastre pelo menos um ingrediente antes de criar receitas!"))
            page.snack_bar.open = True
            page.update()
            return

        campo_nome_rec = ft.TextField(label="Nome da Receita *", hint_text="Ex.: Bolo de Cenoura com Gelado", border_radius=12)
        campo_rendimento = ft.TextField(label="Rendimento (unidades ou porções) *", value="1", keyboard_type=ft.KeyboardType.NUMBER, border_radius=12)
        campo_embalagem = ft.TextField(label="Custo Embalagens (R$)", value="0,00", keyboard_type=ft.KeyboardType.NUMBER, border_radius=12)
        campo_extras = ft.TextField(label="Custos Extras / Gás (R$)", value="0,00", keyboard_type=ft.KeyboardType.NUMBER, border_radius=12)
        campo_margem = ft.TextField(label="Margem de Lucro (%) *", value="100", keyboard_type=ft.KeyboardType.NUMBER, border_radius=12)

        mensagem_rec = ft.Text("", size=12, color="#B00020")
        ingredientes_selecionados = []
        lista_insumos_ui = ft.Column(spacing=8)

        def adicionar_insumo_ui(e=None):
            dropdown_ingrediente = ft.Dropdown(
                label="Selecione o ingrediente",
                expand=2,
                options=[
                    ft.dropdown.Option(str(ing["id"]), f"{ing['nome']} ({ing['unidade_base']})")
                    for ing in ingredientes_disponiveis
                ],
            )
            campo_qtd_usada = ft.TextField(
                label="Qtd usada",
                expand=1,
                keyboard_type=ft.KeyboardType.NUMBER,
            )

            linha = ft.Row(
                controls=[
                    dropdown_ingrediente,
                    campo_qtd_usada,
                ]
            )

            ingredientes_selecionados.append((dropdown_ingrediente, campo_qtd_usada))
            lista_insumos_ui.controls.append(linha)
            page.update()

        adicionar_insumo_ui()

        def salvar_nova_receita(e=None):
            try:
                nome = campo_nome_rec.value.strip()
                if not nome:
                    mensagem_rec.value = "Preencha o nome da receita."
                    page.update()
                    return

                rendimento = float(campo_rendimento.value.replace(",", "."))
                custo_emb = float(campo_embalagem.value.replace(",", "."))
                custo_ext = float(campo_extras.value.replace(",", "."))
                margem = float(campo_margem.value.replace(",", "."))

                lista_ing_salvar = []
                for drop, campo_q in ingredientes_selecionados:
                    if drop.value and campo_q.value:
                        lista_ing_salvar.append({
                            "ingrediente_id": int(drop.value),
                            "quantidade_usada": float(campo_q.value.replace(",", "."))
                        })

                if not lista_ing_salvar:
                    mensagem_rec.value = "Adicione ao menos um ingrediente com quantidade."
                    page.update()
                    return

                cadastrar_receita(
                    nome=nome,
                    rendimento_unidades=rendimento,
                    custo_embalagem_centavos=round(custo_emb * 100),
                    custos_extras_centavos=round(custo_ext * 100),
                    margem_lucro_pct=margem,
                    lista_ingredientes=lista_ing_salvar,
                )

                abrir_receitas()

            except Exception as err:
                mensagem_rec.value = f"Erro ao salvar receita: {err}"
                page.update()

        tela = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=14,
            controls=[
                ft.Container(
                    padding=ft.Padding.only(left=15, right=20, top=20, bottom=5),
                    content=ft.Row(
                        controls=[
                            ft.Container(
                                padding=8,
                                border_radius=10,
                                on_click=abrir_receitas,
                                content=ft.Icon(ft.Icons.ARROW_BACK, color=MARROM, size=24),
                            ),
                            ft.Text("Nova Receita / Ficha Técnica", size=20, weight=ft.FontWeight.BOLD, color=MARROM),
                        ],
                    ),
                ),
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=18),
                    content=ft.Column(
                        spacing=12,
                        controls=[
                            campo_nome_rec,
                            ft.Row(controls=[campo_rendimento, campo_margem]),
                            ft.Row(controls=[campo_embalagem, campo_extras]),
                            ft.Divider(color=ROSA_CLARO),
                            ft.Text("Ingredientes Utilizados", weight=ft.FontWeight.BOLD, color=MARROM),
                            lista_insumos_ui,
                            ft.TextButton("  Mais um ingrediente", icon=ft.Icons.ADD, on_click=adicionar_insumo_ui),
                            mensagem_rec,
                            ft.Container(
                                width=380,
                                padding=14,
                                bgcolor=ROSA,
                                border_radius=12,
                                on_click=salvar_nova_receita,
                                content=ft.Row(
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    controls=[
                                        ft.Icon(ft.Icons.SAVE_OUTLINED, color=BRANCO),
                                        ft.Text("Salvar e Calcular Receita", color=BRANCO, weight=ft.FontWeight.BOLD),
                                    ],
                                ),
                            ),
                        ],
                    ),
                ),
            ],
        )

        page.controls.clear()
        page.add(tela)
        page.update()

    # ==================================================
    # CABEÇALHO DA HOME
    # ==================================================

    cabecalho = ft.Container(
        padding=ft.Padding.only(left=20, right=20, top=25, bottom=15),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Column(
                    spacing=3,
                    controls=[
                        ft.Text("DM Gulositos", size=25, weight=ft.FontWeight.BOLD, color=MARROM),
                        ft.Text("GESTÃO E PRECIFICAÇÃO", size=10, color=TEXTO_SECUNDARIO),
                    ],
                ),
                ft.Container(
                    bgcolor=BRANCO,
                    padding=12,
                    border_radius=15,
                    content=ft.Icon(ft.Icons.CAKE_OUTLINED, color=ROSA, size=30),
                ),
            ],
        ),
    )

    # ==================================================
    # CARTÃO DE RESUMO
    # ==================================================

    resumo = ft.Container(
        bgcolor=BRANCO,
        padding=20,
        border_radius=18,
        content=ft.Column(
            spacing=15,
            controls=[
                ft.Text("RESUMO DO NEGÓCIO", size=11, weight=ft.FontWeight.BOLD, color=TEXTO_SECUNDARIO),
                ft.Row(
                    controls=[
                        criar_indicador("12", "Produtos cadastrados", MARROM),
                        criar_indicador("R$ 8,50", "Custo médio unitário", MARROM),
                    ],
                ),
                ft.Divider(color=ROSA_CLARO),
                ft.Row(
                    controls=[
                        criar_indicador("35%", "Margem média", ROSA),
                        criar_indicador("R$ 15,00", "Preço médio de venda", MARROM),
                    ],
                ),
            ],
        ),
    )

    # ==================================================
    # ACESSOS PRINCIPAIS
    # ==================================================

    atalhos = ft.Column(
        spacing=12,
        controls=[
            ft.Text("O que deseja fazer?", size=19, weight=ft.FontWeight.BOLD, color=MARROM),
            ft.Row(
                controls=[
                    criar_atalho(ft.Icons.INVENTORY_2_OUTLINED, "Ingredientes", "Insumos e preços", ROSA, abrir_ingredientes),
                    criar_atalho(ft.Icons.MENU_BOOK_OUTLINED, "Receitas", "Fichas técnicas", ROSA, abrir_receitas),
                ],
            ),
            ft.Row(
                controls=[
                    criar_atalho(ft.Icons.CALCULATE_OUTLINED, "Precificação", "Calcular valores", ROSA, abrir_receitas),
                    criar_atalho(ft.Icons.BAR_CHART_OUTLINED, "Relatórios", "Custos e lucros", ROSA),
                ],
            ),
        ],
    )

    # ==================================================
    # MENU INFERIOR
    # ==================================================

    navegacao = ft.NavigationBar(
        selected_index=0,
        on_change=navegar,
        bgcolor=BRANCO,
        indicator_color=ROSA_CLARO,
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.HOME_OUTLINED, selected_icon=ft.Icons.HOME, label="Início"),
            ft.NavigationBarDestination(icon=ft.Icons.INVENTORY_2_OUTLINED, label="Insumos"),
            ft.NavigationBarDestination(icon=ft.Icons.MENU_BOOK_OUTLINED, label="Receitas"),
            ft.NavigationBarDestination(icon=ft.Icons.CALCULATE_OUTLINED, label="Preços"),
            ft.NavigationBarDestination(icon=ft.Icons.MENU, label="Mais"),
        ],
    )

    # ==================================================
    # TELA INICIAL
    # ==================================================

    conteudo = ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        spacing=18,
        controls=[
            cabecalho,
            ft.Container(
                padding=ft.Padding.symmetric(horizontal=18),
                content=ft.Column(
                    spacing=18,
                    controls=[resumo, atalhos],
                ),
            ),
        ],
    )

    page.navigation_bar = navegacao
    page.add(conteudo)


def criar_indicador(valor, descricao, cor):
    return ft.Column(
        expand=True,
        spacing=4,
        controls=[
            ft.Text(valor, size=22, weight=ft.FontWeight.BOLD, color=cor),
            ft.Text(descricao, size=11, color="#876A65"),
        ],
    )


def criar_atalho(icone, titulo, descricao, cor, acao=None):
    return ft.Container(
        expand=True,
        bgcolor="#FFFFFF",
        padding=15,
        border_radius=16,
        on_click=acao,
        content=ft.Column(
            spacing=8,
            controls=[
                ft.Icon(icone, color=cor, size=28),
                ft.Text(titulo, color="#603D3B", weight=ft.FontWeight.BOLD, size=14),
                ft.Text(descricao, color="#876A65", size=11),
            ],
        ),
    )


# ft.run(main)
