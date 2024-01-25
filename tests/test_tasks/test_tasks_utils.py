"""
The MIT License (MIT)

Copyright (c) 2020 David Montague

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

https://github.com/dmontagu/fastapi-utils
"""

import asyncio
import logging
import time
from asyncio import AbstractEventLoop
from typing import Any, NoReturn

import pytest
from _pytest.capture import CaptureFixture
from _pytest.logging import LogCaptureFixture

from ukrdc_fastapi.tasks.utils import repeat_every

logging.basicConfig(level=logging.INFO)


def ignore_exception(_loop: AbstractEventLoop, _context: dict[str, Any]) -> None:
    pass


@pytest.fixture(autouse=True)
def setup_event_loop(event_loop: AbstractEventLoop) -> None:
    event_loop.set_exception_handler(ignore_exception)


@pytest.mark.asyncio
async def test_repeat_print(capsys: CaptureFixture[str]) -> None:
    @repeat_every(seconds=0.01, max_repetitions=3)
    async def repeatedly_print_hello() -> None:
        print("hello")

    await repeatedly_print_hello()
    await asyncio.sleep(0.1)
    out, err = capsys.readouterr()
    assert out == "hello\n" * 3
    assert err == ""


@pytest.mark.asyncio
async def test_repeat_print_delay(capsys: CaptureFixture[str]) -> None:
    @repeat_every(seconds=0.07, max_repetitions=3)
    def repeatedly_print_hello() -> None:
        print("hello")

    await repeatedly_print_hello()
    await asyncio.sleep(0.1)
    out, err = capsys.readouterr()
    assert out == "hello\n" * 2
    assert err == ""


@pytest.mark.asyncio
async def test_repeat_print_wait(capsys: CaptureFixture[str]) -> None:
    @repeat_every(seconds=0.07, max_repetitions=3, wait_first=True)
    def repeatedly_print_hello() -> None:
        print("hello")

    await repeatedly_print_hello()
    await asyncio.sleep(0.1)
    out, err = capsys.readouterr()
    assert out == "hello\n" * 1
    assert err == ""


@pytest.mark.asyncio
async def test_repeat_unlogged_error(caplog: LogCaptureFixture) -> None:
    @repeat_every(seconds=0.07, max_repetitions=None)
    def log_exc() -> NoReturn:
        raise ValueError("repeat")

    await log_exc()
    await asyncio.sleep(0.1)
    record_tuples = [x for x in caplog.record_tuples if x[0] == __name__]
    print(caplog.record_tuples)
    assert len(record_tuples) == 0


@pytest.mark.asyncio
async def test_repeat_log_error(caplog: LogCaptureFixture) -> None:
    logger = logging.getLogger(__name__)

    @repeat_every(seconds=0.1, max_repetitions=None, logger=logger)
    def log_exc() -> NoReturn:
        raise ValueError("repeat")

    await log_exc()
    n_record_tuples = 0
    record_tuples: list[tuple[Any, ...]] = []
    start_time = time.time()
    while n_record_tuples < 2:  # ensure multiple records are logged
        time_elapsed = time.time() - start_time
        if time_elapsed > 1:
            print(record_tuples)
            assert False, "Test timed out"
        await asyncio.sleep(0.05)
        record_tuples = [x for x in caplog.record_tuples if x[0] == __name__]
        n_record_tuples = len(record_tuples)


@pytest.mark.asyncio
async def test_repeat_raise_error(caplog: LogCaptureFixture, capsys: CaptureFixture[str]) -> None:
    logger = logging.getLogger(__name__)

    @repeat_every(seconds=0.07, max_repetitions=None, raise_exceptions=True, logger=logger)
    def raise_exc() -> NoReturn:
        raise ValueError("repeat")

    await raise_exc()
    await asyncio.sleep(0.1)
    out, err = capsys.readouterr()
    assert out == ""
    assert err == ""
    record_tuples = [x for x in caplog.record_tuples if x[0] == __name__]
    print(caplog.record_tuples)
    assert len(record_tuples) == 1