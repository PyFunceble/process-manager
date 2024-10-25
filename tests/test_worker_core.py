import multiprocessing
import time
from unittest.mock import MagicMock

import pytest

from PyFunceble.ext.process_manager.worker.core import WorkerCore


def mock_target(consumed):
    return f"processed_{consumed}"


def mock_target_exception(consumed):
    raise RuntimeError(f"Test Exception: {consumed}")


def mock_target_eoferror(consumed):
    raise EOFError(f"Test Exception: {consumed}")


@pytest.fixture
def worker_core():
    global_exit_event = multiprocessing.Event()
    worker = WorkerCore(
        name="test_worker",
        global_exit_event=global_exit_event,
        input_queue=multiprocessing.Queue(),
        output_queues=[multiprocessing.Queue()],
        configuration_queue=multiprocessing.Queue(),
        daemon=True,
    )

    return worker


@pytest.fixture
def started_worker_core(worker_core):
    worker_core.target = mock_target
    worker_core.start()

    return worker_core


def test_worker_initialization(worker_core):
    assert worker_core.name == "test_worker"
    assert worker_core.global_exit_event is not None
    assert worker_core.input_queue is not None
    assert worker_core.output_queues is not None
    assert worker_core.configuration_queue is not None
    assert worker_core.daemon is True


def test_extra_args():
    process_manager = WorkerCore(
        name="test_worker", foobar="barfoo", global_exit_event=multiprocessing.Event()
    )
    assert process_manager.name == "test_worker"
    assert process_manager.foobar == "barfoo"


def test_extra_args_not_existing():
    process_manager = WorkerCore(
        name="test_worker", foobar="barfoo", global_exit_event=multiprocessing.Event()
    )

    with pytest.raises(AttributeError):
        _ = process_manager.barfoo


def test_worker_name_setter(worker_core):
    worker_core.name = "new_name"
    assert worker_core.name == "new_name"

    with pytest.raises(TypeError):
        worker_core.name = 123


def test_worker_sharing_delay_setter(worker_core):
    worker_core.sharing_delay = 5.0
    assert worker_core.sharing_delay == 5.0

    with pytest.raises(TypeError):
        worker_core.sharing_delay = "invalid"


def test_worker_shutdown_delay_setter(worker_core):
    worker_core.shutdown_delay = 5.0
    assert worker_core.shutdown_delay == 5.0

    with pytest.raises(TypeError):
        worker_core.shutdown_delay = "invalid"


def test_worker_fetch_delay_setter(worker_core):
    worker_core.fetch_delay = 5.0
    assert worker_core.fetch_delay == 5.0

    with pytest.raises(TypeError):
        worker_core.fetch_delay = "invalid"


def test_exception_exchange(worker_core):
    exception_message = (RuntimeError("Test Exception"), "Test exception")
    worker_core._child_connection.send(exception_message)

    assert isinstance(worker_core.exception[0], RuntimeError)


def test_exception_exchange_no_exception(worker_core):
    assert worker_core.exception is None


def test_push_to_input_queue(worker_core):
    worker_core.push_to_input_queue("test_data")

    assert worker_core.input_queue.get(timeout=3) == ("test_worker", None, "test_data")
    assert worker_core.input_queue.empty()


def test_push_to_input_queue_with_source_worker(worker_core):
    worker_core.push_to_input_queue("test_data", source_worker="source_worker")

    assert worker_core.input_queue.get(timeout=3) == (
        "source_worker",
        None,
        "test_data",
    )
    assert worker_core.input_queue.empty()


def test_push_to_input_queue_with_destination_worker(worker_core):
    worker_core.push_to_input_queue(
        "test_data", destination_worker="destination_worker"
    )

    assert worker_core.input_queue.get(timeout=3) == (
        "test_worker",
        "destination_worker",
        "test_data",
    )
    assert worker_core.input_queue.empty()


def test_push_to_output_queues(worker_core):
    worker_core.push_to_output_queues("test_data")

    for output_queue in worker_core.output_queues:
        assert output_queue.get(timeout=3) == ("test_worker", None, "test_data")
        assert output_queue.empty()


