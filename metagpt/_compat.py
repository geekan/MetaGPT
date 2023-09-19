import platform
import sys
import warnings

if sys.implementation.name == "cpython" and platform.system() == "Windows" and sys.version_info[:2] == (3, 9):
    # https://github.com/python/cpython/pull/92842

    from asyncio.proactor_events import _ProactorBasePipeTransport

    def pacth_del(self, _warn=warnings.warn):
        if self._sock is not None:
            _warn(f"unclosed transport {self!r}", ResourceWarning, source=self)
            self._sock.close()

    _ProactorBasePipeTransport.__del__ = pacth_del
