#!/usr/bin/env python
# -*- coding: utf-8 -*-
# refs to `voyager process_monitor.py`

import re
import subprocess
import threading
import warnings
from typing import List

import psutil

from metagpt.logs import define_log_level


class SubprocessMonitor:
    def __init__(
        self,
        commands: List[str],
        name: str,
        ready_match: str = r".*",
        callback_match: str = r"^(?!x)x$",  # regex that will never match
        callback: callable = None,
        finished_callback: callable = None,
    ):
        self.commands = commands
        self.name = name
        self.logger = define_log_level(name=name)
        self.process = None
        self.ready_match = ready_match
        self.ready_event = None
        self.ready_line = None
        self.callback_match = callback_match
        self.callback = callback
        self.finished_callback = finished_callback
        self.thread = None

    def _start(self):
        self.logger.info(f"Starting subprocess with commands: {self.commands}")

        self.process = psutil.Popen(
            self.commands,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )
        self.logger.info(f"Subprocess {self.name} started with PID {self.process.pid}.")
        for line in iter(self.process.stdout.readline, ""):
            self.logger.info(line.strip())
            if re.search(self.ready_match, line):
                self.ready_line = line
                self.logger.info("Subprocess is ready.")
                self.ready_event.set()
            if re.search(self.callback_match, line):
                self.callback()
        if not self.ready_event.is_set():
            self.ready_event.set()
            warnings.warn(f"Subprocess {self.name} failed to start.")
        if self.finished_callback:
            self.finished_callback()

    def run(self):
        self.ready_event = threading.Event()
        self.ready_line = None
        self.thread = threading.Thread(target=self._start)
        self.thread.start()
        self.ready_event.wait()

    def stop(self):
        self.logger.info("Stopping subprocess.")
        if self.process and self.process.is_running():
            self.process.terminate()
            self.process.wait()

    @property
    def is_running(self):
        if self.process is None:
            return False
        return self.process.is_running()
