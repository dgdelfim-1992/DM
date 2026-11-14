import sqlite3
import math
import json
from datetime import datetime, date, timedelta

from servicos.precificacao_service import (
    calcular_preco_sugerido,
    calcular_indicadores_preco_praticado,
)

from database.caminhos import (
    PASTA_PROJETO,
    CAMINHO_BANCO,
    CAMINHO_BANCO_LEGADO,
    migrar_banco_legado_se_necessario,
)
from servicos.backup_service import criar_backup_automatico


# =========================================================
# CONEXÃO COM O BANCO
# =========================================================
def obter_conexao():
    migrar_banco_legado_se_necessario()
    CAMINHO_BANCO.parent.mkdir(parents=True, exist_ok=True)
    conexao = sqlite3.connect(CAMINHO_BANCO)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao

# =========================================================
# CRIAÇÃO E ATUALIZAÇÃO DAS TABELAS
# =========================================================
def criar_tabelas():
    criar_tabela_precificacao_v2()
    criar_tabelas_orcamentos()
    conexao = obter_conexao()
    try:
        conexao.executescript("""
            CREATE TABLE IF NOT EXISTS custos_fixos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT NOT NULL,
                valor_centavos INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS configuracoes (
                chave TEXT PRIMARY KEY,
                valor TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS ingredientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                marca TEXT,
                fornecedor TEXT,
                quantidade_compra REAL NOT NULL,
                unidade_compra TEXT NOT NULL,
                preco_pago_centavos INTEGER NOT NULL,
                quantidade_base REAL NOT NULL,
                unidade_base TEXT NOT NULL,
                custo_por_unidade_base REAL NOT NULL,
                observacoes TEXT,
                ativo INTEGER DEFAULT 1,
                criado_em TEXT NOT NULL,
                atualizado_em TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS historico_precos_ingredientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ingrediente_id INTEGER NOT NULL,
                nome TEXT NOT NULL,
                quantidade_compra REAL NOT NULL,
                unidade_compra TEXT NOT NULL,
                preco_pago_centavos INTEGER NOT NULL,
                quantidade_base REAL NOT NULL,
                unidade_base TEXT NOT NULL,
                custo_por_unidade_base REAL NOT NULL,
                registrado_em TEXT NOT NULL,
                FOREIGN KEY (ingrediente_id) REFERENCES ingredientes(id)
            );

            CREATE INDEX IF NOT EXISTS idx_historico_precos_ingrediente
            ON historico_precos_ingredientes (ingrediente_id, id);
            
            CREATE TABLE IF NOT EXISTS receitas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                tipo TEXT NOT NULL DEFAULT 'PRODUTO',
                rendimento_unidades REAL NOT NULL DEFAULT 1,
                custo_embalagem_centavos INTEGER DEFAULT 0,
                margem_lucro_pct REAL NOT NULL DEFAULT 100.0,
                taxa_cartao_pct REAL DEFAULT 0.0,
                ativo INTEGER DEFAULT 1,
                criado_em TEXT NOT NULL,
                atualizado_em TEXT NOT NULL,
                tempo_preparo_min REAL NOT NULL DEFAULT 0,
                tempo_batedeira_min REAL NOT NULL DEFAULT 0,
                tempo_forno_min REAL NOT NULL DEFAULT 0,
                unidade_rendimento TEXT NOT NULL DEFAULT 'un'
            );
            CREATE TABLE IF NOT EXISTS receita_itens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receita_pai_id INTEGER NOT NULL,
                ingrediente_id INTEGER,
                sub_receita_id INTEGER,
                quantidade_usada REAL NOT NULL,
                FOREIGN KEY (receita_pai_id) REFERENCES receitas(id) ON DELETE CASCADE,
                FOREIGN KEY (ingrediente_id) REFERENCES ingredientes(id),
                FOREIGN KEY (sub_receita_id) REFERENCES receitas(id)
            );
            CREATE TABLE IF NOT EXISTS precificacao_produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receita_id INTEGER NOT NULL UNIQUE,
                custo_embalagem_centavos INTEGER NOT NULL DEFAULT 0,
                margem_lucro_pct REAL NOT NULL DEFAULT 100,
                taxa_cartao_pct REAL NOT NULL DEFAULT 0,
                atualizado_em TEXT NOT NULL,
                FOREIGN KEY (receita_id) REFERENCES receitas(id)
            );
            CREATE TABLE IF NOT EXISTS precificacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receita_id INTEGER NOT NULL UNIQUE,
                quantidade_embalagem REAL NOT NULL DEFAULT 1,
                embalagem_centavos INTEGER NOT NULL DEFAULT 0,
                markup REAL NOT NULL DEFAULT 0,
                impostos REAL NOT NULL DEFAULT 0,
                taxa_cartao REAL NOT NULL DEFAULT 0,
                taxa_delivery REAL NOT NULL DEFAULT 0,
                preco_praticado_centavos INTEGER,
                embalagem_id INTEGER,
                quantidade_embalagem_insumo REAL NOT NULL DEFAULT 1,
                sacola_id INTEGER,
                quantidade_sacola REAL NOT NULL DEFAULT 0,
                ativo INTEGER DEFAULT 1,
                criado_em TEXT NOT NULL,
                atualizado_em TEXT NOT NULL,
                FOREIGN KEY (receita_id) REFERENCES receitas(id)
            );
            CREATE TABLE IF NOT EXISTS historico_precificacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                precificacao_id INTEGER NOT NULL,
                preco_sugerido_centavos INTEGER NOT NULL,
                preco_praticado_centavos INTEGER,
                custo_total_centavos INTEGER NOT NULL,
                registrado_em TEXT NOT NULL,
                FOREIGN KEY (precificacao_id) REFERENCES precificacoes(id)
            );
        """)
        conexao.execute("""
            INSERT OR IGNORE INTO configuracoes(chave, valor)
            VALUES ('horas_produtivas_mensais', '220')
        """)
        conexao.execute("""
            INSERT OR IGNORE INTO configuracoes (chave, valor)
            VALUES ('faturamento_mensal', '2000.00')
        """)

        # Migrações seguras corrigidas para usar a variável conexao correta
        colunas_receitas = [
            coluna["name"] for coluna in conexao.execute("PRAGMA table_info(receitas)").fetchall()
        ]
        novas_colunas_rec = {
            "tempo_preparo_min": "REAL NOT NULL DEFAULT 0",
            "tempo_batedeira_min": "REAL NOT NULL DEFAULT 0",
            "tempo_forno_min": "REAL NOT NULL DEFAULT 0",
            "unidade_rendimento": "TEXT NOT NULL DEFAULT 'un'"
        }
        for nome_coluna, tipo_coluna in novas_colunas_rec.items():
            if nome_coluna not in colunas_receitas:
                conexao.execute(f"ALTER TABLE receitas ADD COLUMN {nome_coluna} {tipo_coluna}")

        colunas_prec = [
            linha["name"] for linha in conexao.execute("PRAGMA table_info(precificacoes)").fetchall()
        ]
        novas_colunas_prec = {
            "embalagem_id": "INTEGER",
            "quantidade_embalagem_insumo": "REAL NOT NULL DEFAULT 1",
            "sacola_id": "INTEGER",
            "quantidade_sacola": "REAL NOT NULL DEFAULT 0"
        }
        for nome_coluna, tipo_coluna in novas_colunas_prec.items():
            if nome_coluna not in colunas_prec:
                conexao.execute(f"ALTER TABLE precificacoes ADD COLUMN {nome_coluna} {tipo_coluna}")

        # Cria um registro inicial para os ingredientes já cadastrados.
        # Não representa um preço antigo: é apenas o ponto de partida
        # para as próximas comparações.
        conexao.execute("""
            INSERT INTO historico_precos_ingredientes (
                ingrediente_id,
                nome,
                quantidade_compra,
                unidade_compra,
                preco_pago_centavos,
                quantidade_base,
                unidade_base,
                custo_por_unidade_base,
                registrado_em
            )
            SELECT
                i.id,
                i.nome,
                i.quantidade_compra,
                i.unidade_compra,
                i.preco_pago_centavos,
                i.quantidade_base,
                i.unidade_base,
                i.custo_por_unidade_base,
                COALESCE(i.atualizado_em, i.criado_em)
            FROM ingredientes i
            WHERE NOT EXISTS (
                SELECT 1
                FROM historico_precos_ingredientes h
                WHERE h.ingrediente_id = i.id
            )
        """)

        conexao.commit()
    finally:
        conexao.close()


# =========================================================
# CONVERSÃO DE UNIDADES
# =========================================================
def converter_para_base(quantidade, unidade):
    """Converte kg/g, l/ml ou unidades para a unidade-base correspondente."""
    try:
        quantidade = float(quantidade)
    except (TypeError, ValueError) as erro:
        raise ValueError("A quantidade deve ser numérica.") from erro

    if not math.isfinite(quantidade) or quantidade <= 0:
        raise ValueError("A quantidade precisa ser um número finito maior que zero.")

    unidade = (unidade or "").strip().lower()
    conversoes = {
        "kg": (1000, "g"),
        "g": (1, "g"),
        "l": (1000, "ml"),
        "litro": (1000, "ml"),
        "litros": (1000, "ml"),
        "ml": (1, "ml"),
        "un": (1, "un"),
        "unidade": (1, "un"),
        "unidades": (1, "un")
    }
    if unidade not in conversoes:
        raise ValueError(f"Unidade não reconhecida: {unidade}")

    fator, unidade_base = conversoes[unidade]
    return quantidade * fator, unidade_base


def calcular_custo_unitario(preco_pago_centavos, quantidade_base):
    """Calcula o custo por unidade-base, rejeitando entradas inválidas."""
    try:
        preco_pago_centavos = float(preco_pago_centavos)
        quantidade_base = float(quantidade_base)
    except (TypeError, ValueError) as erro:
        raise ValueError("Preço e quantidade devem ser numéricos.") from erro

    if not math.isfinite(preco_pago_centavos) or not math.isfinite(quantidade_base):
        raise ValueError("Preço e quantidade devem ser números finitos.")
    if preco_pago_centavos < 0 or quantidade_base <= 0:
        raise ValueError("O preço não pode ser negativo e a quantidade deve ser maior que zero.")

    return (preco_pago_centavos / 100) / quantidade_base


