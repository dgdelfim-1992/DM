# DM Gulositos

Aplicativo de apoio à gestão de uma doceria, desenvolvido em Python, Flet e SQLite.

## Funcionalidades

- Cadastro de insumos, fornecedores e histórico de preços.
- Receitas e sub-receitas com fichas técnicas e tempos de produção.
- Custos fixos, mão de obra e taxas de pagamento.
- Precificação com custos, markup, impostos e taxas.
- Orçamentos, histórico de versões e acompanhamento de status.
- Agenda de produção e entregas.
- Painel inicial e relatórios.
- Backup automático, exportação e restauração do banco de dados.

## Estrutura do projeto

- `DM_Gulositos.py`: inicialização e composição da aplicação.
- `telas/`: telas e fluxos da interface.
- `componentes/`: componentes visuais compartilhados.
- `servicos/`: regras de negócio independentes da interface.
- `database/`: persistência e operações SQLite.
- `tests/`: testes automatizados.
- `docs/`: documentação técnica.

## Ambiente de desenvolvimento

Recomenda-se Python 3.12, 3.13 ou 3.14. A configuração de build seleciona uma versão compatível dentro desse intervalo.

No Windows, dentro da pasta do projeto:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install flet==1.0.4
```

Execute a aplicação com `flet run --module-name DM_Gulositos` ou use `python DM_Gulositos.py`. Para gerar o APK, use `flet build apk`.

## Testes automatizados

Com o ambiente virtual ativado:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Os testes de serviços que manipulam SQLite devem usar bancos temporários. Não utilize o banco real da doceria para testes destrutivos.

## Proteção dos dados

- O banco de produção fica em `database/dm_gulositos.db` e não deve ser versionado.
- Cópias automáticas e cópias anteriores à restauração ficam em `database/backups/`.
- O backup exportado deve ser guardado em local separado do dispositivo.
- A restauração substitui os dados atuais; confirme o arquivo antes de prosseguir.
- Antes da restauração, o aplicativo cria uma cópia de segurança do banco atual.
- Depois de restaurar, feche e abra novamente o aplicativo para que todas as telas utilizem o banco restaurado.

## Branch de desenvolvimento

As melhorias modulares estão sendo realizadas na branch `refatoracao-modular`. A branch `main` deve permanecer estável até a conclusão da revisão e da preparação da versão.
