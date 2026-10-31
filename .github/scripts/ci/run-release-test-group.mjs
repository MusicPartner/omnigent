import { spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const GROUP_IDS = [
  "portable-codex-lifecycle",
  "attachment-cache",
  "attachment-consumers",
  "process-shutdown",
];
const SCRIPT_PATH = fileURLToPath(import.meta.url);
export const REPOSITORY_ROOT = path.resolve(path.dirname(SCRIPT_PATH), "../../..");
const MANIFEST_PATH = new URL("./release-test-groups.json", import.meta.url);

class ReleaseTestGroupError extends Error {}

export function validateManifest(manifest) {
  if (!manifest || typeof manifest !== "object" || Array.isArray(manifest)) {
    throw new ReleaseTestGroupError("Release test group manifest must be an object.");
  }
  if (manifest.schemaVersion !== 1) {
    throw new ReleaseTestGroupError("Release test group manifest schemaVersion must be 1.");
  }

  const { groups } = manifest;
  if (!groups || typeof groups !== "object" || Array.isArray(groups)) {
    throw new ReleaseTestGroupError("Release test group manifest groups must be an object.");
  }
  const groupIds = Object.keys(groups);
  if (groupIds.length !== GROUP_IDS.length || GROUP_IDS.some((id, index) => groupIds[index] !== id)) {
    throw new ReleaseTestGroupError("Release test group manifest must contain the four known groups in order.");
  }
  for (const id of GROUP_IDS) {
    const args = groups[id];
    if (!Array.isArray(args) || args.length < 3 || args.some((arg) => typeof arg !== "string" || arg.length === 0)) {
      throw new ReleaseTestGroupError(`Release test group ${id} must be a non-empty string array.`);
    }
    if (args[0] !== "run" || args[1] !== "pytest") {
      throw new ReleaseTestGroupError(`Release test group ${id} must begin with run pytest.`);
    }
  }
  return manifest;
}

export function getGroupArguments(manifest, groupId) {
  if (!GROUP_IDS.includes(groupId)) {
    throw new ReleaseTestGroupError("Unknown release test group ID.");
  }
  validateManifest(manifest);
  return [...manifest.groups[groupId]];
}

function readManifest() {
  try {
    return JSON.parse(readFileSync(MANIFEST_PATH, "utf8"));
  } catch {
    throw new ReleaseTestGroupError("Unable to read the release test group manifest.");
  }
}

export function runReleaseTestGroup(
  groupId,
  { manifest, spawnSyncImpl = spawnSync, cwd = REPOSITORY_ROOT, env = process.env } = {},
) {
  const args = getGroupArguments(manifest ?? readManifest(), groupId);
  const result = spawnSyncImpl("uv", args, {
    cwd,
    env,
    shell: false,
    stdio: "inherit",
  });
  if (result?.error) {
    const code = typeof result.error.code === "string" && /^[A-Z0-9_]+$/.test(result.error.code)
      ? ` (${result.error.code})`
      : "";
    throw new ReleaseTestGroupError(`Unable to start uv${code}.`);
  }
  if (result?.signal) {
    const signal = typeof result.signal === "string" && /^[A-Z0-9]+$/.test(result.signal)
      ? result.signal
      : "a signal";
    throw new ReleaseTestGroupError(`uv was terminated by ${signal}.`);
  }
  if (!Number.isInteger(result?.status) || result.status < 0) {
    throw new ReleaseTestGroupError("uv exited without a process status.");
  }
  return result.status;
}

export function main(argv, { runGroup = runReleaseTestGroup } = {}) {
  if (!Array.isArray(argv) || argv.length !== 1) {
    throw new ReleaseTestGroupError("Usage: node run-release-test-group.mjs <group-id>.");
  }
  if (!GROUP_IDS.includes(argv[0])) {
    throw new ReleaseTestGroupError("Unknown release test group ID.");
  }
  return runGroup(argv[0]);
}

function isMainModule() {
  return Boolean(process.argv[1]) && path.resolve(process.argv[1]) === path.resolve(SCRIPT_PATH);
}

if (isMainModule()) {
  try {
    process.exitCode = main(process.argv.slice(2));
  } catch (error) {
    const message = error instanceof ReleaseTestGroupError
      ? error.message
      : "Unexpected release test runner failure.";
    console.error(message);
    process.exitCode = 1;
  }
}