# =========================================================
# INGREDIENTES
# =========================================================
def cadastrar_ingrediente(
    nome,
    marca,
    fornecedor,
    quantidade_compra,
    unidade_compra,
    preco_pago_centavos,
    observacoes=""
):
    nome = (nome or "").strip()

    if not nome:
        raise ValueError("Informe o nome do ingrediente.")

    quantidade_base, unidade_base = converter_para_base(
        quantidade_compra,
        unidade_compra
    )

    custo_unitario = calcular_custo_unitario(
        preco_pago_centavos,
        quantidade_base
    )

    agora_iso = datetime.now().isoformat(timespec="seconds")
    unidade_normalizada = unidade_compra.strip().lower()

    conexao = obter_conexao()

    try:
        cursor = conexao.execute("""
            INSERT INTO ingredientes (
                nome,
                marca,
                fornecedor,
                quantidade_compra,
                unidade_compra,
                preco_pago_centavos,
                quantidade_base,
                unidade_base,
                custo_por_unidade_base,
                observacoes,
                ativo,
                criado_em,
                atualizado_em
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
        """, (
            nome,
            marca.strip() if marca else None,
            fornecedor.strip() if fornecedor else None,
            quantidade_compra,
            unidade_normalizada,
            preco_pago_centavos,
            quantidade_base,
            unidade_base,
            custo_unitario,
            observacoes.strip() if observacoes else None,
            agora_iso,
            agora_iso
        ))

        ingrediente_id = cursor.lastrowid

        # Registra o preço inicial no histórico.
        conexao.execute("""
            INSERT INTO historico_precos_ingredientes (
                ingrediente_id,
                nome,
                quantidade_compra,
                unidade_compra,
                preco_pago_centavos,
                quantidade_base,
                unidade_base,
                custo_por_unidade_base,
                registrado_em
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ingrediente_id,
            nome,
            quantidade_compra,
            unidade_normalizada,
            preco_pago_centavos,
            quantidade_base,
            unidade_base,
            custo_unitario,
            agora_iso
        ))

        conexao.commit()
        return ingrediente_id

    finally:
        conexao.close()

def listar_ingredientes():
    conexao = obter_conexao()
    try:
        return conexao.execute("""
            SELECT * FROM ingredientes WHERE ativo = 1 ORDER BY nome COLLATE NOCASE
        """).fetchall()
    finally:
        conexao.close()

def obter_ingrediente(ingrediente_id):
    conexao = obter_conexao()
    try:
        return conexao.execute("""
            SELECT * FROM ingredientes WHERE id = ? AND ativo = 1
        """, (ingrediente_id,)).fetchone()
    finally:
        conexao.close()

def listar_historico_precos_ingrediente(ingrediente_id):
    """Retorna o histórico de preços de um ingrediente, do mais recente ao mais antigo."""
    conexao = obter_conexao()
    try:
        return conexao.execute("""
            SELECT
                id,
                ingrediente_id,
                nome,
                quantidade_compra,
                unidade_compra,
                preco_pago_centavos,
                quantidade_base,
                unidade_base,
                custo_por_unidade_base,
                registrado_em
            FROM historico_precos_ingredientes
            WHERE ingrediente_id = ?
            ORDER BY id DESC
        """, (ingrediente_id,)).fetchall()
    finally:
        conexao.close()


def atualizar_ingrediente(
    ingrediente_id,
    nome,
    marca,
    fornecedor,
    quantidade_compra,
    unidade_compra,
    preco_pago_centavos,
    observacoes=""
):
    nome = (nome or "").strip()

    if not nome:
        raise ValueError("Informe o nome do ingrediente.")

    unidade_normalizada = (unidade_compra or "").strip().lower()

    quantidade_base, unidade_base = converter_para_base(
        quantidade_compra,
        unidade_normalizada
    )

    custo_unitario = calcular_custo_unitario(
        preco_pago_centavos,
        quantidade_base
    )

    agora_iso = datetime.now().isoformat(timespec="seconds")

    conexao = obter_conexao()

    try:
        anterior = conexao.execute("""
            SELECT *
            FROM ingredientes
            WHERE id = ? AND ativo = 1
        """, (ingrediente_id,)).fetchone()

        if anterior is None:
            raise ValueError("Ingrediente não encontrado.")

        # Verifica se houve alteração que afeta o custo.
        houve_alteracao_preco = (
            int(anterior["preco_pago_centavos"]) != int(preco_pago_centavos)
            or float(anterior["quantidade_compra"]) != float(quantidade_compra)
            or anterior["unidade_compra"] != unidade_normalizada
            or anterior["unidade_base"] != unidade_base
        )

        conexao.execute("""
            UPDATE ingredientes SET
                nome = ?,
                marca = ?,
                fornecedor = ?,
                quantidade_compra = ?,
                unidade_compra = ?,
                preco_pago_centavos = ?,
                quantidade_base = ?,
                unidade_base = ?,
                custo_por_unidade_base = ?,
                observacoes = ?,
                atualizado_em = ?
            WHERE id = ?
        """, (
            nome,
            marca.strip() if marca else None,
            fornecedor.strip() if fornecedor else None,
            quantidade_compra,
            unidade_normalizada,
            preco_pago_centavos,
            quantidade_base,
            unidade_base,
            custo_unitario,
            observacoes.strip() if observacoes else None,
            agora_iso,
            ingrediente_id
        ))

        # Só registra histórico quando o custo ou a apresentação
        # da embalagem realmente mudar.
        if houve_alteracao_preco:
            conexao.execute("""
                INSERT INTO historico_precos_ingredientes (
                    ingrediente_id,
                    nome,
                    quantidade_compra,
                    unidade_compra,
                    preco_pago_centavos,
                    quantidade_base,
                    unidade_base,
                    custo_por_unidade_base,
                    registrado_em
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ingrediente_id,
                nome,
                quantidade_compra,
                unidade_normalizada,
                preco_pago_centavos,
                quantidade_base,
                unidade_base,
                custo_unitario,
                agora_iso
            ))

        conexao.commit()
        return True

    finally:
        conexao.close()

def listar_alertas_aumento_ingredientes():
    conexao = obter_conexao()

    try:
        registros = conexao.execute("""
            SELECT
                i.id AS ingrediente_id,
                i.nome AS nome_atual,
                h.id AS historico_id,
                h.nome,
                h.preco_pago_centavos,
                h.quantidade_compra,
                h.unidade_compra,
                h.unidade_base,
                h.custo_por_unidade_base,
                h.registrado_em
            FROM ingredientes i
            INNER JOIN historico_precos_ingredientes h
                ON h.ingrediente_id = i.id
            WHERE i.ativo = 1
            ORDER BY i.id, h.id DESC
        """).fetchall()

        historicos = {}

        for registro in registros:
            ingrediente_id = registro["ingrediente_id"]

            if ingrediente_id not in historicos:
                historicos[ingrediente_id] = []

            historicos[ingrediente_id].append(registro)

        alertas = []

        for ingrediente_id, historico in historicos.items():

            # É necessário ter pelo menos dois registros.
            if len(historico) < 2:
                continue

            atual = historico[0]
            anterior = historico[1]

            # Não compara unidades-base diferentes.
            if atual["unidade_base"] != anterior["unidade_base"]:
                continue

            custo_atual = float(atual["custo_por_unidade_base"])
            custo_anterior = float(anterior["custo_por_unidade_base"])

            if custo_anterior <= 0:
                continue

            aumento = custo_atual - custo_anterior

            if aumento > 0:
                percentual = (aumento / custo_anterior) * 100

                alertas.append({
                    "ingrediente_id": ingrediente_id,
                    "nome": atual["nome_atual"],
                    "unidade_base": atual["unidade_base"],
                    "custo_anterior": custo_anterior,
                    "custo_atual": custo_atual,
                    "aumento_percentual": percentual,
                    "preco_anterior": anterior["preco_pago_centavos"] / 100,
                    "preco_atual": atual["preco_pago_centavos"] / 100,
                    "data_atual": atual["registrado_em"],
                })

        alertas.sort(
            key=lambda item: item["aumento_percentual"],
            reverse=True
        )

        return alertas

    finally:
        conexao.close()

def excluir_ingrediente(ingrediente_id):
    conexao = obter_conexao()
    try:
        referencia = conexao.execute("""
            SELECT COUNT(*) FROM receita_itens WHERE ingrediente_id = ?
        """, (ingrediente_id,)).fetchone()[0]

        if referencia > 0:
            raise ValueError(
                "Este ingrediente está vinculado a uma ou mais receitas. "
                "Remova-o das receitas antes de excluí-lo."
            )
        conexao.execute("""
            UPDATE ingredientes SET ativo = 0, atualizado_em = ? WHERE id = ?
        """, (datetime.now().isoformat(timespec="seconds"), ingrediente_id))
        conexao.commit()
        return True
    finally:
        conexao.close()

# =========================================================
# CUSTOS FIXOS
# =========================================================
def _validar_custo_fixo(descricao, valor_centavos):
    descricao = (descricao or "").strip()
    if not descricao:
        raise ValueError("Informe a descrição do custo fixo.")

    try:
        valor_numerico = float(valor_centavos)
    except (TypeError, ValueError) as erro:
        raise ValueError("O valor do custo fixo deve ser numérico.") from erro

    if not math.isfinite(valor_numerico) or valor_numerico < 0:
        raise ValueError("O valor do custo fixo deve ser finito e não negativo.")
    if not valor_numerico.is_integer():
        raise ValueError("O valor do custo fixo deve ser informado em centavos inteiros.")

    return descricao, int(valor_numerico)


def cadastrar_custo_fixo(descricao, valor_centavos):
    descricao, valor_centavos = _validar_custo_fixo(descricao, valor_centavos)
    conexao = obter_conexao()
    try:
        cursor = conexao.execute("""
            INSERT INTO custos_fixos (descricao, valor_centavos) VALUES (?, ?)
        """, (descricao, valor_centavos))
        conexao.commit()
        return cursor.lastrowid
    finally:
        conexao.close()


def atualizar_custo_fixo(custo_id, descricao, valor_centavos):
    descricao, valor_centavos = _validar_custo_fixo(descricao, valor_centavos)
    conexao = obter_conexao()
    try:
        cursor = conexao.execute("""
            UPDATE custos_fixos SET descricao = ?, valor_centavos = ? WHERE id = ?
        """, (descricao, valor_centavos, custo_id))
        if cursor.rowcount == 0:
            raise ValueError("Custo fixo não encontrado.")
        conexao.commit()
        return True
    finally:
        conexao.close()


def excluir_custo_fixo(custo_id):
    conexao = obter_conexao()
    try:
        cursor = conexao.execute("DELETE FROM custos_fixos WHERE id = ?", (custo_id,))
        if cursor.rowcount == 0:
            raise ValueError("Custo fixo não encontrado.")
        conexao.commit()
        return True
    finally:
        conexao.close()

def obter_fator_custo_fixo():
    conexao = obter_conexao()
    try:
        total_custos = conexao.execute("""
            SELECT SUM(valor_centavos) FROM custos_fixos
        """).fetchone()[0] or 0

        fat_row = conexao.execute("""
            SELECT valor FROM configuracoes WHERE chave = 'faturamento_mensal'
        """).fetchone()

        faturamento = float(fat_row["valor"]) if fat_row else 2000.0
        if faturamento <= 0:
            return 0.0
        return (total_custos / 100) / faturamento
    finally:
        conexao.close()

def listar_custos_fixos():
    conexao = obter_conexao()
    try:
        return conexao.execute("""
            SELECT * FROM custos_fixos ORDER BY descricao
        """).fetchall()
    finally:
        conexao.close()


