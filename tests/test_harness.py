"""Suíte de testes automatizados do módulo TaskAnalyzer.

Este módulo implementa o Test Harness completo cobrindo os cenários de aceite
definidos na especificação técnica SDD (specs/task_analyzer_spec.md) e nas
diretrizes de governança (CONTEXT_RULES.md).
"""

from copy import deepcopy
from typing import Any
import pytest

from src.task_analyzer import TaskValidationError, analyze_tasks


def test_cenario_1_caminho_feliz() -> None:
    """Valida o cálculo consolidado de métricas em um lote de tarefas variadas.

    Cenário 1 da especificação:
    - Tarefa 1 (ALTA): criada 08:00, prazo 12:00, concluída 10:00 (2.0h, no prazo).
    - Tarefa 2 (MEDIA): criada 08:00, prazo 10:00, concluída 12:00 (4.0h, atrasada).
    - Tarefa 3 (BAIXA): criada 09:00, prazo 18:00, status 'PENDENTE', data_conclusao=None.

    Args:
        None.

    Returns:
        None.

    Raises:
        AssertionError: Se qualquer métrica calculada divergir da especificação.
    """
    lote_tarefas: list[dict[str, Any]] = [
        {
            "id": "TASK-001",
            "titulo": "Implementar módulo de segurança",
            "prioridade": "ALTA",
            "data_criacao": "2026-03-01T08:00:00",
            "prazo": "2026-03-01T12:00:00",
            "data_conclusao": "2026-03-01T10:00:00",
            "status": "CONCLUIDA",
        },
        {
            "id": "TASK-002",
            "titulo": "Refatorar camada de persistência",
            "prioridade": "MEDIA",
            "data_criacao": "2026-03-01T08:00:00",
            "prazo": "2026-03-01T10:00:00",
            "data_conclusao": "2026-03-01T12:00:00",
            "status": "CONCLUIDA",
        },
        {
            "id": "TASK-003",
            "titulo": "Documentar contratos de API",
            "prioridade": "BAIXA",
            "data_criacao": "2026-03-01T09:00:00",
            "prazo": "2026-03-01T18:00:00",
            "data_conclusao": None,
            "status": "PENDENTE",
        },
    ]

    resultado: dict[str, Any] = analyze_tasks(tasks=lote_tarefas)

    # Asserções das métricas globais
    assert resultado["total_tarefas"] == 3
    assert resultado["total_concluidas"] == 2
    assert resultado["total_pendentes"] == 1
    assert resultado["tempo_medio_conclusao_horas"] == 3.0
    assert resultado["taxa_atraso_percentual"] == 50.0

    # Asserções das métricas agrupadas por prioridade
    metricas_prioridade: dict[str, dict[str, Any]] = resultado["metricas_por_prioridade"]

    metricas_alta: dict[str, Any] = metricas_prioridade["ALTA"]
    assert metricas_alta["total"] == 1
    assert metricas_alta["tempo_medio_horas"] == 2.0
    assert metricas_alta["taxa_atraso_percentual"] == 0.0

    metricas_media: dict[str, Any] = metricas_prioridade["MEDIA"]
    assert metricas_media["total"] == 1
    assert metricas_media["tempo_medio_horas"] == 4.0
    assert metricas_media["taxa_atraso_percentual"] == 100.0

    metricas_baixa: dict[str, Any] = metricas_prioridade["BAIXA"]
    assert metricas_baixa["total"] == 1
    assert metricas_baixa["tempo_medio_horas"] == 0.0
    assert metricas_baixa["taxa_atraso_percentual"] == 0.0


def test_cenario_2_inconsistencia_cronologica_conclusao_anterior_criacao() -> None:
    """Valida que data de conclusão anterior à criação dispara TaskValidationError.

    Cenário 2 da especificação:
    - Tarefa com data_conclusao < data_criacao deve lançar TaskValidationError
      com a mensagem exata 'Data de conclusão não pode ser anterior à data de criação.'.

    Args:
        None.

    Returns:
        None.

    Raises:
        AssertionError: Se a exceção esperada não for lançada ou mensagem divergir.
    """
    lote_invalido: list[dict[str, Any]] = [
        {
            "id": "TASK-INV-001",
            "titulo": "Tarefa com viagem no tempo",
            "prioridade": "ALTA",
            "data_criacao": "2026-03-01T10:00:00",
            "prazo": "2026-03-01T12:00:00",
            "data_conclusao": "2026-03-01T08:00:00",
            "status": "CONCLUIDA",
        }
    ]

    mensagem_esperada: str = "Data de conclusão não pode ser anterior à data de criação."

    with pytest.raises(TaskValidationError) as exc_info:
        analyze_tasks(tasks=lote_invalido)

    assert str(exc_info.value) == mensagem_esperada


