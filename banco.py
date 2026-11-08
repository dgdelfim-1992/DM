import sqlite3
import json
from pathlib import Path
from datetime import datetime, date, timedelta

PASTA_PROJETO = Path(__file__).resolve().parent.parent
CAMINHO_BANCO = PASTA_PROJETO / "database" / "dm_gulositos.db"

# =========================================================
# CONEXÃO COM O BANCO
# =========================================================
def obter_conexao():
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
    unidade = unidade.strip().lower()
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
    if quantidade <= 0:
        raise ValueError("A quantidade precisa ser maior que zero.")
    fator, unidade_base = conversoes[unidade]
    return quantidade * fator, unidade_base

def calcular_custo_unitario(preco_pago_centavos, quantidade_base):
    if preco_pago_centavos < 0 or quantidade_base <= 0:
        raise ValueError("Valores inválidos para cálculo.")
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
def cadastrar_custo_fixo(descricao, valor_centavos):
    conexao = obter_conexao()
    try:
        conexao.execute("""
            INSERT INTO custos_fixos (descricao, valor_centavos) VALUES (?, ?)
        """, (descricao.strip(), valor_centavos))
        conexao.commit()
    finally:
        conexao.close()

def atualizar_custo_fixo(custo_id, descricao, valor_centavos):
    conexao = obter_conexao()
    try:
        conexao.execute("""
            UPDATE custos_fixos SET descricao = ?, valor_centavos = ? WHERE id = ?
        """, (descricao.strip(), valor_centavos, custo_id))
        conexao.commit()
    finally:
        conexao.close()

def excluir_custo_fixo(custo_id):
    conexao = obter_conexao()
    try:
        conexao.execute("DELETE FROM custos_fixos WHERE id = ?", (custo_id,))
        conexao.commit()
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