def obter_faturamento_mensal():
    """Retorna o faturamento mensal de referência configurado."""
    conexao = obter_conexao()
    try:
        linha = conexao.execute(
            "SELECT valor FROM configuracoes WHERE chave = 'faturamento_mensal'"
        ).fetchone()
        return str(linha["valor"]) if linha else "2000.00"
    finally:
        conexao.close()


def salvar_faturamento_mensal(valor):
    """Valida e salva o faturamento mensal de referência."""
    try:
        numero = float(str(valor).replace(",", ".").strip())
    except (TypeError, ValueError) as erro:
        raise ValueError("Informe um faturamento mensal válido.") from erro
    if not math.isfinite(numero) or numero <= 0:
        raise ValueError("O faturamento mensal deve ser maior que zero.")
    conexao = obter_conexao()
    try:
        conexao.execute(
            "INSERT OR REPLACE INTO configuracoes (chave, valor) "
            "VALUES ('faturamento_mensal', ?)",
            (str(valor).replace(",", ".").strip(),),
        )
        conexao.commit()
        return numero
    finally:
        conexao.close()

# =========================================================
# RECEITAS E SUB-RECEITAS
# =========================================================
def _validar_dados_receita(
    conexao,
    nome,
    tipo,
    rendimento_unidades,
    custo_embalagem_centavos,
    margem_lucro_pct,
    taxa_cartao_pct,
    lista_itens,
    tempo_preparo_min,
    tempo_batedeira_min,
    tempo_forno_min,
    unidade_rendimento,
    receita_id=None,
):
    """Valida e normaliza os dados antes de gravar uma ficha técnica."""
    nome = (nome or "").strip()
    tipo = (tipo or "").strip().upper()
    unidade_rendimento = (unidade_rendimento or "un").strip().lower()

    if not nome:
        raise ValueError("Informe o nome da receita.")
    if tipo not in ("PRODUTO", "SUB_RECEITA"):
        raise ValueError("O tipo de receita deve ser PRODUTO ou SUB_RECEITA.")
    if unidade_rendimento not in ("un", "g"):
        raise ValueError("A unidade de rendimento deve ser un ou g.")

    def numero_finito(valor, descricao, minimo=None, estritamente_maior=False):
        try:
            numero = float(valor)
        except (TypeError, ValueError) as erro:
            raise ValueError(f"{descricao} deve ser numérico.") from erro
        if not math.isfinite(numero):
            raise ValueError(f"{descricao} deve ser um número finito.")
        if minimo is not None:
            if estritamente_maior and numero <= minimo:
                raise ValueError(f"{descricao} deve ser maior que {minimo}.")
            if not estritamente_maior and numero < minimo:
                raise ValueError(f"{descricao} não pode ser negativo.")
        return numero

    rendimento = numero_finito(
        rendimento_unidades, "O rendimento", minimo=0, estritamente_maior=True
    )
    embalagem = numero_finito(
        custo_embalagem_centavos, "O custo de embalagem", minimo=0
    )
    margem = numero_finito(margem_lucro_pct, "A margem de lucro", minimo=0)
    taxa = numero_finito(taxa_cartao_pct, "A taxa de cartão", minimo=0)
    tempos = [
        numero_finito(tempo_preparo_min, "O tempo de preparo", minimo=0),
        numero_finito(tempo_batedeira_min, "O tempo de batedeira", minimo=0),
        numero_finito(tempo_forno_min, "O tempo de forno", minimo=0),
    ]

    if not isinstance(lista_itens, (list, tuple)) or not lista_itens:
        raise ValueError("Adicione ao menos um ingrediente ou sub-receita.")

    itens_normalizados = []
    for indice, item in enumerate(lista_itens, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"O item {indice} da receita é inválido.")

        ingrediente_id = item.get("ingrediente_id")
        sub_receita_id = item.get("sub_receita_id")
        tem_ingrediente = ingrediente_id is not None
        tem_sub_receita = sub_receita_id is not None

        if tem_ingrediente == tem_sub_receita:
            raise ValueError(
                f"O item {indice} deve informar somente um ingrediente ou uma sub-receita."
            )

        quantidade = numero_finito(
            item.get("quantidade_usada"),
            f"A quantidade do item {indice}",
            minimo=0,
            estritamente_maior=True,
        )

        if tem_ingrediente:
            try:
                ingrediente_id = int(ingrediente_id)
            except (TypeError, ValueError) as erro:
                raise ValueError(f"O ingrediente do item {indice} é inválido.") from erro
            ingrediente = conexao.execute(
                "SELECT id FROM ingredientes WHERE id = ? AND ativo = 1",
                (ingrediente_id,),
            ).fetchone()
            if not ingrediente:
                raise ValueError(f"O ingrediente do item {indice} não existe ou está inativo.")
            itens_normalizados.append({
                "ingrediente_id": ingrediente_id,
                "sub_receita_id": None,
                "quantidade_usada": quantidade,
            })
        else:
            try:
                sub_receita_id = int(sub_receita_id)
            except (TypeError, ValueError) as erro:
                raise ValueError(f"A sub-receita do item {indice} é inválida.") from erro
            sub_receita = conexao.execute(
                """
                SELECT id FROM receitas
                WHERE id = ? AND ativo = 1 AND tipo = 'SUB_RECEITA'
                """,
                (sub_receita_id,),
            ).fetchone()
            if not sub_receita:
                raise ValueError(
                    f"A sub-receita do item {indice} não existe, está inativa ou não é uma sub-receita."
                )

            if receita_id is not None:
                ciclo = conexao.execute(
                    """
                    WITH RECURSIVE dependencias(id) AS (
                        SELECT ?
                        UNION
                        SELECT ri.sub_receita_id
                        FROM receita_itens ri
                        JOIN dependencias d ON ri.receita_pai_id = d.id
                        WHERE ri.sub_receita_id IS NOT NULL
                    )
                    SELECT 1 FROM dependencias WHERE id = ? LIMIT 1
                    """,
                    (sub_receita_id, receita_id),
                ).fetchone()
                if ciclo:
                    raise ValueError(
                        "Esta alteração criaria um ciclo entre receitas e sub-receitas."
                    )

            itens_normalizados.append({
                "ingrediente_id": None,
                "sub_receita_id": sub_receita_id,
                "quantidade_usada": quantidade,
            })

    return {
        "nome": nome,
        "tipo": tipo,
        "rendimento_unidades": rendimento,
        "custo_embalagem_centavos": embalagem,
        "margem_lucro_pct": margem,
        "taxa_cartao_pct": taxa,
        "lista_itens": itens_normalizados,
        "tempo_preparo_min": tempos[0],
        "tempo_batedeira_min": tempos[1],
        "tempo_forno_min": tempos[2],
        "unidade_rendimento": unidade_rendimento,
    }


def cadastrar_receita(nome, tipo, rendimento_unidades, custo_embalagem_centavos, margem_lucro_pct, taxa_cartao_pct, lista_itens, tempo_preparo_min=0, tempo_batedeira_min=0, tempo_forno_min=0, unidade_rendimento="un"):
    conexao = obter_conexao()
    try:
        dados = _validar_dados_receita(
            conexao,
            nome,
            tipo,
            rendimento_unidades,
            custo_embalagem_centavos,
            margem_lucro_pct,
            taxa_cartao_pct,
            lista_itens,
            tempo_preparo_min,
            tempo_batedeira_min,
            tempo_forno_min,
            unidade_rendimento,
        )
        agora_iso = datetime.now().isoformat(timespec="seconds")
        cursor = conexao.execute(
            """
            INSERT INTO receitas (
                nome, tipo, rendimento_unidades, custo_embalagem_centavos, margem_lucro_pct, taxa_cartao_pct,
                ativo, criado_em, atualizado_em, tempo_preparo_min, tempo_batedeira_min, tempo_forno_min, unidade_rendimento
            ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?)
            """,
            (
                dados["nome"], dados["tipo"], dados["rendimento_unidades"],
                dados["custo_embalagem_centavos"], dados["margem_lucro_pct"],
                dados["taxa_cartao_pct"], agora_iso, agora_iso,
                dados["tempo_preparo_min"], dados["tempo_batedeira_min"],
                dados["tempo_forno_min"], dados["unidade_rendimento"],
            ),
        )
        receita_id = cursor.lastrowid
        for item in dados["lista_itens"]:
            conexao.execute(
                """
                INSERT INTO receita_itens (
                    receita_pai_id, ingrediente_id, sub_receita_id, quantidade_usada
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    receita_id, item["ingrediente_id"],
                    item["sub_receita_id"], item["quantidade_usada"],
                ),
            )
        conexao.commit()
        return receita_id
    finally:
        conexao.close()


def listar_receitas_ativas(tipo=None):
    """Lista receitas ativas, opcionalmente filtradas por tipo."""
    conexao = obter_conexao()
    try:
        if tipo:
            return conexao.execute(
                "SELECT * FROM receitas WHERE ativo = 1 AND tipo = ? ORDER BY nome",
                (str(tipo).strip().upper(),),
            ).fetchall()
        return conexao.execute(
            "SELECT * FROM receitas WHERE ativo = 1 ORDER BY nome"
        ).fetchall()
    finally:
        conexao.close()


def listar_produtos_finais():
    """Lista somente as receitas do tipo produto final."""
    return listar_receitas_ativas("PRODUTO")


def listar_sub_receitas_ativas():
    """Lista somente as sub-receitas ativas."""
    return listar_receitas_ativas("SUB_RECEITA")


def obter_dados_relatorio_geral():
    """Busca em uma única conexão os dados-base do relatório gerencial."""
    conexao = obter_conexao()
    try:
        receitas = conexao.execute(
            "SELECT * FROM receitas WHERE ativo = 1 ORDER BY tipo DESC, nome"
        ).fetchall()
        custos = conexao.execute(
            "SELECT * FROM custos_fixos ORDER BY descricao"
        ).fetchall()
        ingredientes = conexao.execute(
            "SELECT * FROM ingredientes WHERE ativo = 1 ORDER BY nome"
        ).fetchall()
        linha_faturamento = conexao.execute(
            "SELECT valor FROM configuracoes WHERE chave = 'faturamento_mensal'"
        ).fetchone()
        faturamento = float(linha_faturamento["valor"]) if linha_faturamento else 2000.0
        return {
            "receitas": receitas,
            "custos": custos,
            "ingredientes": ingredientes,
            "faturamento_alvo": faturamento,
        }
    finally:
        conexao.close()

def obter_receita(receita_id):
    conexao = obter_conexao()
    try:
        receita = conexao.execute("SELECT * FROM receitas WHERE id = ? AND ativo = 1", (receita_id,)).fetchone()
        if not receita:
            return None
        itens = conexao.execute("SELECT * FROM receita_itens WHERE receita_pai_id = ?", (receita_id,)).fetchall()
        return {"receita": receita, "itens": itens}
    finally:
        conexao.close()

def atualizar_receita(receita_id, nome, tipo, rendimento_unidades, custo_embalagem_centavos, margem_lucro_pct, taxa_cartao_pct, lista_itens, tempo_preparo_min=0, tempo_batedeira_min=0, tempo_forno_min=0, unidade_rendimento="un"):
    conexao = obter_conexao()
    try:
        receita_atual = conexao.execute(
            "SELECT id FROM receitas WHERE id = ? AND ativo = 1",
            (receita_id,),
        ).fetchone()
        if not receita_atual:
            raise ValueError("Receita não encontrada ou inativa.")

        dados = _validar_dados_receita(
            conexao,
            nome,
            tipo,
            rendimento_unidades,
            custo_embalagem_centavos,
            margem_lucro_pct,
            taxa_cartao_pct,
            lista_itens,
            tempo_preparo_min,
            tempo_batedeira_min,
            tempo_forno_min,
            unidade_rendimento,
            receita_id=receita_id,
        )
        agora_iso = datetime.now().isoformat(timespec="seconds")
        conexao.execute(
            """
            UPDATE receitas SET
                nome = ?, tipo = ?, rendimento_unidades = ?, custo_embalagem_centavos = ?, margem_lucro_pct = ?,
                taxa_cartao_pct = ?, atualizado_em = ?, tempo_preparo_min = ?, tempo_batedeira_min = ?,
                tempo_forno_min = ?, unidade_rendimento = ?
            WHERE id = ?
            """,
            (
                dados["nome"], dados["tipo"], dados["rendimento_unidades"],
                dados["custo_embalagem_centavos"], dados["margem_lucro_pct"],
                dados["taxa_cartao_pct"], agora_iso, dados["tempo_preparo_min"],
                dados["tempo_batedeira_min"], dados["tempo_forno_min"],
                dados["unidade_rendimento"], receita_id,
            ),
        )

        conexao.execute("DELETE FROM receita_itens WHERE receita_pai_id = ?", (receita_id,))
        for item in dados["lista_itens"]:
            conexao.execute(
                """
                INSERT INTO receita_itens (
                    receita_pai_id, ingrediente_id, sub_receita_id, quantidade_usada
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    receita_id, item["ingrediente_id"],
                    item["sub_receita_id"], item["quantidade_usada"],
                ),
            )

        conexao.commit()
        return True
    finally:
        conexao.close()

