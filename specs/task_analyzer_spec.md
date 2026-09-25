```markdown
# ESPECIFICAÇÃO TÉCNICA EXECUTÁVEL (SDD) - TASKANALYZER

## 1. VISÃO GERAL E PROPÓSITO
O módulo `TaskAnalyzer` é um motor determinístico e analítico em memória projetado para apurar métricas de produtividade, eficiência e prazos a partir de coleções de tarefas corporativas. Atua como uma biblioteca pura, sem persistência em disco ou banco de dados.

---

## 2. CONTRATO EXECUTÁVEL DE INTERFACE

### 2.1 Assinatura da Função Pública Principal
A função pública principal deve seguir estritamente a assinatura abaixo[cite: 5]:

```python
def analyze_tasks(tasks: list[dict]) -> dict:
    """Processa um lote de tarefas e retorna métricas consolidadas de produtividade.

    Args:
        tasks: Lista de dicionários representando as tarefas a serem analisadas.

    Returns:
        Dicionário com métricas consolidadas e detalhamento por prioridade.

    Raises:
        TaskValidationError: Se houver inconsistência cronológica entre datas
            ou ausência de campos obrigatórios.
    """

```

### 2.2 Estrutura do Payload de Entrada (`tasks: list[dict]`)

Cada dicionário contido na lista de entrada deve possuir os seguintes campos obrigatórios e restrições:

| Campo | Tipo | Obrigatório | Descrição e Restrições |
| --- | --- | --- | --- |
| `id` | `str` | Sim | Identificador alfanumérico único da tarefa (não vazio).

 |
| `titulo` | `str` | Sim | Título ou descrição da tarefa.

 |
| `prioridade` | `str` | Sim | Valores aceitos estritamente: `'BAIXA'`, `'MEDIA'` ou `'ALTA'`.

 |
| `data_criacao` | `str` | Sim | Data e hora em padrão ISO 8601 (ex.: `'2026-03-01T08:00:00'`).

 |
| `prazo` | `str` | Sim | Data e hora limite de conclusão em padrão ISO 8601.

 |
| `data_conclusao` | `str | None` | Não | Data/hora de conclusão em padrão ISO 8601, ou `None` se pendente.

 |
| `status` | `str` | Sim | Valores aceitos estritamente: `'PENDENTE'` ou `'CONCLUIDA'`.

 |

### 2.3 Estrutura do Payload de Saída (`dict`)

O dicionário retornado por `analyze_tasks` deve conter as seguintes chaves:

| Chave | Tipo | Descrição e Critério |
| --- | --- | --- |
| `total_tarefas` | `int` | Quantidade bruta total de tarefas recebidas na lista. |
| `total_concluidas` | `int` | Quantidade de tarefas com `status == 'CONCLUIDA'`. |
| `total_pendentes` | `int` | Quantidade de tarefas com `status == 'PENDENTE'`.

 |
| `tempo_medio_conclusao_horas` | `float` | Média em horas decimais entre `data_criacao` e `data_conclusao`. Retornar `0.0` se não houver concluídas. |
| `taxa_atraso_percentual` | `float` | Percentual (0.0 a 100.0) de tarefas concluídas com `data_conclusao > prazo`. Retornar `0.0` se não houver concluídas. |
| `metricas_por_prioridade` | `dict` | Dicionário com chaves `'BAIXA'`, `'MEDIA'` e `'ALTA'`, contendo individualmente `total`, `tempo_medio_horas` e `taxa_atraso_percentual`. |

---

## 3. REGRAS DE NEGÓCIO E RESTRIÇÕES RÍGIDAS

1. **Elegibilidade Temporal:** Apenas tarefas com `status == 'CONCLUIDA'` e `data_conclusao != None` entram no cálculo de médias de duração e atraso.


2. **Consistência Cronológica Obrigatória:** Uma tarefa não pode possuir `data_conclusao < data_criacao` ou `prazo < data_criacao`. Caso identificado, deve-se disparar a exceção customizada `TaskValidationError` com mensagem clara.


3. **Prevenção de Divisão por Zero:** Caso o lote recebido seja vazio (`[]`) ou não possua tarefas concluídas, as médias e taxas percentuais devem retornar `0.0`, sem interrupção por exceções de tempo de execução.
4. **Imutabilidade:** O processamento não deve modificar os dicionários ou referências recebidas no lote de entrada.



---

## 4. CENÁRIOS DE ACEITE (TEST HARNESS)

### Cenário 1: Sucesso no Cálculo Consolidado (Caminho Feliz)

* **Dado:** Um lote de tarefas válidas contendo:
* Tarefa 1 (Prioridade: 'ALTA'): criada às 08:00, prazo às 12:00, concluída às 10:00 (duração: 2.0h, no prazo).


* Tarefa 2 (Prioridade: 'MEDIA'): criada às 08:00, prazo às 10:00, concluída às 12:00 (duração: 4.0h, atrasada).


* Tarefa 3 (Prioridade: 'BAIXA'): criada às 09:00, prazo às 18:00, status 'PENDENTE', `data_conclusao=None`.




* **Quando:** A função `analyze_tasks(tasks)` for executada.


* **Então:** Deve retornar:
* `total_tarefas = 3`
* `total_concluidas = 2`
* `total_pendentes = 1`

* `tempo_medio_conclusao_horas = 3.0`
* `taxa_atraso_percentual = 50.0`
* Detalhamento por prioridade computado com precisão.





### Cenário 2: Inconsistência Cronológica (Exceção Tratada)

* **Dado:** Um lote contendo ao menos uma tarefa com `data_conclusao < data_criacao`.
* **Quando:** A função `analyze_tasks(tasks)` for executada.


* **Então:** O sistema deve disparar `TaskValidationError` com a mensagem `"Data de conclusão não pode ser anterior à data de criação."`.

### Cenário 3: Casos de Borda (Divisão por Zero)

* **Dado:** Uma lista contendo apenas tarefas com `status == 'PENDENTE'` ou lista vazia `[]`.
* **Quando:** A função `analyze_tasks(tasks)` for executada.


* **Então:** O processamento deve concluir retornando `total_concluidas = 0`, `tempo_medio_conclusao_horas = 0.0` e `taxa_atraso_percentual = 0.0`.

```

```