"""
The tool to check the availability or syntax of domain, IP or URL.

-- The process manager library for and from the PyFunceble project.

::


    ██████╗ ██╗   ██╗███████╗██╗   ██╗███╗   ██╗ ██████╗███████╗██████╗ ██╗     ███████╗
    ██╔══██╗╚██╗ ██╔╝██╔════╝██║   ██║████╗  ██║██╔════╝██╔════╝██╔══██╗██║     ██╔════╝
    ██████╔╝ ╚████╔╝ █████╗  ██║   ██║██╔██╗ ██║██║     █████╗  ██████╔╝██║     █████╗
    ██╔═══╝   ╚██╔╝  ██╔══╝  ██║   ██║██║╚██╗██║██║     ██╔══╝  ██╔══██╗██║     ██╔══╝
    ██║        ██║   ██║     ╚██████╔╝██║ ╚████║╚██████╗███████╗██████╔╝███████╗███████╗
    ╚═╝        ╚═╝   ╚═╝      ╚═════╝ ╚═╝  ╚═══╝ ╚═════╝╚══════╝╚═════╝ ╚══════╝╚══════╝

This is the module that provides the core components of our process manager.

Author:
    Nissar Chababy, @funilrys, contactTATAfunilrysTODTODcom

Special thanks:
    https://pyfunceble.github.io/#/special-thanks

Contributors:
    https://pyfunceble.github.io/#/contributors

Project link:
    https://github.com/funilrys/PyFunceble

Project documentation:
    https://docs.pyfunceble.com

Project homepage:
    https://pyfunceble.github.io/

License:
::


    Copyright 2017, 2018, 2019, 2020, 2022, 2023, 2024 Nissar Chababy

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        https://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

import functools
import logging
import multiprocessing
import multiprocessing.context
import multiprocessing.managers
import multiprocessing.queues
import multiprocessing.synchronize
import os
import queue
import random
from typing import Any, Callable, List, Optional

from PyFunceble.ext.process_manager.worker.core import WorkerCore

logger = logging.getLogger("PyFunceble.ext.process_manager")
logger.setLevel(logging.CRITICAL)


class ProcessManagerCore:
    """
    This is the core of the process manager. It provides the basic methods
    to work with.

    It has been designed to be used as a parent class.
    """

    STD_NAME: str = "pyfunceble-process-manager"
    """
    The standard name of the process manager.

    .. note::
        The name of the worker will be in the format:

        ppm-{STD_NAME}-{worker_number}

    """

    WORKER_CLASS: WorkerCore
    """
    The class which is going to be used as worker. This is a mandatory attribute
    and its value should be a class that inherits from our :code:`WorkerCore`.

    .. note::

        This is a mandatory attribute and its value should be a class that
        inherits from :code:`multiprocessing.Process`. It is although recommended
        to inherit from :code:`PyFunceble.ext.process_manager.worker.WorkerCore`.
    """

    AVAILABLE_CPU_COUNT = os.cpu_count()
    """
    Represents the number of CPU available on the current machine.
    """

    input_datasets: Optional[List] = []
    """
    Stores and exposes the input datasets. This is a list of data that we
    have to send to the input queue of the worker(s) before we start them.

    It should be a list of data. The data is up to you, but it must be a list.
    """

    output_datasets: Optional[List] = []
    """
    Stores and exposes the output datasets. This is a list of data that we
    have to send to the output queue(s) of the worker(s) before we start them.

    It should be a list of data. The data is up to you, but it must be a list.
    """

    configuration_datasets: Optional[List] = []
    """
    Stores and exposes the configuration datasets. This is a list of data that we
    have to send to the configuration queue of the worker(s) before we start them.

    It should be a list of data. The data is up to you, but it must be a list.
    """

    manager: Optional[multiprocessing.managers.SyncManager] = None
    """
    Stores and exposes the manager of the worker.

    The manager is used to initialize the worker's queue(s) - when not explicitly
    provided by the end-user.

    When initialized, it will be a :code:`multiprocessing.Manager()` object.
    """

    global_exit_event: Optional[multiprocessing.synchronize.Event] = None
    """
    Stores and exposes the global exit event of the worker.

    The global exit event is used to tell the worker to stop its work.

    When initialized, it will be a :code:`multiprocessing.Event()` object.
    """

    configuration_queue: Optional[multiprocessing.queues.Queue] = None
    """
    Stores and exposes the configuration queue of the worker.

    The configuration queue is used to send or share configuration data between
    the process manager and the managed worker.
    """

    input_queue: Optional[multiprocessing.queues.Queue] = None
    """
    Stores and exposes the input queue of the worker.
    """

    output_queues: Optional[List[multiprocessing.queues.Queue]] = None
    """
    Store and expose the output queue(s) of the worker.
    """

    daemon: Optional[bool] = None
    """
    Store and expose the daemon status of the worker.

    When set to :code:`True`, the worker will be a daemon.
    """

    spread_stop_signal: bool = False
    """
    Whether we have to spread the stop signal to the output queue(s) of the
    worker(s).
    """

    spread_wait_signal: bool = False
    """
    Whether we have to spread the wait signal to the output queue(s) of the
    worker(s).
    """

    targeted_processing: Optional[bool] = None
    """
    Whether the worker should strictly process data that are intended for it.

    .. note::
        When set to :code:`True`, the worker will only process data that are
        intended for it. If the data are not intended for it, the worker will
        push the data back to the input queue.

        When set to :code:`False`, the worker will process all data that are
        pushed to the input queue.
    """

    delay_message_sharing: Optional[bool] = None
    """
    Whether we have to delay the sharing of the message to queue(s).
    """

    delay_shutdown: Optional[bool] = None
    """
    Whether we have to delay the shutdown of the worker.

    .. note::
        This is useful when you just want to be able to
    """

    raise_exception: Optional[bool] = None
    """
    Whether we have to raise any exception or just store/share it.
    """

    sharing_delay: Optional[float] = None
    """
    The number of seconds to wait before sharing the message.
    """

    shutdown_delay: Optional[float] = None
    """
    The number of seconds to wait before shutting down the worker.
    """

    fetch_delay: Optional[float] = None
    """
    The number of seconds to wait before fetching the next dataset.
    """

    _extra_args: Optional[dict] = None
    """
    The extra arguments that were passed to the worker through the
    :code:`kwargs` parameter.
    """

    created_workers: Optional[List[WorkerCore]] = None
    running_workers: Optional[List[WorkerCore]] = None

    _max_workers: Optional[int] = 1

    def __init__(
        self,
        max_workers: Optional[int] = None,
        *,
        manager: Optional[multiprocessing.managers.SyncManager] = None,
        input_queue: Optional[queue.Queue] = None,
        generate_input_queue: bool = True,
        output_queue: Optional[queue.Queue] = None,
        output_queue_count: int = 1,
        generate_output_queue: bool = True,
        configuration_queue: Optional[queue.Queue] = None,
        generate_configuration_queue: bool = True,
        daemon: Optional[bool] = None,
        spread_stop_signal: bool = None,
        spread_wait_signal: bool = None,
        delay_message_sharing: bool = None,
        delay_shutdown: bool = None,
        raise_exception: bool = None,
        targeted_processing: bool = None,
        sharing_delay: Optional[float] = None,
        shutdown_delay: Optional[float] = None,
        fetch_delay: Optional[float] = None,
        **kwargs,
    ):
        self.created_workers = []
        self.running_workers = []

        self._max_workers = max_workers or self.cpu_count

        self.daemon = daemon or False
        self.targeted_processing = targeted_processing or True
        self.delay_message_sharing = delay_message_sharing or False
        self.delay_shutdown = delay_shutdown or False
        self.raise_exception = raise_exception or False

        if manager is None:
            self.manager = multiprocessing.Manager()
        else:
            self.manager = manager

        self.global_exit_event = self.manager.Event()

        if spread_stop_signal is not None:
            self.spread_stop_signal = spread_stop_signal

        if spread_wait_signal is not None:
            self.spread_wait_signal = spread_wait_signal

        if sharing_delay is not None:
            self.sharing_delay = sharing_delay

        if shutdown_delay is not None:
            self.shutdown_delay = shutdown_delay

        if fetch_delay is not None:
            self.fetch_delay = fetch_delay

        if not input_queue and generate_input_queue:
            self.input_queue = self.manager.Queue()
        else:
            self.input_queue = input_queue

        if not output_queue and generate_output_queue:
            self.output_queues = [
                self.manager.Queue() for _ in range(max(1, output_queue_count))
            ]
        elif output_queue:
            self.output_queues = (
                [output_queue] if not isinstance(output_queue, list) else output_queue
            )

        if not configuration_queue and generate_configuration_queue:
            self.configuration_queue = self.manager.Queue()

        self._extra_args = kwargs

        self.__post_init__()

    def __post_init__(self) -> None:
        """
        Called after the initialization of the worker, this method can be used
        by the child class to initialize their own workflows.
        """

    def __getattr__(self, attribute: str) -> Any:
        """
        Provides the value of the given attribute.

        :param str attribute:
            The attribute to get the value of.
        """

        if self._extra_args and attribute in self._extra_args:
            return self._extra_args[attribute]

        raise AttributeError(f"{self.__class__.__name__} has no attribute {attribute}")

    def ensure_worker_class_is_set(func: Callable[..., Any]) -> Callable[..., Any]:
        """
        Decorator which ensures that the worker class is set before launching
        the decorated method.
        """

        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            if not self.WORKER_CLASS:
                raise TypeError(f"<{self.__class__.__name__}.WORKER_CLASS> is not set.")

            return func(self, *args, **kwargs)  # pylint: disable=not-callable

        return wrapper

    def ensure_worker_spawned(func: Callable[..., Any]) -> Callable[..., Any]:
        """
        Decorator which ensures that at least one has been spawned before
        launching the decorated method.
        """

        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            if not self.created_workers:
                self.spawn_workers(start=False)

            return func(self, *args, **kwargs)  # pylint: disable=not-callable

        return wrapper

    def ignore_if_running(func: Callable[..., Any]) -> Callable[..., Any]:
        """
        Decorator which ensures that the decorated method is ignored if at least
        one worker is running.
        """

        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            if self.is_running():
                return self

            return func(self, *args, **kwargs)  # pylint: disable=not-callable

        return wrapper

    @property
    def name(self) -> str:
        """
        Provides the sanitized name of the process manager.
        """

        return f"ppm-{self.STD_NAME}"

    @property
    def cpu_count(self) -> int:
        """
        Provides the number of CPU that the process has to use.

        This method assumes that we we should always leave 2 CPUs available.
        Meaning that if you have more than 2 CPUs, we will return the number
        of CPUs minus 2. Otherwise, we return the number of CPUs.
        """

        if self.AVAILABLE_CPU_COUNT > 2:
            return self.AVAILABLE_CPU_COUNT - 2

        return self.AVAILABLE_CPU_COUNT

    @property
    def max_workers(self) -> int:
        """
        Provides the maximum number of workers that we are allowed to create.
        """

        return self._max_workers

    @max_workers.setter
    def max_workers(self, value: int) -> None:
        """
        Sets the maximum number of workers that we are allowed to create.

        :param int value:
            The value to set.

        :raise TypeError:
            When the given value is not an integer.
        """

        if not isinstance(value, int):
            raise TypeError(f"<value> should be {int}, {type(value)} given.")

        self._max_workers = max(1, value)

    def is_running(self) -> bool:
        """
        Checks if at least one worker is running.
        """

        if not self.running_workers:
            return False

        return any(x.is_alive() for x in self.running_workers)

    @ensure_worker_spawned
    def push_to_input_queue(
        self,
        data: Any,
        *,
        source_worker: Optional[str] = None,
        all_queues: bool = False,
    ) -> "ProcessManagerCore":
        """
        Pushes the given data to the currently managed input queue.

        :param any data:
            The data to spread.
        :param str source_worker:
            The name to use to identify the worker or process that is sending
            the data.

            If this is not set, we will use the name of the process manager.
        :param bool all_queues:
            Whether we have to spread the data to the queues of all workers instead
            of just the first one reached.

            .. warning::

                When this is set to :code:`True`, the system will spread the data
                to all workers. This means that it might be possible that the data
                is sent to the same worker multiple times.
        """

        if self.is_running():
            workers = self.running_workers
        else:
            workers = self.created_workers

        source_worker = source_worker or self.name

        if all_queues:
            for worker in workers:
                worker.push_to_input_queue(
                    data, source_worker=source_worker, destination_worker=worker.name
                )
        elif workers:
            random.choice(workers).push_to_input_queue(
                data, source_worker=source_worker
            )

        logger.debug("%s-manager | Pushed to input queue: %r", self.STD_NAME, data)

        return self

    @ensure_worker_spawned
    def push_to_output_queues(
        self,
        data: Any,
        *,
        source_worker: Optional[str] = None,
        all_queues: bool = False,
    ) -> "ProcessManagerCore":
        """
        Pushes the given data to the currently managed output queue.

        :param any data:
            The data to spread.
        :param str source_worker:
            The name to use to identify the worker or process that is sending
            the data.

            If this is not set, we will use the name of the process manager.
        :param bool all_queues:
            Whether we have to spread the data to the queues of all workers instead
            of just the first one reached.

            .. warning::

                When this is set to :code:`True`, the system will spread the data
                to all workers. This means that it might be possible that the data
                is sent to the same worker multiple times.
        """

        if self.is_running():
            workers = self.running_workers
        else:
            workers = self.created_workers

        source_worker = source_worker or f"ppm-{self.STD_NAME}"

        if all_queues:
            for worker in workers:
                worker.push_to_output_queues(
                    data, source_worker=source_worker, destination_worker=worker.name
                )
        elif workers:
            random.choice(workers).push_to_output_queues(
                data, source_worker=source_worker
            )

        logger.debug("%s-manager | Pushed to output queues: %r", self.STD_NAME, data)

        return self

    @ensure_worker_spawned
    def push_to_configuration_queue(
        self, data: Any, *, source_worker: Optional[str] = None, all_queues: bool = True
    ) -> "ProcessManagerCore":
        """
        Pushes the given data to the currently managed configuration queue.

        :param any data:
            The data to spread.

        :param str source_worker:
            The name to use to identify the worker or process that is sending
            the data.
        :param bool all_queues:
            Whether we have to spread the data to the queues of all workers instead
            of just the first one reached.

            .. warning::

                When this is set to :code:`True`, the system will spread the data
                to all workers. This means that it might be possible that the data
                is sent to the same worker multiple times.
        """

        if self.is_running():
            workers = self.running_workers
        else:
            workers = self.created_workers

        source_worker = source_worker or f"ppm-{self.STD_NAME}"

        if all_queues:
            for worker in workers:
                worker.push_to_configuration_queue(
                    data, source_worker=source_worker, destination_worker=worker.name
                )
        elif workers:
            random.choice(workers).push_to_configuration_queue(
                data, source_worker=source_worker
            )

        logger.debug(
            "%s-manager | Pushed to configuration queue: %r", self.STD_NAME, data
        )

        return self

    def spawn_worker(
        self, *, start: bool = False, daemon: bool = None
    ) -> Optional[WorkerCore]:
        """
        Spawns and configures a (single) new worker.

        :param bool start:
            Tell us if we have to start the worker after its creation.
        :param bool daemon:
            Tell us if the worker should be a daemon.

            .. note::
                If this is not set, we will use the value of the
                :code:`daemon` attribute.
        """

        if len(self.running_workers) >= self.max_workers:
            return None

        worker = self.WORKER_CLASS(
            name=f"ppm-{self.STD_NAME}-{len(self.created_workers) + 1}",
            input_queue=self.input_queue,
            output_queues=self.output_queues,
            global_exit_event=self.global_exit_event,
            configuration_queue=self.configuration_queue,
            daemon=daemon or self.daemon,
            spread_stop_signal=self.spread_stop_signal,
            spread_wait_signal=self.spread_wait_signal,
            targeted_processing=self.targeted_processing,
            delay_message_sharing=self.delay_message_sharing,
            delay_shutdown=self.delay_shutdown,
            raise_exception=self.raise_exception,
            sharing_delay=self.sharing_delay,
            shutdown_delay=self.shutdown_delay,
            fetch_delay=self.fetch_delay,
            **self._extra_args,
        )

        if self.is_running():
            # Just to make sure that the worker is aware that it might not not alone.
            worker.concurrent_workers_names = [x.name for x in self.created_workers]
        else:
            worker.concurrent_workers_names = [x.name for x in self.running_workers]

        self.created_workers.append(worker)

        if start:
            worker.start()
            self.running_workers.append(worker)

        logger.debug("%s-manager | Worker spawned: %r", self.STD_NAME, worker.name)

        return worker

    def spawn_workers(self, *, start: bool = False) -> "ProcessManagerCore":
        """
        Spawns and configures the number of workers that we are allowed to create.

        :param bool start:
            Tell us if we have to start the worker after its creation.
        """

        for _ in range(self.max_workers):
            self.spawn_worker(start=start)

        return self

    def push_stop_signal(
        self, *, source_worker: Optional[str] = None
    ) -> "ProcessManagerCore":
        """
        Sends the stop signal to the worker(s).

        :param str source_worker:
            The name to use to identify the worker or process that is sending
            the data.
        """

        self.push_to_input_queue("stop", source_worker=source_worker, all_queues=True)

        return self

    def push_wait_signal(
        self, *, source_worker: Optional[str] = None
    ) -> "ProcessManagerCore":
        """
        Sends the wait signal to the worker(s).

        :param str source_worker:
            The name to use to identify the worker or process that is sending
            the data.
        """

        self.push_to_input_queue("wait", source_worker=source_worker, all_queues=True)

        return self

    def terminate_worker(self, worker: WorkerCore) -> "ProcessManagerCore":
        """
        Terminates the given worker.

        :param WorkerCore worker:
            The worker to terminate.
        """

        logger.debug("%s-manager | Terminating worker: %r", self.STD_NAME, worker.name)

        worker.terminate()
        worker.join()

        if worker in self.running_workers:
            self.running_workers.remove(worker)

        if worker in self.created_workers:
            self.created_workers.remove(worker)

        del worker

        logger.debug("%s-manager | Worker terminated.", self.STD_NAME)

        return self

    def terminate(self) -> "ProcessManagerCore":
        """
        Terminates the worker(s).
        """

        logger.debug("%s-manager | Terminating all workers.", self.STD_NAME)

        workers = list(set(self.running_workers + self.created_workers))

        if workers:
            # Set the global exit event to tell the workers to stop.
            random.choice(workers).global_exit_event.set()

        for worker in workers:
            if not worker.is_alive():
                continue

            # Wait for each worker to terminate.
            self.terminate_worker(worker)

        # When all workers are terminated, we send a stop message to the workers
        # that depends on the currently managed workers.
        self.push_to_output_queues("stop", all_queues=True)

        logger.debug("%s-manager | All workers terminated.", self.STD_NAME)

        return self

    def wait(self) -> "ProcessManagerCore":
        """
        Waits for all workers to finish their work.
        """

        for worker in self.running_workers:
            logger.debug(
                "%s-manager | Waiting for worker: %r", self.STD_NAME, worker.name
            )

            try:
                worker.join()
                worker.terminate()
            except KeyboardInterrupt:  # pragma: no cover
                pass

            self.running_workers.remove(worker)
            self.created_workers.remove(worker)

            if worker.exception:
                worker_error, trace = worker.exception

                self.terminate()
                logging.critical(
                    "%s-manager | Worker %r raised an exception:\n%s",
                    self.STD_NAME,
                    worker.name,
                    trace,
                )

                raise worker_error

            logger.debug(
                "%s-manager | Still running workers: %r",
                self.STD_NAME,
                self.running_workers,
            )

            logger.debug(
                "%s-manager | Still running workers: %r",
                self.STD_NAME,
                self.running_workers,
            )

        for worker in self.created_workers:
            logger.debug(
                "%s-manager | Waiting for worker - created: %r",
                self.STD_NAME,
                worker.name,
            )

            worker.terminate()
            self.created_workers.remove(worker)

            if worker.exception:
                worker_error, trace = worker.exception

                self.terminate()
                logging.critical(
                    "%s-manager | Worker %r raised an exception:\n%s",
                    self.STD_NAME,
                    worker.name,
                    trace,
                )

                raise worker_error

            logger.debug(
                "%s-manager | Still created workers: %r",
                self.STD_NAME,
                self.created_workers,
            )

        # Double safety.
        self.terminate()

        return self

    @ensure_worker_class_is_set
    @ensure_worker_spawned
    @ignore_if_running
    def start(self) -> "ProcessManagerCore":
        """
        Starts the worker(s).
        """

        for worker in self.created_workers:
            worker.start()
            self.running_workers.append(worker)

        for data in self.input_datasets:
            self.push_to_input_queue(data, source_worker="ppm")

        for data in self.output_datasets:
            self.push_to_output_queues(data, source_worker="ppm")

        for data in self.configuration_datasets:
            self.push_to_configuration_queue(data, source_worker="ppm")

        return self