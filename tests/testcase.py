__copyright__ = "Copyright (c) 2026 Alex Laird"
__license__ = "MIT"

import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.normpath(os.path.join(os.path.abspath(os.path.dirname(__file__)), ".."))


class ActionTestCase(unittest.TestCase):
    """
    Runs an action's script the way its ``action.yml`` does: inputs as environment variables, from a git repo working
    directory, with outputs written to ``GITHUB_OUTPUT``. Tests only see what the script does, not what it's written
    in.
    """

    def setUp(self):
        self.work_dir = tempfile.mkdtemp()
        self.fake_bin = tempfile.mkdtemp()
        self.github_output = os.path.join(tempfile.mkdtemp(), "output")
        open(self.github_output, "w").close()

        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "Test")
        self.git("config", "user.email", "test@example.com")

    def tearDown(self):
        for path in [self.work_dir, self.fake_bin, os.path.dirname(self.github_output)]:
            shutil.rmtree(path, ignore_errors=True)

    def run_action(self, action, cwd=None, **env):
        script_dir = os.path.join(ROOT, action)
        python_script = os.path.join(script_dir, f"{action}.py")
        command = [sys.executable, python_script] if os.path.exists(python_script) \
            else ["bash", os.path.join(script_dir, f"{action}.sh")]

        action_env = dict(os.environ,
                          PATH=f"{self.fake_bin}{os.pathsep}{os.environ['PATH']}",
                          GITHUB_OUTPUT=self.github_output,
                          **env)

        return subprocess.run(command, cwd=cwd or self.work_dir, env=action_env, capture_output=True, text=True)

    def outputs(self):
        """
        The outputs written so far, reading both ``name=value`` and multiline ``name<<DELIMITER`` entries.
        """
        values = {}
        with open(self.github_output) as f:
            lines = f.read().splitlines()

        i = 0
        while i < len(lines):
            line = lines[i]
            if "<<" in line and ("=" not in line or line.index("<<") < line.index("=")):
                name, delimiter = line.split("<<", 1)
                end = lines.index(delimiter, i + 1)
                values[name] = "\n".join(lines[i + 1:end])
                i = end + 1
            else:
                name, value = line.split("=", 1)
                values[name] = value
                i += 1

        return values

    def git(self, *args, cwd=None):
        return subprocess.run(["git", *args], cwd=cwd or self.work_dir, check=True, capture_output=True,
                              text=True).stdout.strip()

    def path(self, *parts):
        return os.path.join(self.work_dir, *parts)

    def read(self, *parts):
        with open(self.path(*parts)) as f:
            return f.read()

    def given_file(self, name, content):
        with open(self.path(name), "w") as f:
            f.write(content)

    def given_commit(self, message="commit", *tags):
        self.git("commit", "-q", "--allow-empty", "-m", message)
        for tag in tags:
            self.git("tag", tag)
        return self.git("rev-parse", "HEAD")

    def given_tags(self, *tags):
        return self.given_commit("commit", *tags)

    def given_fake_command(self, name, script):
        path = os.path.join(self.fake_bin, name)
        with open(path, "w") as f:
            f.write(script)
        os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC)

    def assert_succeeds(self, result):
        self.assertEqual(0, result.returncode, f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")

    def assert_fails(self, result):
        self.assertNotEqual(0, result.returncode, f"expected a failure\nstdout:\n{result.stdout}")