def excluir_receita(receita_id):
    conexao = obter_conexao()
    try:
        conexao.execute("UPDATE receitas SET ativo = 0 WHERE id = ?", (receita_id,))
        conexao.commit()
    finally:
        conexao.close()

# =========================================================
# CÁLCULO DO CUSTO DA RECEITA
# =========================================================
def calcular_custo_receita(receita_id):
    conexao = obter_conexao()
    try:
        receita = conexao.execute("SELECT * FROM receitas WHERE id = ? AND ativo = 1", (receita_id,)).fetchone()
        if not receita:
            return None
        itens = conexao.execute("SELECT * FROM receita_itens WHERE receita_pai_id = ?", (receita_id,)).fetchall()

        custo_insumos = 0.0
        for item in itens:
            if item["ingrediente_id"] is not None:
                ingrediente = conexao.execute("SELECT custo_por_unidade_base FROM ingredientes WHERE id = ? AND ativo = 1", (item["ingrediente_id"],)).fetchone()
                if ingrediente:
                    custo_insumos += (item["quantidade_usada"] * ingrediente["custo_por_unidade_base"])
            elif item["sub_receita_id"] is not None:
                sub_receita = calcular_custo_receita(item["sub_receita_id"])
                if sub_receita:
                    custo_insumos += (item["quantidade_usada"] * sub_receita["custo_unitario"])

        rendimento = receita["rendimento_unidades"]
        if rendimento <= 0:
            rendimento = 1
        custo_unitario = custo_insumos / rendimento

        return {
            "custo_insumos": custo_insumos,
            "custo_total": custo_insumos,
            "custo_unitario": custo_unitario,
            "rendimento": rendimento,
            "unidade_rendimento": receita["unidade_rendimento"]
        }
    finally:
        conexao.close()

# =========================================================
# PRECIFICAÇÃO INDEPENDENTE
# =========================================================
def salvar_precificacao_produto(receita_id, custo_embalagem_centavos, margem_lucro_pct, taxa_cartao_pct):
    agora_iso = datetime.now().isoformat(timespec="seconds")
    conexao = obter_conexao()
    try:
        conexao.execute("""
            INSERT INTO precificacao_produtos (
                receita_id, custo_embalagem_centavos, margem_lucro_pct, taxa_cartao_pct, atualizado_em
            ) VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(receita_id) DO UPDATE SET
                custo_embalagem_centavos = excluded.custo_embalagem_centavos,
                margem_lucro_pct = excluded.margem_lucro_pct,
                taxa_cartao_pct = excluded.taxa_cartao_pct,
                atualizado_em = excluded.atualizado_em
        """, (receita_id, custo_embalagem_centavos, margem_lucro_pct, taxa_cartao_pct, agora_iso))
        conexao.commit()
        return True
    finally:
        conexao.close()

def obter_precificacao_produto(receita_id):
    conexao = obter_conexao()
    try:
        return conexao.execute("SELECT * FROM precificacao_produtos WHERE receita_id = ?", (receita_id,)).fetchone()
    finally:
        conexao.close()

def calcular_precificacao_produto(receita_id):
    custo = calcular_custo_receita(receita_id)
    if not custo:
        return None
    precificacao = obter_precificacao_produto(receita_id)
    if not precificacao:
        return None

    rendimento = custo["rendimento"]
    if rendimento <= 0: return None

    custo_insumos = custo["custo_insumos"]
    custo_embalagem = precificacao["custo_embalagem_centavos"] / 100
    custo_fixo = calcular_custo_fixo_proporcional(receita_id)
    custo_mao_obra = calcular_custo_mao_obra_proporcional(receita_id)
    custo_total = custo_insumos + custo_embalagem + custo_fixo + custo_mao_obra
    custo_unitario = custo_total / rendimento

    margem_pct = float(precificacao["margem_lucro_pct"])
    taxa_pct = float(precificacao["taxa_cartao_pct"])
    impostos_pct = obter_impostos_pct()
    preco_venda = calcular_preco_sugerido(
        custo_unitario, margem_pct, impostos_pct, taxa_pct
    )

    return {
        "custo_insumos": custo_insumos, "custo_embalagem": custo_embalagem, "custo_fixo": custo_fixo,
        "custo_mao_obra": custo_mao_obra,
        "custo_total": custo_total, "custo_unitario": custo_unitario, "preco_venda_sugerido": preco_venda,
        "lucro_unitario": preco_venda - custo_unitario, "rendimento": rendimento, "unidade_rendimento": custo["unidade_rendimento"]
    }


def salvar_tempos_receita(receita_id, preparo, batedeira, forno):
    preparo = float(preparo or 0)
    batedeira = float(batedeira or 0)
    forno = float(forno or 0)

    if min(preparo, batedeira, forno) < 0:
        raise ValueError("Os tempos não podem ser negativos.")

    con = obter_conexao()
    try:
        con.execute("""
            UPDATE receitas
            SET tempo_preparo_min=?,
                tempo_batedeira_min=?,
                tempo_forno_min=?
            WHERE id=?
        """, (preparo, batedeira, forno, receita_id))
        con.commit()
    finally:
        con.close()


# =========================================================
# CONFIGURAÇÃO E RATEIO DE CUSTOS FIXOS POR HORA
# =========================================================
def obter_horas_produtivas_mensais():
    con = obter_conexao()
    try:
        resultado = con.execute("SELECT valor FROM configuracoes WHERE chave = 'horas_produtivas_mensais'").fetchone()
        return float(resultado["valor"]) if resultado else 220.0
    finally:
        con.close()

def salvar_horas_produtivas_mensais(horas):
    try:
        horas = float(horas)
    except (TypeError, ValueError) as erro:
        raise ValueError("As horas produtivas devem ser numéricas.") from erro
    if not math.isfinite(horas) or horas <= 0:
        raise ValueError("As horas produtivas devem ser finitas e maiores que zero.")
    con = obter_conexao()
    try:
        con.execute("""
            INSERT INTO configuracoes(chave, valor) VALUES ('horas_produtivas_mensais', ?)
            ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor
        """, (str(horas),))
        con.commit()
    finally:
        con.close()

def obter_remuneracao_mensal_desejada():
    """Retorna a remuneração mensal desejada para remunerar o trabalho."""
    con = obter_conexao()
    try:
        resultado = con.execute("SELECT valor FROM configuracoes WHERE chave = 'remuneracao_mensal_desejada'").fetchone()
        return float(resultado["valor"]) if resultado else 0.0
    finally:
        con.close()


def salvar_remuneracao_mensal_desejada(valor):
    try:
        valor = float(valor)
    except (TypeError, ValueError) as erro:
        raise ValueError("A remuneração mensal desejada deve ser numérica.") from erro
    if not math.isfinite(valor) or valor < 0:
        raise ValueError("A remuneração mensal desejada deve ser finita e não negativa.")
    con = obter_conexao()
    try:
        con.execute("""INSERT INTO configuracoes(chave, valor)
            VALUES ('remuneracao_mensal_desejada', ?)
            ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor""", (str(valor),))
        con.commit()
    finally:
        con.close()


def obter_valor_hora_mao_obra():
    horas = obter_horas_produtivas_mensais()
    return obter_remuneracao_mensal_desejada() / horas if horas > 0 else 0.0


def calcular_custo_mao_obra_proporcional(receita_id, fator_proporcao=1.0):
    """Mão de obra direta: preparo + batedeira; não inclui tempo passivo de forno."""
    receita_dados = obter_receita(receita_id)
    if not receita_dados:
        return 0.0
    receita = receita_dados["receita"]
    # Preparo e acompanhamento da batedeira compõem o trabalho direto.
    # O forno é tratado como tempo passivo de ocupação, sem mão de obra direta.
    minutos_ativos = (
        float(receita["tempo_preparo_min"] or 0)
        + float(receita["tempo_batedeira_min"] or 0)
    )
    fator_proporcao = float(fator_proporcao)
    if fator_proporcao < 0:
        raise ValueError("A proporção da receita não pode ser negativa.")
    return (minutos_ativos / 60.0) * obter_valor_hora_mao_obra() * fator_proporcao


def obter_custo_fixo_por_hora():
    total_centavos = sum(int(c["valor_centavos"]) for c in listar_custos_fixos())
    horas = obter_horas_produtivas_mensais()
    if horas <= 0: return 0.0
    return (total_centavos / 100) / horas

