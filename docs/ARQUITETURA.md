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
- [ ] Extrair ingredientes e receitas.
- [ ] Separar cálculos de precificação em serviços.
- [ ] Extrair relatórios e painel inicial.
- [ ] Criar/validar testes automatizados, execução web e build APK.

A extração da agenda preserva os filtros por status e data, ordenação das entregas, destaque de atrasos/entregas do dia e atualização do status de produção. A validação funcional ainda depende da execução local do aplicativo.


A tela de orçamentos foi extraída preservando criação e edição, seleção/exclusão em lote com dupla confirmação, filtros por status, histórico de versões, atualização de status, simulação por modalidade de pagamento e geração da mensagem para compartilhamento. O módulo recebe explicitamente os callbacks de persistência e os componentes compartilhados. A validação de sintaxe em ambiente Python/Flet e o teste funcional ainda precisam ser executados localmente.
