import sqlite3
from collections.abc import Callable, Mapping, Sequence

from .openrouter import (
    OpenRouterResponseError,
    request_grounded_answer,
    request_sql_proposal,
)
from .safe_sql import GeneratedQueryRejectedError, execute_validated_query


QUESTION_MAX_LENGTH = 500
Record = dict[str, str | int | float | None]
SQLRequester = Callable[[str], tuple[dict[str, str], str]]
AnswerRequester = Callable[
    [str, str, Sequence[Mapping[str, str | int | float | None]]],
    tuple[dict[str, str], str],
]


class InvalidInsightQuestionError(ValueError):
    pass


def _normalize_question(question: str) -> str:
    normalized = question.strip()
    if not normalized:
        raise InvalidInsightQuestionError("Enter a question about saved hotel data.")
    if len(normalized) > QUESTION_MAX_LENGTH:
        raise InvalidInsightQuestionError(
            f"Keep the saved hotel question to {QUESTION_MAX_LENGTH} characters or fewer."
        )
    return normalized


def _trace(
    *,
    model: str,
    proposed_sql: str | None,
    validation_status: str,
    query_executed: bool,
    records: list[Record],
    second_request_sent: bool,
) -> dict[str, object]:
    return {
        "model": model,
        "proposed_sql": proposed_sql,
        "validation_status": validation_status,
        "query_executed": query_executed,
        "retrieved_records": records,
        "second_request_sent": second_request_sent,
    }


def answer_saved_hotel_question(
    connection: sqlite3.Connection,
    question: str,
    *,
    sql_requester: SQLRequester = request_sql_proposal,
    answer_requester: AnswerRequester = request_grounded_answer,
) -> dict[str, object]:
    """Run the two-request RAG pipeline around one bounded read-only SQL query."""

    normalized_question = _normalize_question(question)
    proposal, model = sql_requester(normalized_question)
    if proposal["status"] == "insufficient_data":
        return {
            "status": "insufficient_data",
            "question": normalized_question,
            "count": 0,
            "records": [],
            "message": proposal["message"],
            "model": model,
            "trace": _trace(
                model=model,
                proposed_sql=None,
                validation_status="not_run",
                query_executed=False,
                records=[],
                second_request_sent=False,
            ),
        }

    proposed_sql = proposal["sql"]
    try:
        records = execute_validated_query(connection, proposed_sql)
    except GeneratedQueryRejectedError as error:
        return {
            "status": "rejected_query",
            "question": normalized_question,
            "count": 0,
            "records": [],
            "message": str(error),
            "model": model,
            "trace": _trace(
                model=model,
                proposed_sql=proposed_sql,
                validation_status="rejected",
                query_executed=False,
                records=[],
                second_request_sent=False,
            ),
        }

    outcome, answer_model = answer_requester(
        normalized_question,
        proposed_sql,
        records,
    )
    if answer_model != model:
        raise OpenRouterResponseError("answer_generation")

    response: dict[str, object] = {
        "status": outcome["status"],
        "question": normalized_question,
        "count": len(records),
        "records": records,
        "model": model,
        "trace": _trace(
            model=model,
            proposed_sql=proposed_sql,
            validation_status="passed",
            query_executed=True,
            records=records,
            second_request_sent=True,
        ),
    }
    if outcome["status"] == "answer":
        response["answer"] = outcome["answer"]
    else:
        response["message"] = outcome["message"]
    return response
