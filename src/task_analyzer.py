"""Módulo de análise de tarefas corporativas e cálculo de métricas de produtividade.

Este módulo implementa o motor analítico determinístico TaskAnalyzer, responsável
por processar lotes de tarefas corporativas em memória, validando integridade estrutural
e cronológica, e consolidando indicadores de produtividade, atraso e distribuição por prioridade.
"""

from dataclasses import dataclass
from datetime import datetime
import logging
from typing import Any, Final

# Configuração do logger estruturado do módulo
logger: logging.Logger = logging.getLogger(__name__)

CAMPOS_OBRIGATORIOS: Final[frozenset[str]] = frozenset({
    "id",
    "titulo",
    "prioridade",
    "data_criacao",
    "prazo",
    "status",
})

PRIORIDADES_VALIDAS: Final[frozenset[str]] = frozenset({
    "BAIXA",
    "MEDIA",
    "ALTA",
})

STATUS_VALIDOS: Final[frozenset[str]] = frozenset({
    "PENDENTE",
    "CONCLUIDA",
})


class TaskValidationError(Exception):
    """Exceção customizada para erros de validação e inconsistências de tarefas.

    Utilizada quando há ausência de campos obrigatórios, valores inválidos,
    identificadores duplicados ou inconsistências cronológicas entre datas.

    Args:
        message: Descrição explicativa do erro de validação.

    Returns:
        None.

    Raises:
        None.
    """

    def __init__(self, message: str) -> None:
        """Inicializa a exceção com a mensagem de validação correspondente.

        Args:
            message: Mensagem descritiva do erro ocorrido.

        Returns:
            None.

        Raises:
            None.
        """
        super().__init__(message)
        self.message: str = message


@dataclass(frozen=True)
class _TaskData:
    """Representação imutável dos dados processados e validados de uma tarefa.

    Args:
        id: Identificador alfanumérico único da tarefa.
        titulo: Título descritivo da tarefa.
        prioridade: Prioridade da tarefa ('BAIXA', 'MEDIA', 'ALTA').
        status: Status de execução ('PENDENTE', 'CONCLUIDA').
        data_criacao: Data e hora de criação da tarefa.
        prazo: Data e hora limite para conclusão.
        data_conclusao: Data e hora em que a tarefa foi concluída, ou None se pendente.
        duracao_horas: Duração da execução em horas decimais se concluída, ou None.
        esta_atrasada: Indica se a conclusão ocorreu após o prazo estipulado.

    Returns:
        None.

    Raises:
        None.
    """

    id: str
    titulo: str
    prioridade: str
    status: str
    data_criacao: datetime
    prazo: datetime
    data_conclusao: datetime | None
    duracao_horas: float | None
    esta_atrasada: bool