# =========================================================
# RECEITAS E SUB-RECEITAS
# =========================================================
def cadastrar_receita(nome, tipo, rendimento_unidades, custo_embalagem_centavos, margem_lucro_pct, taxa_cartao_pct, lista_itens, tempo_preparo_min=0, tempo_batedeira_min=0, tempo_forno_min=0, unidade_rendimento="un"):
    nome = (nome or "").strip()
    unidade_rendimento = (unidade_rendimento or "un").strip().lower()

    if not nome: raise ValueError("Informe o nome da receita.")
    if rendimento_unidades <= 0: raise ValueError("O rendimento precisa ser maior que zero.")
    if unidade_rendimento not in ("un", "g"): raise ValueError("A unidade de rendimento deve ser un ou g.")
    tempos = [tempo_preparo_min, tempo_batedeira_min, tempo_forno_min]
    if any(tempo < 0 for tempo in tempos): raise ValueError("Os tempos não podem ser negativos.")

    agora_iso = datetime.now().isoformat(timespec="seconds")
    conexao = obter_conexao()

    try:
        cursor = conexao.execute("""
            INSERT INTO receitas (
                nome, tipo, rendimento_unidades, custo_embalagem_centavos, margem_lucro_pct, taxa_cartao_pct,
                ativo, criado_em, atualizado_em, tempo_preparo_min, tempo_batedeira_min, tempo_forno_min, unidade_rendimento
            ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?)
        """, (
            nome, tipo, rendimento_unidades, custo_embalagem_centavos, margem_lucro_pct, taxa_cartao_pct,
            agora_iso, agora_iso, tempo_preparo_min, tempo_batedeira_min, tempo_forno_min, unidade_rendimento
        ))
        receita_id = cursor.lastrowid
        for item in lista_itens:
            conexao.execute("""
                INSERT INTO receita_itens (receita_pai_id, ingrediente_id, sub_receita_id, quantidade_usada)
                VALUES (?, ?, ?, ?)
            """, (receita_id, item.get("ingrediente_id"), item.get("sub_receita_id"), item["quantidade_usada"]))
        conexao.commit()
        return receita_id
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
    nome = (nome or "").strip()
    unidade_rendimento = (unidade_rendimento or "un").strip().lower()

    if not nome: raise ValueError("Informe o nome da receita.")
    if rendimento_unidades <= 0: raise ValueError("O rendimento precisa ser maior que zero.")
    if unidade_rendimento not in ("un", "g"): raise ValueError("A unidade de rendimento deve ser un ou g.")
    tempos = [tempo_preparo_min, tempo_batedeira_min, tempo_forno_min]
    if any(tempo < 0 for tempo in tempos): raise ValueError("Os tempos não podem ser negativos.")

    agora_iso = datetime.now().isoformat(timespec="seconds")
    conexao = obter_conexao()

    try:
        conexao.execute("""
            UPDATE receitas SET
                nome = ?, tipo = ?, rendimento_unidades = ?, custo_embalagem_centavos = ?, margem_lucro_pct = ?,
                taxa_cartao_pct = ?, atualizado_em = ?, tempo_preparo_min = ?, tempo_batedeira_min = ?,
                tempo_forno_min = ?, unidade_rendimento = ?
            WHERE id = ?
        """, (
            nome, tipo, rendimento_unidades, custo_embalagem_centavos, margem_lucro_pct, taxa_cartao_pct,
            agora_iso, tempo_preparo_min, tempo_batedeira_min, tempo_forno_min, unidade_rendimento, receita_id
        ))

        conexao.execute("DELETE FROM receita_itens WHERE receita_pai_id = ?", (receita_id,))
        for item in lista_itens:
            conexao.execute("""
                INSERT INTO receita_itens (receita_pai_id, ingrediente_id, sub_receita_id, quantidade_usada)
                VALUES (?, ?, ?, ?)
            """, (receita_id, item.get("ingrediente_id"), item.get("sub_receita_id"), item["quantidade_usada"]))

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
    fator_fixo = obter_fator_custo_fixo()
    custo_fixo = custo_insumos * fator_fixo
    custo_total = custo_insumos + custo_embalagem + custo_fixo
    custo_unitario = custo_total / rendimento

    margem = precificacao["margem_lucro_pct"] / 100
    taxa = precificacao["taxa_cartao_pct"] / 100
    preco_com_margem = custo_unitario * (1 + margem)
    divisor = 1 - taxa
    if divisor <= 0: raise ValueError("A taxa do cartão precisa ser menor que 100%.")
    preco_venda = preco_com_margem / divisor

    return {
        "custo_insumos": custo_insumos, "custo_embalagem": custo_embalagem, "custo_fixo": custo_fixo,
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
    horas = float(horas)
    if horas <= 0: raise ValueError("As horas produtivas devem ser maiores que zero.")
    con = obter_conexao()
    try:
        con.execute("""
            INSERT INTO configuracoes(chave, valor) VALUES ('horas_produtivas_mensais', ?)
            ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor
        """, (str(horas),))
        con.commit()
    finally:
        con.close()

def obter_custo_fixo_por_hora():
    total_centavos = sum(int(c["valor_centavos"]) for c in listar_custos_fixos())
    horas = obter_horas_produtivas_mensais()
    if horas <= 0: return 0.0
    return (total_centavos / 100) / horas

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
    tempo_unidade_venda = tempo_total_minutos * fracao_receita
    custo_fixo_hora = obter_custo_fixo_por_hora()
    custo_fixo = (tempo_unidade_venda / 60) * custo_fixo_hora

    custo_embalagem = calcular_custo_embalagem(embalagem_id, quantidade_embalagem) if embalagem_id else 0.0
    custo_sacola = calcular_custo_embalagem(sacola_id, quantidade_sacola) if sacola_id else 0.0

    custo_total = custo_insumos + custo_fixo + custo_embalagem + custo_sacola
    preco_sugerido = custo_total * (1 + markup)

    return {
        "nome": receita["nome"], "rendimento": rendimento, "unidade_rendimento": receita["unidade_rendimento"],
        "quantidade_venda": quantidade_venda, "custo_insumos": custo_insumos, "tempo_total_minutos": tempo_total_minutos,
        "tempo_unidade_venda": tempo_unidade_venda, "custo_fixo_hora": custo_fixo_hora, "custo_fixo": custo_fixo,
        "custo_embalagem": custo_embalagem, "custo_sacola": custo_sacola, "custo_total": custo_total,
        "markup": markup, "preco_sugerido": preco_sugerido,
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
                FOREIGN KEY (receita_id) REFERENCES receitas(id)
            )
        """)

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

        conexao.commit()

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
    taxa_cartao_pct=None
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
                    preco_praticado_centavos = ?
                WHERE id = ?
            """, (
                receita_id,
                quantidade_embalagem,
                custo_embalagem_centavos,
                markup_ideal_pct,
                preco_praticado_centavos,
                id
            ))

            precificacao_id = id

        else:
            cursor = conexao.execute("""
                INSERT INTO precificacao_v2 (
                    receita_id,
                    quantidade_embalagem,
                    custo_embalagem_centavos,
                    markup_ideal_pct,
                    preco_praticado_centavos
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                receita_id,
                quantidade_embalagem,
                custo_embalagem_centavos,
                markup_ideal_pct,
                preco_praticado_centavos
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
            margem_minima_pct
        )

        if not resultado:
            raise ValueError("Não foi possível calcular a precificação.")
        if resultado["status"] != "Dentro da Margem":
            raise ValueError(
                f"Preço não salvo: a margem real é {resultado['margem_real_pct']:.2f}%, "
                f"abaixo do mínimo de {margem_minima_pct:.2f}%."
            )

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
                custo_total_centavos,
                preco_sugerido_centavos,
                preco_praticado_centavos,
                markup_aplicado_pct,
                margem_contribuicao_centavos,
                status,
                registrado_em
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        valor = float(taxas.get(campo, 0))
        if valor < 0 or valor >= 100:
            raise ValueError("Cada taxa deve estar entre 0% e 99,99%.")
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
    valor = float(valor)
    if valor < 0 or valor >= 10000:
        raise ValueError("O markup ideal deve estar entre 0% e 9999,99%.")
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
    valor = float(valor)
    if valor < 0 or valor >= 100:
        raise ValueError("A margem mínima deve estar entre 0% e 99,99%.")

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


def calcular_simulacao_precificacao(receita_id, quantidade_embalagem, custo_embalagem_centavos, markup_ideal_pct, preco_praticado_centavos, taxa_cartao_pct, margem_minima_pct=None):
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
    
    # 2. Custo Fixo Proporcional
    tempo_total_minutos = (receita['tempo_preparo_min'] or 0) + (receita['tempo_batedeira_min'] or 0) + (receita['tempo_forno_min'] or 0)
    custo_fixo_hora = obter_custo_fixo_por_hora()
    custo_fixo_receita_inteira = (tempo_total_minutos / 60.0) * custo_fixo_hora
    custo_fixo = custo_fixo_receita_inteira * fator_proporcao
    
    # 3. Custo Embalagem
    custo_embalagem = custo_embalagem_centavos / 100.0
    
    # 4. Custo Total
    custo_total = custo_insumo + custo_fixo + custo_embalagem
    
    # 5. Preço Sugerido Base
    # O preço sugerido não depende de uma modalidade específica.
    # As taxas são aplicadas separadamente na comparação por forma de pagamento.
    preco_sugerido = custo_total * (1 + (markup_ideal_pct / 100.0))
    
    # 6. Analise do Preço Praticado
    preco_praticado = preco_praticado_centavos / 100.0
    
    # Markup Aplicado = (Preço Praticado - Custo Total) / Custo Total
    markup_aplicado_pct = ((preco_praticado - custo_total) / custo_total * 100.0) if custo_total > 0 else 0
    
    # Margem de Contribuição = Preço Praticado - Custo Total - (Preço Praticado * Taxa Cartão)
    imposto_cartao = preco_praticado * (taxa_cartao_pct / 100.0)
    margem_contribuicao = preco_praticado - custo_total - imposto_cartao
    
    if margem_minima_pct is None:
        margem_minima_pct = obter_margem_minima()
    margem_real_pct = (margem_contribuicao / preco_praticado * 100.0) if preco_praticado > 0 else 0.0
    status = "Dentro da Margem" if margem_real_pct >= margem_minima_pct else "Abaixo da Margem Mínima"
    
    return {
        "custo_insumo": custo_insumo,
        "custo_fixo": custo_fixo,
        "custo_embalagem": custo_embalagem,
        "custo_total": custo_total,
        "preco_sugerido": preco_sugerido,
        "preco_praticado": preco_praticado,
        "markup_aplicado_pct": markup_aplicado_pct,
        "margem_contribuicao": margem_contribuicao,
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

        conexao.commit()
    finally:
        conexao.close()


def salvar_orcamento(dados):
    """Salva o orçamento e seus itens como fotografia dos valores da data."""
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
            SET cliente=?, status='Em elaboração', validade=?, data_entrega=?, desconto_tipo=?, desconto_valor=?, modalidade=?,
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


def atualizar_status_orcamento(orcamento_id, status):
    permitidos = {"Em elaboração", "Enviado", "Aprovado", "Recusado"}
    if status not in permitidos:
        raise ValueError("Status de orçamento inválido.")
    conexao = obter_conexao()
    try:
        conexao.execute("""
            UPDATE orcamentos
            SET status = ?, atualizado_em = ?
            WHERE id = ?
        """, (status, datetime.now().isoformat(timespec="seconds"), orcamento_id))
        conexao.commit()
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
            "entregas_proximos_7_dias": quantidade_entregas,
            "entregas": entregas,
            "atividades": atividades,
        }
    finally:
        conexao.close()
