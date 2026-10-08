"""Tests for shared Windows-aware command splitting."""

from __future__ import annotations

import shlex

import pytest

from omnigent.native.shell import split_command


def test_split_command_windows_keeps_backslashes_and_strips_quotes() -> None:
    command = '"C:\\Program Files\\x.exe" -m "@scope/pkg"'
    assert split_command(command, windows=True) == [
        "C:\\Program Files\\x.exe",
        "-m",
        "@scope/pkg",
    ]


def test_split_command_posix_matches_shlex_split() -> None:
    command = "uv tool upgrade 'my pkg' --extra foo"
    assert split_command(command, windows=False) == shlex.split(command)


def test_split_command_unbalanced_quote_raises_on_both_platforms() -> None:
    command = "echo 'unterminated"
    with pytest.raises(ValueError):
        split_command(command, windows=True)
    with pytest.raises(ValueError):
        split_command(command, windows=False)


def test_split_command_windows_leaves_non_matching_token_untouched() -> None:
    assert split_command("a'", windows=True) == ["a'"]
