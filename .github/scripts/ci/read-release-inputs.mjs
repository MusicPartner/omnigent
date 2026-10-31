import { copyFileSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const SCRIPT_PATH = fileURLToPath(import.meta.url);
const SCRIPT_DIRECTORY = path.dirname(SCRIPT_PATH);
const INPUTS_FILENAME = "release-inputs.json";
const SCRIPT_FILENAME = "read-release-inputs.mjs";
const RELEASE_SHA_FIELDS = [
  "CHARACTERIZATION_SHA",
  "VALIDATED_BASE_SHA",
  "RELEASE_SOURCE_SHA",
  "ISOLATION_SOURCE_SHA",
  "PLATFORM_MARKER_BASELINE_SHA",
];
const ENVIRONMENT_FIELDS = [
  ...RELEASE_SHA_FIELDS,
  "CONTRACT_TESTS",
  "WINDOWS_LAUNCHER_TOOLSET_VERSION",
  "WINDOWS_SDK_VERSION",
];
const SAFE_CONTRACT_TARGET = /^[A-Za-z0-9_./:-]+$/;
const SAFE_TOOLCHAIN_VERSION = /^\d+(?:\.\d+)+$/;

export class ReleaseInputsError extends Error {}

export function validateReleaseInputs(inputs) {
  if (!inputs || typeof inputs !== "object" || Array.isArray(inputs)) {
    throw new ReleaseInputsError("Release inputs must be an object.");
  }
  const expectedKeys = ["schemaVersion", ...ENVIRONMENT_FIELDS].sort();
  if (Object.keys(inputs).sort().join("\n") !== expectedKeys.join("\n")) {
    throw new ReleaseInputsError(
      "Release inputs contain missing or unknown fields.",
    );
  }
  if (inputs.schemaVersion !== 1) {
    throw new ReleaseInputsError("Release inputs schemaVersion must be 1.");
  }
  for (const field of RELEASE_SHA_FIELDS) {
    if (
      typeof inputs[field] !== "string" ||
      !/^[0-9a-f]{40}$/.test(inputs[field])
    ) {
      throw new ReleaseInputsError(
        `Release input ${field} must be a full lowercase Git SHA.`,
      );
    }
  }
  if (
    !Array.isArray(inputs.CONTRACT_TESTS)
    || inputs.CONTRACT_TESTS.length === 0
    || inputs.CONTRACT_TESTS.some(
      (target) => typeof target !== "string" || !SAFE_CONTRACT_TARGET.test(target),
    )
  ) {
    throw new ReleaseInputsError(
      "CONTRACT_TESTS must be an ordered array of literal pytest targets.",
    );
  }
  for (const field of [
    "WINDOWS_LAUNCHER_TOOLSET_VERSION",
    "WINDOWS_SDK_VERSION",
  ]) {
    if (
      typeof inputs[field] !== "string" ||
      !SAFE_TOOLCHAIN_VERSION.test(inputs[field])
    ) {
      throw new ReleaseInputsError(
        `Release input ${field} must be a dotted numeric version.`,
      );
    }
  }
  return inputs;
}

function loadInputs(directory) {
  let parsed;
  try {
    parsed = JSON.parse(
      readFileSync(path.join(directory, INPUTS_FILENAME), "utf8"),
    );
  } catch {
    throw new ReleaseInputsError("Unable to read release-inputs.json.");
  }
  return validateReleaseInputs(parsed);
}

export function writeGitHubEnvironment(environmentPath, inputs) {
  validateReleaseInputs(inputs);
  const lines = ENVIRONMENT_FIELDS.map((field) => {
    const value =
      field === "CONTRACT_TESTS" ? inputs[field].join(" ") : inputs[field];
    return `${field}=${value}`;
  });
  writeFileSync(environmentPath, `${lines.join("\n")}\n`, {
    flag: "a",
    encoding: "utf8",
  });
}

export function stageReleaseInputs({
  stageDirectory,
  githubEnvironmentPath,
  sourceDirectory = SCRIPT_DIRECTORY,
}) {
  if (typeof stageDirectory !== "string" || stageDirectory.length === 0) {
    throw new ReleaseInputsError("A staging directory is required.");
  }
  if (
    typeof githubEnvironmentPath !== "string" ||
    githubEnvironmentPath.length === 0
  ) {
    throw new ReleaseInputsError("A GitHub environment file is required.");
  }
  const destination = path.resolve(stageDirectory);
  mkdirSync(destination, { recursive: true });
  copyFileSync(
    path.join(sourceDirectory, INPUTS_FILENAME),
    path.join(destination, INPUTS_FILENAME),
  );
  copyFileSync(
    path.join(sourceDirectory, SCRIPT_FILENAME),
    path.join(destination, SCRIPT_FILENAME),
  );
  const inputs = loadInputs(destination);
  writeGitHubEnvironment(githubEnvironmentPath, inputs);
  return inputs;
}

export function main(argv) {
  if (
    !Array.isArray(argv) ||
    argv.length !== 4 ||
    argv[0] !== "--stage" ||
    argv[2] !== "--github-env"
  ) {
    throw new ReleaseInputsError(
      "Usage: node read-release-inputs.mjs --stage <runner-temp-dir> --github-env <environment-file>.",
    );
  }
  return stageReleaseInputs({
    stageDirectory: argv[1],
    githubEnvironmentPath: argv[3],
  });
}

function isMainModule() {
  return Boolean(process.argv[1]) && path.resolve(process.argv[1]) === path.resolve(SCRIPT_PATH);
}

if (isMainModule()) {
  try {
    main(process.argv.slice(2));
  } catch (error) {
    console.error(error instanceof ReleaseInputsError ? error.message : "Unable to stage release inputs.");
    process.exitCode = 1;
  }
}
