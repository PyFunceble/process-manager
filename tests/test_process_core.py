from unittest.mock import MagicMock

import pytest

from PyFunceble.ext.process_manager.core import ProcessManagerCore


class DummyWorker:

    def __init__(self, *args, **kwargs):
        self.name = kwargs.get("name", "dummy-worker")
        self.is_alive = MagicMock(return_value=True)
        self.push_to_input_queue = MagicMock()
        self.push_to_output_queues = MagicMock()
        self.push_to_configuration_queue = MagicMock()
        self.terminate = MagicMock()
        self.join = MagicMock()
        self.global_exit_event = MagicMock()
        self.terminating_event = MagicMock()
        self.start = MagicMock()
        self.exception = None
        self.target = MagicMock()
        self.exitcode = MagicMock()


ProcessManagerCore.WORKER_CLASS = DummyWorker


@pytest.fixture
def process_manager():
    return ProcessManagerCore(max_workers=2)


def test_initialization(process_manager):
    assert process_manager.max_workers == 2
    assert process_manager.daemon is False
    assert process_manager.targeted_processing is True
    assert process_manager.delay_message_sharing is False
    assert process_manager.delay_shutdown is False
    assert process_manager.raise_exception is False
    assert process_manager.input_queue is not None
    assert process_manager.output_queues is not None
    assert process_manager.configuration_queue is not None
    assert process_manager.created_workers == []
    assert process_manager.running_workers == []
    assert process_manager.delay_message_sharing is False
    assert process_manager.delay_shutdown is False
    assert process_manager.raise_exception is False
    assert process_manager.dynamic_up_scaling is False
    assert process_manager.dynamic_down_scaling is False


def test_extra_args():
    process_manager = ProcessManagerCore(max_workers=2, foobar="barfoo")
    assert process_manager.max_workers == 2
    assert process_manager.foobar == "barfoo"


def test_extra_args_not_existing():
    process_manager = ProcessManagerCore(max_workers=2, foobar="barfoo")

    with pytest.raises(AttributeError):
        _ = process_manager.barfoo


def test_ensure_worker_class_is_set(process_manager):
    process_manager.WORKER_CLASS = None

    with pytest.raises(TypeError):
        process_manager.start()


def test_ensure_worker_spawned(process_manager):
    process_manager.start()
    assert len(process_manager.created_workers) == 2


def test_ignore_if_running(process_manager):
    process_manager.input_datasets = ["input_data"]
    process_manager.output_datasets = ["output_data"]
    process_manager.configuration_datasets = ["configuration_data"]

    process_manager.push_to_input_queue = MagicMock()
    process_manager.push_to_output_queues = MagicMock()
    process_manager.push_to_configuration_queue = MagicMock()

    process_manager.start()

    process_manager.push_to_input_queue.assert_called_with(
        "input_data", source_worker="ppm"
    )
    process_manager.push_to_output_queues.assert_called_with(
        "output_data", source_worker="ppm"
    )
    process_manager.push_to_configuration_queue.assert_called_with(
        "configuration_data", source_worker="ppm"
    )
    assert len(process_manager.running_workers) == 2

    process_manager.push_to_input_queue.reset_mock()
    process_manager.push_to_output_queues.reset_mock()
    process_manager.push_to_configuration_queue.reset_mock()

    process_manager.start()

    process_manager.push_to_input_queue.assert_not_called()
    process_manager.push_to_output_queues.assert_not_called()
    process_manager.push_to_configuration_queue.assert_not_called()

    assert len(process_manager.running_workers) == 2


def test_cpu_count(process_manager):
    process_manager.AVAILABLE_CPU_COUNT = 2
    assert process_manager.cpu_count == 2

    process_manager.AVAILABLE_CPU_COUNT = 3
    assert process_manager.cpu_count == 1


def test_max_workers(process_manager):
    process_manager.max_workers = 3
    assert process_manager.max_workers == 3

    process_manager.max_workers = 0
    assert process_manager.max_workers == 1

    process_manager.max_workers = -1
    assert process_manager.max_workers == 1

    with pytest.raises(TypeError):
        process_manager.max_workers = "1.0"


def test_queue_size(process_manager):
    assert process_manager.queue_size == 0

    process_manager.input_queue.put("test_data")
    process_manager.input_queue.put("test_data")
    process_manager.input_queue.put("test_data")
    process_manager.input_queue.put("test_data")

    assert process_manager.queue_size == 4


def test_queue_size_with_no_queue(process_manager):
    process_manager.input_queue = None
    assert process_manager.queue_size == 0


