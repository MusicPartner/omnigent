import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import {
  existsSync,
  mkdtempSync,
  readFileSync,
  readdirSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";
import {
  ReleaseInputsError,
  stageReleaseInputs,
  stageReleaseInputsWithProfile,
  validateReleaseInputs,
} from "./read-release-inputs.mjs";

const SCRIPT_DIRECTORY = path.dirname(fileURLToPath(import.meta.url));
const manifest = JSON.parse(
  readFileSync(path.join(SCRIPT_DIRECTORY, "release-inputs.json"), "utf8"),
);
const fixture = JSON.parse(
  readFileSync(
    path.join(SCRIPT_DIRECTORY, "fixtures/release-inputs.e1714.json"),
    "utf8",
  ),
);

function temporaryDirectory(callback) {
  const directory = mkdtempSync(
    path.join(os.tmpdir(), "omnigent-release-inputs-"),
  );
  try {
    callback(directory);
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
}

async function temporaryDirectoryAsync(callback) {
  const directory = mkdtempSync(
    path.join(os.tmpdir(), "omnigent-release-inputs-"),
  );
  try {
    await callback(directory);
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
}

test("manifest matches the independently frozen e1714 release inputs", () => {
  assert.equal(fixture.sourceSha, "e1714c416d2608f7bfd5bf4ea93ee81b108d7311");
  assert.equal(manifest.schemaVersion, 1);
  const { schemaVersion: _schemaVersion, ...inputs } = manifest;
  assert.deepEqual(inputs, fixture.inputs);
  assert.deepEqual(validateReleaseInputs(manifest), manifest);
});

test("schema-1 legacy staging remains an exact two-file stage with ordered inputs", () => {
    temporaryDirectory((directory) => {
      const stage = path.join(directory, "runner-temp", "release-inputs");
      const githubEnvironment = path.join(directory, "GITHUB_ENV");
      const staged = stageReleaseInputs({
        stageDirectory: stage,
        githubEnvironmentPath: githubEnvironment,
      });

      assert.deepEqual(staged, manifest);
      assert.deepEqual(readdirSync(stage).sort(), [
        "read-release-inputs.mjs",
        "release-inputs.json",
      ]);
      assert.equal(
        readFileSync(githubEnvironment, "utf8"),
        [
          `CHARACTERIZATION_SHA=${fixture.inputs.CHARACTERIZATION_SHA}`,
          `VALIDATED_BASE_SHA=${fixture.inputs.VALIDATED_BASE_SHA}`,
          `RELEASE_SOURCE_SHA=${fixture.inputs.RELEASE_SOURCE_SHA}`,
          `ISOLATION_SOURCE_SHA=${fixture.inputs.ISOLATION_SOURCE_SHA}`,
          `PLATFORM_MARKER_BASELINE_SHA=${fixture.inputs.PLATFORM_MARKER_BASELINE_SHA}`,
          `CONTRACT_TESTS=${fixture.inputs.CONTRACT_TESTS.join(" ")}`,
          `WINDOWS_LAUNCHER_TOOLSET_VERSION=${fixture.inputs.WINDOWS_LAUNCHER_TOOLSET_VERSION}`,
          `WINDOWS_SDK_VERSION=${fixture.inputs.WINDOWS_SDK_VERSION}`,
          "",
        ].join("\n"),
      );
    });
});

test("legacy CLI keeps the original --stage and --github-env invocation", () => {
  temporaryDirectory((directory) => {
    const stage = path.join(directory, "legacy-stage");
    const githubEnvironment = path.join(directory, "GITHUB_ENV");
    const result = spawnSync(
      process.execPath,
      [
        path.join(SCRIPT_DIRECTORY, "read-release-inputs.mjs"),
        "--stage",
        stage,
        "--github-env",
        githubEnvironment,
      ],
      { encoding: "utf8" },
    );

    assert.equal(result.status, 0, result.stderr);
    assert.deepEqual(readdirSync(stage).sort(), [
      "read-release-inputs.mjs",
      "release-inputs.json",
    ]);
    assert.equal(
      readFileSync(githubEnvironment, "utf8"),
      [
        `CHARACTERIZATION_SHA=${fixture.inputs.CHARACTERIZATION_SHA}`,
        `VALIDATED_BASE_SHA=${fixture.inputs.VALIDATED_BASE_SHA}`,
        `RELEASE_SOURCE_SHA=${fixture.inputs.RELEASE_SOURCE_SHA}`,
        `ISOLATION_SOURCE_SHA=${fixture.inputs.ISOLATION_SOURCE_SHA}`,
        `PLATFORM_MARKER_BASELINE_SHA=${fixture.inputs.PLATFORM_MARKER_BASELINE_SHA}`,
        `CONTRACT_TESTS=${fixture.inputs.CONTRACT_TESTS.join(" ")}`,
        `WINDOWS_LAUNCHER_TOOLSET_VERSION=${fixture.inputs.WINDOWS_LAUNCHER_TOOLSET_VERSION}`,
        `WINDOWS_SDK_VERSION=${fixture.inputs.WINDOWS_SDK_VERSION}`,
        "",
      ].join("\n"),
    );
  });
});

test("profile staging returns resolved baseline, check mode, and candidate metadata", async () => {
  await temporaryDirectoryAsync(async (directory) => {
    const staged = await stageReleaseInputsWithProfile({
      stageDirectory: path.join(directory, "stage"),
      githubEnvironmentPath: path.join(directory, "GITHUB_ENV"),
      ref: "refs/heads/windows-parity/v0.20-isolation-p3-p5",
      candidateSha: "96ee061d690a26ef37f9d432a98231105fa68d9f",
    });
    assert.deepEqual(staged.inputs, manifest);
    assert.deepEqual(staged.resolvedProfile, {
      id: "v0.20-isolation-p3-p5",
      ref: "refs/heads/windows-parity/v0.20-isolation-p3-p5",
      previousStableSHA: "d43340fec4e7d2d767f319d715e84aa82f4d1bc8",
      targetStableSHA: "bfd8ab5624e34aa72c01fb451e11c2a0e1aae3ee",
      baselineSHA: fixture.inputs.ISOLATION_SOURCE_SHA,
      baselineCheck: "ancestor",
      candidateSHA: "96ee061d690a26ef37f9d432a98231105fa68d9f",
    });
  });
});

test("opt-in CLI stages a profile and companion reader that remain callable standalone", () => {
  temporaryDirectory((directory) => {
    const stage = path.join(directory, "profile-stage");
    const environment = path.join(directory, "GITHUB_ENV");
    const ref = "refs/heads/windows-parity/v0.19-isolation-p1-p2";
    const candidateSha = "96ee061d690a26ef37f9d432a98231105fa68d9f";
    const result = spawnSync(
      process.execPath,
      [
        path.join(SCRIPT_DIRECTORY, "read-release-inputs.mjs"),
        "--stage",
        stage,
        "--github-env",
        environment,
        "--ref",
        ref,
        "--candidate-sha",
        candidateSha,
      ],
      { encoding: "utf8" },
    );

    assert.equal(result.status, 0, result.stderr);
    assert.deepEqual(readdirSync(stage).sort(), [
      "read-release-inputs.mjs",
      "release-inputs.json",
      "release-profiles.json",
      "release-profiles.mjs",
    ]);
    assert.equal(
      readFileSync(environment, "utf8").split("\n").slice(-6).join("\n"),
      [
        "RELEASE_PROFILE_ID=v0.19-isolation-p1-p2",
        `RELEASE_BASELINE_SHA=${fixture.inputs.CHARACTERIZATION_SHA}`,
        "RELEASE_BASELINE_CHECK=characterization-parent",
        `RELEASE_CHARACTERIZATION_PARENT_SHA=${fixture.inputs.VALIDATED_BASE_SHA}`,
        `RELEASE_CANDIDATE_SHA=${candidateSha}`,
        "",
      ].join("\n"),
    );

    const secondStage = path.join(directory, "detached-stage");
    const secondEnvironment = path.join(directory, "DETACHED_GITHUB_ENV");
    const detachedResult = spawnSync(
      process.execPath,
      [
        path.join(stage, "read-release-inputs.mjs"),
        "--stage",
        secondStage,
        "--github-env",
        secondEnvironment,
        "--ref",
        "refs/heads/windows-parity/v0.20-integration",
        "--candidate-sha",
        candidateSha,
      ],
      { encoding: "utf8" },
    );
    assert.equal(detachedResult.status, 0, detachedResult.stderr);
    assert.deepEqual(readdirSync(secondStage).sort(), readdirSync(stage).sort());
    assert.equal(
      readFileSync(secondEnvironment, "utf8").split("\n").slice(-5).join("\n"),
      [
        "RELEASE_PROFILE_ID=v0.20-integration",
        `RELEASE_BASELINE_SHA=${fixture.inputs.RELEASE_SOURCE_SHA}`,
        "RELEASE_BASELINE_CHECK=ancestor",
        `RELEASE_CANDIDATE_SHA=${candidateSha}`,
        "",
      ].join("\n"),
    );
  });
});

test("invalid opt-in refs, candidate SHAs, and argv order do not mutate outputs", () => {
  temporaryDirectory((directory) => {
    const requests = [
      ["refs/heads/main", "96ee061d690a26ef37f9d432a98231105fa68d9f"],
      ["refs/heads/windows-parity/x;echo-bad", "96ee061d690a26ef37f9d432a98231105fa68d9f"],
      ["refs/heads/windows-parity/v0.20-integration", "96ee061d;echo-bad"],
    ];
    for (const [index, [ref, candidateSha]] of requests.entries()) {
      const stage = path.join(directory, `rejected-${index}`);
      const environment = path.join(directory, `GITHUB_ENV-${index}`);
      writeFileSync(environment, "existing\n", "utf8");
      const result = spawnSync(
        process.execPath,
        [
          path.join(SCRIPT_DIRECTORY, "read-release-inputs.mjs"),
          "--stage",
          stage,
          "--github-env",
          environment,
          "--ref",
          ref,
          "--candidate-sha",
          candidateSha,
        ],
        { encoding: "utf8" },
      );
      assert.notEqual(result.status, 0);
      assert.equal(existsSync(stage), false);
      assert.equal(readFileSync(environment, "utf8"), "existing\n");
    }

    const reorderedStage = path.join(directory, "reordered");
    const reorderedEnvironment = path.join(directory, "GITHUB_ENV-reordered");
    const reordered = spawnSync(
      process.execPath,
      [
        path.join(SCRIPT_DIRECTORY, "read-release-inputs.mjs"),
        "--stage",
        reorderedStage,
        "--github-env",
        reorderedEnvironment,
        "--candidate-sha",
        "96ee061d690a26ef37f9d432a98231105fa68d9f",
        "--ref",
        "refs/heads/windows-parity/v0.20-integration",
      ],
      { encoding: "utf8" },
    );
    assert.notEqual(reordered.status, 0);
    assert.equal(existsSync(reorderedStage), false);
    assert.equal(existsSync(reorderedEnvironment), false);
  });
});

test("an invalid copied profile leaves the stage and GitHub environment untouched", () => {
  temporaryDirectory((directory) => {
    const initialStage = path.join(directory, "initial-stage");
    const initialEnvironment = path.join(directory, "INITIAL_GITHUB_ENV");
    const valid = spawnSync(
      process.execPath,
      [
        path.join(SCRIPT_DIRECTORY, "read-release-inputs.mjs"),
        "--stage",
        initialStage,
        "--github-env",
        initialEnvironment,
        "--ref",
        "refs/heads/windows-parity/v0.20-integration",
        "--candidate-sha",
        "96ee061d690a26ef37f9d432a98231105fa68d9f",
      ],
      { encoding: "utf8" },
    );
    assert.equal(valid.status, 0, valid.stderr);

    const invalidProfiles = JSON.parse(
      readFileSync(path.join(initialStage, "release-profiles.json"), "utf8"),
    );
    invalidProfiles.profiles[1].verificationMode = "ancestor;echo-bad";
    writeFileSync(
      path.join(initialStage, "release-profiles.json"),
      `${JSON.stringify(invalidProfiles)}\n`,
      "utf8",
    );
    const stage = path.join(directory, "must-not-exist");
    const environment = path.join(directory, "PRESERVE_GITHUB_ENV");
    writeFileSync(environment, "existing\n", "utf8");
    const result = spawnSync(
      process.execPath,
      [
        path.join(initialStage, "read-release-inputs.mjs"),
        "--stage",
        stage,
        "--github-env",
        environment,
        "--ref",
        "refs/heads/windows-parity/v0.20-integration",
        "--candidate-sha",
        "96ee061d690a26ef37f9d432a98231105fa68d9f",
      ],
      { encoding: "utf8" },
    );
    assert.notEqual(result.status, 0);
    assert.equal(existsSync(stage), false);
    assert.equal(readFileSync(environment, "utf8"), "existing\n");
  });
});

test("manifest validation rejects malformed pins, targets, toolchains, and unknown fields", () => {
    const invalidCases = [
      [{ ...manifest, CHARACTERIZATION_SHA: "a07520" }, /CHARACTERIZATION_SHA/],
      [
        {
          ...manifest,
          CONTRACT_TESTS: ["tests/test_ok.py", "--dangerous\nvalue"],
        },
        /literal pytest targets/,
      ],
      [{ ...manifest, WINDOWS_SDK_VERSION: "latest" }, /WINDOWS_SDK_VERSION/],
      [{ ...manifest, extra: "ignored?" }, /unknown fields/],
      [{ ...manifest, CONTRACT_TESTS: [] }, /ordered array/],
    ];
    for (const [invalid, message] of invalidCases) {
      assert.throws(
        () => validateReleaseInputs(invalid),
        (error) => {
          assert.ok(error instanceof ReleaseInputsError);
          assert.match(error.message, message);
          return true;
        },
      );
    }
});
