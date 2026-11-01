import { copyFileSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const SCRIPT_PATH = fileURLToPath(import.meta.url);
const SCRIPT_DIRECTORY = path.dirname(SCRIPT_PATH);
const INPUTS_FILENAME = "release-inputs.json";
const SCRIPT_FILENAME = "read-release-inputs.mjs";
const PROFILES_FILENAME = "release-profiles.json";
const PROFILES_SCRIPT_FILENAME = "release-profiles.mjs";
const PROFILE_ENVIRONMENT_FIELDS = [
  "RELEASE_PROFILE_ID",
  "RELEASE_BASELINE_SHA",
  "RELEASE_BASELINE_CHECK",
  "RELEASE_CHARACTERIZATION_PARENT_SHA",
  "RELEASE_CANDIDATE_SHA",
];
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

function loadProfiles(directory) {
  try {
    return JSON.parse(
      readFileSync(path.join(directory, PROFILES_FILENAME), "utf8"),
    );
  } catch {
    throw new ReleaseInputsError("Unable to read release-profiles.json.");
  }
}

function validateStageArguments({ stageDirectory, githubEnvironmentPath }) {
  if (typeof stageDirectory !== "string" || stageDirectory.length === 0) {
    throw new ReleaseInputsError("A staging directory is required.");
  }
  if (
    typeof githubEnvironmentPath !== "string" ||
    githubEnvironmentPath.length === 0
  ) {
    throw new ReleaseInputsError("A GitHub environment file is required.");
  }
}

function writeProfileGitHubEnvironment(
  environmentPath,
  inputs,
  profile,
  profileEnvironmentFields,
) {
  const lines = ENVIRONMENT_FIELDS.map((field) => {
    const value =
      field === "CONTRACT_TESTS" ? inputs[field].join(" ") : inputs[field];
    return `${field}=${value}`;
  });
  const metadata = {
    RELEASE_PROFILE_ID: profile.id,
    RELEASE_BASELINE_SHA: profile.baselineSHA,
    RELEASE_BASELINE_CHECK: profile.baselineCheck,
    RELEASE_CANDIDATE_SHA: profile.candidateSHA,
  };
  if (profile.characterizedParentSHA) {
    metadata.RELEASE_CHARACTERIZATION_PARENT_SHA =
      profile.characterizedParentSHA;
  }
  for (const field of profileEnvironmentFields) {
    if (Object.hasOwn(metadata, field)) {
      lines.push(`${field}=${metadata[field]}`);
    }
  }
  writeFileSync(environmentPath, `${lines.join("\n")}\n`, {
    flag: "a",
    encoding: "utf8",
  });
}

export async function stageReleaseInputsWithProfile({
  stageDirectory,
  githubEnvironmentPath,
  ref,
  candidateSha,
  sourceDirectory = SCRIPT_DIRECTORY,
}) {
  validateStageArguments({ stageDirectory, githubEnvironmentPath });
  const inputs = loadInputs(sourceDirectory);
  const profiles = loadProfiles(sourceDirectory);
  let profileModule;
  try {
    profileModule = await import(
      pathToFileURL(path.join(sourceDirectory, PROFILES_SCRIPT_FILENAME)).href
    );
  } catch {
    throw new ReleaseInputsError("Unable to load release-profiles.mjs.");
  }
  if (
    typeof profileModule.resolveReleaseProfile !== "function" ||
    !Array.isArray(profileModule.PROFILE_ENVIRONMENT_FIELDS) ||
    profileModule.PROFILE_ENVIRONMENT_FIELDS.join("\n") !==
      PROFILE_ENVIRONMENT_FIELDS.join("\n")
  ) {
    throw new ReleaseInputsError("Invalid release profile companion interface.");
  }
  let resolvedProfile;
  try {
    resolvedProfile = profileModule.resolveReleaseProfile(profiles, inputs, {
      ref,
      candidateSha,
    });
  } catch (error) {
    throw new ReleaseInputsError(
      error instanceof Error ? error.message : "Invalid release profile.",
    );
  }

  const destination = path.resolve(stageDirectory);
  mkdirSync(destination, { recursive: true });
  for (const filename of [
    INPUTS_FILENAME,
    SCRIPT_FILENAME,
    PROFILES_FILENAME,
    PROFILES_SCRIPT_FILENAME,
  ]) {
    copyFileSync(path.join(sourceDirectory, filename), path.join(destination, filename));
  }
  writeProfileGitHubEnvironment(
    githubEnvironmentPath,
    inputs,
    resolvedProfile,
    PROFILE_ENVIRONMENT_FIELDS,
  );
  return { inputs, resolvedProfile };
}

export function main(argv) {
  if (!Array.isArray(argv)) {
    throw new ReleaseInputsError(
      "Usage: node read-release-inputs.mjs --stage <runner-temp-dir> --github-env <environment-file>.",
    );
  }
  if (
    argv.length === 4 &&
    argv[0] === "--stage" &&
    argv[2] === "--github-env"
  ) {
    return stageReleaseInputs({
      stageDirectory: argv[1],
      githubEnvironmentPath: argv[3],
    });
  }
  if (
    argv.length === 8 &&
    argv[0] === "--stage" &&
    argv[2] === "--github-env" &&
    argv[4] === "--ref" &&
    argv[6] === "--candidate-sha"
  ) {
    return stageReleaseInputsWithProfile({
      stageDirectory: argv[1],
      githubEnvironmentPath: argv[3],
      ref: argv[5],
      candidateSha: argv[7],
    });
  }
  throw new ReleaseInputsError(
    "Usage: node read-release-inputs.mjs --stage <runner-temp-dir> --github-env <environment-file> [--ref <refs/heads/branch> --candidate-sha <full-lowercase-sha>].",
  );
}

function isMainModule() {
  return Boolean(process.argv[1]) && path.resolve(process.argv[1]) === path.resolve(SCRIPT_PATH);
}

if (isMainModule()) {
  const reportFailure = (error) => {
    console.error(error instanceof ReleaseInputsError ? error.message : "Unable to stage release inputs.");
    process.exitCode = 1;
  };
  try {
    const result = main(process.argv.slice(2));
    if (result && typeof result.then === "function") {
      result.catch(reportFailure);
    }
  } catch (error) {
    reportFailure(error);
  }
}
