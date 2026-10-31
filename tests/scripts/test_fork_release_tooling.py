"""Independent contracts for fork release workflow helper extraction."""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import re
import subprocess
import zipfile
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
CI = ROOT / ".github" / "scripts" / "ci"
AUDIT_PATH = CI / "audit-platform-markers.py"
AUDIT_FIXTURE = CI / "fixtures" / "platform-markers.bfd8.json"
AUDIT = importlib.util.spec_from_file_location("audit_platform_markers", AUDIT_PATH)
assert AUDIT is not None and AUDIT.loader is not None
_audit = importlib.util.module_from_spec(AUDIT)
AUDIT.loader.exec_module(_audit)
WINDOWS_FIXTURE = CI / "fixtures" / "windows-bundle.e1714.json"
RELEASE_INPUT_FIXTURE = CI / "fixtures" / "release-inputs.e1714.json"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "fork-release-ci.yml"
E1714_SHA = "e1714c416d2608f7bfd5bf4ea93ee81b108d7311"


def _load_script(name: str, filename: str):
    specification = importlib.util.spec_from_file_location(name, CI / filename)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


_wheel_verifier = _load_script("verify_windows_wheel", "verify-windows-wheel.py")
_bundle_assembler = _load_script("assemble_windows_bundle", "assemble-windows-bundle.py")


def _fixture_contract() -> dict:
    return json.loads(AUDIT_FIXTURE.read_text(encoding="utf-8"))


def test_pinned_bfd8_fixture_matches_immutable_git_source_symbols_and_decorators() -> None:
    fixture = _fixture_contract()
    assert fixture["baselineSha"] == "bfd8ab5624e34aa72c01fb451e11c2a0e1aae3ee"
    for path, expected in fixture["snapshots"].items():
        source = subprocess.check_output(
            ["git", "show", f"{fixture['baselineSha']}:{path}"], cwd=ROOT
        )
        tree = ast.parse(source, filename=path)
        actual = _audit._snapshot(tree)
        assert actual == (expected["testCount"], expected["testDecoratorsSha256"]), path


def test_candidate_retains_pinned_symbols_and_approved_platform_decorators() -> None:
    results = _audit.audit_repository(ROOT, "bfd8ab5624e34aa72c01fb451e11c2a0e1aae3ee")
    assert len(results) == 5
    assert all("target tests retained" in result for result in results)


