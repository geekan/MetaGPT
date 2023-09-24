import platform
import sys
import warnings

if sys.implementation.name == "cpython" and platform.system() == "Windows":
    import asyncio

    if sys.version_info[:2] == (3, 9):
        from asyncio.proactor_events import _ProactorBasePipeTransport

        # https://github.com/python/cpython/pull/92842
        def pacth_del(self, _warn=warnings.warn):
            if self._sock is not None:
                _warn(f"unclosed transport {self!r}", ResourceWarning, source=self)
                self._sock.close()

        _ProactorBasePipeTransport.__del__ = pacth_del

    if sys.version_info >= (3, 9, 0):
        from semantic_kernel.orchestration import sk_function as _  # noqa: F401

        # caused by https://github.com/microsoft/semantic-kernel/pull/1416
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
