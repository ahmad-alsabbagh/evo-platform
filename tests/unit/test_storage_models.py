from evo_platform.storage.models import EvaluationRun


def test_evaluation_run_table_contract() -> None:
    columns = EvaluationRun.__table__.c
    assert columns["id"].primary_key
    assert columns["dataset_hash"].nullable is False
    assert columns["payload"].nullable is False