def _validate_raw_task_structure(task: Any, seen_ids: set[str]) -> None:
    """Valida a integridade estrutural e os tipos básicos de um registro de tarefa.

    Args:
        task: Objeto a ser validado, esperado ser um dicionário com os campos obrigatórios.
        seen_ids: Conjunto contendo identificadores únicos já registrados no lote.

    Returns:
        None.

    Raises:
        TaskValidationError: Se o item não for um dicionário, se faltarem campos
            obrigatórios, se o id for duplicado/inválido, ou se prioridade/status
            possuírem valores não permitidos.
    """
    if not isinstance(task, dict):
        mensagem_erro: str = f"Cada tarefa deve ser um dicionário. Tipo recebido: {type(task).__name__}."
        logger.error(mensagem_erro)
        raise TaskValidationError(mensagem_erro)

    for campo in CAMPOS_OBRIGATORIOS:
        if campo not in task:
            mensagem_erro = f"Campo obrigatório ausente na tarefa: '{campo}'."
            logger.error(mensagem_erro)
            raise TaskValidationError(mensagem_erro)

    task_id: Any = task["id"]
    if not isinstance(task_id, str) or not task_id.strip():
        mensagem_erro = "O campo 'id' deve ser uma string não vazia."
        logger.error(mensagem_erro)
        raise TaskValidationError(mensagem_erro)

    if task_id in seen_ids:
        mensagem_erro = f"Identificador duplicado encontrado no lote: '{task_id}'."
        logger.error(mensagem_erro)
        raise TaskValidationError(mensagem_erro)
    seen_ids.add(task_id)

    titulo: Any = task["titulo"]
    if not isinstance(titulo, str):
        mensagem_erro = f"O campo 'titulo' da tarefa '{task_id}' deve ser uma string."
        logger.error(mensagem_erro)
        raise TaskValidationError(mensagem_erro)

    prioridade: Any = task["prioridade"]
    if prioridade not in PRIORIDADES_VALIDAS:
        mensagem_erro = (
            f"Prioridade inválida na tarefa '{task_id}': '{prioridade}'. "
            f"Valores permitidos: {sorted(PRIORIDADES_VALIDAS)}."
        )
        logger.error(mensagem_erro)
        raise TaskValidationError(mensagem_erro)

    status: Any = task["status"]
    if status not in STATUS_VALIDOS:
        mensagem_erro = (
            f"Status inválido na tarefa '{task_id}': '{status}'. "
            f"Valores permitidos: {sorted(STATUS_VALIDOS)}."
        )
        logger.error(mensagem_erro)
        raise TaskValidationError(mensagem_erro)

    data_conclusao: Any = task.get("data_conclusao")
    if data_conclusao is not None and not isinstance(data_conclusao, str):
        mensagem_erro = (
            f"O campo 'data_conclusao' da tarefa '{task_id}' deve ser uma string ISO 8601 ou None."
        )
        logger.error(mensagem_erro)
        raise TaskValidationError(mensagem_erro)


def _parse_iso_datetime(valor_data: str, nome_campo: str, task_id: str) -> datetime:
    """Converte uma string no formato ISO 8601 em objeto datetime nativo.

    Args:
        valor_data: String contendo a data e hora no padrão ISO 8601.
        nome_campo: Nome do campo avaliado para fins de rastreabilidade de erro.
        task_id: Identificador da tarefa para enriquecimento do log e da mensagem de erro.

    Returns:
        Instância de datetime correspondente à data fornecida.

    Raises:
        TaskValidationError: Se a string não estiver no formato ISO 8601 válido.
    """
    if not isinstance(valor_data, str):
        mensagem_erro: str = (
            f"O campo '{nome_campo}' da tarefa '{task_id}' deve ser uma string no padrão ISO 8601."
        )
        logger.error(mensagem_erro)
        raise TaskValidationError(mensagem_erro)

    try:
        data_convertida: datetime = datetime.fromisoformat(valor_data)
        return data_convertida
    except (ValueError, TypeError) as exc:
        mensagem_erro = (
            f"Formato de data inválido no campo '{nome_campo}' da tarefa '{task_id}': '{valor_data}'. "
            "Esperado padrão ISO 8601."
        )
        logger.error(mensagem_erro)
        raise TaskValidationError(mensagem_erro) from exc


