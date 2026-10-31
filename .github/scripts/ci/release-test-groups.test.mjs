import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";
import {
  getGroupArguments,
  main,
  REPOSITORY_ROOT,
  runReleaseTestGroup,
  validateManifest,
} from "./run-release-test-group.mjs";

const SCRIPT_DIRECTORY = path.dirname(fileURLToPath(import.meta.url));
const manifest = JSON.parse(readFileSync(new URL("./release-test-groups.json", import.meta.url), "utf8"));
const fixture = JSON.parse(
  readFileSync(new URL("./fixtures/release-test-groups.a67684ae.json", import.meta.url), "utf8"),
);
const workflow = readFileSync(new URL("../../workflows/fork-release-ci.yml", import.meta.url), "utf8").replace(/\r\n/g, "\n");
const GROUP_IDS = [
  "portable-codex-lifecycle",
  "attachment-cache",
  "attachment-consumers",
  "process-shutdown",
];
const GROUP_STEPS = [
  ["portable-codex-lifecycle", "Portable Codex lifecycle and platform-scoped fixtures"],
  ["attachment-cache", "Native attachment cache and Windows handle security"],
  ["attachment-consumers", "Native attachment consumers and resume delivery"],
  ["process-shutdown", "Owned process shutdown, native shell discovery and Codex Stop regressions"],
];

function jobSection(jobName, nextJobName) {
  const start = workflow.indexOf(`  ${jobName}:`);
  const end = workflow.indexOf(`  ${nextJobName}:`, start + 1);
  assert.notEqual(start, -1, `missing workflow job ${jobName}`);
  assert.notEqual(end, -1, `missing next workflow job ${nextJobName}`);
  return workflow.slice(start, end);
}

function stepSection(job, stepName) {
  const marker = `      - name: ${stepName}\n`;
  const start = job.indexOf(marker);
  assert.notEqual(start, -1, `missing workflow step ${stepName}`);
  const next = job.indexOf("\n      - name:", start + marker.length);
  return job.slice(start, next === -1 ? job.length : next);
}

test("manifest matches the independently frozen a67684ae baseline argv", () => {
  assert.equal(fixture.baselineSha, "a67684ae0fc2299c8efc2e5f37824c71c8f044a6");
  assert.equal(manifest.schemaVersion, 1);
  assert.deepEqual(Object.keys(manifest.groups), GROUP_IDS);
  assert.deepEqual(manifest.groups, fixture.groups);
  for (const id of GROUP_IDS) {
    assert.deepEqual(getGroupArguments(manifest, id), fixture.groups[id]);
  }
});

test("runner expands each complete uv argv and preserves spawn options", () => {
  const cwd = "C:\\workspaces\\Omnigent 東京\\release test";
  for (const id of GROUP_IDS) {
    let spawnCount = 0;
    const status = runReleaseTestGroup(id, {
      manifest,
      cwd,
      spawnSyncImpl(command, args, options) {
        spawnCount += 1;
        assert.equal(command, "uv");
        assert.deepEqual(args, fixture.groups[id]);
        assert.equal(options.cwd, cwd);
        assert.strictEqual(options.env, process.env);
        assert.equal(options.shell, false);
        assert.equal(options.stdio, "inherit");
        return { status: 0, signal: null, error: null };
      },
    });
    assert.equal(status, 0);
    assert.equal(spawnCount, 1);
  }
  assert.equal(REPOSITORY_ROOT, path.resolve(SCRIPT_DIRECTORY, "../../.."));
});

test("-k selection remains one literal argv element with the original flags", () => {
  const args = fixture.groups["attachment-consumers"];
  const filterIndex = args.indexOf("-k");
  assert.notEqual(filterIndex, -1);
  assert.equal(args[filterIndex + 1], "image or attachment or zip or resize or input_file or path_traversal or connected_builds or replica");
  assert.equal(args[filterIndex + 2], "-n");
  assert.deepEqual(fixture.groups["portable-codex-lifecycle"].slice(-6), ["-n", "0", "-p", "no:cacheprovider", "-q", "-ra"]);
  assert.deepEqual(fixture.groups["attachment-cache"].slice(-6), ["-n", "0", "-p", "no:cacheprovider", "-q", "--timeout=30"]);
  assert.deepEqual(fixture.groups["attachment-consumers"].slice(-6), ["-n", "0", "-p", "no:cacheprovider", "-q", "--timeout=30"]);
  assert.deepEqual(fixture.groups["process-shutdown"].slice(-5), ["-n", "0", "-p", "no:cacheprovider", "-q"]);
});

test("manifest validation rejects malformed groups before spawning", () => {
  const malformed = structuredClone(manifest);
  malformed.groups["attachment-cache"] = ["run", "pytest", 7];
  assert.throws(() => validateManifest(malformed), /non-empty string array/);

  let spawnCount = 0;
  assert.throws(
    () => runReleaseTestGroup("portable-codex-lifecycle", {
      manifest: malformed,
      spawnSyncImpl() {
        spawnCount += 1;
        return { status: 0 };
      },
    }),
    /non-empty string array/,
  );
  assert.equal(spawnCount, 0);

  assert.throws(() => getGroupArguments(manifest, "unknown"), /Unknown release test group ID/);
  assert.throws(() => validateManifest({ ...manifest, schemaVersion: 2 }), /schemaVersion must be 1/);
});

