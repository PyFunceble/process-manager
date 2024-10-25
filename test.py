import logging
from PyFunceble.ext.process_manager import ProcessManagerCore, WorkerCore


# logging.basicConfig(
#     format="%(asctime)s :: %(filename)s:%(lineno)s %(levelname)s :: %(message)s",
#     level=logging.DEBUG,
#     datefmt="%Y-%m-%d %H:%M:%S",
# )


class NewProcessManager(ProcessManagerCore):
    WORKER_CLASS = WorkerCore


proc_manager = NewProcessManager(max_workers=3, delay_shutdown=False)

proc_manager.start()

proc_manager.push_stop_signal()
proc_manager.wait()