def _validate_chronological_consistency(
    dt_criacao: datetime,
    dt_prazo: datetime,
    dt_conclusao: datetime | None,
    task_id: str,
) -> None:
    """Valida a consistência cronológica entre criação, prazo e conclusão.

    Args:
        dt_criacao: Data e hora de criação da tarefa.
        dt_prazo: Data e hora de prazo estipulado para a tarefa.
        dt_conclusao: Data e hora de conclusão da tarefa, se concluída, ou None.
        task_id: Identificador da tarefa para contextualização em logs e exceções.

    Returns:
        None.

    Raises:
        TaskValidationError: Se o prazo for anterior à data de criação, se a data
            de conclusão for anterior à data de criação, ou se houver incompatibilidade
            de fuso horário.
    """
    try:
        if dt_prazo < dt_criacao:
            mensagem_erro_prazo: str = (
                f"O prazo da tarefa '{task_id}' não pode ser anterior à data de criação."
            )
            logger.error(mensagem_erro_prazo)
            raise TaskValidationError("O prazo não pode ser anterior à data de criação.")

        if dt_conclusao is not None and dt_conclusao < dt_criacao:
            mensagem_erro_conclusao: str = (
                f"Data de conclusão da tarefa '{task_id}' é anterior à data de criação."
            )
            logger.error(mensagem_erro_conclusao)
            raise TaskValidationError("Data de conclusão não pode ser anterior à data de criação.")
    except TypeError as exc:
        mensagem_erro_fuso: str = (
            f"Incompatibilidade entre fusos horários das datas na tarefa '{task_id}'."
        )
        logger.error(mensagem_erro_fuso)
        raise TaskValidationError("Incompatibilidade de fuso horário entre as datas.") from exc


def _calculate_task_duration_and_delay(
    status: str,
    dt_criacao: datetime,
    dt_prazo: datetime,
    dt_conclusao: datetime | None,
) -> tuple[float | None, bool]:
    """Calcula a duração em horas e o status de atraso de uma tarefa individual.

    Apenas tarefas com status 'CONCLUIDA' e data de conclusão preenchida
    possuem cálculo de duração e aferição de atraso.

    Args:
        status: Situação da tarefa ('PENDENTE' ou 'CONCLUIDA').
        dt_criacao: Objeto datetime de criação da tarefa.
        dt_prazo: Objeto datetime do prazo limite estipulado.
        dt_conclusao: Objeto datetime da conclusão ou None.

    Returns:
        Tupla contendo a duração em horas decimais (ou None) e booleano indicando atraso.

    Raises:
        TaskValidationError: Se houver divergência de fuso horário durante comparação.
    """
    if status == "CONCLUIDA" and dt_conclusao is not None:
        try:
            diferenca_segundos: float = (dt_conclusao - dt_criacao).total_seconds()
            duracao_horas: float = diferenca_segundos / 3600.0
            esta_atrasada: bool = dt_conclusao > dt_prazo
            return duracao_horas, esta_atrasada
        except TypeError as exc:
            mensagem_erro: str = "Incompatibilidade de fuso horário ao comparar conclusão e prazo."
            logger.error(mensagem_erro)
            raise TaskValidationError(mensagem_erro) from exc

    return None, False


def _process_single_task(task: dict, seen_ids: set[str]) -> _TaskData:
    """Processa, valida e extrai os dados estruturados de um único registro de tarefa.

    Args:
        task: Dicionário contendo os dados brutos da tarefa.
        seen_ids: Conjunto de identificadores de tarefas já validados para unicidade.

    Returns:
        Objeto imutável _TaskData contendo os dados validados e computados.

    Raises:
        TaskValidationError: Se ocorrer qualquer violação de integridade ou cronologia.
    """
    _validate_raw_task_structure(task=task, seen_ids=seen_ids)

    task_id: str = str(task["id"])
    titulo: str = str(task["titulo"])
    prioridade: str = str(task["prioridade"])
    status: str = str(task["status"])

    dt_criacao: datetime = _parse_iso_datetime(
        valor_data=task["data_criacao"],
        nome_campo="data_criacao",
        task_id=task_id,
    )
    dt_prazo: datetime = _parse_iso_datetime(
        valor_data=task["prazo"],
        nome_campo="prazo",
        task_id=task_id,
    )

    data_conclusao_raw: Any = task.get("data_conclusao")
    dt_conclusao: datetime | None = None
    if data_conclusao_raw is not None:
        dt_conclusao = _parse_iso_datetime(
            valor_data=data_conclusao_raw,
            nome_campo="data_conclusao",
            task_id=task_id,
        )

    _validate_chronological_consistency(
        dt_criacao=dt_criacao,
        dt_prazo=dt_prazo,
        dt_conclusao=dt_conclusao,
        task_id=task_id,
    )

    resultado_duracao_atraso: tuple[float | None, bool] = (
        _calculate_task_duration_and_delay(
            status=status,
            dt_criacao=dt_criacao,
            dt_prazo=dt_prazo,
            dt_conclusao=dt_conclusao,
        )
    )
    duracao_horas: float | None = resultado_duracao_atraso[0]
    esta_atrasada: bool = resultado_duracao_atraso[1]

    logger.debug(
        "Tarefa '%s' validada com sucesso: prioridade=%s, status=%s, duracao=%s, atrasada=%s.",
        task_id,
        prioridade,
        status,
        duracao_horas,
        esta_atrasada,
    )

    return _TaskData(
        id=task_id,
        titulo=titulo,
        prioridade=prioridade,
        status=status,
        data_criacao=dt_criacao,
        prazo=dt_prazo,
        data_conclusao=dt_conclusao,
        duracao_horas=duracao_horas,
        esta_atrasada=esta_atrasada,
    )