test("runner forwards child status and reports spawn failure or signal as nonzero errors", () => {
  assert.equal(
    runReleaseTestGroup("attachment-cache", {
      manifest,
      spawnSyncImpl: () => ({ status: 23, signal: null }),
    }),
    23,
  );
  assert.throws(
    () => runReleaseTestGroup("attachment-cache", {
      manifest,
      spawnSyncImpl: () => ({ error: Object.assign(new Error("secret-bearing detail"), { code: "ENOENT" }) }),
    }),
    (error) => error.message === "Unable to start uv (ENOENT)." && !error.message.includes("secret-bearing"),
  );
  assert.throws(
    () => runReleaseTestGroup("attachment-cache", {
      manifest,
      spawnSyncImpl: () => ({ status: null, signal: "SIGTERM" }),
    }),
    /uv was terminated by SIGTERM/,
  );
});

test("CLI entry rejects extra arguments without dispatching a group", () => {
  let dispatchCount = 0;
  assert.throws(
    () => main(["portable-codex-lifecycle", "unexpected"], {
      runGroup() {
        dispatchCount += 1;
        return 0;
      },
    }),
    /Usage: node run-release-test-group\.mjs <group-id>/,
  );
  assert.equal(dispatchCount, 0);
});

test("both workflow lanes call the original four named groups once and in order", () => {
  const lanes = [
    jobSection("focused-linux", "windows-native"),
    jobSection("windows-native", "build-windows-artifact"),
  ];
  for (const lane of lanes) {
    const setup = lane.indexOf("      - name: Set up pnpm for desktop shutdown regressions");
    const nodeTest = lane.indexOf("      - name: Release test-group runner contracts");
    assert.notEqual(setup, -1);
    assert.notEqual(nodeTest, -1);
    assert.ok(setup < nodeTest, "pnpm setup must precede the Node contract test");
    const calls = [];
    for (const [id, stepName] of GROUP_STEPS) {
      assert.equal(lane.split(`      - name: ${stepName}\n`).length - 1, 1, `${stepName} must occur once`);
      const command = `node .github/scripts/ci/run-release-test-group.mjs ${id}`;
      assert.equal(lane.split(command).length - 1, 1, `${id} must be invoked once`);
      const step = stepSection(lane, stepName);
      assert.match(step, new RegExp(`run: node \.github/scripts/ci/run-release-test-group\\.mjs ${id}`));
      assert.doesNotMatch(step, /uv run pytest/);
      calls.push({ id, index: lane.indexOf(`      - name: ${stepName}`) });
    }
    assert.deepEqual(calls.map(({ id }) => id), GROUP_IDS);
    assert.ok(nodeTest < calls[0].index, "Node contract tests must precede the Python groups");
    for (let index = 1; index < calls.length; index += 1) {
      assert.ok(calls[index - 1].index < calls[index].index, "release groups must retain their original order");
    }
    assert.ok(
      lane.indexOf("      - name: Install desktop test runtime dependencies without Electron") > calls.at(-1).index,
      "desktop runtime installation must remain after the Python groups",
    );
  }
});

test("isolation branch runs source-matched contracts and exact branch-only audits", () => {
  const triggers = workflow.slice(0, workflow.indexOf("\npermissions:"));
  assert.doesNotMatch(triggers, /windows-parity\/v0\.20-isolation-p3-p5/);
  assert.match(triggers, /workflow_dispatch:/);
  assert.match(workflow, /ISOLATION_SOURCE_SHA: a67684ae0fc2299c8efc2e5f37824c71c8f044a6/);
  assert.match(
    workflow,
    /if: \$\{\{ github\.ref == 'refs\/heads\/windows-parity\/v0\.19-isolation-p1-p2' \|\| github\.ref == 'refs\/heads\/windows-parity\/v0\.20-integration' \|\| github\.ref == 'refs\/heads\/windows-parity\/v0\.20-isolation-p3-p5' \}\}/,
  );
  assert.match(
    workflow,
    /elif \[\[ "\$GITHUB_REF" == refs\/heads\/windows-parity\/v0\.20-isolation-p3-p5 \]\]; then\s+baseline="\$ISOLATION_SOURCE_SHA"\s+git merge-base --is-ancestor "\$baseline" "\$GITHUB_SHA"/,
  );
  assert.match(
    workflow,
    /if: \$\{\{ github\.ref == 'refs\/heads\/windows-parity\/v0\.20-integration' \|\| github\.ref == 'refs\/heads\/windows-parity\/v0\.20-isolation-p3-p5' \}\}/g,
  );
  assert.match(workflow, /baseline="\$RELEASE_SOURCE_SHA"\s+git merge-base --is-ancestor "\$baseline" "\$GITHUB_SHA"/);
  assert.match(workflow, /CONTRACT_TESTS: >-/);
});

test("maintenance candidate buffer owner and paste safety run on both contract platforms", () => {
  const job = jobSection("terminal-preparation-contracts", "focused-linux");
  assert.match(job, /os: \[ubuntu-latest, windows-latest\]/);
  const step = stepSection(job, "Verify candidate buffer routing and paste failure safety");
  assert.match(step, /if: \$\{\{ github\.ref == 'refs\/heads\/windows-parity\/v0\.20-isolation-p3-p5' \}\}/);
  assert.match(step, /tests\/test_native_mux\.py/);
  assert.match(step, /::test_inject_user_message_pastes_content_then_submits/);
  assert.match(step, /::test_inject_user_message_buffer_failure_cleans_file_without_submitting/);
  assert.match(step, /-n 0 --reruns 0 --timeout=30 -p no:cacheprovider -q -ra/);
  assert.match(step, /--junitxml=isolation-buffer-routing\.xml/);
  assert.match(stepSection(job, "Upload candidate buffer routing evidence"), /buffer-routing-\$\{\{ matrix\.os \}\}-\$\{\{ github\.sha \}\}/);
});
