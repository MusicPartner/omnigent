from __future__ import annotations

import ctypes
import ctypes.wintypes


def command_line_to_argv(command_line: str) -> list[str]:
    """Parse a process command line with the native Windows argument rules."""
    shell32 = ctypes.WinDLL("shell32", use_last_error=True)
    shell32.CommandLineToArgvW.argtypes = [
        ctypes.wintypes.LPCWSTR,
        ctypes.POINTER(ctypes.c_int),
    ]
    shell32.CommandLineToArgvW.restype = ctypes.POINTER(ctypes.wintypes.LPWSTR)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    count = ctypes.c_int()
    values = shell32.CommandLineToArgvW(command_line, ctypes.byref(count))
    if not values:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        return [values[index] for index in range(count.value)]
    finally:
        kernel32.LocalFree(values)
