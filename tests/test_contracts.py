from coi_contracts import (
    Event,
    EventType,
    Run,
    RunStatus,
    RuntimeFailure,
    Tier,
    WorkerRequest,
    WorkerResult,
    event_from_dict,
    new_id,
    run_from_dict,
    to_jsonable,
)


def test_run_worker_and_event_contracts_round_trip():
    run = Run(run_id=new_id("run"), task_type="repo.bootstrap", mandate="demo")
    request = WorkerRequest(
        request_id=new_id("worker"),
        run_id=run.run_id,
        tribe_id="reuben",
        tier=Tier.TIER_4,
        task_type=run.task_type,
        mandate=run.mandate,
        prompt="demo",
    )
    result = WorkerResult(
        request_id=request.request_id,
        run_id=run.run_id,
        worker_id="reuben:mock",
        status=RunStatus.SUCCEEDED,
        output={"summary": "ok", "confidence": 1.0},
    )
    event = Event(
        event_id=new_id("event"),
        run_id=run.run_id,
        event_type=EventType.WORKER_COMPLETED,
        message="done",
        payload={"result": to_jsonable(result)},
    )

    assert run_from_dict(to_jsonable(run)).run_id == run.run_id
    assert event_from_dict(to_jsonable(event)).event_type == EventType.WORKER_COMPLETED
    assert to_jsonable(RuntimeFailure("x", "y"))["code"] == "x"