def test_cenario_3_casos_de_borda_lista_vazia() -> None:
    """Valida o tratamento seguro de lista vazia sem divisão por zero.

    Cenário 3 da especificação:
    - Entrada vazia [] deve retornar totais e taxas zerados com segurança.

    Args:
        None.

    Returns:
        None.

    Raises:
        AssertionError: Se os retornos não forem zeros seguros ou se houver erro.
    """
    lote_vazio: list[dict[str, Any]] = []

    resultado: dict[str, Any] = analyze_tasks(tasks=lote_vazio)

    assert resultado["total_tarefas"] == 0
    assert resultado["total_concluidas"] == 0
    assert resultado["total_pendentes"] == 0
    assert resultado["tempo_medio_conclusao_horas"] == 0.0
    assert resultado["taxa_atraso_percentual"] == 0.0

    metricas_prioridade: dict[str, dict[str, Any]] = resultado["metricas_por_prioridade"]
    for prioridade in ["BAIXA", "MEDIA", "ALTA"]:
        dados_p: dict[str, Any] = metricas_prioridade[prioridade]
        assert dados_p["total"] == 0
        assert dados_p["tempo_medio_horas"] == 0.0
        assert dados_p["taxa_atraso_percentual"] == 0.0


def test_cenario_3_casos_de_borda_apenas_pendentes() -> None:
    """Valida o cálculo com lote contendo exclusivamente tarefas pendentes.

    Cenário 3 da especificação:
    - Sem tarefas concluídas, médias e percentuais devem ser 0.0 sem erros de runtime.

    Args:
        None.

    Returns:
        None.

    Raises:
        AssertionError: Se totais divergirem ou se médias não forem zeradas.
    """
    lote_pendentes: list[dict[str, Any]] = [
        {
            "id": "TASK-PEND-001",
            "titulo": "Investigação técnica preliminar",
            "prioridade": "BAIXA",
            "data_criacao": "2026-03-01T08:00:00",
            "prazo": "2026-03-02T18:00:00",
            "data_conclusao": None,
            "status": "PENDENTE",
        },
        {
            "id": "TASK-PEND-002",
            "titulo": "Auditoria de dependências",
            "prioridade": "ALTA",
            "data_criacao": "2026-03-01T09:00:00",
            "prazo": "2026-03-01T17:00:00",
            "data_conclusao": None,
            "status": "PENDENTE",
        },
    ]

    resultado: dict[str, Any] = analyze_tasks(tasks=lote_pendentes)

    assert resultado["total_tarefas"] == 2
    assert resultado["total_concluidas"] == 0
    assert resultado["total_pendentes"] == 2
    assert resultado["tempo_medio_conclusao_horas"] == 0.0
    assert resultado["taxa_atraso_percentual"] == 0.0

    metricas_prioridade: dict[str, dict[str, Any]] = resultado["metricas_por_prioridade"]
    assert metricas_prioridade["BAIXA"]["total"] == 1
    assert metricas_prioridade["BAIXA"]["tempo_medio_horas"] == 0.0
    assert metricas_prioridade["BAIXA"]["taxa_atraso_percentual"] == 0.0

    assert metricas_prioridade["ALTA"]["total"] == 1
    assert metricas_prioridade["ALTA"]["tempo_medio_horas"] == 0.0
    assert metricas_prioridade["ALTA"]["taxa_atraso_percentual"] == 0.0

    assert metricas_prioridade["MEDIA"]["total"] == 0
    assert metricas_prioridade["MEDIA"]["tempo_medio_horas"] == 0.0
    assert metricas_prioridade["MEDIA"]["taxa_atraso_percentual"] == 0.0


def test_inconsistencia_cronologica_prazo_anterior_criacao() -> None:
    """Valida que prazo anterior à data de criação dispara TaskValidationError.

    Args:
        None.

    Returns:
        None.

    Raises:
        AssertionError: Se a exceção esperada não for lançada.
    """
    lote_prazo_invalido: list[dict[str, Any]] = [
        {
            "id": "TASK-INV-002",
            "titulo": "Tarefa com prazo no passado",
            "prioridade": "MEDIA",
            "data_criacao": "2026-03-01T10:00:00",
            "prazo": "2026-03-01T09:00:00",
            "data_conclusao": None,
            "status": "PENDENTE",
        }
    ]

    with pytest.raises(TaskValidationError) as exc_info:
        analyze_tasks(tasks=lote_prazo_invalido)

    assert "O prazo não pode ser anterior à data de criação." in str(exc_info.value)


