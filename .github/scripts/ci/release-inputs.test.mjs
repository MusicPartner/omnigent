import assert from "node:assert/strict";
import { mkdtempSync, readFileSync, readdirSync, rmSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";
import {
  ReleaseInputsError,
  stageReleaseInputs,
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

test("manifest matches the independently frozen e1714 release inputs", () => {
  assert.equal(fixture.sourceSha, "e1714c416d2608f7bfd5bf4ea93ee81b108d7311");
  assert.equal(manifest.schemaVersion, 1);
  const { schemaVersion: _schemaVersion, ...inputs } = manifest;
  assert.deepEqual(inputs, fixture.inputs);
  assert.deepEqual(validateReleaseInputs(manifest), manifest);
});

test("staging copies only the candidate reader and manifest and emits ordered literal inputs", () => {
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