def test_push_to_output_queues_with_source_worker(worker_core):
    worker_core.push_to_output_queues("test_data", source_worker="source_worker")

    for output_queue in worker_core.output_queues:
        assert output_queue.get(timeout=3) == ("source_worker", None, "test_data")
        assert output_queue.empty()


def test_push_to_output_queues_with_destination_worker(worker_core):
    worker_core.push_to_output_queues(
        "test_data", destination_worker="destination_worker"
    )

    for output_queue in worker_core.output_queues:
        assert output_queue.get(timeout=3) == (
            "test_worker",
            "destination_worker",
            "test_data",
        )
        assert output_queue.empty()


def test_push_to_configuration_queue(worker_core):
    worker_core.push_to_configuration_queue("test_data")

    assert worker_core.configuration_queue.get(timeout=3) == (
        "test_worker",
        None,
        "test_data",
    )
    assert worker_core.configuration_queue.empty()


def test_push_to_configuration_queue_with_source_worker(worker_core):
    worker_core.push_to_configuration_queue("test_data", source_worker="source_worker")

    assert worker_core.configuration_queue.get(timeout=3) == (
        "source_worker",
        None,
        "test_data",
    )
    assert worker_core.configuration_queue.empty()


def test_push_to_configuration_queue_with_destination_worker(worker_core):
    worker_core.push_to_configuration_queue(
        "test_data", destination_worker="destination_worker"
    )

    assert worker_core.configuration_queue.get(timeout=3) == (
        "test_worker",
        "destination_worker",
        "test_data",
    )
    assert worker_core.configuration_queue.empty()


def test_target(worker_core):
    assert worker_core.target("test_data") == "test_data"


def test_share_message(worker_core):
    worker_core.share_message("test_message")

    assert worker_core.input_queue.get(timeout=3) == (
        "test_worker",
        None,
        "test_message",
    )
    assert worker_core.input_queue.empty()

    for output_queue in worker_core.output_queues:
        assert output_queue.get(timeout=3) == ("test_worker", None, "test_message")
        assert output_queue.empty()


def test_share_message_with_delay(worker_core):
    time.sleep = MagicMock()

    worker_core.sharing_delay = 5.0
    worker_core.share_message("test_message", apply_delay=True)

    time.sleep.assert_called_once_with(5.0)

    assert worker_core.input_queue.get(timeout=3) == (
        "test_worker",
        None,
        "test_message",
    )
    assert worker_core.input_queue.empty()

    for output_queue in worker_core.output_queues:
        assert output_queue.get(timeout=3) == ("test_worker", None, "test_message")
        assert output_queue.empty()


def test_share_message_output_queue_only(worker_core):
    worker_core.share_message("test_message", output_queue_only=True)

    assert worker_core.input_queue.empty()

    for output_queue in worker_core.output_queues:
        assert output_queue.get(timeout=3) == ("test_worker", None, "test_message")
        assert output_queue.empty()


def test_share_message_overall(worker_core):
    worker_core.concurrent_workers_names = ["test_worker_2"]
    worker_core.share_message("test_message", overall=True)

    assert worker_core.input_queue.get(timeout=3) == (
        "test_worker",
        "test_worker",
        "test_message",
    )
    assert worker_core.input_queue.get(timeout=3) == (
        "test_worker",
        "test_worker_2",
        "test_message",
    )
    assert worker_core.input_queue.empty()

    for output_queue in worker_core.output_queues:
        assert output_queue.get(timeout=3) == ("test_worker", None, "test_message")
        assert output_queue.empty()


def test_share_message_overall_with_delay(worker_core):
    time.sleep = MagicMock()

    worker_core.sharing_delay = 5.0
    worker_core.concurrent_workers_names = ["test_worker_2"]
    worker_core.share_message("test_message", overall=True, apply_delay=True)

    time.sleep.assert_called_with(5.0)

    assert worker_core.input_queue.get(timeout=3) == (
        "test_worker",
        "test_worker",
        "test_message",
    )
    assert worker_core.input_queue.get(timeout=3) == (
        "test_worker",
        "test_worker_2",
        "test_message",
    )
    assert worker_core.input_queue.empty()

    for output_queue in worker_core.output_queues:
        assert output_queue.get(timeout=3) == ("test_worker", None, "test_message")
        assert output_queue.empty()


