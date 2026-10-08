import json
import sqlite3
from contextlib import closing
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from app import openrouter
from app.database import DATA_DIRECTORY, connect_database, initialize_database
from app.hotel_insights import answer_saved_hotel_question
from app.openrouter import OpenRouterResponseError
from app.safe_sql import GeneratedQueryRejectedError, execute_validated_query


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "revised_part2_fixed_sample.json"
OPENROUTER_TEST_KEY = "openrouter-test-key-never-return"
OPENROUTER_TEST_MODEL = "nvidia/class-nemotron:free"


class StubResponse:
    def __init__(self, payload: object, *, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code
        self.is_success = 200 <= status_code < 300

    def json(self) -> object:
        if isinstance(self._payload, ValueError):
            raise self._payload
        return self._payload


def provider_payload(content: str) -> dict[str, object]:
    return {"choices": [{"message": {"content": content}}]}


def load_fixed_sample() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def seed_fixed_sample(connection: sqlite3.Connection) -> dict[str, object]:
    sample = load_fixed_sample()
    for hotel in sample["hotels"]:
        cursor = connection.execute(
            """
            INSERT INTO saved_hotels (
                provider_place_id, hotel_name, address, latitude, longitude
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                hotel["provider_place_id"],
                hotel["hotel_name"],
                hotel["address"],
                hotel["latitude"],
                hotel["longitude"],
            ),
        )
        saved_hotel_id = cursor.lastrowid
        connection.executemany(
            "INSERT INTO saved_hotel_zips (saved_hotel_id, searched_zip) VALUES (?, ?)",
            [(saved_hotel_id, zip_code) for zip_code in hotel["searched_zips"]],
        )
        connection.executemany(
            """
            INSERT INTO demo_hotel_nights (
                saved_hotel_id, night_date, nightly_rate_cents, rooms_available
            ) VALUES (?, ?, ?, ?)
            """,
            [
                (saved_hotel_id, night_date, rate, rooms)
                for night_date, rate, rooms in hotel["nights"]
            ],
        )
    connection.commit()
    return sample


def configure_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", OPENROUTER_TEST_KEY)
    monkeypatch.setenv("OPENROUTER_MODEL", OPENROUTER_TEST_MODEL)


def application_snapshot(connection: sqlite3.Connection) -> dict[str, list[tuple]]:
    tables = (
        "hotels",
        "users",
        "trips",
        "bookings",
        "booking_id_sequence",
        "seed_metadata",
        "saved_hotels",
        "saved_hotel_zips",
        "demo_hotel_nights",
    )
    return {
        table: [tuple(row) for row in connection.execute(f"SELECT * FROM {table}")]
        for table in tables
    }


def test_fixed_sample_two_requests_wrap_validated_sql_and_exact_records(
    connection: sqlite3.Connection,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sample = seed_fixed_sample(connection)
    configure_provider(monkeypatch)
    events: list[str] = []
    requests: list[dict[str, object]] = []

    def trace(statement: str) -> None:
        if "AS generated_result" in statement:
            events.append("validated_sql_execution")

    def fake_post(_url, **kwargs):
        requests.append(kwargs["json"])
        if len(requests) == 1:
            events.append("model_request_1")
            return StubResponse(
                provider_payload(
                    json.dumps({"status": "query", "sql": sample["sql"]})
                )
            )
        events.append("model_request_2")
        return StubResponse(
            provider_payload(
                json.dumps(
                    {"status": "answer", "answer": sample["expected_answer"]}
                )
            )
        )

    connection.set_trace_callback(trace)
    monkeypatch.setattr(openrouter.httpx, "post", fake_post)
    result = answer_saved_hotel_question(connection, sample["question"])
    connection.set_trace_callback(None)

    assert events == [
        "model_request_1",
        "validated_sql_execution",
        "model_request_2",
    ]
    assert len(requests) == 2
    assert requests[0]["model"] == OPENROUTER_TEST_MODEL
    assert requests[1]["model"] == OPENROUTER_TEST_MODEL
    assert result["status"] == "answer"
    assert result["records"] == sample["expected_records"]
    assert result["answer"] == sample["expected_answer"]
    assert result["trace"] == {
        "model": OPENROUTER_TEST_MODEL,
        "proposed_sql": sample["sql"],
        "validation_status": "passed",
        "query_executed": True,
        "retrieved_records": sample["expected_records"],
        "second_request_sent": True,
    }
    expected_json = json.dumps(
        sample["expected_records"],
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    second_user_message = requests[1]["messages"][1]["content"]
    assert f"RETRIEVED_RECORDS:\n{expected_json}" in second_user_message
    assert OPENROUTER_TEST_KEY not in json.dumps(result)


def test_fixed_query_covers_checkout_missing_sold_out_rooms_totals_zip_and_joins(
    connection: sqlite3.Connection,
) -> None:
    sample = seed_fixed_sample(connection)

    records = execute_validated_query(connection, sample["sql"])

    assert records == sample["expected_records"]
    record = records[0]
    assert record["searched_zip"] == "02108"
    assert record["stay_nights"] == 3
    assert record["minimum_rooms_available"] == 2
    assert record["total_cost_cents"] == 67_000
    assert connection.execute(
        "SELECT COUNT(*) FROM saved_hotel_zips WHERE saved_hotel_id = "
        "(SELECT saved_hotel_id FROM saved_hotels WHERE provider_place_id = ?) ",
        ("fixture-eligible",),
    ).fetchone()[0] == 2
    assert {
        "fixture-missing-middle",
        "fixture-sold-out",
        "fixture-insufficient-rooms",
        "fixture-other-zip",
    }.isdisjoint({row["provider_place_id"] for row in records})


def test_out_of_coverage_is_insufficient_without_sql_or_second_request(
    connection: sqlite3.Connection,
) -> None:
    sample = seed_fixed_sample(connection)
    calls: list[str] = []

    def sql_requester(_question):
        calls.append("first")
        return (
            {
                "status": "insufficient_data",
                "message": "The requested November stay is outside October 10-14 coverage.",
            },
            OPENROUTER_TEST_MODEL,
        )

    def answer_requester(*_args):
        calls.append("second")
        raise AssertionError("The second request must not run")

    result = answer_saved_hotel_question(
        connection,
        sample["out_of_coverage_question"],
        sql_requester=sql_requester,
        answer_requester=answer_requester,
    )

    assert calls == ["first"]
    assert result["status"] == "insufficient_data"
    assert result["trace"]["query_executed"] is False
    assert result["trace"]["second_request_sent"] is False


def test_successful_empty_query_reaches_second_request_as_no_matches(
    connection: sqlite3.Connection,
) -> None:
    seed_fixed_sample(connection)
    calls: list[str] = []

    def sql_requester(_question):
        calls.append("first")
        return (
            {
                "status": "query",
                "sql": (
                    "SELECT provider_place_id, hotel_name FROM saved_hotels "
                    "WHERE provider_place_id = 'not-present' LIMIT 10"
                ),
            },
            OPENROUTER_TEST_MODEL,
        )

    def answer_requester(_question, _sql, records):
        calls.append("second")
        assert records == []
        return (
            {
                "status": "no_matches",
                "message": "No saved hotels match the requested conditions.",
            },
            OPENROUTER_TEST_MODEL,
        )

    result = answer_saved_hotel_question(
        connection,
        "Find a provider that is not present.",
        sql_requester=sql_requester,
        answer_requester=answer_requester,
    )

    assert calls == ["first", "second"]
    assert result["status"] == "no_matches"
    assert result["count"] == 0
    assert result["trace"]["query_executed"] is True
    assert result["trace"]["second_request_sent"] is True


@pytest.mark.parametrize(
    ("sql", "outcome"),
    [
        (
            "SELECT provider_place_id FROM saved_hotels WHERE 0 LIMIT 5",
            {"status": "answer", "answer": "A hotel exists."},
        ),
        (
            "SELECT provider_place_id FROM saved_hotels LIMIT 5",
            {
                "status": "no_matches",
                "message": "No saved hotels match the requested conditions.",
            },
        ),
    ],
)
def test_answer_status_must_agree_with_retrieved_records(
    connection: sqlite3.Connection,
    sql: str,
    outcome: dict[str, str],
) -> None:
    seed_fixed_sample(connection)

    def sql_requester(_question):
        return {"status": "query", "sql": sql}, OPENROUTER_TEST_MODEL

    def answer_requester(_question, _sql, _records):
        return outcome, OPENROUTER_TEST_MODEL

    with pytest.raises(OpenRouterResponseError) as error:
        answer_saved_hotel_question(
            connection,
            "Find saved hotels.",
            sql_requester=sql_requester,
            answer_requester=answer_requester,
        )

    assert error.value.stage == "answer_generation"


@pytest.mark.parametrize(
    "disallowed_sql",
    [
        "DELETE FROM saved_hotels",
        "SELECT * FROM saved_hotels; DELETE FROM saved_hotels",
        "SELECT * FROM users",
        "PRAGMA table_info(saved_hotels)",
        "SELECT load_extension('anything') FROM saved_hotels",
        "ATTACH DATABASE 'other.db' AS other",
    ],
)
def test_disallowed_sql_is_rejected_without_execution_second_call_or_changes(
    connection: sqlite3.Connection,
    disallowed_sql: str,
) -> None:
    seed_fixed_sample(connection)
    before = application_snapshot(connection)
    second_calls = 0

    def sql_requester(_question):
        return {"status": "query", "sql": disallowed_sql}, OPENROUTER_TEST_MODEL

    def answer_requester(*_args):
        nonlocal second_calls
        second_calls += 1
        raise AssertionError("Rejected SQL must not reach request two")

    result = answer_saved_hotel_question(
        connection,
        "Use a labeled rejected-query fixture.",
        sql_requester=sql_requester,
        answer_requester=answer_requester,
    )

    assert result["status"] == "rejected_query"
    assert result["trace"]["validation_status"] == "rejected"
    assert result["trace"]["query_executed"] is False
    assert result["trace"]["second_request_sent"] is False
    assert second_calls == 0
    assert application_snapshot(connection) == before


def test_result_and_query_work_limits_are_enforced(
    connection: sqlite3.Connection,
) -> None:
    connection.executemany(
        """
        INSERT INTO saved_hotels (
            provider_place_id, hotel_name, address, latitude, longitude
        ) VALUES (?, ?, ?, 0, 0)
        """,
        [(f"limit-{index:03d}", f"Limit Hotel {index:03d}", "Fixture") for index in range(60)],
    )
    connection.commit()

    with pytest.raises(GeneratedQueryRejectedError, match="exceeded 50 rows"):
        execute_validated_query(
            connection,
            "SELECT provider_place_id FROM saved_hotels ORDER BY provider_place_id",
        )

    with pytest.raises(GeneratedQueryRejectedError, match="work limit"):
        execute_validated_query(
            connection,
            "SELECT COUNT(*) FROM saved_hotels AS a "
            "CROSS JOIN saved_hotels AS b CROSS JOIN saved_hotels AS c "
            "CROSS JOIN saved_hotels AS d",
        )


@pytest.mark.parametrize(
    "content",
    [
        "not JSON",
        json.dumps({"status": "query"}),
        json.dumps({"status": "unknown", "sql": "SELECT * FROM saved_hotels"}),
    ],
)
def test_malformed_first_response_causes_no_sql_or_second_model_call(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    content: str,
) -> None:
    configure_provider(monkeypatch)
    calls = 0

    def fake_post(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        return StubResponse(provider_payload(content))

    monkeypatch.setattr(openrouter.httpx, "post", fake_post)
    response = client.post("/api/hotel-insights", json={"question": "Find saved hotels."})

    assert response.status_code == 502
    assert response.json() == {"detail": "OpenRouter SQL generation failed."}
    assert calls == 1


def test_malformed_or_failed_second_call_is_answer_generation_error(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_provider(monkeypatch)
    responses = iter(
        [
            StubResponse(
                provider_payload(
                    json.dumps(
                        {
                            "status": "query",
                            "sql": "SELECT provider_place_id FROM saved_hotels LIMIT 5",
                        }
                    )
                )
            ),
            StubResponse(provider_payload("not JSON")),
        ]
    )
    monkeypatch.setattr(openrouter.httpx, "post", lambda *_args, **_kwargs: next(responses))

    response = client.post("/api/hotel-insights", json={"question": "Find saved hotels."})

    assert response.status_code == 502
    assert response.json() == {"detail": "OpenRouter answer generation failed."}


@pytest.mark.parametrize(
    ("limited_stage", "expected_detail", "expected_calls"),
    [
        ("sql_generation", "OpenRouter SQL generation is temporarily rate limited.", 1),
        ("answer_generation", "OpenRouter answer generation is temporarily rate limited.", 2),
    ],
)
def test_simulated_rate_limits_do_not_use_live_quota(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    limited_stage: str,
    expected_detail: str,
    expected_calls: int,
) -> None:
    configure_provider(monkeypatch)
    calls = 0

    def fake_post(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        if limited_stage == "sql_generation" or calls == 2:
            return StubResponse({}, status_code=429)
        return StubResponse(
            provider_payload(
                json.dumps(
                    {
                        "status": "query",
                        "sql": "SELECT provider_place_id FROM saved_hotels LIMIT 5",
                    }
                )
            )
        )

    monkeypatch.setattr(openrouter.httpx, "post", fake_post)
    response = client.post("/api/hotel-insights", json={"question": "Find saved hotels."})

    assert response.status_code == 429
    assert response.json() == {"detail": expected_detail}
    assert calls == expected_calls


@pytest.mark.parametrize("model", [None, "nvidia/not-free", "openrouter/free"])
def test_missing_or_disallowed_model_is_rejected_before_network_use(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    model: str | None,
) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", OPENROUTER_TEST_KEY)
    if model is None:
        monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
    else:
        monkeypatch.setenv("OPENROUTER_MODEL", model)
    monkeypatch.setattr(
        openrouter.httpx,
        "post",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("Network must not be used")
        ),
    )

    response = client.post("/api/hotel-insights", json={"question": "Find hotels."})

    assert response.status_code == 503
    assert response.json() == {
        "detail": "OpenRouter insights service is not configured."
    }


def test_provider_timeout_and_network_errors_are_sanitized_by_stage(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_provider(monkeypatch)
    request = httpx.Request("POST", openrouter.OPENROUTER_CHAT_URL)
    monkeypatch.setattr(
        openrouter.httpx,
        "post",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(httpx.TimeoutException("secret", request=request)),
    )
    timeout = client.post("/api/hotel-insights", json={"question": "Find hotels."})
    assert timeout.status_code == 504
    assert timeout.json() == {"detail": "OpenRouter SQL generation timed out."}

    monkeypatch.setattr(
        openrouter.httpx,
        "post",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(httpx.ConnectError("secret", request=request)),
    )
    network = client.post("/api/hotel-insights", json={"question": "Find hotels."})
    assert network.status_code == 502
    assert network.json() == {"detail": "OpenRouter SQL generation failed."}


def test_question_validation_happens_before_provider_use(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        openrouter.httpx,
        "post",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("Provider must not be used")
        ),
    )

    blank = client.post("/api/hotel-insights", json={"question": "   "})
    too_long = client.post("/api/hotel-insights", json={"question": "x" * 501})

    assert blank.status_code == 400
    assert blank.json()["detail"] == "Enter a question about saved hotel data."
    assert too_long.status_code == 400
    assert "500 characters" in too_long.json()["detail"]


def test_health_and_insight_responses_never_expose_credentials(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_provider(monkeypatch)
    monkeypatch.setattr(
        openrouter.httpx,
        "post",
        lambda *_args, **_kwargs: StubResponse({}, status_code=429),
    )

    health = client.get("/api/health")
    insight = client.post("/api/hotel-insights", json={"question": "Find hotels."})

    assert health.status_code == 200
    assert insight.status_code == 429
    assert OPENROUTER_TEST_KEY not in health.text
    assert OPENROUTER_TEST_KEY not in insight.text
    assert OPENROUTER_TEST_MODEL not in health.text


def test_fixture_mutations_use_only_the_temporary_test_database(
    database_path: Path,
) -> None:
    initialize_database(database_path, DATA_DIRECTORY)
    with closing(connect_database(database_path)) as connection:
        seed_fixed_sample(connection)
        assert connection.execute("SELECT COUNT(*) FROM saved_hotels").fetchone()[0] == 5