def calcular_custo_fixo_proporcional(receita_id, fator_proporcao=1.0):
    """
    Calcula o custo fixo da fração de uma receita usando o tempo produtivo.
    Mantém a precisão fracionária durante o cálculo; arredondamento fica
    restrito à apresentação ou à gravação em centavos.
    """
    receita_dados = obter_receita(receita_id)
    if not receita_dados:
        return 0.0

    receita = receita_dados["receita"]
    tempo_total_minutos = (
        float(receita["tempo_preparo_min"] or 0)
        + float(receita["tempo_batedeira_min"] or 0)
        + float(receita["tempo_forno_min"] or 0)
    )

    fator_proporcao = float(fator_proporcao)
    if fator_proporcao < 0:
        raise ValueError("A proporção da receita não pode ser negativa.")

    custo_fixo_hora = obter_custo_fixo_por_hora()
    return (tempo_total_minutos / 60.0) * custo_fixo_hora * fator_proporcao

def calcular_custo_embalagem(ingrediente_id, quantidade):
    if not ingrediente_id or float(quantidade) <= 0: return 0.0
    ingrediente = obter_ingrediente(ingrediente_id)
    if not ingrediente: raise ValueError("Embalagem ou sacola não encontrada.")
    return float(ingrediente["custo_por_unidade_base"]) * float(quantidade)

# =========================================================
# CÁLCULO COMPLETO DA PRECIFICAÇÃO
# =========================================================
def calcular_precificacao_completa(receita_id, quantidade_venda, embalagem_id=None, quantidade_embalagem=0, sacola_id=None, quantidade_sacola=0, markup=1.0):
    receita_dados = obter_receita(receita_id)
    if not receita_dados: raise ValueError("Receita não encontrada.")

    receita = receita_dados["receita"]
    if receita["tipo"] != "FINAL" and receita["tipo"] != "PRODUTO":
        raise ValueError("A precificação aceita somente produtos do tipo FINAL ou PRODUTO.")

    quantidade_venda = float(quantidade_venda)
    rendimento = float(receita["rendimento_unidades"])
    markup = float(markup)

    if quantidade_venda <= 0: raise ValueError("Informe uma quantidade de venda maior que zero.")
    if rendimento <= 0: raise ValueError("O rendimento da receita precisa ser maior que zero.")
    if markup < 0: raise ValueError("O markup não pode ser negativo.")

    custo_receita = calcular_custo_receita(receita_id)
    fracao_receita = quantidade_venda / rendimento
    custo_insumos = custo_receita["custo_total"] * fracao_receita

    tempo_preparo = float(receita["tempo_preparo_min"] or 0)
    tempo_batedeira = float(receita["tempo_batedeira_min"] or 0)
    tempo_forno = float(receita["tempo_forno_min"] or 0)

    tempo_total_minutos = tempo_preparo + tempo_batedeira + tempo_forno
    tempo_ativo_minutos = tempo_preparo + tempo_batedeira
    tempo_unidade_venda = tempo_total_minutos * fracao_receita
    custo_fixo = calcular_custo_fixo_proporcional(receita_id, fracao_receita)
    custo_mao_obra = calcular_custo_mao_obra_proporcional(receita_id, fracao_receita)
    custo_fixo_hora = obter_custo_fixo_por_hora()
    valor_hora_mao_obra = obter_valor_hora_mao_obra()

    custo_embalagem = calcular_custo_embalagem(embalagem_id, quantidade_embalagem) if embalagem_id else 0.0
    custo_sacola = calcular_custo_embalagem(sacola_id, quantidade_sacola) if sacola_id else 0.0

    custo_total = custo_insumos + custo_mao_obra + custo_fixo + custo_embalagem + custo_sacola
    impostos_pct = obter_impostos_pct()
    taxas = obter_taxas_pagamento()
    taxa_referencia = max([float(v) for v in taxas.values()] or [0.0])
    preco_sugerido = calcular_preco_sugerido(
        custo_total, markup * 100.0, impostos_pct, taxa_referencia
    )

    return {
        "nome": receita["nome"], "rendimento": rendimento, "unidade_rendimento": receita["unidade_rendimento"],
        "quantidade_venda": quantidade_venda, "custo_insumos": custo_insumos, "tempo_total_minutos": tempo_total_minutos,
        "tempo_ativo_minutos": tempo_ativo_minutos,
        "tempo_unidade_venda": tempo_unidade_venda, "custo_fixo_hora": custo_fixo_hora, "custo_fixo": custo_fixo,
        "valor_hora_mao_obra": valor_hora_mao_obra, "custo_mao_obra": custo_mao_obra,
        "custo_embalagem": custo_embalagem, "custo_sacola": custo_sacola, "custo_total": custo_total,
        "markup": markup, "preco_sugerido": preco_sugerido,
        "impostos_pct": impostos_pct, "taxa_referencia_pct": taxa_referencia,
    }

def salvar_precificacao_completa(receita_id, quantidade_venda, embalagem_id, quantidade_embalagem, sacola_id, quantidade_sacola, markup, preco_praticado_centavos=None):
    calculo = calcular_precificacao_completa(receita_id, quantidade_venda, embalagem_id, quantidade_embalagem, sacola_id, quantidade_sacola, markup)
    stamp = datetime.now().isoformat(timespec="seconds")
    con = obter_conexao()
    try:
        con.execute("""
            INSERT INTO precificacoes (
                receita_id, quantidade_embalagem, embalagem_centavos, markup, impostos, taxa_cartao, taxa_delivery,
                preco_praticado_centavos, embalagem_id, quantidade_embalagem_insumo, sacola_id, quantidade_sacola,
                ativo, criado_em, atualizado_em
            ) VALUES (?, ?, 0, ?, 0, 0, 0, ?, ?, ?, ?, ?, 1, ?, ?)
            ON CONFLICT(receita_id) DO UPDATE SET
                quantidade_embalagem=excluded.quantidade_embalagem, embalagem_centavos=0, markup=excluded.markup,
                impostos=0, taxa_cartao=0, taxa_delivery=0, preco_praticado_centavos=excluded.preco_praticado_centavos,
                embalagem_id=excluded.embalagem_id, quantidade_embalagem_insumo=excluded.quantidade_embalagem_insumo,
                sacola_id=excluded.sacola_id, quantidade_sacola=excluded.quantidade_sacola, ativo=1, atualizado_em=excluded.atualizado_em
        """, (
            receita_id, float(quantidade_venda), float(markup), preco_praticado_centavos, embalagem_id,
            float(quantidade_embalagem), sacola_id, float(quantidade_sacola), stamp, stamp,
        ))

        row = con.execute("SELECT id FROM precificacoes WHERE receita_id=?", (receita_id,)).fetchone()

        con.execute("""
            INSERT INTO historico_precificacoes (
                precificacao_id, preco_sugerido_centavos, preco_praticado_centavos, custo_total_centavos, registrado_em
            ) VALUES (?, ?, ?, ?, ?)
        """, (row["id"], round(calculo["preco_sugerido"] * 100), preco_praticado_centavos, round(calculo["custo_total"] * 100), stamp))

        con.commit()
        return row["id"]
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()



def criar_tabela_precificacao_v2():
    conexao = obter_conexao()
    try:
        conexao.execute("""
            CREATE TABLE IF NOT EXISTS precificacao_v2 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receita_id INTEGER NOT NULL,
                quantidade_embalagem REAL NOT NULL,
                custo_embalagem_centavos INTEGER NOT NULL,
                markup_ideal_pct REAL NOT NULL,
                preco_praticado_centavos INTEGER NOT NULL,
                embalagem_id INTEGER,
                quantidade_embalagem_insumo REAL NOT NULL DEFAULT 0,
                sacola_id INTEGER,
                quantidade_sacola REAL NOT NULL DEFAULT 0,
                FOREIGN KEY (receita_id) REFERENCES receitas(id),
                FOREIGN KEY (embalagem_id) REFERENCES ingredientes(id),
                FOREIGN KEY (sacola_id) REFERENCES ingredientes(id)
            )
        """)

        colunas_precificacao = {
            coluna["name"] for coluna in conexao.execute("PRAGMA table_info(precificacao_v2)").fetchall()
        }
        novas_colunas_precificacao = {
            "embalagem_id": "INTEGER",
            "quantidade_embalagem_insumo": "REAL NOT NULL DEFAULT 0",
            "sacola_id": "INTEGER",
            "quantidade_sacola": "REAL NOT NULL DEFAULT 0",
        }
        for nome_coluna, tipo_coluna in novas_colunas_precificacao.items():
            if nome_coluna not in colunas_precificacao:
                conexao.execute(f"ALTER TABLE precificacao_v2 ADD COLUMN {nome_coluna} {tipo_coluna}")

        # Histórico exclusivo da precificação atual
        conexao.execute("""
            CREATE TABLE IF NOT EXISTS historico_precificacao_v2 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                precificacao_id INTEGER NOT NULL,
                receita_id INTEGER NOT NULL,
                nome_receita TEXT NOT NULL,
                quantidade_embalagem REAL NOT NULL,
                custo_embalagem_centavos INTEGER NOT NULL,
                taxa_cartao_pct REAL NOT NULL,
                markup_ideal_pct REAL NOT NULL,
                custo_insumo_centavos INTEGER NOT NULL,
                custo_fixo_centavos INTEGER NOT NULL,
                custo_total_centavos INTEGER NOT NULL,
                preco_sugerido_centavos INTEGER NOT NULL,
                preco_praticado_centavos INTEGER NOT NULL,
                markup_aplicado_pct REAL NOT NULL,
                margem_contribuicao_centavos INTEGER NOT NULL,
                status TEXT NOT NULL,
                registrado_em TEXT NOT NULL,
                FOREIGN KEY (precificacao_id)
                    REFERENCES precificacao_v2(id) ON DELETE CASCADE,
                FOREIGN KEY (receita_id)
                    REFERENCES receitas(id)
            )
        """)

        conexao.execute("""
            CREATE INDEX IF NOT EXISTS idx_historico_precificacao_v2
            ON historico_precificacao_v2(precificacao_id)
        """)

        colunas_historico = {
            coluna["name"] for coluna in conexao.execute("PRAGMA table_info(historico_precificacao_v2)").fetchall()
        }
        if "custo_mao_obra_centavos" not in colunas_historico:
            conexao.execute("ALTER TABLE historico_precificacao_v2 ADD COLUMN custo_mao_obra_centavos INTEGER NOT NULL DEFAULT 0")
        if "impostos_pct" not in colunas_historico:
            conexao.execute("ALTER TABLE historico_precificacao_v2 ADD COLUMN impostos_pct REAL NOT NULL DEFAULT 0")

        conexao.commit()

    finally:
        conexao.close()

