"""UI launcher가 현재 작업 폴더와 무관하게 실행되는지 시험."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


class UiLauncherTests(unittest.TestCase):
    def test_check_works_outside_project_directory(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        launcher = project_root / "run_ui.py"
        result = self._run_check_outside_project(launcher)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("UI launcher import check: OK", result.stdout)

    def test_app_file_check_works_when_executed_directly(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        app_file = project_root / "app.py"
        result = self._run_check_outside_project(app_file)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("UI launcher import check: OK", result.stdout)

    def test_check_works_after_project_is_copied(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporary_root:
            copied_project = Path(temporary_root) / "copied-project"
            copied_project.mkdir()
            shutil.copy2(project_root / "app.py", copied_project / "app.py")
            shutil.copy2(project_root / "run_ui.py", copied_project / "run_ui.py")
            shutil.copytree(
                project_root / "src",
                copied_project / "src",
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
            )
            result = subprocess.run(
                [sys.executable, str(copied_project / "app.py"), "--check"],
                cwd=temporary_root,
                env=self._test_environment(),
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("UI launcher import check: OK", result.stdout)

    def _run_check_outside_project(
        self,
        script: Path,
    ) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as other_directory:
            return subprocess.run(
                [sys.executable, str(script), "--check"],
                cwd=other_directory,
                env=self._test_environment(),
                capture_output=True,
                text=True,
                check=False,
            )

    def _test_environment(self) -> dict[str, str]:
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        return environment


if __name__ == "__main__":
    unittest.main()