def test_queue_full(process_manager):
    process_manager.max_workers = 3
    assert process_manager.queue_full is False
    assert process_manager.is_queue_full() is False
    assert process_manager.queue_size == 0

    process_manager.input_queue.put("test_data")
    process_manager.input_queue.put("test_data")

    assert process_manager.queue_size == 2
    assert process_manager.queue_full is False
    assert process_manager.is_queue_full() is False

    process_manager.input_queue.put("test_data")
    process_manager.input_queue.put("test_data")

    assert process_manager.queue_size == 4
    assert process_manager.queue_full is True
    assert process_manager.is_queue_full() is True


def test_add_dependent_manager(process_manager):
    dependent_manager = ProcessManagerCore(max_workers=2)
    dependent_manager.STD_NAME = "dependent_manager"
    process_manager.add_dependent_manager(dependent_manager)

    assert dependent_manager in process_manager.dependent_managers
    assert process_manager.dependent_managers[0].name == "ppm-dependent_manager"


def test_relink_queues(process_manager):
    process_manager.output_queues = [MagicMock()]

    dependent_manager = ProcessManagerCore(max_workers=2, generate_input_queue=False)
    dependent_manager.STD_NAME = "dependent_manager"

    assert dependent_manager.input_queue is None

    process_manager.add_dependent_manager(dependent_manager)
    assert dependent_manager.input_queue == process_manager.output_queues[0]


def test_relink_queues_with_no_output_queues(process_manager):
    process_manager.output_queues = []

    dependent_manager = ProcessManagerCore(max_workers=2, generate_input_queue=False)
    dependent_manager.STD_NAME = "dependent_manager"

    assert dependent_manager.input_queue is None

    process_manager.add_dependent_manager(dependent_manager)
    assert dependent_manager.input_queue is None


def test_relink_queues_with_more_dependencies_than_output_queues(process_manager):
    process_manager.output_queues = [MagicMock()]

    dependent_manager = ProcessManagerCore(max_workers=2, generate_input_queue=False)
    dependent_manager.STD_NAME = "dependent_manager"

    assert dependent_manager.input_queue is None

    process_manager.add_dependent_manager(dependent_manager)

    assert dependent_manager.input_queue == process_manager.output_queues[0]

    new_dependent_manager = ProcessManagerCore(
        max_workers=2, generate_input_queue=False
    )
    new_dependent_manager.STD_NAME = "new_dependent_manager"

    assert new_dependent_manager.input_queue is None

    process_manager.add_dependent_manager(new_dependent_manager)

    assert new_dependent_manager.input_queue == process_manager.output_queues[0]

    process_manager.add_dependent_manager(new_dependent_manager)


def test_remove_dependent_manager(process_manager):
    dependent_manager = ProcessManagerCore(max_workers=2)

    process_manager.add_dependent_manager(dependent_manager)

    assert dependent_manager in process_manager.dependent_managers

    process_manager.remove_dependent_manager(dependent_manager)

    assert dependent_manager not in process_manager.dependent_managers


def test_spawn_worker(process_manager):
    worker = process_manager.spawn_worker()
    assert worker is not None
    assert worker.name == "ppm-pyfunceble-process-manager-1"
    assert len(process_manager.created_workers) == 1


def test_is_running(process_manager):
    assert process_manager.is_running() is False

    worker = process_manager.spawn_worker(start=True)
    assert process_manager.is_running() is True

    process_manager.terminate_worker(worker)

    assert process_manager.is_running() is False


def test_spawn_worker_max_workers(process_manager):
    process_manager.running_workers = [DummyWorker() for _ in range(4)]
    process_manager.created_workers = [DummyWorker() for _ in range(4)]

    worker = process_manager.spawn_worker()

    assert worker is None


def test_spawn_worker_running_workers_full(process_manager):
    process_manager.running_workers = [DummyWorker() for _ in range(4)]
    process_manager.created_workers = [DummyWorker() for _ in range(4)]

    worker = process_manager.spawn_worker(start=True)

    assert worker is None


def test_spawn_worker_running_workers_full_with_force(process_manager):
    process_manager.running_workers = [DummyWorker() for _ in range(4)]
    process_manager.created_workers = [DummyWorker() for _ in range(4)]

    worker = process_manager.spawn_worker(force=True)

    assert worker is not None
    assert worker.name == "ppm-pyfunceble-process-manager-5"


def test_push_to_input_queue(process_manager):
    process_manager.spawn_worker()
    process_manager.push_to_input_queue("test_data")
    worker = process_manager.created_workers[0]
    worker.push_to_input_queue.assert_called_with(
        "test_data", source_worker="ppm-pyfunceble-process-manager"
    )