def listar_relatorio_precificacao_v2():
    """
    Retorna uma linha por precificação ativa, acompanhada do histórico mais
    recente salvo para ela.

    Os valores financeiros vêm do histórico, e não são recalculados com os
    custos atuais. Precificações sem histórico também são retornadas, com os
    campos do histórico definidos como None.
    """
    conexao = obter_conexao()
    try:
        return conexao.execute("""
            SELECT
                p.id AS precificacao_id,
                p.receita_id,
                r.nome AS nome_receita_atual,
                r.rendimento_unidades,
                r.unidade_rendimento,
                h.id AS historico_id,
                h.nome_receita,
                h.quantidade_embalagem,
                h.custo_embalagem_centavos,
                h.taxa_cartao_pct,
                h.markup_ideal_pct,
                h.custo_insumo_centavos,
                h.custo_fixo_centavos,
                h.custo_mao_obra_centavos,
                h.impostos_pct,
                h.custo_total_centavos,
                h.preco_sugerido_centavos,
                h.preco_praticado_centavos,
                h.markup_aplicado_pct,
                h.margem_contribuicao_centavos,
                h.status,
                h.registrado_em
            FROM precificacao_v2 p
            INNER JOIN receitas r ON r.id = p.receita_id
            LEFT JOIN historico_precificacao_v2 h
                ON h.id = (
                    SELECT h2.id
                    FROM historico_precificacao_v2 h2
                    WHERE h2.precificacao_id = p.id
                    ORDER BY h2.registrado_em DESC, h2.id DESC
                    LIMIT 1
                )
            WHERE r.ativo = 1
            ORDER BY r.nome COLLATE NOCASE, p.id
        """).fetchall()
    finally:
        conexao.close()


def listar_precificacoes():
    conexao = obter_conexao()
    try:
        return conexao.execute('''
            SELECT p.*, r.nome as nome_receita, r.rendimento_unidades, r.unidade_rendimento
            FROM precificacao_v2 p
            JOIN receitas r ON p.receita_id = r.id
            WHERE r.ativo = 1
            ORDER BY r.nome
        ''').fetchall()
    finally:
        conexao.close()

def obter_precificacao_v2(precificacao_id):
    conexao = obter_conexao()
    try:
        return conexao.execute('SELECT * FROM precificacao_v2 WHERE id = ?', (precificacao_id,)).fetchone()
    finally:
        conexao.close()


def salvar_precificacao_v2(
    id,
    receita_id,
    quantidade_embalagem,
    custo_embalagem_centavos,
    markup_ideal_pct,
    preco_praticado_centavos,
    margem_minima_pct=None,
    taxa_cartao_pct=None,
    embalagem_id=None,
    quantidade_embalagem_insumo=0,
    sacola_id=None,
    quantidade_sacola=0
):
    conexao = obter_conexao()

    try:
        taxa_cartao = (
            obter_taxa_cartao()
            if taxa_cartao_pct is None
            else float(taxa_cartao_pct)
        )
        if taxa_cartao < 0 or taxa_cartao >= 100:
            raise ValueError("A taxa de pagamento deve estar entre 0% e 99,99%.")
        if margem_minima_pct is None:
            margem_minima_pct = obter_margem_minima()
        margem_minima_pct = float(margem_minima_pct)
        if margem_minima_pct < 0 or margem_minima_pct >= 100:
            raise ValueError("A margem mínima deve estar entre 0% e 99,99%.")

        if id:
            conexao.execute("""
                UPDATE precificacao_v2
                SET receita_id = ?,
                    quantidade_embalagem = ?,
                    custo_embalagem_centavos = ?,
                    markup_ideal_pct = ?,
                    preco_praticado_centavos = ?,
                    embalagem_id = ?,
                    quantidade_embalagem_insumo = ?,
                    sacola_id = ?,
                    quantidade_sacola = ?
                WHERE id = ?
            """, (
                receita_id, quantidade_embalagem, custo_embalagem_centavos,
                markup_ideal_pct, preco_praticado_centavos,
                embalagem_id, quantidade_embalagem_insumo, sacola_id, quantidade_sacola, id
            ))

            precificacao_id = id

        else:
            cursor = conexao.execute("""
                INSERT INTO precificacao_v2 (
                    receita_id,
                    quantidade_embalagem,
                    custo_embalagem_centavos,
                    markup_ideal_pct,
                    preco_praticado_centavos,
                    embalagem_id,
                    quantidade_embalagem_insumo,
                    sacola_id,
                    quantidade_sacola
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                receita_id, quantidade_embalagem, custo_embalagem_centavos,
                markup_ideal_pct, preco_praticado_centavos,
                embalagem_id, quantidade_embalagem_insumo, sacola_id, quantidade_sacola
            ))

            precificacao_id = cursor.lastrowid

        receita = conexao.execute("""
            SELECT nome
            FROM receitas
            WHERE id = ?
        """, (receita_id,)).fetchone()

        if not receita:
            raise ValueError("Produto não encontrado.")

        resultado = calcular_simulacao_precificacao(
            receita_id,
            quantidade_embalagem,
            custo_embalagem_centavos,
            markup_ideal_pct,
            preco_praticado_centavos,
            taxa_cartao,
            margem_minima_pct,
            embalagem_id,
            quantidade_embalagem_insumo,
            sacola_id,
            quantidade_sacola
        )

        if not resultado:
            raise ValueError("Não foi possível calcular a precificação.")
        # Preços abaixo da margem mínima também são registrados para permitir
        # acompanhar o preço realmente praticado. O status fica no histórico.
        conexao.execute(
            """INSERT INTO configuracoes (chave, valor)
               VALUES ('margem_minima_pct', ?)
               ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor""",
            (str(margem_minima_pct),)
        )

        registrado_em = datetime.now().isoformat(timespec="seconds")

        conexao.execute("""
            INSERT INTO historico_precificacao_v2 (
                precificacao_id,
                receita_id,
                nome_receita,
                quantidade_embalagem,
                custo_embalagem_centavos,
                taxa_cartao_pct,
                markup_ideal_pct,
                custo_insumo_centavos,
                custo_fixo_centavos,
                custo_mao_obra_centavos,
                impostos_pct,
                custo_total_centavos,
                preco_sugerido_centavos,
                preco_praticado_centavos,
                markup_aplicado_pct,
                margem_contribuicao_centavos,
                status,
                registrado_em
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            precificacao_id,
            receita_id,
            receita["nome"],
            quantidade_embalagem,
            custo_embalagem_centavos,
            taxa_cartao,
            markup_ideal_pct,
            round(resultado["custo_insumo"] * 100),
            round(resultado["custo_fixo"] * 100),
            round(resultado["custo_mao_obra"] * 100),
            resultado["impostos_pct"],
            round(resultado["custo_total"] * 100),
            round(resultado["preco_sugerido"] * 100),
            preco_praticado_centavos,
            resultado["markup_aplicado_pct"],
            round(resultado["margem_contribuicao"] * 100),
            resultado["status"],
            registrado_em
        ))

        conexao.commit()
        return precificacao_id

    except Exception:
        conexao.rollback()
        raise

    finally:
        conexao.close()

def excluir_precificacao_v2(id):
    conexao = obter_conexao()
    try:
        conexao.execute('DELETE FROM precificacao_v2 WHERE id = ?', (id,))
        conexao.commit()
    finally:
        conexao.close()

def obter_taxas_pagamento():
    """Retorna as taxas globais configuradas para cada forma de pagamento."""
    conexao = obter_conexao()
    try:
        valores = {
            row["chave"]: float(row["valor"])
            for row in conexao.execute(
                """SELECT chave, valor FROM configuracoes
                   WHERE chave IN (
                       'taxa_pix', 'taxa_dinheiro', 'taxa_debito',
                       'taxa_credito_avista', 'taxa_credito_parcelado',
                       'taxa_cartao'
                   )"""
            ).fetchall()
        }
        return {
            "pix": valores.get("taxa_pix", 0.0),
            "dinheiro": valores.get("taxa_dinheiro", 0.0),
            "debito": valores.get("taxa_debito", 0.0),
            "credito_avista": valores.get("taxa_credito_avista", valores.get("taxa_cartao", 0.0)),
            "credito_parcelado": valores.get("taxa_credito_parcelado", 0.0),
        }
    finally:
        conexao.close()


def salvar_taxas_pagamento(taxas):
    """Valida e grava todas as taxas globais em uma única transação."""
    chaves = {
        "pix": "taxa_pix",
        "dinheiro": "taxa_dinheiro",
        "debito": "taxa_debito",
        "credito_avista": "taxa_credito_avista",
        "credito_parcelado": "taxa_credito_parcelado",
    }
    valores = {}
    for campo, chave in chaves.items():
        try:
            valor = float(taxas.get(campo, 0))
        except (TypeError, ValueError) as erro:
            raise ValueError("Cada taxa deve ser numérica.") from erro
        if not math.isfinite(valor) or valor < 0 or valor >= 100:
            raise ValueError("Cada taxa deve ser finita e estar entre 0% e 99,99%.")
        valores[chave] = str(valor)

    conexao = obter_conexao()
    try:
        for chave, valor in valores.items():
            conexao.execute(
                """INSERT INTO configuracoes (chave, valor)
                   VALUES (?, ?)
                   ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor""",
                (chave, valor)
            )
        # Mantém compatibilidade com telas e registros antigos.
        conexao.execute(
            """INSERT INTO configuracoes (chave, valor)
               VALUES ('taxa_cartao', ?)
               ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor""",
            (valores["taxa_credito_avista"],)
        )
        conexao.commit()
    finally:
        conexao.close()


def obter_taxa_cartao():
    """Compatibilidade: taxa antiga equivale ao crédito à vista."""
    return obter_taxas_pagamento()["credito_avista"]


def obter_impostos_pct():
    conexao = obter_conexao()
    try:
        row = conexao.execute(
            "SELECT valor FROM configuracoes WHERE chave = 'impostos_pct'"
        ).fetchone()
        return float(row["valor"]) if row else 0.0
    finally:
        conexao.close()


def salvar_impostos_pct(valor):
    try:
        valor = float(valor)
    except (TypeError, ValueError) as erro:
        raise ValueError("Os impostos devem ser numéricos.") from erro
    if not math.isfinite(valor) or valor < 0 or valor >= 100:
        raise ValueError("Os impostos devem ser finitos e estar entre 0% e 99,99%.")
    conexao = obter_conexao()
    try:
        conexao.execute(
            """INSERT INTO configuracoes(chave, valor) VALUES ('impostos_pct', ?)
               ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor""",
            (str(valor),)
        )
        conexao.commit()
    finally:
        conexao.close()


def obter_markup_ideal():
    """Retorna o markup ideal global; usa 100% como padrão inicial."""
    conexao = obter_conexao()
    try:
        row = conexao.execute(
            "SELECT valor FROM configuracoes WHERE chave = 'markup_ideal_pct'"
        ).fetchone()
        return float(row["valor"]) if row else 100.0
    finally:
        conexao.close()


def salvar_markup_ideal(valor):
    try:
        valor = float(valor)
    except (TypeError, ValueError) as erro:
        raise ValueError("O markup ideal deve ser numérico.") from erro
    if not math.isfinite(valor) or valor < 0 or valor >= 10000:
        raise ValueError("O markup ideal deve ser finito e estar entre 0% e 9999,99%.")
    conexao = obter_conexao()
    try:
        conexao.execute(
            """INSERT INTO configuracoes (chave, valor)
               VALUES ('markup_ideal_pct', ?)
               ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor""",
            (str(valor),)
        )
        conexao.commit()
    finally:
        conexao.close()