@pytest.mark.parametrize(
    "campo_faltante",
    ["id", "titulo", "prioridade", "data_criacao", "prazo", "status"],
)
def test_validacao_ausencia_campos_obrigatorios(campo_faltante: str) -> None:
    """Valida que a ausência de qualquer campo obrigatório dispara TaskValidationError.

    Args:
        campo_faltante: Nome do campo removido do payload de teste.

    Returns:
        None.

    Raises:
        AssertionError: Se a exceção esperada não for disparada.
    """
    tarefa_base: dict[str, Any] = {
        "id": "TASK-REQ-001",
        "titulo": "Tarefa para teste de obrigatoriedade",
        "prioridade": "ALTA",
        "data_criacao": "2026-03-01T08:00:00",
        "prazo": "2026-03-01T12:00:00",
        "status": "PENDENTE",
    }
    tarefa_incompleta: dict[str, Any] = deepcopy(tarefa_base)
    del tarefa_incompleta[campo_faltante]

    with pytest.raises(TaskValidationError) as exc_info:
        analyze_tasks(tasks=[tarefa_incompleta])

    assert f"Campo obrigatório ausente na tarefa: '{campo_faltante}'." in str(exc_info.value)


def test_validacao_prioridade_invalida() -> None:
    """Valida que prioridade fora do conjunto aceito dispara TaskValidationError.

    Args:
        None.

    Returns:
        None.

    Raises:
        AssertionError: Se a exceção esperada não for disparada.
    """
    lote_prioridade_invalida: list[dict[str, Any]] = [
        {
            "id": "TASK-PRIO-001",
            "titulo": "Tarefa com prioridade inexistente",
            "prioridade": "URGENTE",
            "data_criacao": "2026-03-01T08:00:00",
            "prazo": "2026-03-01T12:00:00",
            "status": "PENDENTE",
        }
    ]

    with pytest.raises(TaskValidationError) as exc_info:
        analyze_tasks(tasks=lote_prioridade_invalida)

    assert "Prioridade inválida" in str(exc_info.value)


def test_validacao_status_invalido() -> None:
    """Valida que status fora do conjunto aceito dispara TaskValidationError.

    Args:
        None.

    Returns:
        None.

    Raises:
        AssertionError: Se a exceção esperada não for disparada.
    """
    lote_status_invalido: list[dict[str, Any]] = [
        {
            "id": "TASK-STAT-001",
            "titulo": "Tarefa em andamento",
            "prioridade": "ALTA",
            "data_criacao": "2026-03-01T08:00:00",
            "prazo": "2026-03-01T12:00:00",
            "status": "EM_ANDAMENTO",
        }
    ]

    with pytest.raises(TaskValidationError) as exc_info:
        analyze_tasks(tasks=lote_status_invalido)

    assert "Status inválido" in str(exc_info.value)


def test_validacao_id_duplicado() -> None:
    """Valida que identificadores duplicados no mesmo lote disparam TaskValidationError.

    Args:
        None.

    Returns:
        None.

    Raises:
        AssertionError: Se a exceção esperada não for disparada.
    """
    lote_duplicado: list[dict[str, Any]] = [
        {
            "id": "TASK-DUP-001",
            "titulo": "Primeira ocorrência",
            "prioridade": "ALTA",
            "data_criacao": "2026-03-01T08:00:00",
            "prazo": "2026-03-01T12:00:00",
            "status": "PENDENTE",
        },
        {
            "id": "TASK-DUP-001",
            "titulo": "Segunda ocorrência com mesmo ID",
            "prioridade": "MEDIA",
            "data_criacao": "2026-03-01T09:00:00",
            "prazo": "2026-03-01T15:00:00",
            "status": "PENDENTE",
        },
    ]

    with pytest.raises(TaskValidationError) as exc_info:
        analyze_tasks(tasks=lote_duplicado)

    assert "Identificador duplicado encontrado" in str(exc_info.value)


def test_validacao_formato_data_invalido() -> None:
    """Valida que datas fora do padrão ISO 8601 disparam TaskValidationError.

    Args:
        None.

    Returns:
        None.

    Raises:
        AssertionError: Se a exceção esperada não for disparada.
    """
    lote_data_invalida: list[dict[str, Any]] = [
        {
            "id": "TASK-DATE-001",
            "titulo": "Data com formato incorreto",
            "prioridade": "ALTA",
            "data_criacao": "01/03/2026 08:00",
            "prazo": "2026-03-01T12:00:00",
            "status": "PENDENTE",
        }
    ]

    with pytest.raises(TaskValidationError) as exc_info:
        analyze_tasks(tasks=lote_data_invalida)

    assert "Formato de data inválido" in str(exc_info.value)


