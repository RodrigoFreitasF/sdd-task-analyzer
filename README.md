# SDD TaskAnalyzer 📊

Módulo analítico e determinístico de produtividade e análise de tarefas corporativas desenvolvido segundo o paradigma **Spec-Driven Development (SDD)**, com geração assistida por IA, governança rígida de contexto e homologação via **Test Harness** automatizado.

Projeto desenvolvido para a disciplina de **Bootcamp III** (Fase 2 - Entrega Intermediária).

---

## 🚀 Tecnologias e Diretrizes

- **Linguagem:** Python 3.11+
- **Testes Automatizados:** Pytest 8+
- **Paradigma:** Spec-Driven Development (SDD) & AI Harness
- **Padrões de Código:** PEP 8, Type Hints em 100% do código e Google Style Docstrings
- **Controle de Versão:** Git com fluxo baseado em branches de feature e Pull Requests

---

## 📁 Estrutura do Repositório

```text
sdd-task-analyzer/
├── README.md                 # Documentação geral e instruções do projeto
├── CONTEXT_RULES.md          # Regras persistentes de governança para agentes de IA
├── .gitignore                # Arquivos ignorados no versionamento
├── requirements.txt          # Dependências do projeto (pytest)
├── specs/
│   └── task_analyzer_spec.md # Contrato executável e especificação SDD da Fase 1
├── tests/
│   └── test_harness.py       # Suíte de testes automatizados com pytest
└── src/
    └── task_analyzer.py      # Código-fonte homologado gerado com auxílio de IA