def _calculate_mean_duration(duracoes: list[float]) -> float:
    """Calcula a média aritmética das durações em horas com duas casas decimais.

    Prevenção de divisão por zero: caso a lista esteja vazia, retorna 0.0.

    Args:
        duracoes: Lista de durações em horas decimais de tarefas concluídas.

    Returns:
        Média das durações arredondada em duas casas decimais ou 0.0 se vazia.

    Raises:
        None.
    """
    total_itens: int = len(duracoes)
    if total_itens == 0:
        return 0.0

    soma_duracoes: float = sum(duracoes)
    media: float = soma_duracoes / total_itens
    return round(media, 2)


def _calculate_delay_rate(total_concluidas: int, total_atrasadas: int) -> float:
    """Calcula o percentual de tarefas com atraso em relação ao total de concluídas.

    Prevenção de divisão por zero: caso não haja concluídas, retorna 0.0.

    Args:
        total_concluidas: Quantidade total de tarefas concluídas elegíveis.
        total_atrasadas: Quantidade de tarefas concluídas que extrapolaram o prazo.

    Returns:
        Taxa percentual de atraso (0.0 a 100.0) arredondada em duas casas decimais.

    Raises:
        None.
    """
    if total_concluidas == 0:
        return 0.0

    percentual: float = (total_atrasadas / total_concluidas) * 100.0
    return round(percentual, 2)


