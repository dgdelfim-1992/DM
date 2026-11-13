"""Telas de receitas e fichas técnicas do DM Gulositos."""


def criar_abrir_receitas(dependencias):
    """Monta as telas de receitas com dependências injetadas."""
    ft = dependencias["ft"]
    page = dependencias["page"]
    BRANCO = dependencias["BRANCO"]
    MARROM = dependencias["MARROM"]
    ROSA = dependencias["ROSA"]
    ROSA_CLARO = dependencias["ROSA_CLARO"]
    TEXTO_SECUNDARIO = dependencias["TEXTO_SECUNDARIO"]
    indice_atual = dependencias["indice_atual"]
    navegacao_ref = dependencias["navegacao_ref"]
    filtro_receita = dependencias["filtro_receita"]
    obter_conexao = dependencias["obter_conexao"]
    excluir_receita = dependencias["excluir_receita"]
    mostrar_aviso = dependencias["mostrar_aviso"]
    criar_dialogo_padrao = dependencias["criar_dialogo_padrao"]
    calcular_custo_receita = dependencias["calcular_custo_receita"]
    criar_cabecalho_padrao = dependencias["criar_cabecalho_padrao"]
    criar_botao_primario = dependencias["criar_botao_primario"]
    listar_ingredientes = dependencias["listar_ingredientes"]
    obter_receita = dependencias["obter_receita"]
    criar_dropdown_padrao = dependencias["criar_dropdown_padrao"]
    criar_campo_padrao = dependencias["criar_campo_padrao"]
    atualizar_receita = dependencias["atualizar_receita"]
    cadastrar_receita = dependencias["cadastrar_receita"]

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
    
                    mostrar_aviso(f"Erro ao excluir receita: {erro}", "#C62828")
    
            dialogo_primeiro = criar_dialogo_padrao(
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
    
            dialogo_segundo = criar_dialogo_padrao(
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
                    padding=18,
                    border_radius=18,
                    content=ft.Column(
                        spacing=10,
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
                criar_cabecalho_padrao(
                    "Receitas / Fichas Técnicas",
                    f"{len(receitas_filtradas)} receita(s) exibida(s)",
                    voltar_inicio,
                ),
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=18),
                    content=botoes_filtro,
                ),
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=18),
                    content=criar_botao_primario(
                        "Nova Receita / Ficha Técnica",
                        lambda e: abrir_cadastro_receita(),
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
        navegacao_ref["controle"].selected_index = 2
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
    
        dropdown_tipo = criar_dropdown_padrao(
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
    
        campo_nome_rec = criar_campo_padrao(
            label="Nome da Receita *",
            hint_text="Ex.: BiscoNut / Massa Base",
            value=rec["nome"] if em_edicao else "",
            border_radius=12,
        )
    
        # --------------------------------------------------
        # RENDIMENTO E UNIDADE
        # --------------------------------------------------
    
        campo_rendimento = criar_campo_padrao(
            label="Quantidade do rendimento *",
            value=(
                str(rec["rendimento_unidades"])
                if em_edicao else "1"
            ),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12,
            expand=True,
        )
    
        dropdown_unidade_rendimento = criar_dropdown_padrao(
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
    
        campo_tempo_preparo = criar_campo_padrao(
            label="Tempo de preparo (min)",
            value=(
                str(rec["tempo_preparo_min"] or 0)
                if em_edicao else "0"
            ),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12,
        )
    
        campo_tempo_batedeira = criar_campo_padrao(
            label="Tempo de batedeira (min)",
            value=(
                str(rec["tempo_batedeira_min"] or 0)
                if em_edicao else "0"
            ),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=12,
        )
    
        campo_tempo_forno = criar_campo_padrao(
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
    
            dropdown_combo = criar_dropdown_padrao(
                label="Selecione o Insumo ou Sub-receita",
                value=opcao_val,
                expand=2,
                options=opcoes_combo,
            )
    
            campo_qtd_usada = criar_campo_padrao(
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
    

    return abrir_receitas