def test_share_message_overall_with_explicit_dependencies(worker_core):
    worker_core.concurrent_workers_names = ["test_worker_2"]
    worker_core.dependent_workers_names = ["test_worker_3"]

    worker_core.share_message("test_message", overall=True)

    assert worker_core.input_queue.get(timeout=3) == (
        "test_worker",
        "test_worker",
        "test_message",
    )
    assert worker_core.input_queue.get(timeout=3) == (
        "test_worker",
        "test_worker_2",
        "test_message",
    )
    assert worker_core.input_queue.empty()

    for output_queue in worker_core.output_queues:
        assert output_queue.get(timeout=3) == (
            "test_worker",
            "test_worker_3",
            "test_message",
        )
        assert output_queue.empty()


def test_share_message_overall_with_explicit_dependencies_and_delay(worker_core):
    time.sleep = MagicMock()

    worker_core.sharing_delay = 5.0
    worker_core.concurrent_workers_names = ["test_worker_2"]
    worker_core.dependent_workers_names = ["test_worker_3"]

    worker_core.share_message("test_message", overall=True, apply_delay=True)

    time.sleep.assert_called_with(5.0)

    assert worker_core.input_queue.get(timeout=3) == (
        "test_worker",
        "test_worker",
        "test_message",
    )
    assert worker_core.input_queue.get(timeout=3) == (
        "test_worker",
        "test_worker_2",
        "test_message",
    )
    assert worker_core.input_queue.empty()

    for output_queue in worker_core.output_queues:
        assert output_queue.get(timeout=3) == (
            "test_worker",
            "test_worker_3",
            "test_message",
        )
        assert output_queue.empty()


def test_share_wait_signal(worker_core):
    worker_core.share_wait_signal()

    assert worker_core.input_queue.get(timeout=3) == ("test_worker", None, "wait")
    assert worker_core.input_queue.empty()

    for output_queue in worker_core.output_queues:
        assert output_queue.get(timeout=3) == ("test_worker", None, "wait")
        assert output_queue.empty()


def test_share_stop_signal(worker_core):
    worker_core.share_stop_signal()

    assert worker_core.input_queue.get(timeout=3) == ("test_worker", None, "stop")
    assert worker_core.input_queue.empty()

    for output_queue in worker_core.output_queues:
        assert output_queue.get(timeout=3) == ("test_worker", None, "stop")
        assert output_queue.empty()


def test_take_a_break(worker_core):
    time.sleep = MagicMock()

    worker_core.take_a_break(mode="standard")

    time.sleep.assert_called_once_with(worker_core.FETCH_DELAY_SECONDS)
    time.sleep.reset_mock()

    worker_core.fetch_delay = 5.0
    worker_core.take_a_break(mode="standard")

    time.sleep.assert_called_once_with(5.0)


def test_take_a_break_shutdown_mode(worker_core):
    time.sleep = MagicMock()

    worker_core.take_a_break(mode="shutdown")

    time.sleep.assert_not_called()
    time.sleep.reset_mock()

    worker_core.delay_shutdown = True
    worker_core.take_a_break(mode="shutdown")

    time.sleep.assert_called_once_with(worker_core.SHUTDOWN_DELAY_SECONDS)
    time.sleep.reset_mock()

    worker_core.shutdown_delay = 5.0
    worker_core.take_a_break(mode="shutdown")

    time.sleep.assert_called_once_with(5.0)


def test_take_a_break_unknown_mode(worker_core):
    time.sleep = MagicMock()

    worker_core.take_a_break(mode="unknown")

    time.sleep.assert_not_called()


def test_perform_external_checks(worker_core):
    assert worker_core.perform_external_preflight_checks() is True
    assert worker_core.perform_external_poweron_checks() is True
    assert worker_core.perform_external_poweroff_checks() is True
    assert worker_core.perform_external_inflight_checks("test_data") is True
    assert worker_core.perform_external_postflight_checks("test_result") is True


