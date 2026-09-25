# CONTEXT RULES - GOVERNANÇA DE DESENVOLVIMENTO COM IA

Este arquivo define as restrições inegociáveis e diretrizes arquiteturais que qualquer assistente ou agente de Inteligência Artificial deve seguir estritamente ao propor ou gerar código para o projeto `TaskAnalyzer`.

---

## 1. DIRETRIZES ARQUITETURAIS OBRIGATÓRIAS

- **Versão da Linguagem:** Python 3.11 ou superior obrigatório.
- **Tipagem Estática:** Uso mandatório de *Type Hints* (anotações de tipo) em 100% das funções, métodos, parâmetros e retornos (utilizar módulos nativos e `typing`).
- **Princípio de Responsabilidade Única (SRP):** Manter funções pequenas, altamente coesas e focadas em uma única tarefa lógica.
- **Padrão de Código Limpo e PEP 8:** Seguir estritamente as convenções de nomenclatura, espaçamento e boas práticas da PEP 8.
- **Documentação Formal:** Todas as classes, funções e métodos públicos devem conter docstrings no formato **Google Style** (com seções `Args:`, `Returns:` e `Raises:`).
- **Observabilidade:** Utilizar o módulo nativo `logging` para registrar mensagens informativas de processamento e alertas/erros em fluxos anômalos.
- **Tratamento de Exceções:** Tratar exceções de forma específica e explícita, nunca utilizando blocos genéricos `except Exception: pass`.
- **Prevenção de Divisão por Zero:** Casos sem tarefas ou sem tarefas concluídas devem retornar médias e percentuais zerados (`0.0`), sem interrupção de execução.

---

## 2. PROIBIÇÕES EXPLÍCITAS (REGRAS RESTRITIVAS)

- **Proibido o uso de bibliotecas externas não autorizadas:** Para a lógica do módulo analítico em `src/task_analyzer.py`, utilizar exclusivamente módulos da biblioteca padrão do Python (`datetime`, `logging`, `typing`, etc.). Bibliotecas de terceiros como `pandas`, `numpy` ou `arrow` são expressamente proibidas.
- **Proibida a persistência em disco ou banco de dados:** O módulo atua exclusivamente em memória. Não salvar arquivos locais (`.json`, `.csv`, `.txt`, `.db`) e não interagir com bancos de dados.
- **Proibida a alteração do contrato de negócio:** Não alterar os nomes da função pública (`analyze_tasks`), da exceção customizada (`TaskValidationError`) ou as chaves e tipos do dicionário de saída especificados na SDD.
- **Proibida a alteração da suíte de testes:** A IA não pode remover, adaptar ou flexibilizar os testes fornecidos no Test Harness (`tests/test_harness.py`) para mascarar falhas de implementação.
- **Proibido assumir comportamentos omitidos:** Em caso de dúvida ou regra de negócio não especificada, a IA deve solicitar esclarecimentos ao desenvolvedor humano em vez de supor implementações arbitrárias.
- **Proibida a alteração da estrutura de pastas:** A arquitetura com `specs/`, `src/` e `tests/` deve ser respeitada sem acréscimo de diretórios não planejados.

---

## 3. PROTOCOLO DE INTERAÇÃO COM O AGENTE

1. O agente deve confirmar o entendimento deste arquivo antes de gerar qualquer implementação.
2. Todo código sugerido será submetido a execução automatizada de testes (`pytest`) e homologação crítica por desenvolvedor humano antes de ser versionado.