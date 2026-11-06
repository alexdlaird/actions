__copyright__ = "Copyright (c) 2026 Alex Laird"
__license__ = "MIT"

import os
import subprocess
import time

from tests.testcase import ROOT, ActionTestCase

SCRIPT = os.path.join(ROOT, "ios-deploy-lock", "ios-deploy-lock.sh")


class TestIosDeployLock(ActionTestCase):
    def setUp(self):
        super().setUp()
        self.lock = os.path.join(self.work_dir, "ios-deploy.lock")
        self.jobs = []

    def tearDown(self):
        for job in self.jobs:
            if job.poll() is None:
                job.kill()
                job.wait()
        super().tearDown()

    def env(self, run_id, mode="acquire"):
        return dict(os.environ, MODE=mode, LOCK_PATH=self.lock, STALE_MINUTES="110", POLL_SECONDS="0.2",
                    GITHUB_REPOSITORY="owner/app", GITHUB_RUN_ID=str(run_id), GITHUB_RUN_ATTEMPT="1")

    def given_job_holding_the_lock(self, run_id):
        step = os.path.join(self.fake_bin, "step.sh")
        with open(step, "w") as f:
            f.write(f'"{SCRIPT}"\n')
        worker = os.path.join(self.fake_bin, "Runner.Worker")
        with open(worker, "w") as f:
            f.write(f'#!/bin/bash\nbash --noprofile --norc -e -o pipefail "{step}"\nsleep 60\n')
        os.chmod(worker, 0o755)
        job = subprocess.Popen(["bash", worker], env=self.env(run_id), stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
        self.jobs.append(job)
        owner = os.path.join(self.lock, "owner")
        deadline = time.time() + 10
        while not (os.path.exists(owner) and open(owner).read().strip()):
            self.assertLess(time.time(), deadline, "the job never took the lock")
            time.sleep(0.05)
        return job

    def acquire(self, run_id, timeout):
        return subprocess.run(["bash", SCRIPT], env=self.env(run_id), capture_output=True, text=True,
                              timeout=timeout)

    def test_a_job_keeps_the_lock_after_the_step_that_took_it_ends(self):
        # GIVEN
        self.given_job_holding_the_lock(1)

        # WHEN / THEN
        with self.assertRaises(subprocess.TimeoutExpired, msg="a second deploy must wait while the first job runs"):
            self.acquire(2, timeout=2)

    def test_the_lock_is_broken_once_the_holding_job_is_gone(self):
        # GIVEN
        job = self.given_job_holding_the_lock(1)
        job.kill()
        job.wait()

        # WHEN
        result = self.acquire(2, timeout=10)

        # THEN
        self.assert_succeeds(result)
        self.assertIn("Breaking a stale lock held by owner/app run 1 attempt 1", result.stdout)
        with open(os.path.join(self.lock, "owner")) as f:
            self.assertTrue(f.read().endswith("owner/app run 2 attempt 1\n"))

    def test_a_lock_from_before_the_fix_naming_an_ended_step_is_broken(self):
        # GIVEN
        ended = subprocess.Popen(["true"])
        ended.wait()
        os.mkdir(self.lock)
        with open(os.path.join(self.lock, "owner"), "w") as f:
            f.write(f"{ended.pid} owner/app run 1 attempt 1\n")

        # WHEN
        result = self.acquire(2, timeout=10)

        # THEN
        self.assert_succeeds(result)

    def test_only_the_holder_releases_the_lock(self):
        # GIVEN
        self.given_job_holding_the_lock(1)

        # WHEN
        other = subprocess.run(["bash", SCRIPT], env=self.env(2, mode="release"), capture_output=True, text=True)

        # THEN
        self.assert_succeeds(other)
        self.assertTrue(os.path.exists(self.lock), "another job's release leaves it held")

        # WHEN
        holder = subprocess.run(["bash", SCRIPT], env=self.env(1, mode="release"), capture_output=True, text=True)

        # THEN
        self.assert_succeeds(holder)
        self.assertFalse(os.path.exists(self.lock), "released by the job that took it")