def test_run(worker_core):
    worker_core.global_exit_event.set()
    worker_core.run()

    assert worker_core.exit_event.is_set()


def test_terminate_method(worker_core, monkeypatch):
    monkeypatch.setattr("multiprocessing.Process.terminate", lambda x: None)

    worker_core.terminate()

    assert worker_core.exit_event.is_set()
    assert worker_core.input_queue.get(timeout=3) == (
        "test_worker",
        "test_worker",
        "stop",
    )


def test_run_with_global_exit_event(started_worker_core):
    worker_core = started_worker_core
    worker_core.global_exit_event.set()

    worker_core.push_to_input_queue("wait")

    worker_core.join()
    worker_core.terminate()

    assert worker_core.exit_event.is_set()


def test_run_with_exit_event(started_worker_core):
    worker_core = started_worker_core
    worker_core.exit_event.set()

    worker_core.push_to_input_queue("wait")

    worker_core.join()
    worker_core.terminate()

    assert worker_core.exit_event.is_set()


def test_run_with_data_processing(started_worker_core):
    worker_core = started_worker_core

    worker_core.push_to_input_queue("test_data")
    worker_core.push_to_input_queue("stop")

    worker_core.join()
    worker_core.terminate()

    assert worker_core.output_queues[0].get(timeout=3) == (
        "test_worker",
        None,
        "processed_test_data",
    )
    assert worker_core.output_queues[0].get(timeout=3) == ("test_worker", None, "stop")
    assert worker_core.output_queues[0].empty()


def test_run_with_stop_signal(started_worker_core):
    worker_core = started_worker_core
    worker_core.push_to_input_queue("stop")

    worker_core.join()
    worker_core.terminate()

    assert worker_core.exit_event.is_set()


def test_run_with_wait_signal(started_worker_core):
    worker_core = started_worker_core
    worker_core.spread_wait_signal = True

    worker_core.push_to_input_queue("wait")
    worker_core.push_to_input_queue("stop")

    worker_core.join()
    worker_core.terminate()

    assert worker_core.input_queue.get(timeout=3) == (
        "test_worker",
        "test_worker",
        "wait",
    )
    assert worker_core.input_queue.get(timeout=3) == (
        "test_worker",
        "test_worker",
        "stop",
    )
    assert worker_core.input_queue.get(timeout=3) == (
        "test_worker",
        "test_worker",
        "stop",
    )
    assert worker_core.input_queue.empty()

    for output_queue in worker_core.output_queues:
        assert output_queue.get(timeout=3) == ("test_worker", None, "wait")
        assert output_queue.get(timeout=3) == ("test_worker", None, "stop")
        assert output_queue.empty()


def test_run_with_exception(worker_core):
    worker_core.target = mock_target_exception
    worker_core.start()

    assert worker_core.exception is None

    worker_core.push_to_input_queue("test_data")
    worker_core.push_to_input_queue("stop")

    worker_core.join()
    worker_core.terminate()

    assert isinstance(worker_core.exception[0], RuntimeError)
    assert worker_core.exception[1].startswith("Traceback (most recent")


def test_run_with_eof_error(worker_core):
    worker_core.target = mock_target_eoferror
    worker_core.start()

    assert worker_core.exception is None

    worker_core.push_to_input_queue("test_data")

    worker_core.join()

    assert worker_core.global_exit_event.is_set()


def test_run_with_type_error(started_worker_core):
    worker_core = started_worker_core

    worker_core.input_queue.put(("test_worker", None, 123))
    worker_core.input_queue.put(("test_worker", None, 22))
    worker_core.input_queue.put(("foobar",))

    worker_core.join()
    worker_core.terminate()

    for output_queue in worker_core.output_queues:
        assert output_queue.get(timeout=3) == ("test_worker", None, "processed_123")
        assert output_queue.get(timeout=3) == ("test_worker", None, "processed_22")
        assert output_queue.empty()

    worker_core.push_to_input_queue("stop")
