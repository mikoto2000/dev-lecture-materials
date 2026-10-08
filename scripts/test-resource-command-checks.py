#!/usr/bin/env python3
"""Test observation assertions/command bounds without claiming Docker coverage."""
from __future__ import annotations

import contextlib
import importlib.util
import io
from pathlib import Path
import sys
import unittest
from unittest import mock

sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location(
    "compose_monitoring", Path(__file__).with_name("test-compose-monitoring.py"))
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)

SPACE = "Filesystem Size Used Avail Use% Mounted on\n/dev/test 100G 99G 1G 99% /lab/.state\n"
INODES = "Filesystem Inodes IUsed IFree IUse% Mounted on\n/dev/test 1000 999 1 100% /lab/.state\n"
STATS_HEADER = "CONTAINER ID NAME CPU % MEM USAGE / LIMIT MEM % NET I/O BLOCK I/O PIDS\n"
PING = "3 packets transmitted, 3 received, 0% packet loss, time 2000ms\n"


def stats(service):
    # Large values are legitimate observations, not portable failure thresholds.
    return (STATS_HEADER + f"abcdef123456 {lab.PROJECT}-{service}-1 250.00% "
            "950MiB / 1GiB 92.77% 1kB / 2kB 3kB / 4kB 999\n")


class ObservationTests(unittest.TestCase):
    def setUp(self):
        self.capture = contextlib.redirect_stdout(io.StringIO())
        self.capture.__enter__()
        self.addCleanup(self.capture.__exit__, None, None, None)

    def test_resources_have_scoped_commands_and_timeouts(self):
        with mock.patch.object(lab, "compose", side_effect=[SPACE, INODES, stats("demo"), stats("kuma")]) as run:
            lab.observe_resources()
        self.assertEqual(run.call_args_list, [
            mock.call("exec", "-T", "demo", "df", "-h", "/lab/.state", timeout=15),
            mock.call("exec", "-T", "demo", "df", "-i", "/lab/.state", timeout=15),
            mock.call("stats", "--no-stream", "demo", timeout=30),
            mock.call("stats", "--no-stream", "kuma", timeout=30),
        ])

    def test_resource_output_must_identify_requested_observation(self):
        for outputs in (
            ["", INODES, stats("demo"), stats("kuma")],
            [SPACE.replace("/lab/.state", "/"), INODES, stats("demo"), stats("kuma")],
            [SPACE, SPACE, stats("demo"), stats("kuma")],
            [SPACE, INODES, stats("demo").replace("PIDS", "OTHER"), stats("kuma")],
            [SPACE, INODES, stats("demo").replace(lab.PROJECT, "another-project"), stats("kuma")],
            [SPACE, INODES, stats("demo") + stats("kuma"), stats("kuma")],
        ):
            with self.subTest(outputs=outputs), mock.patch.object(lab, "compose", side_effect=outputs):
                with self.assertRaises(AssertionError):
                    lab.observe_resources()

    def test_dns_and_ping_have_one_target_and_timeouts(self):
        with mock.patch.object(lab, "compose", side_effect=["172.20.0.2 demo\n", PING]) as run:
            lab.observe_network()
        self.assertEqual(run.call_args_list, [
            mock.call("exec", "-T", "kuma", "getent", "hosts", "demo", timeout=15),
            mock.call("exec", "-T", "kuma", "ping", "-c", "3", "-W", "1", "-w", "5", "demo", timeout=15),
        ])

    def test_dns_requires_an_address(self):
        for output in ("", "demo\n", "not-an-ip demo\n"):
            with self.subTest(output=output), mock.patch.object(lab, "compose", return_value=output):
                with self.assertRaises((AssertionError, ValueError)):
                    lab.observe_network()

    def test_ping_requires_the_three_probe_summary(self):
        for output in ("", "3 packets transmitted, 0 received, 100% packet loss\n"):
            with self.subTest(output=output), mock.patch.object(lab, "compose", return_value=output):
                with self.assertRaises(AssertionError):
                    lab.ping_demo()


if __name__ == "__main__":
    unittest.main()
