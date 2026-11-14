# Arquitetura do DM Gulositos

## Objetivo

Evoluir o aplicativo de forma incremental, separando interface, regras de negócio e persistência sem perder funcionalidades nem dados existentes.

## Estrutura adotada

- `DM_Gulositos.py`: ponto de entrada e composição inicial da aplicação.
- `telas/`: telas independentes, recebendo dependências por parâmetros/callbacks.
- `componentes/`: componentes visuais compartilhados.
- `servicos/`: regras de negócio e cálculos que não pertencem à interface.
- `database/`: conexão, schema, consultas e migrações SQLite.
- `assets/`: recursos visuais e arquivos estáticos.
- `docs/`: documentação técnica e decisões de arquitetura.

## Regras de manutenção

1. Não alterar a branch `main` durante a refatoração.
2. Não recriar nem apagar o banco de dados para acomodar mudanças de código.
3. Alterações de schema devem ser feitas por migrações compatíveis e com backup prévio.
4. Telas não devem executar SQL diretamente; devem chamar a camada `database` ou serviços.
5. Cálculos de precificação e regras financeiras devem ser centralizados em serviços, preservando os resultados já validados.
6. Componentes compartilhados devem receber parâmetros explícitos, evitando dependências ocultas da função `main`.
7. Cada extração deve ser pequena, revisada e validada antes da próxima.
8. Não incorporar branches divergentes inteiras; portar somente arquivos cuja compatibilidade tenha sido conferida.

## Etapas

1. Estabelecer uma branch isolada e corrigir a organização física da camada de banco.
2. Extrair menu e componentes compartilhados por injeção de callbacks.
3. Extrair telas individualmente, mantendo a navegação atual.
4. Separar serviços de precificação, relatórios e validações.
5. Introduzir migrações e testes automatizados para operações críticas.
6. Desenvolver dashboard, clientes, estoque, financeiro e sincronização após a base modular estar estável.
7. Validar execução web, APK e preservação de dados antes de abrir PR para `main`.

## Situação inicial

A versão analisada concentra a interface em `DM_Gulositos.py` e possui uma camada de persistência publicada em uma branch diferente. A camada de banco está sendo portada para `database/banco.py` sem mesclar o histórico divergente da branch `database`.


## Situação da refatoração

- [x] Criar branch isolada `refatoracao-modular`.
- [x] Organizar a camada de banco em `database/banco.py`, sem mesclar o histórico divergente da branch `database`.
- [x] Extrair o menu para `telas/menu.py`.
- [x] Extrair builders visuais compartilhados para `componentes/ui.py`.
- [x] Extrair a agenda de produção para `telas/agenda.py`, recebendo Flet, estado, callbacks e funções de persistência por injeção de dependências.
- [x] Extrair orçamentos e histórico de versões para `telas/orcamentos.py`, com dependências injetadas pelo app principal.
- [x] Extrair ingredientes para `telas/ingredientes.py`, com dependências injetadas.
- [x] Extrair receitas e fichas técnicas para `telas/receitas.py`, com dependências injetadas.
- [x] Extrair custos fixos, remuneração e parâmetros gerais para `telas/custos_fixos.py`.
- [x] Separar fórmulas puras de precificação em `servicos/precificacao_service.py`.
- [x] Adicionar testes unitários para as fórmulas centrais de preço e margem.
- [x] Extrair relatórios e painel inicial para `telas/relatorios.py`.
- [ ] Criar/validar testes automatizados, execução web e build APK.

A extração da agenda preserva os filtros por status e data, ordenação das entregas, destaque de atrasos/entregas do dia e atualização do status de produção. A validação funcional ainda depende da execução local do aplicativo.


A tela de orçamentos foi extraída preservando criação e edição, seleção/exclusão em lote com dupla confirmação, filtros por status, histórico de versões, atualização de status, simulação por modalidade de pagamento e geração da mensagem para compartilhamento. O módulo recebe explicitamente os callbacks de persistência e os componentes compartilhados. A validação de sintaxe em ambiente Python/Flet e o teste funcional ainda precisam ser executados localmente.


A tela de ingredientes foi extraída para `telas/ingredientes.py`, preservando listagem, alertas de aumento de preços, cadastro/edição, cálculo de custo unitário, histórico de preços e exclusão com dupla confirmação. O módulo recebe os recursos de interface e persistência por injeção de dependências. A validação funcional continua pendente de execução local.


As telas de receitas e fichas técnicas foram extraídas para `telas/receitas.py`, preservando listagem e filtros por tipo, exclusão lógica com dupla confirmação, cadastro/edição, seleção de ingredientes e sub-receitas, rendimento e unidade, tempos de produção e gravação por meio das funções existentes de persistência. A validação funcional permanece pendente de execução local.


A tela de custos fixos foi extraída para `telas/custos_fixos.py`, preservando o cadastro/edição/exclusão de despesas, faturamento mensal alvo, remuneração desejada, horas produtivas mensais, impostos, markup ideal, margem mínima e taxas por forma de pagamento. As funções de persistência existentes são injetadas no módulo. A validação funcional ainda depende da execução local.


Relatórios e painel inicial foram extraídos para `telas/relatorios.py`, preservando indicadores, relatórios de produtos e sub-receitas, atalhos, próximas encomendas e atividades recentes. As telas modulares usam uma referência compartilhada para a barra de navegação, pois ela é instanciada depois das fábricas de tela dentro de `main()`; isso evita acessar a variável antes de sua inicialização.


## Serviço de precificação

As fórmulas sem acesso a banco ou interface foram centralizadas em `servicos/precificacao_service.py`: cálculo do preço sugerido a partir de custo, markup, impostos e taxas; e cálculo dos indicadores do preço praticado (markup aplicado, margem de contribuição e resultado após rateio). A camada `database/banco.py` continua responsável por buscar os dados e orquestrar os custos, delegando essas fórmulas ao serviço. Foram adicionados testes unitários em `tests/test_precificacao_service.py`. Os testes ainda precisam ser executados no ambiente local do projeto.


## Serviço de backup e restauração

As rotinas de backup foram centralizadas em `servicos/backup_service.py`. O serviço cria cópias consistentes pela API de backup do SQLite, valida a integridade e a presença das tabelas essenciais, limita a retenção dos backups automáticos e gera bytes para exportação.

Na restauração, o arquivo selecionado é gravado em um temporário e validado antes de qualquer substituição. Quando já existe um banco ativo, o serviço finaliza as operações pendentes e cria uma cópia em `database/backups/` antes de substituir o arquivo. A interface solicita duas confirmações e orienta o usuário a reiniciar o aplicativo após a restauração.

Os testes do serviço usam bancos SQLite temporários e não devem acessar o banco real da doceria.


## Identidade e configuração de build

O projeto utiliza `pyproject.toml` como configuração central do Flet. O nome exibido é **DM Gulositos**, a versão inicial desta configuração é **1.0.0** e o módulo de entrada é `DM_Gulositos.py`. O identificador interno do projeto permanece `dm`; não foi definido um novo `org` ou `bundle_id`, evitando alterar sem necessidade o identificador derivado pelo build anterior.

Os recursos visuais do aplicativo ficam em `assets/icon.svg` e `assets/splash.svg`. A cor de fundo da abertura usa a paleta clara da aplicação. O build deve ser conferido no ambiente local antes de distribuir a versão.