def test_push_to_input_queue_with_all_queues(process_manager):
    process_manager.spawn_worker()
    process_manager.spawn_worker()
    process_manager.spawn_worker()

    process_manager.push_to_input_queue("test_data", all_queues=True)

    for index, worker in enumerate(process_manager.created_workers):
        worker.push_to_input_queue.assert_called_with(
            "test_data",
            source_worker="ppm-pyfunceble-process-manager",
            destination_worker=f"ppm-pyfunceble-process-manager-{index+1}",
        )


def test_push_to_output_queues(process_manager):
    process_manager.spawn_worker()
    process_manager.push_to_output_queues("test_data")
    worker = process_manager.created_workers[0]
    worker.push_to_output_queues.assert_called_with(
        "test_data", source_worker="ppm-pyfunceble-process-manager-manager"
    )


def test_push_to_output_queues_with_all_queues(process_manager):
    process_manager.spawn_worker()
    process_manager.spawn_worker()
    process_manager.spawn_worker()

    process_manager.push_to_output_queues("test_data", all_queues=True)

    for index, worker in enumerate(process_manager.created_workers):
        worker.push_to_output_queues.assert_called_with(
            "test_data",
            source_worker="ppm-pyfunceble-process-manager-manager",
            destination_worker=f"ppm-pyfunceble-process-manager-{index+1}",
        )


def test_push_to_output_queues_with_dependent_manager(process_manager):
    dependent_manager = ProcessManagerCore(max_workers=1)
    dummy_worker = DummyWorker()
    dependent_manager.created_workers = [dummy_worker]
    dependent_manager.running_workers = [dummy_worker]

    dependent_manager.STD_NAME = "dependent_manager"
    process_manager.add_dependent_manager(dependent_manager)

    process_manager.push_to_output_queues("test_data")

    (
        process_manager.dependent_managers[0]
        .created_workers[0]
        .push_to_input_queue.assert_called_with(
            "test_data", source_worker="ppm-pyfunceble-process-manager-manager"
        )
    )
    dummy_worker.push_to_input_queue.assert_called_with(
        "test_data", source_worker="ppm-pyfunceble-process-manager-manager"
    )


def test_push_to_configuration_queue(process_manager):
    process_manager.spawn_worker()
    process_manager.push_to_configuration_queue("test_data", all_queues=False)
    worker = process_manager.created_workers[0]
    worker.push_to_configuration_queue.assert_called_with(
        "test_data",
        source_worker="ppm-pyfunceble-process-manager-manager",
    )


def test_push_to_configuration_queue_with_all_queues(process_manager):
    process_manager.spawn_worker()
    process_manager.spawn_worker()
    process_manager.spawn_worker()

    process_manager.push_to_configuration_queue("test_data", all_queues=True)

    for index, worker in enumerate(process_manager.created_workers):
        worker.push_to_configuration_queue.assert_called_with(
            "test_data",
            source_worker="ppm-pyfunceble-process-manager-manager",
            destination_worker=f"ppm-pyfunceble-process-manager-{index+1}",
        )


def test_push_stop_signal(process_manager):
    process_manager.push_stop_signal()

    for index, worker in enumerate(process_manager.created_workers):
        worker.push_to_input_queue.assert_called_with(
            "__stop__",
            source_worker="ppm-pyfunceble-process-manager",
            destination_worker=f"ppm-pyfunceble-process-manager-{index+1}",
        )


def test_wait_signal(process_manager):
    process_manager.push_wait_signal()

    for index, worker in enumerate(process_manager.created_workers):
        worker.push_to_input_queue.assert_called_with(
            "__wait__",
            source_worker="ppm-pyfunceble-process-manager",
            destination_worker=f"ppm-pyfunceble-process-manager-{index+1}",
        )


def test_wait(process_manager):
    running_worker = process_manager.spawn_worker(start=True)
    created_worker = process_manager.spawn_worker()

    process_manager.push_to_input_queue("__wait__", all_queues=True)

    process_manager.wait()

    running_worker.join.assert_called_once()
    created_worker.join.assert_called_once()


def test_wait_with_exception(process_manager):
    worker = process_manager.spawn_worker()

    worker.exception = (RuntimeError("Test exception"), "Test Exception")

    with pytest.raises(RuntimeError):
        process_manager.wait()


def test_wait_with_terminate_on_exception(process_manager):
    process_manager.shutdown_on_exception = True
    worker = process_manager.spawn_worker(start=True)

    process_manager.terminate = MagicMock()

    worker.exception = (RuntimeError("Test exception"), "Test Exception")

    with pytest.raises(RuntimeError):
        process_manager.wait()

    process_manager.terminate.assert_called_once()