def test_validacao_tipo_payload_invalido() -> None:
    """Valida que payloads que não sejam listas de dicionários disparam TaskValidationError.

    Args:
        None.

    Returns:
        None.

    Raises:
        AssertionError: Se a exceção esperada não for disparada.
    """
    # Teste de payload não sendo lista
    with pytest.raises(TaskValidationError) as exc_info_nao_lista:
        analyze_tasks(tasks="não é uma lista")  # type: ignore[arg-type]

    assert "deve ser uma lista de dicionários" in str(exc_info_nao_lista.value)

    # Teste de item da lista não sendo dicionário
    with pytest.raises(TaskValidationError) as exc_info_item_invalido:
        analyze_tasks(tasks=["não é um dicionário"])  # type: ignore[list-item]

    assert "Cada tarefa deve ser um dicionário" in str(exc_info_item_invalido.value)


def test_imutabilidade_payload_entrada() -> None:
    """Garante que a execução de analyze_tasks não altera os dados de entrada.

    Args:
        None.

    Returns:
        None.

    Raises:
        AssertionError: Se os dados originais sofrerem mutação durante o processamento.
    """
    lote_original: list[dict[str, Any]] = [
        {
            "id": "TASK-IMUT-001",
            "titulo": "Teste de Imutabilidade",
            "prioridade": "ALTA",
            "data_criacao": "2026-03-01T08:00:00",
            "prazo": "2026-03-01T12:00:00",
            "data_conclusao": "2026-03-01T10:00:00",
            "status": "CONCLUIDA",
        }
    ]
    copia_verificacao: list[dict[str, Any]] = deepcopy(lote_original)

    _resultado_imutabilidade: dict[str, Any] = analyze_tasks(tasks=lote_original)

    assert lote_original == copia_verificacao


def test_tarefa_concluida_exatamente_no_prazo() -> None:
    """Valida que conclusão exatamente no horário limite (data_conclusao == prazo) não conta como atraso.

    Args:
        None.

    Returns:
        None.

    Raises:
        AssertionError: Se a tarefa for considerada atrasada incorretamente.
    """
    lote_pontual: list[dict[str, Any]] = [
        {
            "id": "TASK-PONT-001",
            "titulo": "Tarefa no limite do prazo",
            "prioridade": "ALTA",
            "data_criacao": "2026-03-01T08:00:00",
            "prazo": "2026-03-01T12:00:00",
            "data_conclusao": "2026-03-01T12:00:00",
            "status": "CONCLUIDA",
        }
    ]

    resultado: dict[str, Any] = analyze_tasks(tasks=lote_pontual)

    assert resultado["tempo_medio_conclusao_horas"] == 4.0
    assert resultado["taxa_atraso_percentual"] == 0.0
    assert resultado["metricas_por_prioridade"]["ALTA"]["taxa_atraso_percentual"] == 0.0


def test_todas_tarefas_concluidas_atrasadas() -> None:
    """Valida o cálculo quando 100% das tarefas concluídas estão atrasadas.

    Args:
        None.

    Returns:
        None.

    Raises:
        AssertionError: Se a taxa de atraso não atingir 100.0%.
    """
    lote_atrasado: list[dict[str, Any]] = [
        {
            "id": "TASK-ATR-001",
            "titulo": "Primeira tarefa atrasada",
            "prioridade": "MEDIA",
            "data_criacao": "2026-03-01T08:00:00",
            "prazo": "2026-03-01T10:00:00",
            "data_conclusao": "2026-03-01T11:00:00",
            "status": "CONCLUIDA",
        },
        {
            "id": "TASK-ATR-002",
            "titulo": "Segunda tarefa atrasada",
            "prioridade": "BAIXA",
            "data_criacao": "2026-03-01T08:00:00",
            "prazo": "2026-03-01T12:00:00",
            "data_conclusao": "2026-03-01T14:00:00",
            "status": "CONCLUIDA",
        },
    ]

    resultado: dict[str, Any] = analyze_tasks(tasks=lote_atrasado)

    assert resultado["total_concluidas"] == 2
    assert resultado["tempo_medio_conclusao_horas"] == 4.5  # (3.0 + 6.0) / 2 = 4.5
    assert resultado["taxa_atraso_percentual"] == 100.0