def obter_margem_minima():
    """Retorna a margem mínima global; usa 20% como padrão inicial."""
    conexao = obter_conexao()
    try:
        row = conexao.execute(
            "SELECT valor FROM configuracoes WHERE chave = 'margem_minima_pct'"
        ).fetchone()
        return float(row['valor']) if row else 20.0
    finally:
        conexao.close()


def salvar_margem_minima(valor):
    try:
        valor = float(valor)
    except (TypeError, ValueError) as erro:
        raise ValueError("A margem mínima deve ser numérica.") from erro
    if not math.isfinite(valor) or valor < 0 or valor >= 100:
        raise ValueError("A margem mínima deve ser finita e estar entre 0% e 99,99%.")

    conexao = obter_conexao()
    try:
        conexao.execute(
            """INSERT INTO configuracoes (chave, valor)
               VALUES ('margem_minima_pct', ?)
               ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor""",
            (str(valor),)
        )
        conexao.commit()
    finally:
        conexao.close()


def calcular_simulacao_precificacao(receita_id, quantidade_embalagem, custo_embalagem_centavos, markup_ideal_pct, preco_praticado_centavos, taxa_cartao_pct, margem_minima_pct=None, embalagem_id=None, quantidade_embalagem_insumo=0, sacola_id=None, quantidade_sacola=0):
    # 1. Custo Base Insumos
    custo_base = calcular_custo_receita(receita_id)
    if not custo_base:
        return None
        
    conexao = obter_conexao()
    try:
        receita = conexao.execute('SELECT * FROM receitas WHERE id = ?', (receita_id,)).fetchone()
    finally:
        conexao.close()
        
    rendimento_receita = receita['rendimento_unidades'] or 1.0
    
    # Custo insumo proporcional à quantidade na embalagem
    fator_proporcao = quantidade_embalagem / rendimento_receita
    custo_insumo = custo_base['custo_insumos'] * fator_proporcao
    
    # Mão de obra direta: preparo + batedeira; exclui o tempo passivo de forno.
    custo_mao_obra = calcular_custo_mao_obra_proporcional(receita_id, fator_proporcao)
    # Despesas fixas: tempo de ocupação, incluindo o forno.
    custo_fixo = calcular_custo_fixo_proporcional(receita_id, fator_proporcao)
    custo_embalagem_manual = custo_embalagem_centavos / 100.0
    custo_embalagem_insumo = calcular_custo_embalagem(embalagem_id, quantidade_embalagem_insumo) if embalagem_id else 0.0
    custo_sacola = calcular_custo_embalagem(sacola_id, quantidade_sacola) if sacola_id else 0.0
    custo_embalagem = custo_embalagem_manual + custo_embalagem_insumo + custo_sacola
    custo_total = custo_insumo + custo_mao_obra + custo_fixo + custo_embalagem
    
    # Preço sugerido cobre o markup e os percentuais incidentes sobre a venda.
    impostos_pct = obter_impostos_pct()
    percentual_total_venda = float(taxa_cartao_pct) + impostos_pct
    if percentual_total_venda < 0 or percentual_total_venda >= 100:
        raise ValueError("A soma de impostos e taxas deve ser inferior a 100%.")
    preco_sugerido = calcular_preco_sugerido(
        custo_total, markup_ideal_pct, impostos_pct, taxa_cartao_pct
    )
    
    # 6. Analise do Preço Praticado
    preco_praticado = preco_praticado_centavos / 100.0
    
    custos_variaveis = custo_insumo + custo_mao_obra + custo_embalagem
    indicadores = calcular_indicadores_preco_praticado(
        preco_praticado,
        custo_total,
        custos_variaveis,
        impostos_pct,
        taxa_cartao_pct,
    )
    markup_aplicado_pct = indicadores["markup_aplicado_pct"]
    imposto_cartao = indicadores["imposto_cartao"]
    imposto_venda = indicadores["imposto_venda"]
    margem_contribuicao = indicadores["margem_contribuicao"]
    resultado_apos_rateio = indicadores["resultado_apos_rateio"]

    if margem_minima_pct is None:
        margem_minima_pct = obter_margem_minima()
    margem_real_pct = indicadores["margem_real_pct"]
    status = "Dentro da Margem" if margem_real_pct >= margem_minima_pct else "Abaixo da Margem Mínima"
    
    return {
        "custo_insumo": custo_insumo,
        "custo_mao_obra": custo_mao_obra,
        "custo_fixo": custo_fixo,
        "custo_embalagem": custo_embalagem,
        "custo_embalagem_manual": custo_embalagem_manual,
        "custo_embalagem_insumo": custo_embalagem_insumo,
        "custo_sacola": custo_sacola,
        "impostos_pct": impostos_pct,
        "valor_impostos": imposto_venda,
        "custo_total": custo_total,
        "preco_sugerido": preco_sugerido,
        "preco_praticado": preco_praticado,
        "markup_aplicado_pct": markup_aplicado_pct,
        "margem_contribuicao": margem_contribuicao,
        "resultado_apos_rateio": resultado_apos_rateio,
        "margem_real_pct": margem_real_pct,
        "margem_minima_pct": margem_minima_pct,
        "status": status
    }


def listar_historico_precificacao_v2(precificacao_id):
    conexao = obter_conexao()

    try:
        return conexao.execute("""
            SELECT *
            FROM historico_precificacao_v2
            WHERE precificacao_id = ?
            ORDER BY registrado_em DESC, id DESC
        """, (precificacao_id,)).fetchall()

    finally:
        conexao.close()



# =========================================================
# ORÇAMENTOS
# =========================================================
def criar_tabelas_orcamentos():
    """Cria as tabelas de orçamento sem alterar dados existentes."""
    conexao = obter_conexao()
    try:
        conexao.executescript("""
            CREATE TABLE IF NOT EXISTS orcamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero TEXT NOT NULL UNIQUE,
                cliente TEXT,
                status TEXT NOT NULL DEFAULT 'Em elaboração',
                validade TEXT,
                data_entrega TEXT,
                desconto_tipo TEXT NOT NULL DEFAULT 'nenhum',
                desconto_valor REAL NOT NULL DEFAULT 0,
                modalidade TEXT NOT NULL DEFAULT 'pix',
                total_referencia_centavos INTEGER NOT NULL DEFAULT 0,
                total_final_centavos INTEGER NOT NULL DEFAULT 0,
                itens_json TEXT NOT NULL,
                resumo_json TEXT NOT NULL,
                mensagem TEXT NOT NULL,
                criado_em TEXT NOT NULL,
                atualizado_em TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS orcamento_itens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                orcamento_id INTEGER NOT NULL,
                receita_id INTEGER,
                nome_produto TEXT NOT NULL,
                quantidade REAL NOT NULL,
                unidade TEXT NOT NULL,
                custo_unitario_centavos INTEGER NOT NULL,
                preco_base_centavos INTEGER NOT NULL,
                preco_final_unitario_centavos INTEGER NOT NULL,
                subtotal_centavos INTEGER NOT NULL,
                snapshot_json TEXT NOT NULL,
                FOREIGN KEY (orcamento_id) REFERENCES orcamentos(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_orcamentos_criado
            ON orcamentos(criado_em DESC);

            CREATE TABLE IF NOT EXISTS orcamento_historico (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                orcamento_id INTEGER NOT NULL,
                numero TEXT NOT NULL,
                snapshot_json TEXT NOT NULL,
                registrado_em TEXT NOT NULL,
                FOREIGN KEY (orcamento_id) REFERENCES orcamentos(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_orcamento_historico
            ON orcamento_historico(orcamento_id, registrado_em DESC);
        """)
        colunas_orcamentos = {
            coluna["name"]
            for coluna in conexao.execute("PRAGMA table_info(orcamentos)").fetchall()
        }
        if "data_entrega" not in colunas_orcamentos:
            conexao.execute("ALTER TABLE orcamentos ADD COLUMN data_entrega TEXT")
        if "status_producao" not in colunas_orcamentos:
            conexao.execute(
                "ALTER TABLE orcamentos ADD COLUMN status_producao TEXT NOT NULL DEFAULT 'Pendente'"
            )

        conexao.commit()
    finally:
        conexao.close()