def test_workflow_policy_and_release_inputs_match_immutable_e1714() -> None:
    original = subprocess.check_output(
        ["git", "show", f"{E1714_SHA}:.github/workflows/fork-release-ci.yml"], cwd=ROOT, text=True
    )
    candidate = WORKFLOW_PATH.read_text(encoding="utf-8")
    baseline_workflow = yaml.load(original, Loader=yaml.BaseLoader)
    candidate_workflow = yaml.load(candidate, Loader=yaml.BaseLoader)
    assert baseline_workflow["on"] == candidate_workflow["on"]
    for key in ("permissions", "concurrency", "env"):
        assert baseline_workflow[key] == candidate_workflow[key]
    assert list(baseline_workflow["jobs"]) == list(candidate_workflow["jobs"])

    extracted_steps = {
        "Stage candidate release inputs",
        "Fork release tooling contracts",
        "Release input staging contracts",
        "Verify approved relay capability and reader safety",
    }
    changed_commands = {
        "Audit reconciled test symbols and platform marker owners",
        "Build optional native launcher candidate",
        "Assert bundled web UI, native asset and console entry points",
        "Assemble Windows bundle",
    }
    expected_additions = {
        "terminal-preparation-contracts": [
            "Stage candidate release inputs",
            "Fork release tooling contracts",
            "Verify approved relay capability and reader safety",
        ],
        "focused-linux": ["Release input staging contracts"],
        "windows-native": ["Release input staging contracts"],
        "build-windows-artifact": ["Stage candidate release inputs"],
        "build-windows-desktop-artifact": [],
    }
    moved_inputs = {
        "CHARACTERIZATION_SHA",
        "VALIDATED_BASE_SHA",
        "RELEASE_SOURCE_SHA",
        "ISOLATION_SOURCE_SHA",
        "CONTRACT_TESTS",
    }
    for job_name, baseline_job in baseline_workflow["jobs"].items():
        candidate_job = candidate_workflow["jobs"][job_name]
        policy_keys = (
            "name",
            "if",
            "needs",
            "runs-on",
            "timeout-minutes",
            "strategy",
            "permissions",
        )
        for key in policy_keys:
            assert baseline_job.get(key) == candidate_job.get(key), (job_name, key)
        baseline_env = dict(baseline_job.get("env", {}))
        candidate_env = dict(candidate_job.get("env", {}))
        if job_name == "terminal-preparation-contracts":
            baseline_env = {
                key: value for key, value in baseline_env.items() if key not in moved_inputs
            }
        assert baseline_env == candidate_env, (job_name, "env")

        old_steps = baseline_job["steps"]
        new_steps = candidate_job["steps"]
        old_names = [step.get("name", step.get("uses")) for step in old_steps]
        new_names = [step.get("name", step.get("uses")) for step in new_steps]
        assert [name for name in new_names if name in extracted_steps] == (
            expected_additions[job_name]
        )
        assert [name for name in new_names if name not in extracted_steps] == old_names, job_name
        new_by_name = {step.get("name", step.get("uses")): step for step in new_steps}
        for old_step in old_steps:
            name = old_step.get("name", old_step.get("uses"))
            new_step = new_by_name[name]
            for key in ("uses", "if", "with", "shell", "env", "working-directory", "id"):
                expected = old_step.get(key)
                if name == "Upload baseline and candidate contract evidence" and key == "with":
                    expected = dict(expected)
                    expected["path"] = expected["path"].replace(
                        "isolation-candidate.xml\n",
                        "isolation-candidate.xml\nisolation-relay-capability.xml\n",
                    )
                assert expected == new_step.get(key), (job_name, name, key)
            if name not in changed_commands:
                assert old_step.get("run") == new_step.get("run"), (job_name, name, "run")

    release_fixture = json.loads(RELEASE_INPUT_FIXTURE.read_text(encoding="utf-8"))
    manifest = json.loads((CI / "release-inputs.json").read_text(encoding="utf-8"))
    original_inputs = baseline_workflow["jobs"]["terminal-preparation-contracts"]["env"]
    release_sha_fields = (
        "CHARACTERIZATION_SHA",
        "VALIDATED_BASE_SHA",
        "RELEASE_SOURCE_SHA",
        "ISOLATION_SOURCE_SHA",
    )
    for key in release_sha_fields:
        assert manifest[key] == original_inputs[key] == release_fixture["inputs"][key]
    assert manifest["CONTRACT_TESTS"] == original_inputs["CONTRACT_TESTS"].split()
    assert manifest["CONTRACT_TESTS"] == release_fixture["inputs"]["CONTRACT_TESTS"]
    launcher_command = baseline_workflow["jobs"]["build-windows-artifact"]["steps"]
    launcher_step = next(
        step
        for step in launcher_command
        if step.get("name") == "Build optional native launcher candidate"
    )
    pins = re.search(r"--toolset-version ([0-9.]+).*--sdk-version ([0-9.]+)", launcher_step["run"])
    assert pins is not None
    assert manifest["WINDOWS_LAUNCHER_TOOLSET_VERSION"] == pins.group(1)
    assert pins.group(1) == release_fixture["inputs"]["WINDOWS_LAUNCHER_TOOLSET_VERSION"]
    assert manifest["WINDOWS_SDK_VERSION"] == pins.group(2)
    assert pins.group(2) == release_fixture["inputs"]["WINDOWS_SDK_VERSION"]
    terminal_steps = baseline_workflow["jobs"]["terminal-preparation-contracts"]["steps"]
    checkout_index = next(
        i
        for i, step in enumerate(terminal_steps)
        if step.get("name") == "Check out isolation candidate"
    )
    selection_index = next(
        i
        for i, step in enumerate(terminal_steps)
        if step.get("name") == "Select the source-matched baseline implementation"
    )
    candidate_steps = candidate_workflow["jobs"]["terminal-preparation-contracts"]["steps"]
    stage_index = next(
        i
        for i, step in enumerate(candidate_steps)
        if step.get("name") == "Stage candidate release inputs"
    )
    candidate_selection_index = next(
        i
        for i, step in enumerate(candidate_steps)
        if step.get("name") == "Select the source-matched baseline implementation"
    )
    assert checkout_index < selection_index
    assert stage_index < candidate_selection_index
    assert '--stage "$RUNNER_TEMP/omnigent-release-inputs"' in candidate_steps[stage_index]["run"]
    candidate_launcher_step = next(
        step
        for step in candidate_workflow["jobs"]["build-windows-artifact"]["steps"]
        if step.get("name") == "Build optional native launcher candidate"
    )
    assert "WINDOWS_LAUNCHER_TOOLSET_VERSION" in candidate_launcher_step["run"]


