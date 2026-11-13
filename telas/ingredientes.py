"""Tela de cadastro, consulta e manutenção de ingredientes."""


def criar_abrir_ingredientes(dependencias):
    """Monta a tela de ingredientes com dependências injetadas."""
    ft = dependencias["ft"]
    page = dependencias["page"]
    BRANCO = dependencias["BRANCO"]
    MARROM = dependencias["MARROM"]
    ROSA = dependencias["ROSA"]
    ROSA_CLARO = dependencias["ROSA_CLARO"]
    TEXTO_SECUNDARIO = dependencias["TEXTO_SECUNDARIO"]
    indice_atual = dependencias["indice_atual"]
    navegacao_ref = dependencias["navegacao_ref"]
    listar_ingredientes = dependencias["listar_ingredientes"]
    listar_alertas_aumento_ingredientes = dependencias["listar_alertas_aumento_ingredientes"]
    excluir_ingrediente = dependencias["excluir_ingrediente"]
    obter_ingrediente = dependencias["obter_ingrediente"]
    atualizar_ingrediente = dependencias["atualizar_ingrediente"]
    cadastrar_ingrediente = dependencias["cadastrar_ingrediente"]
    criar_dialogo_padrao = dependencias["criar_dialogo_padrao"]
    criar_cabecalho_padrao = dependencias["criar_cabecalho_padrao"]
    criar_botao_primario = dependencias["criar_botao_primario"]
    criar_campo_padrao = dependencias["criar_campo_padrao"]
    criar_dropdown_padrao = dependencias["criar_dropdown_padrao"]
    abrir_historico_precos_ingrediente = dependencias["abrir_historico_precos_ingrediente"]
    abrir_menu_opcoes = dependencias["abrir_menu_opcoes"]

    def abrir_ingredientes(e=None):
    
        ingredientes = listar_ingredientes()
        alertas = listar_alertas_aumento_ingredientes()
        cartoes = []
        painel_alertas = []
    
        if alertas:
            itens_alerta = []
    
            for alerta in alertas:
                itens_alerta.append(
                    ft.Container(
                        padding=12,
                        bgcolor="#FFFFFF",
                        border_radius=10,
                        content=ft.Column(
                            spacing=5,
                            controls=[
                                ft.Text(
                                    alerta["nome"],
                                    weight=ft.FontWeight.BOLD,
                                    color=MARROM,
                                    size=14,
                                ),
                                ft.Text(
                                    f"Aumento de "
                                    f"{alerta['aumento_percentual']:.1f}%",
                                    color="#C62828",
                                    weight=ft.FontWeight.BOLD,
                                    size=13,
                                ),
                                ft.Text(
                                    f"Custo por {alerta['unidade_base']}: "
                                    f"R$ {alerta['custo_anterior']:.5f} "
                                    f"→ R$ {alerta['custo_atual']:.5f}",
                                    color=TEXTO_SECUNDARIO,
                                    size=12,
                                ),
                                ft.Text(
                                    f"Embalagem: R$ "
                                    f"{alerta['preco_anterior']:.2f} "
                                    f"→ R$ {alerta['preco_atual']:.2f}",
                                    color=TEXTO_SECUNDARIO,
                                    size=12,
                                ),
                            ],
                        ),
                    )
                )
    
            painel_alertas.append(
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=18),
                    content=ft.Container(
                        padding=14,
                        bgcolor="#FCE8E6",
                        border_radius=14,
                        content=ft.Column(
                            spacing=10,
                            controls=[
                                ft.Row(
                                    spacing=8,
                                    controls=[
                                        ft.Icon(
                                            ft.Icons.WARNING_AMBER_ROUNDED,
                                            color="#C62828",
                                            size=22,
                                        ),
                                        ft.Text(
                                            "ALERTA DE AUMENTO DE PREÇOS",
                                            color="#C62828",
                                            weight=ft.FontWeight.BOLD,
                                            size=13,
                                        ),
                                    ],
                                ),
                                ft.Text(
                                    "O custo destes ingredientes aumentou "
                                    "em relação ao registro anterior.",
                                    color=MARROM,
                                    size=12,
                                ),
                                *itens_alerta,
                            ],
                        ),
                    ),
                )
            )
    
    
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
    
                    dialogo_erro = criar_dialogo_padrao(
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
    
                    dialogo_erro = criar_dialogo_padrao(
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
    
            dialogo_primeiro = criar_dialogo_padrao(
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
    
            dialogo_segundo = criar_dialogo_padrao(
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
                    padding=18,
                    border_radius=18,
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
                                                icon=ft.Icons.HISTORY,
                                                icon_color=MARROM,
                                                tooltip="Ver histórico de preços",
                                                on_click=lambda e, item_id=ingrediente_id, nome=nome_ingrediente:
                                                    abrir_historico_precos_ingrediente(item_id, nome),
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
                criar_cabecalho_padrao(
                    "Ingredientes",
                    f"{len(ingredientes)} ingrediente(s) cadastrado(s)",
                    voltar_inicio,
                ),
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=18),
                    content=criar_botao_primario(
                        "Adicionar ingrediente",
                        abrir_cadastro_ingrediente,
                    ),
                ),
    
                *painel_alertas,
    
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
        navegacao_ref["controle"].selected_index = 2
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
    
        campo_nome = criar_campo_padrao(
            label="Nome do ingrediente *",
            hint_text="Ex.: Farinha de trigo",
            value=ingrediente["nome"] if em_edicao else "",
            border_radius=12,
            border_color=ROSA_CLARO,
        )
    
        campo_marca = criar_campo_padrao(
            label="Marca",
            hint_text="Ex.: Qualy",
            value=(ingrediente["marca"] or "") if em_edicao else "",
            border_radius=12,
            border_color=ROSA_CLARO,
        )
    
        campo_fornecedor = criar_campo_padrao(
            label="Fornecedor ou estabelecimento",
            hint_text="Onde foi comprado?",
            value=(ingrediente["fornecedor"] or "") if em_edicao else "",
            border_radius=12,
            border_color=ROSA_CLARO,
        )
    
        campo_quantidade = criar_campo_padrao(
            label="Quantidade da embalagem *",
            hint_text="Ex.: 500",
            value=str(ingrediente["quantidade_compra"]) if em_edicao else "",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12,
            border_color=ROSA_CLARO,
        )
    
        campo_unidade = criar_dropdown_padrao(
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
    
        campo_preco = criar_campo_padrao(
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
    
        campo_observacoes = criar_campo_padrao(
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
    
        indice_atual["valor"] = 2
        navegacao_ref["controle"].selected_index = 2
        page.controls.clear()
        page.add(tela)
        page.update()
    
    # ==================================================
    # RECEITAS
    # ==================================================
    

    return abrir_ingredientes
