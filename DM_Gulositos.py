import flet as ft

from database.banco import (
    criar_tabelas,
    salvar_tempos_receita,
    salvar_horas_produtivas_mensais,
    obter_horas_produtivas_mensais,
    obter_custo_fixo_por_hora,
    salvar_precificacao_completa,
    calcular_precificacao_completa,
    salvar_precificacao_produto,
    obter_precificacao_produto,
    calcular_precificacao_produto,
    excluir_ingrediente,
    cadastrar_ingrediente,
    listar_ingredientes,
    obter_ingrediente,
    atualizar_ingrediente,
    cadastrar_receita,
    obter_receita,
    atualizar_receita,
    excluir_receita,
    calcular_custo_receita,
    cadastrar_custo_fixo,
    atualizar_custo_fixo,
    excluir_custo_fixo,
    obter_fator_custo_fixo,
    obter_conexao,
)


def main(page: ft.Page):

    criar_tabelas()

    # ==================================================
    # CONFIGURAÇÕES
    # ==================================================

    page.title = "DM Gulositos"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "#F8F1EF"
    page.padding = 0
    page.window.width = 420
    page.window.height = 850

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
        elif indice == 2:
            abrir_receitas()
        elif indice == 3:
            abrir_custos_fixos()
        elif indice == 4:
            abrir_relatorios()
        else:
            navegacao.selected_index = indice_atual["valor"]
            page.update()

    # ==================================================
    # INGREDIENTES
    # ==================================================

    def abrir_ingredientes(e=None):

        ingredientes = listar_ingredientes()
        cartoes = []

        # --------------------------------------------------
        # EXCLUSÃO COM DUPLA CONFIRMAÇÃO
        # --------------------------------------------------

        def solicitar_exclusao(ingrediente_id, nome):

            def fechar_primeiro(e):
                dialogo_primeiro.open = False
                page.update()

            def confirmar_segunda_etapa(e):
                dialogo_primeiro.open = False
                dialogo_segundo.open = True
                page.update()

            def voltar_primeira_etapa(e):
                dialogo_segundo.open = False
                dialogo_primeiro.open = True
                page.update()

            def executar_exclusao(e):

                dialogo_segundo.open = False
                page.update()

                try:
                    excluir_ingrediente(ingrediente_id)
                    abrir_ingredientes()

                except ValueError as erro:

                    def fechar_erro(e):
                        dialogo_erro.open = False
                        page.update()

                    dialogo_erro = ft.AlertDialog(
                        modal=True,
                        title=ft.Text("Não foi possível excluir"),
                        content=ft.Text(str(erro)),
                        actions=[
                            ft.TextButton(
                                "Entendi",
                                on_click=fechar_erro,
                            )
                        ],
                    )

                    page.overlay.append(dialogo_erro)
                    dialogo_erro.open = True
                    page.update()

                except Exception as erro:

                    def fechar_erro(e):
                        dialogo_erro.open = False
                        page.update()

                    dialogo_erro = ft.AlertDialog(
                        modal=True,
                        title=ft.Text("Erro ao excluir"),
                        content=ft.Text(
                            f"Ocorreu um erro inesperado:\n{erro}"
                        ),
                        actions=[
                            ft.TextButton(
                                "Entendi",
                                on_click=fechar_erro,
                            )
                        ],
                    )

                    page.overlay.append(dialogo_erro)
                    dialogo_erro.open = True
                    page.update()

            dialogo_primeiro = ft.AlertDialog(
                modal=True,
                title=ft.Text("Excluir ingrediente?"),
                content=ft.Text(
                    f"Deseja realmente excluir o ingrediente '{nome}'?"
                ),
                actions=[
                    ft.TextButton(
                        "Cancelar",
                        on_click=fechar_primeiro,
                    ),
                    ft.Button(
                        "Continuar",
                        on_click=confirmar_segunda_etapa,
                        bgcolor=ROSA,
                        color=BRANCO,
                    ),
                ],
            )

            dialogo_segundo = ft.AlertDialog(
                modal=True,
                title=ft.Text("Confirmação definitiva"),
                content=ft.Text(
                    f"Esta ação não poderá ser desfeita.\n\n"
                    f"Confirma a exclusão de '{nome}'?"
                ),
                actions=[
                    ft.TextButton(
                        "Voltar",
                        on_click=voltar_primeira_etapa,
                    ),
                    ft.Button(
                        "Excluir definitivamente",
                        on_click=executar_exclusao,
                        bgcolor="#C62828",
                        color=BRANCO,
                    ),
                ],
            )

            page.overlay.append(dialogo_primeiro)
            page.overlay.append(dialogo_segundo)

            dialogo_primeiro.open = True
            page.update()

        # --------------------------------------------------
        # CARTÕES
        # --------------------------------------------------

        for ingrediente in ingredientes:

            preco = ingrediente["preco_pago_centavos"] / 100
            marca = ingrediente["marca"] or "Sem marca informada"
            ingrediente_id = ingrediente["id"]
            nome_ingrediente = ingrediente["nome"]

            cartoes.append(
                ft.Container(
                    bgcolor=BRANCO,
                    padding=16,
                    border_radius=16,
                    on_click=lambda e, item_id=ingrediente_id:
                        abrir_edicao_ingrediente(item_id),
                    content=ft.Column(
                        spacing=9,
                        controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Container(
                                        expand=True,
                                        content=ft.Text(
                                            nome_ingrediente,
                                            size=17,
                                            weight=ft.FontWeight.BOLD,
                                            color=MARROM,
                                        ),
                                    ),
                                    ft.Row(
                                        spacing=2,
                                        controls=[
                                            ft.IconButton(
                                                icon=ft.Icons.EDIT_OUTLINED,
                                                icon_color=ROSA,
                                                tooltip="Editar ingrediente",
                                                on_click=lambda e, item_id=ingrediente_id:
                                                    abrir_edicao_ingrediente(item_id),
                                            ),
                                            ft.IconButton(
                                                icon=ft.Icons.DELETE_OUTLINE,
                                                icon_color="#C62828",
                                                tooltip="Excluir ingrediente",
                                                on_click=lambda e, item_id=ingrediente_id, nome=nome_ingrediente:
                                                    solicitar_exclusao(
                                                        item_id,
                                                        nome,
                                                    ),
                                            ),
                                        ],
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
                        left=15,
                        right=20,
                        top=20,
                        bottom=10,
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
                    content=ft.Column(
                        spacing=12,
                        controls=cartoes,
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

        unidades_antigas = {
            "litro": "l",
            "litros": "l",
            "unidade": "un",
            "unidades": "un",
        }

        unidade_atual = (
            ingrediente["unidade_compra"].strip().lower()
            if em_edicao else "g"
        )

        unidade_atual = unidades_antigas.get(
            unidade_atual,
            unidade_atual,
        )

        if unidade_atual not in ["g", "kg", "ml", "l", "un"]:
            unidade_atual = "g"

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

        campo_unidade = ft.Dropdown(
            label="Unidade de compra *",
            value=unidade_atual,
            border_radius=12,
            border_color=ROSA_CLARO,
            options=[
                ft.dropdown.Option("g", "Gramas (g)"),
                ft.dropdown.Option("kg", "Quilogramas (kg)"),
                ft.dropdown.Option("ml", "Mililitros (ml)"),
                ft.dropdown.Option("l", "Litros (L)"),
                ft.dropdown.Option("un", "Unidade (un)"),
            ],
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

        mensagem = ft.Text(
            "",
            size=12,
            color="#B00020",
        )

        unidades = {
            "kg": (1000, "g"),
            "g": (1, "g"),
            "l": (1000, "ml"),
            "ml": (1, "ml"),
            "un": (1, "un"),
        }

        def atualizar_previa(e=None):

            try:
                quantidade = float(
                    (campo_quantidade.value or "").replace(",", ".")
                )

                preco = float(
                    (campo_preco.value or "").replace(",", ".")
                )

                unidade = campo_unidade.value

                if quantidade <= 0 or preco < 0:
                    raise ValueError

                if unidade not in unidades:
                    raise ValueError

                fator, unidade_base = unidades[unidade]
                custo = preco / (quantidade * fator)

                previa_custo.value = (
                    f"Custo por {unidade_base}: R$ {custo:.5f}"
                )

                previa_custo.color = ROSA

            except (ValueError, AttributeError):
                previa_custo.value = (
                    "Informe quantidade, unidade e preço para calcular."
                )
                previa_custo.color = TEXTO_SECUNDARIO

            page.update()

        campo_quantidade.on_change = atualizar_previa
        campo_unidade.on_change = atualizar_previa
        campo_preco.on_change = atualizar_previa

        if em_edicao:
            atualizar_previa()

        # --------------------------------------------------
        # SALVAR INGREDIENTE
        # --------------------------------------------------

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

                quantidade = float(
                    (campo_quantidade.value or "").replace(",", ".")
                )

                preco = float(
                    (campo_preco.value or "").replace(",", ".")
                )

                unidade = campo_unidade.value

                if quantidade <= 0:
                    mensagem.value = "A quantidade deve ser maior que zero."
                    page.update()
                    return

                if preco < 0:
                    mensagem.value = "O preço não pode ser negativo."
                    page.update()
                    return

                if unidade not in unidades:
                    mensagem.value = "Selecione uma unidade válida."
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

        titulo_formulario = (
            "Editar ingrediente" if em_edicao else "Novo ingrediente"
        )

        texto_botao = (
            "Salvar alterações" if em_edicao else "Salvar ingrediente"
        )

        controles_formulario = [
            campo_nome,
            campo_marca,
            campo_fornecedor,
            ft.Row(
                controls=[
                    ft.Container(
                        expand=2,
                        content=campo_quantidade,
                    ),
                    ft.Container(
                        expand=1,
                        content=campo_unidade,
                    ),
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
                        ft.Icon(
                            ft.Icons.SAVE_OUTLINED,
                            color=BRANCO,
                        ),
                        ft.Text(
                            texto_botao,
                            color=BRANCO,
                            weight=ft.FontWeight.BOLD,
                        ),
                    ],
                ),
            ),
        ]

        tela = ft.Column(
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
                                on_click=abrir_ingredientes,
                                content=ft.Icon(
                                    ft.Icons.ARROW_BACK,
                                    color=MARROM,
                                    size=24,
                                ),
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
                        controls=controles_formulario,
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
    # RECEITAS
    # ==================================================

    filtro_receita = {"tipo": "TODOS"}

    def abrir_receitas(e=None):

        conexao = obter_conexao()

        try:
            receitas_todas = conexao.execute(
                """
                SELECT *
                FROM receitas
                WHERE ativo = 1
                ORDER BY nome
                """
            ).fetchall()
        finally:
            conexao.close()

        receitas_filtradas = [
            r for r in receitas_todas
            if filtro_receita["tipo"] == "TODOS"
            or r["tipo"] == filtro_receita["tipo"]
        ]

        # --------------------------------------------------
        # EXCLUSÃO COM DUPLA CONFIRMAÇÃO
        # --------------------------------------------------

        def confirmar_exclusao_receita(receita_id, nome_receita):

            def cancelar_primeira(e=None):
                dialogo_primeiro.open = False
                page.update()

            def continuar_exclusao(e=None):
                dialogo_primeiro.open = False
                dialogo_segundo.open = True
                page.update()

            def cancelar_segunda(e=None):
                dialogo_segundo.open = False
                page.update()

            def executar_exclusao(e=None):

                try:
                    excluir_receita(receita_id)

                    dialogo_segundo.open = False
                    page.update()

                    abrir_receitas()

                except Exception as erro:

                    dialogo_segundo.open = False

                    page.snack_bar = ft.SnackBar(
                        content=ft.Text(
                            f"Erro ao excluir receita: {erro}"
                        )
                    )

                    page.snack_bar.open = True
                    page.update()

            dialogo_primeiro = ft.AlertDialog(
                modal=True,
                title=ft.Text("Confirmar exclusão"),
                content=ft.Text(
                    f"Deseja realmente excluir a receita '{nome_receita}'?"
                ),
                actions=[
                    ft.TextButton(
                        "Cancelar",
                        on_click=cancelar_primeira,
                    ),
                    ft.TextButton(
                        "Continuar",
                        on_click=continuar_exclusao,
                    ),
                ],
            )

            dialogo_segundo = ft.AlertDialog(
                modal=True,
                title=ft.Text("Segunda confirmação"),
                content=ft.Text(
                    f"Confirma definitivamente a exclusão lógica "
                    f"de '{nome_receita}'?\n\n"
                    f"A receita deixará de aparecer na listagem."
                ),
                actions=[
                    ft.TextButton(
                        "Voltar",
                        on_click=cancelar_segunda,
                    ),
                    ft.TextButton(
                        "Sim, excluir",
                        on_click=executar_exclusao,
                    ),
                ],
            )

            page.overlay.append(dialogo_primeiro)
            page.overlay.append(dialogo_segundo)

            dialogo_primeiro.open = True
            page.update()

        # --------------------------------------------------
        # CARTÕES DAS RECEITAS
        # --------------------------------------------------

        cartoes = []

        for rec in receitas_filtradas:

            calculo = calcular_custo_receita(rec["id"])

            if not calculo:
                continue

            rec_id = rec["id"]
            nome_receita = rec["nome"]

            tipo_tag = (
                "SUB-RECEITA"
                if rec["tipo"] == "SUB_RECEITA"
                else "PRODUTO FINAL"
            )

            custo_insumos = calculo["custo_insumos"]
            rendimento = rec["rendimento_unidades"] or 0

            unidade_rendimento = rec["unidade_rendimento"] or "un"

            if unidade_rendimento not in ("un", "g"):
                unidade_rendimento = "un"

            custo_por_rendimento = (
                custo_insumos / rendimento
                if rendimento > 0
                else 0
            )

            texto_unidade = (
                "grama"
                if unidade_rendimento == "g"
                else "unidade"
            )

            tempo_preparo = rec["tempo_preparo_min"] or 0
            tempo_batedeira = rec["tempo_batedeira_min"] or 0
            tempo_forno = rec["tempo_forno_min"] or 0

            cartoes.append(
                ft.Container(
                    bgcolor=BRANCO,
                    padding=16,
                    border_radius=16,
                    content=ft.Column(
                        spacing=8,
                        controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Container(
                                        expand=True,
                                        content=ft.Text(
                                            nome_receita,
                                            size=17,
                                            weight=ft.FontWeight.BOLD,
                                            color=MARROM,
                                        ),
                                    ),
                                    ft.Container(
                                        content=ft.Text(
                                            tipo_tag,
                                            size=9,
                                            color=BRANCO,
                                            weight=ft.FontWeight.BOLD,
                                        ),
                                        bgcolor=(
                                            ROSA
                                            if rec["tipo"] == "PRODUTO"
                                            else MARROM
                                        ),
                                        padding=ft.Padding.symmetric(
                                            horizontal=8,
                                            vertical=4,
                                        ),
                                        border_radius=8,
                                    ),
                                    ft.Container(
                                        padding=6,
                                        border_radius=8,
                                        on_click=lambda e, item_id=rec_id:
                                            abrir_cadastro_receita(
                                                receita_id=item_id
                                            ),
                                        content=ft.Icon(
                                            ft.Icons.EDIT_OUTLINED,
                                            color=ROSA,
                                            size=21,
                                        ),
                                    ),
                                    ft.Container(
                                        padding=6,
                                        border_radius=8,
                                        on_click=lambda e, item_id=rec_id, nome=nome_receita:
                                            confirmar_exclusao_receita(
                                                item_id,
                                                nome,
                                            ),
                                        content=ft.Icon(
                                            ft.Icons.DELETE_OUTLINED,
                                            color="#B00020",
                                            size=21,
                                        ),
                                    ),
                                ],
                            ),
                            ft.Text(
                                f"Rendimento: {rendimento:g} "
                                f"{unidade_rendimento}",
                                size=12,
                                color=TEXTO_SECUNDARIO,
                            ),
                            ft.Divider(color=ROSA_CLARO),
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text(
                                        "Custo total dos insumos:",
                                        color=MARROM,
                                        size=12,
                                    ),
                                    ft.Text(
                                        f"R$ {custo_insumos:.2f}",
                                        color=MARROM,
                                        size=13,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                ],
                            ),
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text(
                                        f"Custo por {texto_unidade}:",
                                        color=MARROM,
                                        size=12,
                                    ),
                                    ft.Text(
                                        (
                                            f"R$ {custo_por_rendimento:.5f}"
                                            if rendimento > 0
                                            else "Rendimento não informado"
                                        ),
                                        color=ROSA,
                                        size=13,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                ],
                            ),
                            ft.Divider(color=ROSA_CLARO),
                            ft.Text(
                                "TEMPOS DE PRODUÇÃO",
                                size=11,
                                weight=ft.FontWeight.BOLD,
                                color=MARROM,
                            ),
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text(
                                        f"Preparo: {tempo_preparo:g} min",
                                        size=11,
                                        color=TEXTO_SECUNDARIO,
                                    ),
                                    ft.Text(
                                        f"Batedeira: {tempo_batedeira:g} min",
                                        size=11,
                                        color=TEXTO_SECUNDARIO,
                                    ),
                                    ft.Text(
                                        f"Forno: {tempo_forno:g} min",
                                        size=11,
                                        color=TEXTO_SECUNDARIO,
                                    ),
                                ],
                            ),
                            ft.Text(
                                "Use o lápis para editar ou a lixeira para excluir.",
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
                                ft.Icons.MENU_BOOK_OUTLINED,
                                size=40,
                                color=ROSA,
                            ),
                            ft.Text(
                                "Nenhuma receita encontrada para este filtro.",
                                color=MARROM,
                            ),
                        ],
                    ),
                )
            )

        # --------------------------------------------------
        # FILTROS
        # --------------------------------------------------

        def alterar_filtro(novo_tipo):
            filtro_receita["tipo"] = novo_tipo
            abrir_receitas()

        botoes_filtro = ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                ft.Button(
                    "Todos",
                    bgcolor=(
                        ROSA
                        if filtro_receita["tipo"] == "TODOS"
                        else ROSA_CLARO
                    ),
                    color=(
                        BRANCO
                        if filtro_receita["tipo"] == "TODOS"
                        else MARROM
                    ),
                    on_click=lambda e: alterar_filtro("TODOS"),
                ),
                ft.Button(
                    "Produtos",
                    bgcolor=(
                        ROSA
                        if filtro_receita["tipo"] == "PRODUTO"
                        else ROSA_CLARO
                    ),
                    color=(
                        BRANCO
                        if filtro_receita["tipo"] == "PRODUTO"
                        else MARROM
                    ),
                    on_click=lambda e: alterar_filtro("PRODUTO"),
                ),
                ft.Button(
                    "Sub-receitas",
                    bgcolor=(
                        ROSA
                        if filtro_receita["tipo"] == "SUB_RECEITA"
                        else ROSA_CLARO
                    ),
                    color=(
                        BRANCO
                        if filtro_receita["tipo"] == "SUB_RECEITA"
                        else MARROM
                    ),
                    on_click=lambda e: alterar_filtro("SUB_RECEITA"),
                ),
            ],
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
                            ft.Column(
                                spacing=3,
                                controls=[
                                    ft.Text(
                                        "Receitas / Fichas Técnicas",
                                        size=22,
                                        weight=ft.FontWeight.BOLD,
                                        color=MARROM,
                                    ),
                                    ft.Text(
                                        f"{len(receitas_filtradas)} receita(s) exibida(s)",
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
                    content=botoes_filtro,
                ),
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=18),
                    content=ft.Container(
                        width=380,
                        padding=14,
                        bgcolor=ROSA,
                        border_radius=12,
                        on_click=lambda e: abrir_cadastro_receita(),
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            controls=[
                                ft.Icon(ft.Icons.ADD, color=BRANCO),
                                ft.Text(
                                    "Nova Receita / Ficha Técnica",
                                    color=BRANCO,
                                    weight=ft.FontWeight.BOLD,
                                ),
                            ],
                        ),
                    ),
                ),
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=18),
                    content=ft.Column(
                        spacing=12,
                        controls=cartoes,
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
    # CADASTRO E EDIÇÃO DE RECEITA
    # ==================================================

    def abrir_cadastro_receita(e=None, receita_id=None):

        ingredientes_disponiveis = listar_ingredientes()

        conexao = obter_conexao()

        try:
            sub_receitas_disponiveis = conexao.execute(
                """
                SELECT *
                FROM receitas
                WHERE ativo = 1
                AND tipo = 'SUB_RECEITA'
                ORDER BY nome
                """
            ).fetchall()
        finally:
            conexao.close()

        dados_edicao = None
        em_edicao = receita_id is not None

        if em_edicao:

            dados_edicao = obter_receita(receita_id)

            if not dados_edicao or not dados_edicao["receita"]:
                abrir_receitas()
                return

        rec = dados_edicao["receita"] if em_edicao else None

        # --------------------------------------------------
        # TIPO DE RECEITA
        # --------------------------------------------------

        dropdown_tipo = ft.Dropdown(
            label="Tipo de Receita",
            value=rec["tipo"] if em_edicao else "PRODUTO",
            options=[
                ft.dropdown.Option(
                    "PRODUTO",
                    "Produto Final (Venda)",
                ),
                ft.dropdown.Option(
                    "SUB_RECEITA",
                    "Sub-receita (Massa / Recheio Base)",
                ),
            ],
            border_radius=12,
        )

        # --------------------------------------------------
        # NOME
        # --------------------------------------------------

        campo_nome_rec = ft.TextField(
            label="Nome da Receita *",
            hint_text="Ex.: BiscoNut / Massa Base",
            value=rec["nome"] if em_edicao else "",
            border_radius=12,
        )

        # --------------------------------------------------
        # RENDIMENTO E UNIDADE
        # --------------------------------------------------

        campo_rendimento = ft.TextField(
            label="Quantidade do rendimento *",
            value=(
                str(rec["rendimento_unidades"])
                if em_edicao else "1"
            ),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12,
            expand=True,
        )

        dropdown_unidade_rendimento = ft.Dropdown(
            label="Unidade",
            value=(
                rec["unidade_rendimento"]
                if em_edicao else "un"
            ),
            options=[
                ft.dropdown.Option("un", "Unidades (un)"),
                ft.dropdown.Option("g", "Gramas (g)"),
            ],
            border_radius=12,
            expand=True,
        )

        linha_rendimento = ft.Row(
            controls=[
                campo_rendimento,
                dropdown_unidade_rendimento,
            ],
        )

        # --------------------------------------------------
        # TEMPOS DE PRODUÇÃO
        # --------------------------------------------------

        campo_tempo_preparo = ft.TextField(
            label="Tempo de preparo (min)",
            value=(
                str(rec["tempo_preparo_min"] or 0)
                if em_edicao else "0"
            ),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12,
        )

        campo_tempo_batedeira = ft.TextField(
            label="Tempo de batedeira (min)",
            value=(
                str(rec["tempo_batedeira_min"] or 0)
                if em_edicao else "0"
            ),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12,
        )

        campo_tempo_forno = ft.TextField(
            label="Tempo de forno (min)",
            value=(
                str(rec["tempo_forno_min"] or 0)
                if em_edicao else "0"
            ),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12,
        )

        mensagem_rec = ft.Text(
            "",
            size=12,
            color="#B00020",
        )

        # --------------------------------------------------
        # INGREDIENTES E SUB-RECEITAS
        # --------------------------------------------------

        ingredientes_selecionados = []
        lista_insumos_ui = ft.Column(spacing=8)

        opcoes_combo = []

        for ing in ingredientes_disponiveis:
            opcoes_combo.append(
                ft.dropdown.Option(
                    f"ING_{ing['id']}",
                    f"[Insumo] {ing['nome']} ({ing['unidade_base']})",
                )
            )

        for sub in sub_receitas_disponiveis:

            if em_edicao and sub["id"] == receita_id:
                continue

            unidade_sub = sub["unidade_rendimento"] or "un"

            opcoes_combo.append(
                ft.dropdown.Option(
                    f"SUB_{sub['id']}",
                    f"[Sub-Receita] {sub['nome']} ({unidade_sub})",
                )
            )

        def adicionar_insumo_ui(opcao_val=None, qtd_val=""):

            dropdown_combo = ft.Dropdown(
                label="Selecione o Insumo ou Sub-receita",
                value=opcao_val,
                expand=2,
                options=opcoes_combo,
            )

            campo_qtd_usada = ft.TextField(
                label="Qtd usada",
                value=qtd_val,
                expand=1,
                keyboard_type=ft.KeyboardType.NUMBER,
            )

            linha = ft.Row(
                controls=[
                    dropdown_combo,
                    campo_qtd_usada,
                ]
            )

            ingredientes_selecionados.append(
                (dropdown_combo, campo_qtd_usada)
            )

            lista_insumos_ui.controls.append(linha)
            page.update()

        if em_edicao and dados_edicao["itens"]:

            for item in dados_edicao["itens"]:

                if item["ingrediente_id"]:
                    adicionar_insumo_ui(
                        f"ING_{item['ingrediente_id']}",
                        str(item["quantidade_usada"]),
                    )

                elif item["sub_receita_id"]:
                    adicionar_insumo_ui(
                        f"SUB_{item['sub_receita_id']}",
                        str(item["quantidade_usada"]),
                    )

        else:
            adicionar_insumo_ui()

        # --------------------------------------------------
        # SALVAR RECEITA
        # --------------------------------------------------

        def salvar_nova_receita(e=None):

            try:
                nome = (campo_nome_rec.value or "").strip()

                if not nome:
                    mensagem_rec.value = "Preencha o nome da receita."
                    page.update()
                    return

                rendimento = float(
                    (campo_rendimento.value or "").replace(",", ".")
                )

                unidade_rendimento = dropdown_unidade_rendimento.value

                if unidade_rendimento not in ("un", "g"):
                    mensagem_rec.value = (
                        "Selecione a unidade do rendimento."
                    )
                    page.update()
                    return

                tempo_preparo = int(
                    float(
                        (campo_tempo_preparo.value or "0").replace(",", ".")
                    )
                )

                tempo_batedeira = int(
                    float(
                        (campo_tempo_batedeira.value or "0").replace(",", ".")
                    )
                )

                tempo_forno = int(
                    float(
                        (campo_tempo_forno.value or "0").replace(",", ".")
                    )
                )

                if rendimento <= 0:
                    mensagem_rec.value = (
                        "O rendimento deve ser maior que zero."
                    )
                    page.update()
                    return

                if min(
                    tempo_preparo,
                    tempo_batedeira,
                    tempo_forno,
                ) < 0:
                    mensagem_rec.value = (
                        "Os tempos não podem ser negativos."
                    )
                    page.update()
                    return

                if not dropdown_tipo.value:
                    mensagem_rec.value = "Selecione o tipo de receita."
                    page.update()
                    return

                lista_ing_salvar = []

                for drop, campo_q in ingredientes_selecionados:

                    valor_selecionado = drop.value
                    quantidade_texto = (
                        campo_q.value or ""
                    ).strip()

                    if not valor_selecionado and not quantidade_texto:
                        continue

                    if not valor_selecionado or not quantidade_texto:
                        mensagem_rec.value = (
                            "Complete o insumo e a quantidade em cada linha."
                        )
                        page.update()
                        return

                    quantidade = float(
                        quantidade_texto.replace(",", ".")
                    )

                    if quantidade <= 0:
                        mensagem_rec.value = (
                            "A quantidade utilizada deve ser maior que zero."
                        )
                        page.update()
                        return

                    if valor_selecionado.startswith("ING_"):

                        lista_ing_salvar.append(
                            {
                                "ingrediente_id": int(
                                    valor_selecionado.replace("ING_", "")
                                ),
                                "quantidade_usada": quantidade,
                            }
                        )

                    elif valor_selecionado.startswith("SUB_"):

                        lista_ing_salvar.append(
                            {
                                "sub_receita_id": int(
                                    valor_selecionado.replace("SUB_", "")
                                ),
                                "quantidade_usada": quantidade,
                            }
                        )

                if not lista_ing_salvar:
                    mensagem_rec.value = (
                        "Adicione ao menos um ingrediente ou sub-receita "
                        "com quantidade."
                    )
                    page.update()
                    return

                parametros = {
                    "nome": nome,
                    "tipo": dropdown_tipo.value,
                    "rendimento_unidades": rendimento,
                    "custo_embalagem_centavos": 0,
                    "margem_lucro_pct": 0,
                    "taxa_cartao_pct": 0,
                    "lista_itens": lista_ing_salvar,
                    "tempo_preparo_min": tempo_preparo,
                    "tempo_batedeira_min": tempo_batedeira,
                    "tempo_forno_min": tempo_forno,
                    "unidade_rendimento": unidade_rendimento,
                }

                if em_edicao:
                    atualizar_receita(
                        receita_id=receita_id,
                        **parametros,
                    )
                else:
                    cadastrar_receita(**parametros)

                abrir_receitas()

            except ValueError as erro:
                mensagem_rec.value = (
                    f"Verifique os dados informados: {erro}"
                )
                page.update()

            except Exception as erro:
                mensagem_rec.value = (
                    f"Erro ao salvar receita: {erro}"
                )
                page.update()

        titulo_form = (
            "Editar Receita / Ficha Técnica"
            if em_edicao
            else "Nova Receita / Ficha Técnica"
        )

        texto_btn_salvar = (
            "Salvar Alterações"
            if em_edicao
            else "Salvar Ficha Técnica"
        )

        controles_form = [
            dropdown_tipo,
            campo_nome_rec,
            ft.Text(
                "RENDIMENTO DA RECEITA",
                weight=ft.FontWeight.BOLD,
                color=MARROM,
                size=13,
            ),
            linha_rendimento,
            ft.Divider(color=ROSA_CLARO),
            ft.Text(
                "TEMPOS DE PRODUÇÃO",
                weight=ft.FontWeight.BOLD,
                color=MARROM,
                size=13,
            ),
            campo_tempo_preparo,
            campo_tempo_batedeira,
            campo_tempo_forno,
            ft.Divider(color=ROSA_CLARO),
            ft.Text(
                "Ingredientes / Sub-receitas Utilizadas",
                weight=ft.FontWeight.BOLD,
                color=MARROM,
            ),
            lista_insumos_ui,
            ft.TextButton(
                "  Mais um ingrediente",
                icon=ft.Icons.ADD,
                on_click=lambda e: adicionar_insumo_ui(),
            ),
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
                        ft.Icon(
                            ft.Icons.SAVE_OUTLINED,
                            color=BRANCO,
                        ),
                        ft.Text(
                            texto_btn_salvar,
                            color=BRANCO,
                            weight=ft.FontWeight.BOLD,
                        ),
                    ],
                ),
            ),
        ]

        tela = ft.Column(
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
                                on_click=abrir_receitas,
                                content=ft.Icon(
                                    ft.Icons.ARROW_BACK,
                                    color=MARROM,
                                    size=24,
                                ),
                            ),
                            ft.Text(
                                titulo_form,
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                color=MARROM,
                            ),
                        ],
                    ),
                ),
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=18),
                    content=ft.Column(
                        spacing=12,
                        controls=controles_form,
                    ),
                ),
            ],
        )

        page.controls.clear()
        page.add(tela)
        page.update()

    # ==================================================
    # CUSTOS FIXOS E RATEIO
    # ==================================================

    def abrir_custos_fixos(e=None):

        conexao = obter_conexao()

        try:
            custos = conexao.execute(
                "SELECT * FROM custos_fixos ORDER BY descricao"
            ).fetchall()

            faturamento_row = conexao.execute(
                """
                SELECT valor
                FROM configuracoes
                WHERE chave = 'faturamento_mensal'
                """
            ).fetchone()

            faturamento_atual = (
                faturamento_row["valor"]
                if faturamento_row else "2000.00"
            )

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

        campo_faturamento = ft.TextField(
            label="Faturamento Médio Mensal Alvo (R$) *",
            value=str(faturamento_atual),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12,
        )

        mensagem_custos = ft.Text(
            "",
            size=12,
            color=ROSA,
        )

        def salvar_faturamento_acao(e):

            try:
                val = (
                    campo_faturamento.value or ""
                ).replace(",", ".").strip()

                if not val or float(val) <= 0:
                    mensagem_custos.value = (
                        "Informe um faturamento maior que zero."
                    )
                    page.update()
                    return

                conexao = obter_conexao()

                try:
                    conexao.execute(
                        """
                        INSERT OR REPLACE INTO configuracoes
                        (chave, valor)
                        VALUES ('faturamento_mensal', ?)
                        """,
                        (val,),
                    )
                    conexao.commit()
                finally:
                    conexao.close()

                abrir_custos_fixos()

            except Exception as err:
                mensagem_custos.value = f"Erro ao atualizar: {err}"
                page.update()

        # --------------------------------------------------
        # FORMULÁRIO DE CUSTO FIXO
        # --------------------------------------------------

        def abrir_form_custo_fixo(custo=None):

            em_ed = custo is not None

            c_desc = ft.TextField(
                label="Descrição do Custo Fixo *",
                value=custo["descricao"] if em_ed else "",
                border_radius=12,
            )

            c_val = ft.TextField(
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
                            mensagem_custos,
                            ft.Container(
                                width=380,
                                padding=12,
                                bgcolor=ROSA,
                                border_radius=12,
                                on_click=salvar_faturamento_acao,
                                content=ft.Row(
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    controls=[
                                        ft.Text(
                                            "Atualizar Faturamento Mensal",
                                            color=BRANCO,
                                            weight=ft.FontWeight.BOLD,
                                        ),
                                    ],
                                ),
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

        indice_atual["valor"] = 3
        navegacao.selected_index = 3
        page.controls.clear()
        page.add(tela)
        page.update()

    # ==================================================
    # PRECIFICAÇÃO DOS PRODUTOS FINAIS
    # ==================================================

    def abrir_precificacao(e=None):

        conexao = obter_conexao()

        try:
            produtos = conexao.execute(
                """
                SELECT id, nome, rendimento_unidades,
                       unidade_rendimento
                FROM receitas
                WHERE ativo = 1
                  AND tipo = 'PRODUTO'
                ORDER BY nome
                """
            ).fetchall()
        finally:
            conexao.close()

        mensagem = ft.Text(
            "",
            size=12,
            color="#B00020",
        )

        resultado = ft.Container(
            visible=False,
            bgcolor=ROSA_CLARO,
            padding=16,
            border_radius=12,
        )

        campo_embalagem = ft.TextField(
            label="Custo da embalagem (R$)",
            value="0,00",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12,
        )

        campo_margem = ft.TextField(
            label="Margem de lucro desejada (%)",
            value="100",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12,
        )

        campo_taxa = ft.TextField(
            label="Taxa do cartão (%)",
            value="0",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12,
        )

        produto_selecionado = ft.Dropdown(
            label="Selecione o produto final",
            expand=True,
            options=[
                ft.dropdown.Option(
                    str(p["id"]),
                    p["nome"],
                )
                for p in produtos
            ],
        )

        def carregar_precificacao(e=None):

            resultado.visible = False
            mensagem.value = ""

            if not produto_selecionado.value:
                page.update()
                return

            dados = obter_precificacao_produto(
                int(produto_selecionado.value)
            )

            if dados:

                campo_embalagem.value = (
                    f"{dados['custo_embalagem_centavos'] / 100:.2f}"
                    .replace(".", ",")
                )

                campo_margem.value = str(
                    dados["margem_lucro_pct"]
                )

                campo_taxa.value = str(
                    dados["taxa_cartao_pct"]
                )

            else:
                campo_embalagem.value = "0,00"
                campo_margem.value = "100"
                campo_taxa.value = "0"

            page.update()

        produto_selecionado.on_change = carregar_precificacao

        # --------------------------------------------------
        # SALVAR E CALCULAR
        # --------------------------------------------------

        def salvar_e_calcular(e=None):

            try:

                if not produto_selecionado.value:
                    mensagem.value = "Selecione um produto final."
                    page.update()
                    return

                embalagem = float(
                    (campo_embalagem.value or "0").replace(",", ".")
                )

                margem = float(
                    (campo_margem.value or "0").replace(",", ".")
                )

                taxa = float(
                    (campo_taxa.value or "0").replace(",", ".")
                )

                if embalagem < 0 or margem < 0 or taxa < 0:
                    mensagem.value = (
                        "Os valores não podem ser negativos."
                    )
                    page.update()
                    return

                if taxa >= 100:
                    mensagem.value = (
                        "A taxa do cartão deve ser menor que 100%."
                    )
                    page.update()
                    return

                receita_id = int(produto_selecionado.value)

                salvar_precificacao_produto(
                    receita_id=receita_id,
                    custo_embalagem_centavos=round(embalagem * 100),
                    margem_lucro_pct=margem,
                    taxa_cartao_pct=taxa,
                )

                calculo = calcular_precificacao_produto(receita_id)

                if not calculo:
                    mensagem.value = (
                        "Não foi possível calcular. Confira a ficha técnica."
                    )
                    page.update()
                    return

                resultado.content = ft.Column(
                    spacing=9,
                    controls=[
                        ft.Text(
                            "RESULTADO DA PRECIFICAÇÃO",
                            size=12,
                            weight=ft.FontWeight.BOLD,
                            color=MARROM,
                        ),
                        ft.Divider(color=ROSA),
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text(
                                    "Custo dos insumos:",
                                    color=MARROM,
                                ),
                                ft.Text(
                                    f"R$ {calculo['custo_insumos']:.2f}",
                                    weight=ft.FontWeight.BOLD,
                                    color=MARROM,
                                ),
                            ],
                        ),
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text(
                                    "Embalagem:",
                                    color=MARROM,
                                ),
                                ft.Text(
                                    f"R$ {calculo['custo_embalagem']:.2f}",
                                    color=MARROM,
                                ),
                            ],
                        ),
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text(
                                    "Rateio de custos fixos:",
                                    color=MARROM,
                                ),
                                ft.Text(
                                    f"R$ {calculo['custo_fixo']:.2f}",
                                    color=MARROM,
                                ),
                            ],
                        ),
                        ft.Divider(color=ROSA),
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text(
                                    "Custo total do lote:",
                                    color=MARROM,
                                ),
                                ft.Text(
                                    f"R$ {calculo['custo_total']:.2f}",
                                    weight=ft.FontWeight.BOLD,
                                    color=MARROM,
                                ),
                            ],
                        ),
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text(
                                    "Custo por unidade de rendimento:",
                                    color=MARROM,
                                ),
                                ft.Text(
                                    f"R$ {calculo['custo_unitario']:.4f}",
                                    color=MARROM,
                                ),
                            ],
                        ),
                        ft.Divider(color=ROSA),
                        ft.Text(
                            f"PREÇO DE VENDA SUGERIDO: "
                            f"R$ {calculo['preco_venda_sugerido']:.2f}",
                            size=19,
                            weight=ft.FontWeight.BOLD,
                            color=ROSA,
                        ),
                        ft.Text(
                            f"Lucro estimado por unidade: "
                            f"R$ {calculo['lucro_unitario']:.2f}",
                            color=MARROM,
                            weight=ft.FontWeight.BOLD,
                        ),
                    ],
                )

                resultado.visible = True
                mensagem.value = "Precificação salva e calculada."
                mensagem.color = "#2E7D32"

                page.update()

            except ValueError as erro:
                mensagem.value = f"Verifique os valores: {erro}"
                mensagem.color = "#B00020"
                page.update()

            except Exception as erro:
                mensagem.value = f"Erro na precificação: {erro}"
                mensagem.color = "#B00020"
                page.update()

        tela = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=15,
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
                                on_click=voltar_inicio,
                                content=ft.Icon(
                                    ft.Icons.ARROW_BACK,
                                    color=MARROM,
                                    size=24,
                                ),
                            ),
                            ft.Text(
                                "Precificação de Produtos",
                                size=21,
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
                            ft.Text(
                                "A precificação é independente da ficha técnica.",
                                size=12,
                                color=TEXTO_SECUNDARIO,
                            ),
                            produto_selecionado,
                            campo_embalagem,
                            campo_margem,
                            campo_taxa,
                            mensagem,
                            ft.Container(
                                width=380,
                                padding=14,
                                bgcolor=ROSA,
                                border_radius=12,
                                on_click=salvar_e_calcular,
                                content=ft.Row(
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    controls=[
                                        ft.Icon(
                                            ft.Icons.CALCULATE_OUTLINED,
                                            color=BRANCO,
                                        ),
                                        ft.Text(
                                            "Salvar e calcular preço",
                                            color=BRANCO,
                                            weight=ft.FontWeight.BOLD,
                                        ),
                                    ],
                                ),
                            ),
                            resultado,
                        ],
                    ),
                ),
            ],
        )

        page.controls.clear()
        page.add(tela)
        page.update()

    # ==================================================
    # RELATÓRIOS
    # ==================================================

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

                    custo_unitario = (
                        calculo["custo_insumos"] / rendimento
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

        indice_atual["valor"] = 4
        navegacao.selected_index = 4
        page.controls.clear()
        page.add(tela)
        page.update()

    # ==================================================
    # CABEÇALHO DA HOME
    # ==================================================

    cabecalho = ft.Container(
        padding=ft.Padding.only(
            left=20,
            right=20,
            top=25,
            bottom=15,
        ),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Column(
                    spacing=3,
                    controls=[
                        ft.Text(
                            "DM Gulositos",
                            size=25,
                            weight=ft.FontWeight.BOLD,
                            color=MARROM,
                        ),
                        ft.Text(
                            "GESTÃO E PRECIFICAÇÃO",
                            size=10,
                            color=TEXTO_SECUNDARIO,
                        ),
                    ],
                ),
                ft.Container(
                    bgcolor=BRANCO,
                    padding=12,
                    border_radius=15,
                    content=ft.Icon(
                        ft.Icons.CAKE_OUTLINED,
                        color=ROSA,
                        size=30,
                    ),
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
                ft.Text(
                    "RESUMO DO NEGÓCIO",
                    size=11,
                    weight=ft.FontWeight.BOLD,
                    color=TEXTO_SECUNDARIO,
                ),
                ft.Row(
                    controls=[
                        criar_indicador(
                            "29",
                            "Insumos no estoque",
                            MARROM,
                        ),
                        criar_indicador(
                            "19.5%",
                            "Taxa Custo Fixo",
                            MARROM,
                        ),
                    ],
                ),
                ft.Divider(color=ROSA_CLARO),
                ft.Row(
                    controls=[
                        criar_indicador(
                            "100%",
                            "Margem padrão",
                            ROSA,
                        ),
                        criar_indicador(
                            "R$ 2.000",
                            "Fat. Mensal Alvo",
                            MARROM,
                        ),
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
            ft.Text(
                "O que deseja fazer?",
                size=19,
                weight=ft.FontWeight.BOLD,
                color=MARROM,
            ),
            ft.Row(
                controls=[
                    criar_atalho(
                        ft.Icons.INVENTORY_2_OUTLINED,
                        "Ingredientes",
                        "Insumos e preços",
                        ROSA,
                        abrir_ingredientes,
                    ),
                    criar_atalho(
                        ft.Icons.MENU_BOOK_OUTLINED,
                        "Receitas",
                        "Fichas técnicas",
                        ROSA,
                        abrir_receitas,
                    ),
                ],
            ),
            ft.Row(
                controls=[
                    criar_atalho(
                        ft.Icons.CALCULATE_OUTLINED,
                        "Precificação",
                        "Preço de venda dos produtos",
                        ROSA,
                        abrir_precificacao,
                    ),
                    criar_atalho(
                        ft.Icons.BAR_CHART_OUTLINED,
                        "Relatórios",
                        "Custos e lucros",
                        ROSA,
                        abrir_relatorios,
                    ),
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
            ft.NavigationBarDestination(
                icon=ft.Icons.HOME_OUTLINED,
                selected_icon=ft.Icons.HOME,
                label="Início",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.INVENTORY_2_OUTLINED,
                label="Insumos",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.MENU_BOOK_OUTLINED,
                label="Receitas",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.CALCULATE_OUTLINED,
                label="Custos Fixos",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.BAR_CHART_OUTLINED,
                label="Relatórios",
            ),
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
                    controls=[
                        resumo,
                        atalhos,
                    ],
                ),
            ),
        ],
    )

    page.navigation_bar = navegacao
    page.add(conteudo)


# ==================================================
# COMPONENTES AUXILIARES
# ==================================================

def criar_indicador(valor, descricao, cor):

    return ft.Column(
        expand=True,
        spacing=4,
        controls=[
            ft.Text(
                valor,
                size=22,
                weight=ft.FontWeight.BOLD,
                color=cor,
            ),
            ft.Text(
                descricao,
                size=11,
                color="#876A65",
            ),
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
                ft.Icon(
                    icone,
                    color=cor,
                    size=28,
                ),
                ft.Text(
                    titulo,
                    color="#603D3B",
                    weight=ft.FontWeight.BOLD,
                    size=14,
                ),
                ft.Text(
                    descricao,
                    color="#876A65",
                    size=11,
                ),
            ],
        ),
    )


# ==================================================
# EXECUÇÃO
# ==================================================

if __name__ == "__main__":
    ft.run(
        main,
        view=ft.AppView.WEB_BROWSER,
        port=8080,
    )