def test_reconciliation_gate_is_separate_from_frozen_contract_selection() -> None:
    workflow = yaml.load(WORKFLOW_PATH.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    steps = workflow["jobs"]["terminal-preparation-contracts"]["steps"]
    gate = next(
        step
        for step in steps
        if step.get("name") == "Verify approved relay capability and reader safety"
    )
    assert gate["if"] == "${{ github.ref == 'refs/heads/windows-parity/v0.20-isolation-p3-p5' }}"
    assert "test_windows_claude_role_launch_uses_supported_status_fallback" in gate["run"]
    assert "test_windows_reader_uses_non_signalling_probe" in gate["run"]
    assert "--reruns 0" in gate["run"]
    assert "isolation-relay-capability.xml" in gate["run"]


def test_bundle_body_fixture_matches_immutable_e1714_workflow() -> None:
    fixture = json.loads(WINDOWS_FIXTURE.read_text(encoding="utf-8"))
    original = subprocess.check_output(
        ["git", "show", f"{E1714_SHA}:.github/workflows/fork-release-ci.yml"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
    )
    workflow = yaml.load(original, Loader=yaml.BaseLoader)
    steps = workflow["jobs"]["build-windows-artifact"]["steps"]
    assemble_step = next(step for step in steps if step.get("name") == "Assemble Windows bundle")
    pattern = re.compile(
        r"@'\n(.*?)\n'@ \| Set-Content -Encoding (ascii|utf8) "
        r"windows-bundle\\(INSTALL\.cmd|UNINSTALL\.cmd|README\.txt)",
        re.DOTALL,
    )
    bodies = {name: body + "\n" for body, _encoding, name in pattern.findall(assemble_step["run"])}
    assert bodies["INSTALL.cmd"] == fixture["installCommand"]
    assert bodies["UNINSTALL.cmd"] == fixture["uninstallCommand"]
    readme = fixture["readmeTemplate"].replace(
        "   .\\install.ps1 -NoSystemCertificates",
        fixture["readmeNoSystemCertificatesLine"],
    )
    assert bodies["README.txt"] == readme


def test_audit_rejects_missing_test_symbol() -> None:
    path = "tests/example.py"
    baseline = "import pytest\ndef test_kept():\n    pass\ndef test_removed():\n    pass\n"
    candidate = "import pytest\ndef test_kept():\n    pass\n"
    with pytest.raises(_audit.PlatformMarkerAuditError, match="missing test symbols"):
        _audit.audit_source_pair(path, baseline, candidate, {"gatewayFailure": {}})


def test_audit_rejects_lost_decorator() -> None:
    path = "tests/example.py"
    baseline = "import pytest\n@pytest.mark.timeout(20)\ndef test_kept():\n    pass\n"
    candidate = "import pytest\ndef test_kept():\n    pass\n"
    with pytest.raises(_audit.PlatformMarkerAuditError, match="lost decorator"):
        _audit.audit_source_pair(path, baseline, candidate, {"gatewayFailure": {}})


def test_audit_rejects_an_unexpected_decorator() -> None:
    path = "tests/example.py"
    baseline = "import pytest\ndef test_kept():\n    pass\n"
    candidate = "import pytest\n@pytest.mark.skip\ndef test_kept():\n    pass\n"
    with pytest.raises(
        _audit.PlatformMarkerAuditError,
        match="unexpected or misplaced decorators",
    ):
        _audit.audit_source_pair(path, baseline, candidate, {"gatewayFailure": {}})


def test_audit_rejects_a_platform_marker_moved_to_the_wrong_owner() -> None:
    path = "tests/slow_ready.py"
    first = "test_first_message_survives_slow_terminal_startup"
    second = "test_slash_command_waits_for_a_silently_booting_terminal"
    baseline = f"import pytest\ndef {first}():\n    pass\ndef {second}():\n    pass\n"
    candidate = (
        "import pytest\n"
        f"def {first}():\n    pass\n"
        f"@pytest.mark.posix_only\ndef {second}():\n    pass\n"
    )
    fixture = {"expectedPosix": {path: [first]}, "gatewayFailure": {}}
    with pytest.raises(
        _audit.PlatformMarkerAuditError,
        match="unexpected or misplaced decorators",
    ):
        _audit.audit_source_pair(path, baseline, candidate, fixture)


def test_audit_rejects_a_changed_tmux_psmux_matrix() -> None:
    path = "tests/bridge.py"
    name = "test_inject_user_message_pastes_content_then_submits"
    baseline = f"import pytest\ndef {name}():\n    pass\n"
    candidate = (
        "import pytest\n"
        '@pytest.mark.parametrize("windows", [True, False], ids=["psmux", "tmux"])\n'
        f"def {name}():\n    pass\n"
    )
    fixture = {"expectedWindowsMatrix": {path: [name]}, "gatewayFailure": {}}
    with pytest.raises(
        _audit.PlatformMarkerAuditError,
        match="unexpected or misplaced decorators",
    ):
        _audit.audit_source_pair(path, baseline, candidate, fixture)


def test_audit_keeps_gateway_failure_cases_exact_and_portable() -> None:
    fixture = _fixture_contract()
    gateway = fixture["gatewayFailure"]
    baseline = f"import pytest\n@{gateway['target']}\ndef {gateway['test']}():\n    pass\n"
    candidate = f"import pytest\n@{gateway['portable']}\ndef {gateway['test']}():\n    pass\n"
    assert _audit.audit_source_pair(gateway["path"], baseline, candidate, fixture) == 1
    changed = candidate.replace("time.sleep(30)", "time.sleep(31)")
    with pytest.raises(_audit.PlatformMarkerAuditError, match="portable gateway cases changed"):
        _audit.audit_source_pair(gateway["path"], baseline, changed, fixture)


def _write_wheel(path: Path, *, include_ui: bool = True, valid_digest: bool = True) -> bytes:
    asset = b"pinned launcher resource bytes"
    digest = hashlib.sha256(asset if valid_digest else b"other bytes").hexdigest()
    manifest = json.dumps(
        {
            "filename": "private_job_launcher-x64.exe",
            "sha256": digest,
            "build": {"reproducible_verified": True},
        }
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("omnigent/resources/windows_launcher/manifest.json", manifest)
        archive.writestr("omnigent/resources/windows_launcher/private_job_launcher-x64.exe", asset)
        if include_ui:
            archive.writestr("omnigent/server/static/web-ui/index.html", "<main />")
            archive.writestr("omnigent/server/static/web-ui/app.js", "boot()")
        archive.writestr(
            "omnigent-0.20.0.dist-info/entry_points.txt",
            "[console_scripts]\nomni = omnigent.cli:main\nomnigent = omnigent.cli:main\n",
        )
    return asset


def test_wheel_verifier_preserves_resource_ui_and_console_entrypoint_checks(
    tmp_path: Path,
) -> None:
    fixture = json.loads(WINDOWS_FIXTURE.read_text(encoding="utf-8"))
    wheel = tmp_path / "omnigent-0.20.0-py3-none-any.whl"
    _write_wheel(wheel)

    assert _wheel_verifier.verify_wheel(
        tmp_path,
        expected_version=fixture["expectedVersion"],
        source_sha=fixture["sourceSha"],
    ) == str(wheel)


@pytest.mark.parametrize(
    ("include_ui", "valid_digest", "failure"),
    [
        (False, True, "web UI bundle missing"),
        (True, False, "native asset digest mismatch"),
    ],
)
def test_wheel_verifier_rejects_existing_resource_and_ui_failures(
    tmp_path: Path, include_ui: bool, valid_digest: bool, failure: str
) -> None:
    _write_wheel(
        tmp_path / "omnigent-0.20.0-py3-none-any.whl",
        include_ui=include_ui,
        valid_digest=valid_digest,
    )
    with pytest.raises(_wheel_verifier.WheelVerificationError, match=failure):
        _wheel_verifier.verify_wheel(
            tmp_path,
            expected_version="0.20.0",
            source_sha="e1714c416d2608f7bfd5bf4ea93ee81b108d7311",
        )


def test_wheel_verifier_does_not_add_a_single_wheel_cardinality_rule(tmp_path: Path) -> None:
    first = tmp_path / "omnigent-0.19.0-py3-none-any.whl"
    last = tmp_path / "omnigent-0.20.0-py3-none-any.whl"
    _write_wheel(first)
    _write_wheel(last)

    assert _wheel_verifier.verify_wheel(
        tmp_path,
        expected_version="0.20.0",
        source_sha="e1714c416d2608f7bfd5bf4ea93ee81b108d7311",
    ) == str(last)


def test_bundle_assembly_preserves_template_bytes_layout_and_wheel_checksums(
    tmp_path: Path,
) -> None:
    fixture = json.loads(WINDOWS_FIXTURE.read_text(encoding="utf-8"))
    repository = tmp_path / "repository"
    for source_name in _bundle_assembler.BUNDLE_FILES:
        source = repository / source_name
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text(f"fixture:{source_name}\n", encoding="utf-8")
    wheels = tmp_path / "dist"
    wheels.mkdir()
    wheel_bytes = {
        "omnigent-0.20.0-py3-none-any.whl": b"core wheel fixture",
        "omnigent_client-0.20.0-py3-none-any.whl": b"client wheel fixture",
        "omnigent_ui_sdk-0.20.0-py3-none-any.whl": b"ui sdk wheel fixture",
        "other-0.20.0-py3-none-any.whl": b"additional wheel remains allowed",
    }
    for filename, contents in wheel_bytes.items():
        (wheels / filename).write_bytes(contents)
    output = tmp_path / "windows-bundle"

    _bundle_assembler.assemble_bundle(
        repository,
        wheels,
        output,
        expected_version=fixture["expectedVersion"],
        source_sha=fixture["sourceSha"],
    )

    expected_names = {
        "INSTALL.cmd",
        "UNINSTALL.cmd",
        "README.txt",
        "WINDOWS-README.md",
        "TESTING.md",
        "install.ps1",
        "uninstall.ps1",
        "windows_safe_pytest.ps1",
        "SHA256SUMS.txt",
        "wheels",
    }
    assert {path.name for path in output.iterdir()} == expected_names
    newline = "\r\n" if fixture["lineEnding"] == "CRLF" else "\n"
    expected_install = fixture["installCommand"].replace("\n", newline).encode("ascii")
    expected_uninstall = fixture["uninstallCommand"].replace("\n", newline).encode("ascii")
    assert (output / "INSTALL.cmd").read_bytes() == expected_install
    assert (output / "UNINSTALL.cmd").read_bytes() == expected_uninstall
    readme = fixture["readmeTemplate"].replace(
        "   .\\install.ps1 -NoSystemCertificates",
        fixture["readmeNoSystemCertificatesLine"],
    )
    assert (output / "README.txt").read_bytes() == readme.replace("\n", newline).encode("utf-8")
    assert {path.name for path in (output / "wheels").iterdir()} == set(wheel_bytes)
    expected_sums = (
        "\r\n".join(
            f"{hashlib.sha256(contents).hexdigest()}  {filename}"
            for filename, contents in sorted(wheel_bytes.items())
        )
        + "\r\n"
    )
    assert (output / "SHA256SUMS.txt").read_bytes() == expected_sums.encode("ascii")


def test_bundle_assembly_requires_wheels_but_not_a_specific_wheel_count(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    for source_name in _bundle_assembler.BUNDLE_FILES:
        source = repository / source_name
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text("source\n", encoding="utf-8")
    wheels = tmp_path / "dist"
    wheels.mkdir()
    (wheels / "first.whl").write_bytes(b"first")
    (wheels / "second.whl").write_bytes(b"second")
    output = tmp_path / "bundle"

    _bundle_assembler.assemble_bundle(
        repository,
        wheels,
        output,
        expected_version="0.20.0",
        source_sha="e1714c416d2608f7bfd5bf4ea93ee81b108d7311",
    )
    assert len(list((output / "wheels").glob("*.whl"))) == 2
    with pytest.raises(_bundle_assembler.BundleAssemblyError, match="No wheel artifacts"):
        _bundle_assembler.assemble_bundle(
            repository,
            tmp_path / "empty-dist",
            tmp_path / "empty-bundle",
            expected_version="0.20.0",
            source_sha="e1714c416d2608f7bfd5bf4ea93ee81b108d7311",
        )