def test_wait_running_with_exception(process_manager):
    worker = process_manager.spawn_worker(start=True)

    worker.exception = (RuntimeError("Test exception"), "Test Exception")

    with pytest.raises(RuntimeError):
        process_manager.wait()

    worker.join.assert_called_once()


def test_terminate_worker(process_manager):
    created_worker = process_manager.spawn_worker()
    running_worker = process_manager.spawn_worker(start=True)

    assert len(process_manager.created_workers) == 2
    assert len(process_manager.running_workers) == 1

    process_manager.terminate_worker(created_worker)

    created_worker.terminate.assert_called_once()
    created_worker.join.assert_called_once()

    process_manager.terminate_worker(running_worker)

    running_worker.terminate.assert_called_once()
    running_worker.join.assert_called_once()

    assert len(process_manager.created_workers) == 0
    assert len(process_manager.running_workers) == 0


def test_terminate(process_manager):
    process_manager.push_to_output_queues = MagicMock()

    process_manager.spawn_worker()
    process_manager.spawn_worker()

    assert len(process_manager.created_workers) == 2

    process_manager.terminate()

    assert len(process_manager.created_workers) == 0


def test_terminate_wrong_mode(process_manager):
    process_manager.push_to_output_queues = MagicMock()

    process_manager.spawn_worker()
    process_manager.spawn_worker()

    assert len(process_manager.created_workers) == 2

    with pytest.raises(ValueError):
        process_manager.terminate(mode="foobar")

    assert len(process_manager.created_workers) == 2


def test_terminate_hard(process_manager):
    process_manager.push_to_output_queues = MagicMock()

    worker1 = process_manager.spawn_worker()
    worker2 = process_manager.spawn_worker()

    worker1.terminate = MagicMock()
    worker2.terminate = MagicMock()

    assert len(process_manager.created_workers) == 2

    assert process_manager.global_exit_event.is_set() is False
    assert process_manager.terminating_event.is_set() is False

    process_manager.terminate(mode="hard")

    assert process_manager.global_exit_event.is_set() is True
    assert process_manager.terminating_event.is_set() is True

    # In the hard mode, we terminate all workers without waiting for them to finish.
    worker1.terminate.assert_called_once()
    worker2.terminate.assert_called_once()

    assert len(process_manager.created_workers) == 0


def test_terminate_spread_stop_signal(process_manager):
    process_manager.push_to_output_queues = MagicMock()
    process_manager.spread_stop_signal = True

    process_manager.spawn_worker()
    process_manager.spawn_worker()

    assert len(process_manager.created_workers) == 2
    assert len(process_manager.running_workers) == 0

    process_manager.terminate()

    assert len(process_manager.created_workers) == 0
    assert len(process_manager.running_workers) == 0
    process_manager.push_to_output_queues.assert_called_with(
        "__stop__", source_worker=None, all_queues=True
    )


def test_terminate_no_running_workers(process_manager):
    process_manager.push_to_input_queue = MagicMock()
    process_manager.push_to_output_queues = MagicMock()
    process_manager.push_stop_signal = MagicMock()

    process_manager.spawn_worker(start=False)

    assert len(process_manager.created_workers) == 1
    assert len(process_manager.running_workers) == 0
    assert process_manager.terminating_event.is_set() is False

    process_manager.terminate()
    process_manager.push_stop_signal.assert_called()
    process_manager.push_stop_signal.reset_mock()
    assert process_manager.terminating_event.is_set() is True

    process_manager.created_workers = [MagicMock()]
    process_manager.created_workers[0].is_alive = MagicMock(return_value=False)
    process_manager.created_workers[0].terminate = MagicMock()
    process_manager.terminating_event.clear()

    process_manager.terminate()
    process_manager.push_stop_signal.assert_called()
    assert process_manager.terminating_event.is_set() is True

    assert len(process_manager.created_workers) == 0
    assert len(process_manager.running_workers) == 0


def test_start(process_manager):
    process_manager.input_datasets = ["input_data"]
    process_manager.output_datasets = ["output_data"]
    process_manager.configuration_datasets = ["configuration_data"]

    process_manager.spawn_worker()
    process_manager.start()

    worker = process_manager.created_workers[0]
    worker.start.assert_called_once()

    worker.push_to_input_queue.assert_called_with("input_data", source_worker="ppm")
    worker.push_to_output_queues.assert_called_with("output_data", source_worker="ppm")

    for worker in process_manager.created_workers:
        worker.push_to_configuration_queue.assert_called_with(
            "configuration_data", source_worker="ppm", destination_worker=worker.name
        )