def _aggregate_priority_metrics(tasks_data: list[_TaskData]) -> dict[str, dict[str, Any]]:
    """Calcula indicadores consolidados para cada prioridade ('BAIXA', 'MEDIA', 'ALTA').

    Args:
        tasks_data: Lista de instâncias _TaskData validadas.

    Returns:
        Dicionário agrupado por prioridade com total, tempo médio e taxa de atraso.

    Raises:
        None.
    """
    metricas_agrupadas: dict[str, dict[str, Any]] = {}
    prioridades_ordenadas: list[str] = ["BAIXA", "MEDIA", "ALTA"]

    for prioridade in prioridades_ordenadas:
        tarefas_da_prioridade: list[_TaskData] = [
            t for t in tasks_data if t.prioridade == prioridade
        ]
        total_tarefas_prioridade: int = len(tarefas_da_prioridade)

        tarefas_concluidas: list[_TaskData] = [
            t
            for t in tarefas_da_prioridade
            if t.status == "CONCLUIDA" and t.data_conclusao is not None
        ]
        total_concluidas_prioridade: int = len(tarefas_concluidas)

        duracoes_prioridade: list[float] = [
            t.duracao_horas
            for t in tarefas_concluidas
            if t.duracao_horas is not None
        ]
        tempo_medio_prioridade: float = _calculate_mean_duration(duracoes=duracoes_prioridade)

        total_atrasadas_prioridade: int = sum(
            1 for t in tarefas_concluidas if t.esta_atrasada
        )
        taxa_atraso_prioridade: float = _calculate_delay_rate(
            total_concluidas=total_concluidas_prioridade,
            total_atrasadas=total_atrasadas_prioridade,
        )

        metricas_agrupadas[prioridade] = {
            "total": total_tarefas_prioridade,
            "tempo_medio_horas": tempo_medio_prioridade,
            "taxa_atraso_percentual": taxa_atraso_prioridade,
        }

    return metricas_agrupadas


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
    logger.info("Iniciando análise de lote de tarefas.")

    if not isinstance(tasks, list):
        mensagem_erro_lista: str = (
            f"O parâmetro 'tasks' deve ser uma lista de dicionários. Recebido: {type(tasks).__name__}."
        )
        logger.error(mensagem_erro_lista)
        raise TaskValidationError(mensagem_erro_lista)

    total_tarefas_bruto: int = len(tasks)
    if total_tarefas_bruto == 0:
        logger.info("Lote de tarefas vazio recebido. Retornando métricas zeradas.")
        metricas_vazias_prioridade: dict[str, dict[str, Any]] = {
            "BAIXA": {"total": 0, "tempo_medio_horas": 0.0, "taxa_atraso_percentual": 0.0},
            "MEDIA": {"total": 0, "tempo_medio_horas": 0.0, "taxa_atraso_percentual": 0.0},
            "ALTA": {"total": 0, "tempo_medio_horas": 0.0, "taxa_atraso_percentual": 0.0},
        }
        return {
            "total_tarefas": 0,
            "total_concluidas": 0,
            "total_pendentes": 0,
            "tempo_medio_conclusao_horas": 0.0,
            "taxa_atraso_percentual": 0.0,
            "metricas_por_prioridade": metricas_vazias_prioridade,
        }

    seen_ids: set[str] = set()
    tasks_processadas: list[_TaskData] = []

    for task_item in tasks:
        task_data: _TaskData = _process_single_task(task=task_item, seen_ids=seen_ids)
        tasks_processadas.append(task_data)

    total_concluidas: int = sum(
        1 for t in tasks_processadas if t.status == "CONCLUIDA"
    )
    total_pendentes: int = sum(
        1 for t in tasks_processadas if t.status == "PENDENTE"
    )

    tarefas_concluidas_elegiveis: list[_TaskData] = [
        t for t in tasks_processadas if t.status == "CONCLUIDA" and t.data_conclusao is not None
    ]
    total_concluidas_elegiveis: int = len(tarefas_concluidas_elegiveis)

    duracoes_concluidas: list[float] = [
        t.duracao_horas
        for t in tarefas_concluidas_elegiveis
        if t.duracao_horas is not None
    ]
    tempo_medio_geral: float = _calculate_mean_duration(duracoes=duracoes_concluidas)

    total_atrasadas_geral: int = sum(
        1 for t in tarefas_concluidas_elegiveis if t.esta_atrasada
    )
    taxa_atraso_geral: float = _calculate_delay_rate(
        total_concluidas=total_concluidas_elegiveis,
        total_atrasadas=total_atrasadas_geral,
    )

    metricas_prioridade: dict[str, dict[str, Any]] = _aggregate_priority_metrics(
        tasks_data=tasks_processadas
    )

    logger.info(
        "Análise concluída com sucesso: total=%d, concluidas=%d, pendentes=%d, "
        "tempo_medio=%.2f, taxa_atraso=%.2f%%.",
        total_tarefas_bruto,
        total_concluidas,
        total_pendentes,
        tempo_medio_geral,
        taxa_atraso_geral,
    )

    resultado_consolidado: dict[str, Any] = {
        "total_tarefas": total_tarefas_bruto,
        "total_concluidas": total_concluidas,
        "total_pendentes": total_pendentes,
        "tempo_medio_conclusao_horas": tempo_medio_geral,
        "taxa_atraso_percentual": taxa_atraso_geral,
        "metricas_por_prioridade": metricas_prioridade,
    }

    return resultado_consolidado
