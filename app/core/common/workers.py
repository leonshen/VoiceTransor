# -*- coding: utf-8 -*-
"""Thread helpers to run plain functions in a QThreadPool safely."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable, Optional
from PySide6.QtCore import QObject, Signal, QRunnable, Slot

def _enable_dbg():  
    try:
        import debugpy
        if debugpy.is_client_connected():  
            debugpy.debug_this_thread()    
    except Exception:
        pass

def _dbg_inject_breakpoint():
    import os, sys, threading, time
    print(f"[DBG] ENTER worker  pid={os.getpid()} tid={threading.get_ident()} file={__file__} exe={sys.executable}")
    try:
        import debugpy
        if not debugpy.is_client_connected():
            debugpy.wait_for_client()
        debugpy.breakpoint()
    except Exception as e:
        print("[DBG] debug hook failed:", e)
    time.sleep(0.05)
    


class WorkerSignals(QObject):
    """Qt signals emitted by a background task."""
    started = Signal()
    message = Signal(str)
    # percent [0..100], secs_done, secs_total, eta_secs
    progress = Signal(int, float, float, float)
    error = Signal(str)
    result = Signal(object)
    finished = Signal()

    # NEW: for transcript UI streaming
    partial_text   = Signal(str)  # per-chunk text to append
    bootstrap_text = Signal(str)  # initial resume text
    
@dataclass
class TaskSpec:
    """Function plus arguments to be executed in background."""
    fn: Callable[..., Any]
    args: tuple
    kwargs: dict


class FunctionRunnable(QRunnable):
    """Run a plain Python function in Qt's thread pool with signals.

    Notes:
        We set `setAutoDelete(False)` and let the GUI hold a reference to the
        runnable until `finished` arrives. This avoids premature deletion that
        sometimes crashes Python on Windows when signals arrive late.
    """
    def __init__(self, task: TaskSpec, signals: Optional[WorkerSignals] = None) -> None:
        super().__init__()
        self.setAutoDelete(False)  # crucial: manual lifetime management
        self.task = task
        self.signals = signals or WorkerSignals()

    @Slot()
    def run(self) -> None:
        def _emit(sig, *args):
            try:
                sig.emit(*args)
            except RuntimeError:
                # Signal source deleted during app shutdown; ignore.
                return

        try:
            _emit(self.signals.started)
            res = self.task.fn(*self.task.args, **self.task.kwargs)
            _emit(self.signals.result, res)
        except Exception as e:
            _emit(self.signals.error, str(e))
        finally:
            _emit(self.signals.finished)