def _validar_dados_orcamento(dados):
    """Valida os dados do orçamento antes de iniciar qualquer gravação."""
    if not isinstance(dados, dict):
        raise ValueError("Os dados do orçamento são inválidos.")

    numero = str(dados.get("numero", "")).strip()
    if not numero:
        raise ValueError("O número do orçamento é obrigatório.")

    tipo_desconto = dados.get("desconto_tipo", "nenhum")
    if tipo_desconto not in {"nenhum", "percentual", "valor"}:
        raise ValueError("Tipo de desconto inválido.")

    try:
        desconto = float(dados.get("desconto_valor", 0))
        total_referencia = int(dados["total_referencia_centavos"])
        total_final = int(dados["total_final_centavos"])
    except (KeyError, TypeError, ValueError, OverflowError):
        raise ValueError("Valores financeiros do orçamento inválidos.")

    if not math.isfinite(desconto) or desconto < 0:
        raise ValueError("O desconto deve ser um valor finito e não negativo.")
    if tipo_desconto == "percentual" and desconto >= 100:
        raise ValueError("O desconto percentual deve ser menor que 100%.")
    if total_referencia < 0 or total_final < 0:
        raise ValueError("Os totais do orçamento não podem ser negativos.")
    if tipo_desconto == "valor" and desconto * 100 > total_referencia:
        raise ValueError("O desconto não pode superar o valor dos produtos.")

    itens = dados.get("itens")
    if not isinstance(itens, (list, tuple)) or not itens:
        raise ValueError("O orçamento deve possuir pelo menos um produto.")

    for indice, item in enumerate(itens, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Produto {indice}: dados inválidos.")
        if not str(item.get("nome", "")).strip():
            raise ValueError(f"Produto {indice}: nome obrigatório.")
        if not str(item.get("unidade", "")).strip():
            raise ValueError(f"Produto {indice}: unidade obrigatória.")
        try:
            quantidade = float(item["quantidade"])
            valores_centavos = [
                int(item[chave]) for chave in (
                    "custo_unitario_centavos",
                    "preco_base_centavos",
                    "preco_final_unitario_centavos",
                    "subtotal_centavos",
                )
            ]
        except (KeyError, TypeError, ValueError, OverflowError):
            raise ValueError(f"Produto {indice}: quantidade ou valores inválidos.")
        if not math.isfinite(quantidade) or quantidade <= 0:
            raise ValueError(f"Produto {indice}: quantidade deve ser finita e maior que zero.")
        if any(valor < 0 for valor in valores_centavos):
            raise ValueError(f"Produto {indice}: valores não podem ser negativos.")
        if not isinstance(item.get("snapshot_json"), str):
            raise ValueError(f"Produto {indice}: fotografia dos dados inválida.")

    for chave in ("itens_json", "resumo_json", "mensagem"):
        if not isinstance(dados.get(chave), str):
            raise ValueError(f"Campo obrigatório inválido: {chave}.")


def salvar_orcamento(dados):
    """Salva o orçamento e seus itens como fotografia dos valores da data."""
    _validar_dados_orcamento(dados)
    agora = datetime.now().isoformat(timespec="seconds")
    conexao = obter_conexao()
    try:
        cursor = conexao.execute("""
            INSERT INTO orcamentos (
                numero, cliente, status, validade, data_entrega, desconto_tipo, desconto_valor,
                modalidade, total_referencia_centavos, total_final_centavos,
                itens_json, resumo_json, mensagem, criado_em, atualizado_em
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            dados["numero"], dados.get("cliente", ""), dados.get("status", "Em elaboração"),
            dados.get("validade", ""), dados.get("data_entrega") or None,
            dados.get("desconto_tipo", "nenhum"),
            float(dados.get("desconto_valor", 0)), dados.get("modalidade", "pix"),
            int(dados["total_referencia_centavos"]), int(dados["total_final_centavos"]),
            dados["itens_json"], dados["resumo_json"], dados["mensagem"], agora, agora
        ))
        orcamento_id = cursor.lastrowid

        for item in dados["itens"]:
            conexao.execute("""
                INSERT INTO orcamento_itens (
                    orcamento_id, receita_id, nome_produto, quantidade, unidade,
                    custo_unitario_centavos, preco_base_centavos,
                    preco_final_unitario_centavos, subtotal_centavos, snapshot_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                orcamento_id, item.get("receita_id"), item["nome"], float(item["quantidade"]),
                item["unidade"], int(item["custo_unitario_centavos"]),
                int(item["preco_base_centavos"]), int(item["preco_final_unitario_centavos"]),
                int(item["subtotal_centavos"]), item["snapshot_json"]
            ))
        conexao.commit()
        return orcamento_id
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()



def atualizar_orcamento(orcamento_id, dados):
    """Atualiza orçamento e itens em uma única transação."""
    _validar_dados_orcamento(dados)
    agora = datetime.now().isoformat(timespec="seconds")
    conexao = obter_conexao()
    try:
        if not conexao.execute("SELECT id FROM orcamentos WHERE id = ?", (orcamento_id,)).fetchone():
            raise ValueError("Orçamento não encontrado para edição.")
        atual = conexao.execute("SELECT * FROM orcamentos WHERE id = ?", (orcamento_id,)).fetchone()
        conexao.execute("""
            INSERT INTO orcamento_historico (orcamento_id, numero, snapshot_json, registrado_em)
            VALUES (?, ?, ?, ?)
        """, (
            orcamento_id, atual["numero"],
            json.dumps(dict(atual), ensure_ascii=False),
            agora
        ))
        conexao.execute("""
            UPDATE orcamentos
            SET cliente=?, validade=?, data_entrega=?, desconto_tipo=?, desconto_valor=?, modalidade=?,
                total_referencia_centavos=?, total_final_centavos=?, itens_json=?,
                resumo_json=?, mensagem=?, atualizado_em=?
            WHERE id=?
        """, (
            dados.get("cliente",""), dados.get("validade",""), dados.get("data_entrega") or None,
            dados.get("desconto_tipo","nenhum"),
            float(dados.get("desconto_valor",0)), dados.get("modalidade","pix"),
            int(dados["total_referencia_centavos"]), int(dados["total_final_centavos"]),
            dados["itens_json"], dados["resumo_json"], dados["mensagem"], agora, orcamento_id
        ))
        conexao.execute("DELETE FROM orcamento_itens WHERE orcamento_id=?", (orcamento_id,))
        for item in dados["itens"]:
            conexao.execute("""
                INSERT INTO orcamento_itens (
                    orcamento_id, receita_id, nome_produto, quantidade, unidade,
                    custo_unitario_centavos, preco_base_centavos, preco_final_unitario_centavos,
                    subtotal_centavos, snapshot_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                orcamento_id, item.get("receita_id"), item["nome"], float(item["quantidade"]),
                item["unidade"], int(item["custo_unitario_centavos"]), int(item["preco_base_centavos"]),
                int(item["preco_final_unitario_centavos"]), int(item["subtotal_centavos"]), item["snapshot_json"]
            ))
        conexao.commit()
        return orcamento_id
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()


def listar_versoes_orcamento(orcamento_id):
    conexao = obter_conexao()
    try:
        return conexao.execute("""
            SELECT id, numero, snapshot_json, registrado_em
            FROM orcamento_historico
            WHERE orcamento_id = ?
            ORDER BY id DESC
        """, (orcamento_id,)).fetchall()
    finally:
        conexao.close()


def listar_orcamentos():
    conexao = obter_conexao()
    try:
        return conexao.execute("""
            SELECT id, numero, cliente, status, validade, data_entrega,
                   total_final_centavos, criado_em, atualizado_em
            FROM orcamentos
            ORDER BY id DESC
        """).fetchall()
    finally:
        conexao.close()


def obter_orcamento(orcamento_id):
    conexao = obter_conexao()
    try:
        return conexao.execute(
            "SELECT * FROM orcamentos WHERE id = ?", (orcamento_id,)
        ).fetchone()
    finally:
        conexao.close()


def listar_agenda_producao():
    """Lista encomendas aprovadas com data de entrega para a agenda de produção."""
    conexao = obter_conexao()
    try:
        return conexao.execute("""
            SELECT id, numero, cliente, data_entrega, status_producao,
                   total_final_centavos, itens_json, resumo_json, mensagem
            FROM orcamentos
            WHERE status = 'Aprovado'
              AND data_entrega IS NOT NULL
              AND TRIM(data_entrega) <> ''
            ORDER BY data_entrega ASC, id ASC
        """).fetchall()
    finally:
        conexao.close()


def atualizar_status_producao(orcamento_id, status):
    permitidos = {"Pendente", "Em produção", "Concluída"}
    if status not in permitidos:
        raise ValueError("Status de produção inválido.")
    conexao = obter_conexao()
    try:
        conexao.execute("""
            UPDATE orcamentos
            SET status_producao = ?, atualizado_em = ?
            WHERE id = ? AND status = 'Aprovado'
        """, (status, datetime.now().isoformat(timespec="seconds"), orcamento_id))
        if conexao.total_changes == 0:
            raise ValueError("Orçamento aprovado não encontrado.")
        conexao.commit()
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()


def atualizar_status_orcamento(orcamento_id, status):
    permitidos = {"Em elaboração", "Enviado", "Aprovado", "Recusado"}
    if status not in permitidos:
        raise ValueError("Status de orçamento inválido.")
    conexao = obter_conexao()
    try:
        atual = conexao.execute(
            "SELECT * FROM orcamentos WHERE id = ?", (orcamento_id,)
        ).fetchone()
        if not atual:
            raise ValueError("Orçamento não encontrado para atualização de status.")

        if atual["status"] != status:
            agora = datetime.now().isoformat(timespec="seconds")
            snapshot = dict(atual)
            snapshot["_evento"] = "alteracao_status"
            snapshot["_status_anterior"] = atual["status"]
            snapshot["_status_novo"] = status
            conexao.execute("""
                INSERT INTO orcamento_historico (
                    orcamento_id, numero, snapshot_json, registrado_em
                ) VALUES (?, ?, ?, ?)
            """, (
                orcamento_id, atual["numero"],
                json.dumps(snapshot, ensure_ascii=False), agora
            ))
            conexao.execute("""
                UPDATE orcamentos
                SET status = ?, atualizado_em = ?
                WHERE id = ?
            """, (status, agora, orcamento_id))
        conexao.commit()
        return True
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()



def excluir_orcamentos(orcamento_ids):
    """Exclui um ou vários orçamentos e seus itens/históricos relacionados."""
    ids = list(dict.fromkeys(int(valor) for valor in orcamento_ids))
    if not ids:
        return 0

    conexao = obter_conexao()
    try:
        placeholders = ",".join("?" for _ in ids)
        conexao.execute("BEGIN")
        conexao.execute(
            f"DELETE FROM orcamentos WHERE id IN ({placeholders})",
            ids,
        )
        excluidos = conexao.execute("SELECT changes()").fetchone()[0]
        conexao.commit()
        return excluidos
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()


def obter_dados_painel():
    """Retorna indicadores e listas reais para a tela inicial, sem alterar registros."""
    conexao = obter_conexao()
    try:
        contagens = {
            row["status"]: row["quantidade"]
            for row in conexao.execute("""
                SELECT status, COUNT(*) AS quantidade
                FROM orcamentos
                GROUP BY status
            """).fetchall()
        }

        hoje = date.today()
        limite = hoje + timedelta(days=7)
        quantidade_entregas = conexao.execute("""
            SELECT COUNT(*)
            FROM orcamentos
            WHERE status = 'Aprovado'
              AND data_entrega IS NOT NULL
              AND TRIM(data_entrega) <> ''
              AND data_entrega >= ?
              AND data_entrega <= ?
        """, (hoje.isoformat(), limite.isoformat())).fetchone()[0]

        entregas = conexao.execute("""
            SELECT id, numero, cliente, status, data_entrega, total_final_centavos
            FROM orcamentos
            WHERE status = 'Aprovado'
              AND data_entrega IS NOT NULL
              AND TRIM(data_entrega) <> ''
              AND data_entrega >= ?
              AND data_entrega <= ?
            ORDER BY data_entrega ASC, id ASC
            LIMIT 6
        """, (hoje.isoformat(), limite.isoformat())).fetchall()

        atividades = conexao.execute("""
            SELECT tipo, descricao, detalhe, data
            FROM (
                SELECT
                    'Orçamento' AS tipo,
                    COALESCE(NULLIF(cliente, ''), numero) AS descricao,
                    status AS detalhe,
                    atualizado_em AS data
                FROM orcamentos

                UNION ALL

                SELECT
                    'Insumo' AS tipo,
                    nome AS descricao,
                    'Preço registrado' AS detalhe,
                    registrado_em AS data
                FROM historico_precos_ingredientes

                UNION ALL

                SELECT
                    'Precificação' AS tipo,
                    nome_receita AS descricao,
                    'Preço calculado' AS detalhe,
                    registrado_em AS data
                FROM historico_precificacao_v2
            )
            WHERE data IS NOT NULL AND TRIM(data) <> ''
            ORDER BY data DESC
            LIMIT 6
        """).fetchall()

        return {
            "aguardando_retorno": contagens.get("Enviado", 0),
            "aprovados": contagens.get("Aprovado", 0),
            "em_elaboracao": contagens.get("Em elaboração", 0),
            "recusados": contagens.get("Recusado", 0),
            "entregas_proximos_7_dias": quantidade_entregas,
            "entregas": entregas,
            "atividades": atividades,
        }
    finally:
        conexao.close()
