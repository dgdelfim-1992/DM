"""Tela de orçamentos e histórico de versões do DM Gulositos."""


def criar_abrir_orcamentos(dependencias):
    """Monta a tela de orçamentos com dependências fornecidas pelo app principal."""
    ft = dependencias["ft"]
    datetime = dependencias["datetime"]
    json = dependencias["json"]
    page = dependencias["page"]
    BRANCO = dependencias["BRANCO"]
    MARROM = dependencias["MARROM"]
    ROSA = dependencias["ROSA"]
    ROSA_CLARO = dependencias["ROSA_CLARO"]
    TEXTO_SECUNDARIO = dependencias["TEXTO_SECUNDARIO"]
    ids_orcamentos_selecionados = dependencias["ids_orcamentos_selecionados"]
    obter_orcamento = dependencias["obter_orcamento"]
    listar_precificacoes = dependencias["listar_precificacoes"]
    obter_taxas_pagamento = dependencias["obter_taxas_pagamento"]
    obter_margem_minima = dependencias["obter_margem_minima"]
    calcular_simulacao_precificacao = dependencias["calcular_simulacao_precificacao"]
    criar_dialogo_padrao = dependencias["criar_dialogo_padrao"]
    mostrar_aviso = dependencias["mostrar_aviso"]
    excluir_orcamentos = dependencias["excluir_orcamentos"]
    listar_orcamentos = dependencias["listar_orcamentos"]
    atualizar_status_orcamento = dependencias["atualizar_status_orcamento"]
    listar_versoes_orcamento = dependencias["listar_versoes_orcamento"]
    criar_campo_padrao = dependencias["criar_campo_padrao"]
    criar_dropdown_padrao = dependencias["criar_dropdown_padrao"]
    abrir_menu_opcoes = dependencias["abrir_menu_opcoes"]
    indice_atual = dependencias["indice_atual"]
    navegacao_ref = dependencias["navegacao_ref"]
    atualizar_orcamento_salvo = dependencias["atualizar_orcamento_salvo"]
    salvar_orcamento = dependencias["salvar_orcamento"]

    def abrir_orcamentos(e=None, orcamento_id=None, filtro_status=None):
        filtro_status_atual = {"valor": filtro_status or "Todos"}
        registro_edicao = obter_orcamento(orcamento_id) if orcamento_id else None
        precificacoes = listar_precificacoes()
        taxas = obter_taxas_pagamento()
        margem_minima = obter_margem_minima()
        modalidades = [
            ("Dinheiro", "dinheiro"),
            ("Pix", "pix"),
            ("Cartão de débito", "debito"),
            ("Crédito à vista", "credito_avista"),
            ("Crédito parcelado", "credito_parcelado"),
        ]
        produtos = {}
        for prec in precificacoes:
            resultado = calcular_simulacao_precificacao(
                prec["receita_id"],
                prec["quantidade_embalagem"],
                prec["custo_embalagem_centavos"],
                prec["markup_ideal_pct"],
                prec["preco_praticado_centavos"],
                max([float(v) for v in taxas.values()] or [0.0]),
                margem_minima,
                embalagem_id=prec["embalagem_id"],
                quantidade_embalagem_insumo=prec["quantidade_embalagem_insumo"],
                sacola_id=prec["sacola_id"],
                quantidade_sacola=prec["quantidade_sacola"],
            )
            if resultado:
                preco_base = (
                    resultado["preco_praticado"]
                    if resultado["preco_praticado"] > 0
                    else resultado["preco_sugerido"]
                )
                produtos[str(prec["id"])] = {
                    "precificacao_id": prec["id"],
                    "receita_id": prec["receita_id"],
                    "nome": prec["nome_receita"],
                    "unidade": prec["unidade_rendimento"] or "un",
                    "quantidade_embalagem": float(prec["quantidade_embalagem"]),
                    "custo": float(resultado["custo_total"]),
                    "preco_base": float(preco_base),
                }
    
        def formatar_reais(valor):
            return ("R$ {:,.2f}".format(valor)).replace(",", "X").replace(".", ",").replace("X", ".")
    
        def alternar_selecao_orcamento(orcamento_id, selecionado):
            if selecionado:
                ids_orcamentos_selecionados.add(orcamento_id)
            else:
                ids_orcamentos_selecionados.discard(orcamento_id)
    
        def executar_exclusao(dialogo, ids):
            fechar_dialogo(dialogo)
            try:
                quantidade = excluir_orcamentos(ids)
                ids_orcamentos_selecionados.difference_update(ids)
                mostrar_aviso(f"{quantidade} orçamento(s) excluído(s) com sucesso.")
                montar_tela_historico(filtro_status_atual["valor"])
            except Exception as erro:
                mostrar_aviso(f"Não foi possível excluir os orçamentos: {erro}", "#C62828")
    
        def confirmar_exclusao_orcamentos(orcamento_ids):
            ids = list(dict.fromkeys(int(valor) for valor in orcamento_ids))
            if not ids:
                mostrar_aviso("Selecione pelo menos um orçamento para excluir.", "#C62828")
                return
            quantidade = len(ids)
            def abrir_confirmacao_final(e=None):
                fechar_dialogo(dlg_primeira_confirmacao)
                dlg_final = criar_dialogo_padrao(
                    modal=True,
                    title=ft.Text("Confirmação final"),
                    content=ft.Text(
                        f"Esta ação é permanente. Deseja realmente excluir {quantidade} "
                        f"orçamento(s), incluindo seus itens e histórico de alterações?"
                    ),
                    actions=[
                        ft.TextButton("Cancelar", on_click=lambda ev: fechar_dialogo(dlg_final)),
                        ft.Button("Excluir definitivamente", icon=ft.Icons.DELETE_FOREVER, bgcolor="#A52D35", color=BRANCO, on_click=lambda ev: executar_exclusao(dlg_final, ids)),
                    ],
                )
                page.overlay.append(dlg_final)
                dlg_final.open = True
                page.update()
            dlg_primeira_confirmacao = criar_dialogo_padrao(
                modal=True,
                title=ft.Text("Excluir orçamento(s)?"),
                content=ft.Text(f"Você selecionou {quantidade} orçamento(s). Deseja continuar para a confirmação final?"),
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda ev: fechar_dialogo(dlg_primeira_confirmacao)),
                    ft.Button("Continuar", on_click=abrir_confirmacao_final),
                ],
            )
            page.overlay.append(dlg_primeira_confirmacao)
            dlg_primeira_confirmacao.open = True
            page.update()
        def montar_tela_historico(filtro_status=None):
            if filtro_status is not None:
                filtro_status_atual["valor"] = filtro_status
            status_selecionado = filtro_status_atual["valor"]
            registros = listar_orcamentos()
            if status_selecionado != "Todos":
                registros = [r for r in registros if r["status"] == status_selecionado]
            cards = []
            for registro in registros:
                total = registro["total_final_centavos"] / 100
                cores_status = {
                    "Aprovado": ("#D1F0D5", "#1B5E20"),
                    "Recusado": ("#FCE8E8", "#A52D35"),
                    "Enviado": ("#E8F1FA", "#285A83"),
                    "Em elaboração": ("#FFF3E0", "#8A5A16"),
                }
                cor_fundo, cor_texto = cores_status.get(registro["status"], (BRANCO, MARROM))
                cards.append(
                    ft.Container(
                        bgcolor=cor_fundo, padding=14, border_radius=14,
                        content=ft.Column(spacing=7, controls=[
                            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                                ft.Text(f'Orçamento {registro["numero"]}', weight=ft.FontWeight.BOLD, color=MARROM),
                                ft.Row(spacing=4, controls=[
                                    ft.Text(registro["status"], size=11, weight=ft.FontWeight.BOLD, color=cor_texto),
                                    ft.Checkbox(value=registro["id"] in ids_orcamentos_selecionados, tooltip="Selecionar para exclusão em lote", on_change=lambda ev, oid=registro["id"]: alternar_selecao_orcamento(oid, ev.control.value)),
                                ]),
                            ]),
                            ft.Text(registro["cliente"] or "Cliente não informado", color=TEXTO_SECUNDARIO, size=12),
                            ft.Text(f"Total do orçamento (Pix): {formatar_reais(total)}", weight=ft.FontWeight.BOLD, color=MARROM),
                            ft.Row(wrap=True, spacing=4, controls=[
                                ft.IconButton(
                                    icon=ft.Icons.VISIBILITY,
                                    tooltip="Abrir / copiar orçamento",
                                    icon_color=MARROM,
                                    on_click=lambda ev, oid=registro["id"]: abrir_detalhe_orcamento(oid),
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.EDIT,
                                    tooltip="Editar orçamento",
                                    icon_color=MARROM,
                                    on_click=lambda ev, oid=registro["id"]: abrir_orcamentos(orcamento_id=oid),
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.HISTORY,
                                    tooltip="Histórico de alterações",
                                    icon_color=MARROM,
                                    on_click=lambda ev, oid=registro["id"]: abrir_historico_versoes(oid),
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.SEND,
                                    tooltip="Marcar como enviado",
                                    icon_color="#285A83",
                                    on_click=lambda ev, oid=registro["id"]: mudar_status_orcamento(oid, "Enviado"),
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.CHECK_CIRCLE,
                                    tooltip="Aprovar orçamento",
                                    icon_color="#1B5E20",
                                    on_click=lambda ev, oid=registro["id"]: mudar_status_orcamento(oid, "Aprovado"),
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.CANCEL,
                                    tooltip="Recusar orçamento",
                                    icon_color="#A52D35",
                                    on_click=lambda ev, oid=registro["id"]: mudar_status_orcamento(oid, "Recusado"),
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE_OUTLINE,
                                    tooltip="Excluir orçamento",
                                    icon_color="#A52D35",
                                    on_click=lambda ev, oid=registro["id"]: confirmar_exclusao_orcamentos([oid]),
                                ),
                            ]),
                        ])
                    )
                )
            if not cards:
                mensagem_vazia = (
                    "Nenhum orçamento encontrado com este status."
                    if status_selecionado != "Todos"
                    else "Nenhum orçamento salvo ainda."
                )
                cards.append(ft.Text(mensagem_vazia, color=TEXTO_SECUNDARIO))
    
            opcoes_filtro = ["Todos", "Aprovado", "Em elaboração", "Recusado", "Enviado"]
            botoes_filtro = ft.Row(
                wrap=True,
                spacing=6,
                controls=[
                    ft.Button(
                        texto,
                        on_click=lambda ev, status=texto: montar_tela_historico(status),
                        bgcolor=ROSA if texto == status_selecionado else ROSA_CLARO,
                        color=BRANCO if texto == status_selecionado else MARROM,
                    )
                    for texto in opcoes_filtro
                ],
            )
            tela = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, spacing=14, controls=[
                cabecalho_orcamentos("Histórico de orçamentos", abrir_orcamentos),
                ft.Container(padding=ft.Padding.symmetric(horizontal=18), content=ft.Column(spacing=8, controls=[
                    ft.Text("Filtrar por status", size=12, weight=ft.FontWeight.BOLD, color=MARROM),
                    botoes_filtro,
                ])),
                ft.Container(padding=ft.Padding.symmetric(horizontal=18), content=ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                    ft.Text("Selecione para excluir em lote", size=11, color=TEXTO_SECUNDARIO),
                    ft.TextButton("Excluir selecionados", icon=ft.Icons.DELETE, on_click=lambda ev: confirmar_exclusao_orcamentos(sorted(ids_orcamentos_selecionados))),
                ])),
                ft.Container(padding=ft.Padding.symmetric(horizontal=18), content=ft.Column(spacing=12, controls=cards)),
            ])
            page.controls.clear()
            page.add(tela)
            page.update()
    
        def mudar_status_orcamento(orcamento_id, status):
            atualizar_status_orcamento(orcamento_id, status)
            mostrar_aviso(f"Orçamento atualizado: {status}.")
            montar_tela_historico(filtro_status_atual["valor"])
    
        def abrir_historico_versoes(orcamento_id):
            versoes = listar_versoes_orcamento(orcamento_id)
    
            def visualizar_versao(mensagem, numero_versao):
                dlg = criar_dialogo_padrao(
                    modal=True,
                    title=ft.Text(f"Versão anterior — {numero_versao}"),
                    content=ft.Container(
                        width=380,
                        content=criar_campo_padrao(value=mensagem, multiline=True, min_lines=10, max_lines=18, read_only=True)
                    ),
                    actions=[ft.TextButton("Fechar", on_click=lambda ev: fechar_dialogo(dlg))]
                )
                page.overlay.append(dlg)
                dlg.open = True
                page.update()
    
            controles = []
            for versao in versoes:
                dados_anteriores = json.loads(versao["snapshot_json"])
                data_versao = versao["registrado_em"].replace("T", " ")
                evento_status = dados_anteriores.get("_evento") == "alteracao_status"
                if evento_status:
                    descricao_alteracao = (
                        f'Status alterado: {dados_anteriores.get("_status_anterior", "Não informado")} '
                        f'→ {dados_anteriores.get("_status_novo", "Não informado")}'
                    )
                else:
                    descricao_alteracao = f'Status: {dados_anteriores.get("status", "Não informado")}'
                controles.append(
                    ft.Container(
                        bgcolor=ROSA_CLARO, padding=10, border_radius=10,
                        content=ft.Column(spacing=6, controls=[
                            ft.Text(data_versao, size=11, color=MARROM),
                            ft.Text(
                                descricao_alteracao,
                                size=12,
                                weight=ft.FontWeight.BOLD,
                                color="#285A83" if evento_status else MARROM,
                            ),
                            ft.Text(
                                f'Total Pix: {formatar_reais(dados_anteriores["total_final_centavos"] / 100)}',
                                size=12,
                                color=MARROM,
                            ),
                            ft.TextButton(
                                "Ver versão",
                                on_click=lambda ev, msg=dados_anteriores["mensagem"], num=versao["numero"]: visualizar_versao(msg, num),
                            ),
                        ])
                    )
                )
            if not controles:
                controles.append(ft.Text("Este orçamento ainda não possui versões anteriores.", color=TEXTO_SECUNDARIO))
            dlg_historico = criar_dialogo_padrao(
                modal=True,
                title=ft.Text("Histórico de alterações"),
                content=ft.Container(width=400, content=ft.Column(controls=controles, spacing=8, scroll=ft.ScrollMode.AUTO)),
                actions=[ft.TextButton("Fechar", on_click=lambda ev: fechar_dialogo(dlg_historico))]
            )
            page.overlay.append(dlg_historico)
            dlg_historico.open = True
            page.update()
    
        def abrir_detalhe_orcamento(orcamento_id):
            registro = obter_orcamento(orcamento_id)
            if not registro:
                mostrar_aviso("Orçamento não encontrado.", "#C62828")
                return
            mensagem = registro["mensagem"]
            texto = criar_campo_padrao(value=mensagem, multiline=True, min_lines=12, max_lines=22, read_only=True)
            dialogo = criar_dialogo_padrao(
                modal=True,
                title=ft.Text(f'Orçamento {registro["numero"]}'),
                content=ft.Container(width=380, content=texto),
                actions=[
                    ft.TextButton("Editar orçamento", on_click=lambda ev: (fechar_dialogo(dialogo), abrir_orcamentos(orcamento_id=orcamento_id))),
                    ft.TextButton("Histórico de alterações", on_click=lambda ev: abrir_historico_versoes(orcamento_id)),
                    ft.TextButton("Fechar", on_click=lambda ev: fechar_dialogo(dialogo)),
                    ft.Button(
                        "Copiar mensagem",
                        icon=ft.Icons.CONTENT_COPY,
                        action=ft.CopyToClipboard(mensagem),
                        on_click=lambda ev: mostrar_aviso("Texto do orçamento copiado. Pode colar no WhatsApp."),
                    ),
                ],
            )
            page.overlay.append(dialogo)
            dialogo.open = True
            page.update()
    
        def fechar_dialogo(dialogo):
            dialogo.open = False
            page.update()
    
        def cabecalho_orcamentos(titulo, voltar):
            return ft.Container(
                padding=ft.Padding.only(left=15, right=18, top=18, bottom=8),
                content=ft.Row(controls=[
                    ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=MARROM, on_click=voltar),
                    ft.Text(titulo, size=21, weight=ft.FontWeight.BOLD, color=MARROM),
                ])
            )
    
        if not produtos and not registro_edicao:
            mostrar_aviso("Cadastre e salve a precificação de pelo menos um Produto Final.", "#C62828")
            return
    
        cliente = criar_campo_padrao(label="Nome do cliente (opcional)", value=(registro_edicao["cliente"] or "") if registro_edicao else "", border_radius=10)
        validade = criar_campo_padrao(label="Validade do orçamento (ex.: 7 dias)", value=(registro_edicao["validade"] or "7 dias") if registro_edicao else "7 dias", border_radius=10)
    
        data_entrega_salva = (registro_edicao["data_entrega"] or "") if registro_edicao else ""
        if data_entrega_salva:
            try:
                data_entrega_salva = datetime.strptime(
                    data_entrega_salva[:10], "%Y-%m-%d"
                ).strftime("%d/%m/%Y")
            except ValueError:
                pass
    
        data_entrega = criar_campo_padrao(
            label="Data de entrega (opcional)",
            hint_text="DD/MM/AAAA",
            value=data_entrega_salva,
            border_radius=10,
        )
    
        def obter_data_entrega_iso():
            valor = (data_entrega.value or "").strip()
            if not valor:
                return None
            try:
                return datetime.strptime(valor, "%d/%m/%Y").date().isoformat()
            except ValueError:
                raise ValueError(
                    "Informe a data de entrega no formato DD/MM/AAAA."
                )
        dd_produto = criar_dropdown_padrao(
            label="Produto precificado",
            options=[ft.dropdown.Option(k, v["nome"]) for k, v in produtos.items()],
            value=next(iter(produtos)),
            border_radius=10,
        )
        quantidade = criar_campo_padrao(label="Quantidade", value="1", keyboard_type=ft.KeyboardType.NUMBER, width=115, border_radius=10)
        resumo_edicao = json.loads(registro_edicao["resumo_json"] or "{}") if registro_edicao else {}
        dd_tipo_desconto = criar_dropdown_padrao(
            label="Tipo de desconto",
            value=registro_edicao["desconto_tipo"] if registro_edicao else "percentual",
            options=[
                ft.dropdown.Option("percentual", "Percentual (%)"),
                ft.dropdown.Option("valor", "Valor (R$)"),
                ft.dropdown.Option("nenhum", "Sem desconto"),
            ],
            border_radius=10,
            expand=True,
        )
        desconto = criar_campo_padrao(label="Desconto", value=str(registro_edicao["desconto_valor"]) if registro_edicao else "0", keyboard_type=ft.KeyboardType.NUMBER, width=115, border_radius=10)
        sinal_50 = ft.Checkbox(label="Solicitar sinal de 50% para confirmar a encomenda", value=bool(resumo_edicao.get("sinal_50", False)))
        lista_itens = []
        if registro_edicao:
            for item_salvo in json.loads(registro_edicao["itens_json"] or "[]"):
                snapshot = json.loads(item_salvo.get("snapshot_json") or "{}")
                lista_itens.append({
                    "precificacao_id": snapshot.get("precificacao_id"),
                    "receita_id": item_salvo.get("receita_id"),
                    "nome": item_salvo["nome"],
                    "unidade": item_salvo["unidade"],
                    "quantidade_embalagem": float(snapshot.get("quantidade_embalagem", 1) or 1),
                    "custo": float(item_salvo["custo_unitario_centavos"]) / 100,
                    "preco_base": float(item_salvo["preco_base_centavos"]) / 100,
                    "quantidade": float(item_salvo["quantidade"]),
                })
        lista_controle = ft.Column(spacing=8)
        resumo_controle = ft.Column(spacing=8)
        mensagem_preview = criar_campo_padrao(label="Prévia da mensagem para o cliente", multiline=True, min_lines=10, max_lines=18, read_only=True)
        aviso_margem = ft.Text("", size=12, weight=ft.FontWeight.BOLD)
    
        def adicionar_item(ev=None):
            try:
                produto = produtos[dd_produto.value]
                qtd = float((quantidade.value or "0").replace(",", "."))
                if qtd <= 0:
                    raise ValueError("A quantidade deve ser maior que zero.")
                lista_itens.append({**produto, "quantidade": qtd})
                atualizar_orcamento()
                mostrar_aviso(f'{produto["nome"]} adicionado ao orçamento.')
            except Exception as erro:
                mostrar_aviso(str(erro), "#C62828")
    
        def remover_item(indice):
            if 0 <= indice < len(lista_itens):
                lista_itens.pop(indice)
                atualizar_orcamento()
    
        def calcular_totais():
            total_base = sum(item["preco_base"] * item["quantidade"] for item in lista_itens)
            total_custo = sum(item["custo"] * item["quantidade"] for item in lista_itens)
            valor_desconto = float((desconto.value or "0").replace(",", "."))
            if valor_desconto < 0:
                raise ValueError("O desconto não pode ser negativo.")
            if dd_tipo_desconto.value == "percentual":
                if valor_desconto >= 100:
                    raise ValueError("O desconto percentual deve ser menor que 100%.")
                desconto_reais = total_base * valor_desconto / 100
            elif dd_tipo_desconto.value == "valor":
                desconto_reais = valor_desconto
            else:
                desconto_reais = 0
            if desconto_reais > total_base:
                raise ValueError("O desconto não pode superar o valor dos produtos.")
            fator = ((total_base - desconto_reais) / total_base) if total_base > 0 else 1
            totais = {}
            for nome, chave in modalidades:
                taxa = float(taxas.get(chave, 0)) / 100
                if taxa < 0 or taxa >= 1:
                    raise ValueError(f"Taxa inválida para {nome}.")
                totais[chave] = (total_base * fator / (1 - taxa)) if lista_itens else 0
            return total_base, total_custo, desconto_reais, fator, totais
    
        def gerar_mensagem(totais, desconto_reais):
            linhas = [
                "✨ *DM GULOSITOS*",
                "*ORÇAMENTO*",
                "",
                f"Olá, {cliente.value.strip() or 'tudo bem'}! Segue nossa proposta:",
                "",
            ]
            for item in lista_itens:
                linhas.append(f'• {item["nome"]} — {item["quantidade"]:g} {item["unidade"]}(s)')
            linhas += ["", "*Valores por forma de pagamento:*"]
            for nome, chave in modalidades:
                linhas.append(f"• {nome}: {formatar_reais(totais[chave])}")
            if desconto_reais > 0:
                linhas += ["", f"Desconto aplicado: {formatar_reais(desconto_reais)}"]
            linhas.append(f"Validade: {validade.value.strip() or 'a combinar'}")
            data_entrega_iso = obter_data_entrega_iso()
            if data_entrega_iso:
                data_entrega_texto = datetime.strptime(
                    data_entrega_iso, "%Y-%m-%d"
                ).strftime("%d/%m/%Y")
                linhas.append(f"Data de entrega: {data_entrega_texto}")
            if sinal_50.value:
                linhas += ["", "*Condição para encomenda:* solicitamos 50% de sinal para confirmar a reserva."]
                for nome, chave in modalidades:
                    sinal = totais[chave] * 0.5
                    saldo = totais[chave] - sinal
                    linhas.append(f"• {nome}: sinal de {formatar_reais(sinal)} | saldo restante de {formatar_reais(saldo)}")
            linhas += ["", "Será um prazer preparar seu pedido! 💗", "DM Gulositos"]
            return "\n".join(linhas)
    
        def atualizar_orcamento(ev=None):
            try:
                total_base, total_custo, desconto_reais, fator, totais = calcular_totais()
                lista_controle.controls.clear()
                for indice, item in enumerate(lista_itens):
                    lista_controle.controls.append(
                        ft.Container(bgcolor=BRANCO, padding=10, border_radius=10, content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Column(expand=True, spacing=2, controls=[
                                    ft.Text(item["nome"], weight=ft.FontWeight.BOLD, color=MARROM),
                                    ft.Text(f'{item["quantidade"]:g} × {formatar_reais(item["preco_base"])}', size=11, color=TEXTO_SECUNDARIO),
                                ]),
                                ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color="#C62828", on_click=lambda ev, i=indice: remover_item(i)),
                            ]
                        ))
                    )
                resumo_controle.controls.clear()
                for nome, chave in modalidades:
                    taxa = float(taxas.get(chave, 0))
                    total = totais[chave]
                    liquido = total * (1 - taxa / 100)
                    lucro = liquido - total_custo
                    margem = (lucro / total * 100) if total > 0 else 0
                    dentro = margem >= margem_minima
                    resumo_controle.controls.append(
                        ft.Container(bgcolor=ROSA_CLARO, padding=10, border_radius=10, content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Column(expand=True, spacing=2, controls=[
                                    ft.Text(nome, weight=ft.FontWeight.BOLD, color=MARROM),
                                    ft.Text(f"Taxa: {taxa:.2f}%  •  Margem: {margem:.1f}%", size=11, color=TEXTO_SECUNDARIO),
                                    ft.Text("Dentro da margem mínima" if dentro else "Abaixo da margem mínima", size=10, color="#2E7D32" if dentro else "#C62828"),
                                ]),
                                ft.Text(formatar_reais(total), weight=ft.FontWeight.BOLD, color=MARROM),
                            ]
                        ))
                    )
                aviso_margem.value = (
                    "Atenção: uma ou mais formas de pagamento ficam abaixo da margem mínima."
                    if any(
                        ((totais[chave] * (1 - float(taxas.get(chave, 0)) / 100) - total_custo) / totais[chave] * 100 < margem_minima)
                        for _, chave in modalidades if totais[chave] > 0
                    ) else "Todas as formas de pagamento respeitam a margem mínima."
                )
                aviso_margem.color = "#C62828" if aviso_margem.value.startswith("Atenção") else "#2E7D32"
                mensagem_preview.value = gerar_mensagem(totais, desconto_reais) if lista_itens else "Adicione produtos para montar a mensagem."
                botao_salvar_orcamento.action = ft.CopyToClipboard(mensagem_preview.value)
                page.update()
            except Exception as erro:
                aviso_margem.value = str(erro)
                aviso_margem.color = "#C62828"
                page.update()
    
        def salvar_e_copiar(ev=None):
            try:
                if not lista_itens:
                    raise ValueError("Adicione pelo menos um produto ao orçamento.")
                total_base, total_custo, desconto_reais, fator, totais = calcular_totais()
                mensagem = gerar_mensagem(totais, desconto_reais)
                total_final = totais["pix"]
                itens_snapshot = []
                for item in lista_itens:
                    preco_final_base = item["preco_base"] * fator
                    itens_snapshot.append({
                        "receita_id": item["receita_id"],
                        "nome": item["nome"],
                        "quantidade": item["quantidade"],
                        "unidade": item["unidade"],
                        "custo_unitario_centavos": round(item["custo"] * 100),
                        "preco_base_centavos": round(item["preco_base"] * 100),
                        "preco_final_unitario_centavos": round(preco_final_base * 100),
                        "subtotal_centavos": round(preco_final_base * item["quantidade"] * 100),
                        "snapshot_json": json.dumps({
                            "custo_original": item["custo"],
                            "preco_base_original": item["preco_base"],
                            "quantidade_embalagem": item["quantidade_embalagem"],
                            "precificacao_id": item.get("precificacao_id"),
                            "taxas": taxas,
                            "margem_minima": margem_minima,
                        }, ensure_ascii=False),
                    })
                resumo = {
                    "totais_por_modalidade": totais,
                    "taxas": taxas,
                    "margem_minima": margem_minima,
                    "custo_total": total_custo,
                    "desconto_reais": desconto_reais,
                    "desconto_tipo": dd_tipo_desconto.value,
                    "desconto_valor": float((desconto.value or "0").replace(",", ".")),
                    "sinal_50": bool(sinal_50.value),
                }
                numero_orcamento = registro_edicao["numero"] if registro_edicao else f"ORC-{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}"
                dados = {
                    "numero": numero_orcamento,
                    "cliente": cliente.value.strip(),
                    "status": "Em elaboração",
                    "validade": validade.value.strip(),
                    "data_entrega": obter_data_entrega_iso(),
                    "desconto_tipo": dd_tipo_desconto.value,
                    "desconto_valor": resumo["desconto_valor"],
                    "modalidade": "pix",
                    "total_referencia_centavos": round(total_base * 100),
                    "total_final_centavos": round(total_final * 100),
                    "itens_json": json.dumps(itens_snapshot, ensure_ascii=False),
                    "resumo_json": json.dumps(resumo, ensure_ascii=False),
                    "mensagem": mensagem,
                    "itens": itens_snapshot,
                }
                if registro_edicao:
                    atualizar_orcamento_salvo(orcamento_id, dados)
                    mostrar_aviso("Orçamento atualizado com sucesso.")
                else:
                    salvar_orcamento(dados)
                    mostrar_aviso("Orçamento salvo com sucesso.")
                montar_tela_historico()
            except Exception as erro:
                mostrar_aviso(str(erro), "#C62828")
    
        for controle in (dd_tipo_desconto, desconto, sinal_50, data_entrega):
            controle.on_change = atualizar_orcamento
    
        botao_salvar_orcamento = ft.Button(
            "Salvar alterações e copiar mensagem" if registro_edicao else "Salvar orçamento e copiar mensagem",
            icon=ft.Icons.CONTENT_COPY,
            action=ft.CopyToClipboard(mensagem_preview.value),
            on_click=salvar_e_copiar,
            bgcolor=ROSA,
            color=BRANCO,
            expand=True,
        )
    
        tela = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, spacing=14, controls=[
            cabecalho_orcamentos("Editar orçamento" if registro_edicao else "Novo orçamento", abrir_menu_opcoes),
            ft.Container(padding=ft.Padding.symmetric(horizontal=18), content=ft.Column(spacing=12, controls=[
                ft.Text("Editar orçamento" if registro_edicao else "Dados do cliente", size=15, weight=ft.FontWeight.BOLD, color=MARROM),
                cliente, validade, data_entrega,
                ft.Divider(color=ROSA_CLARO),
                ft.Text("Adicionar produtos", size=15, weight=ft.FontWeight.BOLD, color=MARROM),
                dd_produto,
                ft.Row(controls=[quantidade, ft.Button("Adicionar", icon=ft.Icons.ADD, on_click=adicionar_item, bgcolor=ROSA, color=BRANCO)]),
                lista_controle,
                ft.Divider(color=ROSA_CLARO),
                ft.Text("Desconto no orçamento", size=15, weight=ft.FontWeight.BOLD, color=MARROM),
                ft.Row(controls=[dd_tipo_desconto, desconto]),
                ft.Divider(color=ROSA_CLARO),
                ft.Text("Condição de pagamento da encomenda", size=15, weight=ft.FontWeight.BOLD, color=MARROM),
                sinal_50,
                ft.Text("Preços calculados por modalidade", size=15, weight=ft.FontWeight.BOLD, color=MARROM),
                ft.Text(f"Margem mínima configurada: {margem_minima:.1f}%", size=11, color=TEXTO_SECUNDARIO),
                resumo_controle,
                aviso_margem,
                ft.Text("Mensagem pronta para compartilhar", size=15, weight=ft.FontWeight.BOLD, color=MARROM),
                mensagem_preview,
                botao_salvar_orcamento,
                ft.Button("Ver histórico de orçamentos", icon=ft.Icons.HISTORY, on_click=lambda ev: montar_tela_historico(), bgcolor=ROSA_CLARO, color=MARROM),
            ])),
        ])
        indice_atual["valor"] = 2
        navegacao_ref["controle"].selected_index = 2
        page.controls.clear()
        if filtro_status is not None:
            montar_tela_historico(filtro_status)
            return
        page.add(tela)
        atualizar_orcamento()
        page.update()
    

    return abrir_orcamentos
