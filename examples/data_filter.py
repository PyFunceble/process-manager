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

This is a script that provides an example.

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

from typing import Any

from PyFunceble.ext.process_manager import ProcessManagerCore, WorkerCore


class DataFilterWorker(WorkerCore):
    def perform_external_poweron_checks(self) -> bool:
        # This can be used to perform checks before starting the worker.
        # If False is returned, the worker will not start.
        return super().perform_external_poweron_checks()

    def perform_external_poweroff_checks(self) -> bool:
        # This can be used to perform checks before stopping the worker.
        return super().perform_external_poweroff_checks()

    def perform_external_preflight_checks(self) -> bool:
        # This can be used to implement your own logic before the worker
        # starts processing the next data.
        return super().perform_external_preflight_checks()

    def perform_external_inflight_checks(self, consumed: Any) -> bool:
        # This can be used to filter out the consumed data by returning False.
        # For example, filter out data that is not a string.

        print("DataFilter consumed:", consumed)

        if not isinstance(consumed, str):

            print("DataFilter filtered out:", consumed)

            return False
        return super().perform_external_inflight_checks(consumed)

    def perform_external_postflight_checks(self, produced: Any) -> bool:
        # This can be used to implement your own logic after the worker
        # has processed the data.

        print("DataFilter produced:", produced)
        return super().perform_external_postflight_checks(produced)

    def target(self, consumed: Any) -> Any:
        # Here we simply convert the string to uppercase as an example of data
        # processing.
        return consumed.upper()


class DataPrinterWorker(WorkerCore):
    def target(self, consumed: Any) -> Any:
        print("DataPrinter consumed:", consumed)
        return consumed


class DataFilterManager(ProcessManagerCore):
    WORKER_CLASS = DataFilterWorker


class DataPrinterManager(ProcessManagerCore):
    WORKER_CLASS = DataPrinterWorker


if __name__ == "__main__":
    # By default, our interfaces will log to the console.

    data_to_filter = [
        "hello",
        "world",
        123,  # This will be filtered out because it's not a string.
        "PyFunceble",
        None,  # This will be filtered out because it's not a string.
    ]

    # Configure the manager to generate 2 workers/processes.
    data_filter_manager = DataFilterManager(
        max_workers=2, generate_output_queue=True, output_queue_count=1
    )
    # Configure the manager to generate 1 worker/process.
    data_printer_manager = DataPrinterManager(
        max_workers=1,
        input_queue=data_filter_manager.output_queues[0],
        generate_output_queue=False,
    )

    # Start the manager.
    data_filter_manager.start()
    data_printer_manager.start()

    # Push the data to the input queue for further processing.
    for data in data_to_filter:
        print("Controller pushed:", data)
        data_filter_manager.push_to_input_queue(data)

    # Push the stop signal at the end of the input queue to stop the workers.
    # Note:
    #   As the data printer is a dependency of the data filter, we don't need to
    #   stop it explicitly. It will be stopped automatically when the data filter
    #   manager stops.
    #
    data_filter_manager.push_stop_signal()
    # Wait for the manager to finish processing the data.
    data_filter_manager.wait()

    # If we want to terminate the manager and all workers, we can call the
    # terminate method.
    data_filter_manager.terminate()

    print("Data filtered successfully.")
