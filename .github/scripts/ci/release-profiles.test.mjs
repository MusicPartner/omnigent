import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";
import {
  PROFILE_ENVIRONMENT_FIELDS,
  ReleaseProfileError,
  resolveReleaseProfile,
  validateReleaseProfiles,
} from "./release-profiles.mjs";

const SCRIPT_DIRECTORY = path.dirname(fileURLToPath(import.meta.url));
const profiles = JSON.parse(
  readFileSync(path.join(SCRIPT_DIRECTORY, "release-profiles.json"), "utf8"),
);
const inputs = {
  CHARACTERIZATION_SHA: "a07520b5053e24ccbc399356296ad47842d6ed6d",
  VALIDATED_BASE_SHA: "6a7c711308587a2c39dd916c0820af71debfbb67",
  RELEASE_SOURCE_SHA: "430ea3caabec09ff894e92c0c03bfe029361418e",
  ISOLATION_SOURCE_SHA: "a67684ae0fc2299c8efc2e5f37824c71c8f044a6",
  PLATFORM_MARKER_BASELINE_SHA: "bfd8ab5624e34aa72c01fb451e11c2a0e1aae3ee",
};
const candidateSHA = "96ee061d690a26ef37f9d432a98231105fa68d9f";

test("version-1 profiles preserve the three existing release baseline meanings", () => {
  assert.deepEqual(validateReleaseProfiles(profiles), profiles);
  const resolved = profiles.profiles.map((profile) =>
    resolveReleaseProfile(profiles, inputs, {
      ref: profile.ref,
      candidateSha: candidateSHA,
    }),
  );
  assert.deepEqual(
    resolved.map(({ id, baselineSHA, baselineCheck, characterizedParentSHA }) => ({
      id,
      baselineSHA,
      baselineCheck,
      ...(characterizedParentSHA ? { characterizedParentSHA } : {}),
    })),
    [
      {
        id: "v0.19-isolation-p1-p2",
        baselineSHA: inputs.CHARACTERIZATION_SHA,
        baselineCheck: "characterization-parent",
        characterizedParentSHA: inputs.VALIDATED_BASE_SHA,
      },
      {
        id: "v0.20-integration",
        baselineSHA: inputs.RELEASE_SOURCE_SHA,
        baselineCheck: "ancestor",
      },
      {
        id: "v0.20-isolation-p3-p5",
        baselineSHA: inputs.ISOLATION_SOURCE_SHA,
        baselineCheck: "ancestor",
      },
    ],
  );
  assert.deepEqual(PROFILE_ENVIRONMENT_FIELDS, [
    "RELEASE_PROFILE_ID",
    "RELEASE_BASELINE_SHA",
    "RELEASE_BASELINE_CHECK",
    "RELEASE_CHARACTERIZATION_PARENT_SHA",
    "RELEASE_CANDIDATE_SHA",
  ]);
});

test("two future profiles resolve from data without branch-specific resolver logic", () => {
  const futureProfiles = {
    schemaVersion: 1,
    profiles: [
      {
        id: "v0.21-alpha",
        ref: "refs/heads/windows-parity/v0.21-alpha",
        previousStableSHA: "d43340fec4e7d2d767f319d715e84aa82f4d1bc8",
        targetStableSHA: "bfd8ab5624e34aa72c01fb451e11c2a0e1aae3ee",
        baselineSHA: "430ea3caabec09ff894e92c0c03bfe029361418e",
        verificationMode: "ancestor",
      },
      {
        id: "v0.21-beta",
        ref: "refs/heads/windows-parity/v0.21-beta",
        previousStableSHA: "d43340fec4e7d2d767f319d715e84aa82f4d1bc8",
        targetStableSHA: "bfd8ab5624e34aa72c01fb451e11c2a0e1aae3ee",
        baselineInput: "ISOLATION_SOURCE_SHA",
        verificationMode: "ancestor",
      },
    ],
  };
  assert.equal(
    resolveReleaseProfile(futureProfiles, inputs, {
      ref: futureProfiles.profiles[0].ref,
      candidateSha: candidateSHA,
    }).baselineSHA,
    futureProfiles.profiles[0].baselineSHA,
  );
  assert.equal(
    resolveReleaseProfile(futureProfiles, inputs, {
      ref: futureProfiles.profiles[1].ref,
      candidateSha: candidateSHA,
    }).baselineSHA,
    inputs.ISOLATION_SOURCE_SHA,
  );
});

test("profile validation rejects unknown fields, duplicates, unsafe refs, and invalid modes", () => {
  const invalidCases = [
    [{ ...profiles, extra: true }, /unknown fields/],
    [{ ...profiles, schemaVersion: 2 }, /schemaVersion/],
    [
      { ...profiles, profiles: [{ ...profiles.profiles[0], unexpected: "x" }] },
      /missing or unknown fields/,
    ],
    [
      { ...profiles, profiles: [profiles.profiles[0], profiles.profiles[0]] },
      /must be unique/,
    ],
    [
      {
        ...profiles,
        profiles: [{ ...profiles.profiles[1], verificationMode: "ancestor;exit" }],
      },
      /verification mode/,
    ],
    [
      {
        ...profiles,
        profiles: [
          { ...profiles.profiles[1], ref: "refs/heads/release/../main" },
        ],
      },
      /safe branch ref/,
    ],
    [
      {
        ...profiles,
        profiles: [
          { ...profiles.profiles[1], ref: "refs/heads/release.lock" },
        ],
      },
      /safe branch ref/,
    ],
  ];
  for (const [invalid, message] of invalidCases) {
    assert.throws(
      () => validateReleaseProfiles(invalid),
      (error) => {
        assert.ok(error instanceof ReleaseProfileError);
        assert.match(error.message, message);
        return true;
      },
    );
  }
});

test("profile resolution rejects unknown refs and injected or abbreviated candidate SHAs", () => {
  const invalidRequests = [
    [{ ref: "refs/heads/main", candidateSha: candidateSHA }, /No release profile/],
    [
      {
        ref: "refs/heads/windows-parity/v0.20-integration;echo-bad",
        candidateSha: candidateSHA,
      },
      /safe branch ref/,
    ],
    [
      {
        ref: "refs/heads/windows-parity/v0.20-integration",
        candidateSha: "96ee061d;echo-bad",
      },
      /full lowercase Git SHA/,
    ],
    [
      {
        ref: "refs/heads/windows-parity/v0.20-integration",
        candidateSha: "96ee061d",
      },
      /full lowercase Git SHA/,
    ],
  ];
  for (const [request, message] of invalidRequests) {
    assert.throws(
      () => resolveReleaseProfile(profiles, inputs, request),
      (error) => {
        assert.ok(error instanceof ReleaseProfileError);
        assert.match(error.message, message);
        return true;
      },
    );
  }
});

test("profile data cannot authorize main or unrelated branches", () => {
  for (const ref of ["refs/heads/main", "refs/heads/release/v0.21"]) {
    const invalid = {
      schemaVersion: 1,
      profiles: [{ ...profiles.profiles[1], ref }],
    };
    assert.throws(
      () => validateReleaseProfiles(invalid),
      /restricted to Windows parity branches/,
    );
  }
});

test("profile mode and baseline/parent input sources are mutually constrained", () => {
  const invalidProfiles = [
    {
      ...profiles,
      profiles: [
        {
          ...profiles.profiles[0],
          verificationMode: "ancestor",
        },
      ],
    },
    {
      ...profiles,
      profiles: [
        {
          ...profiles.profiles[1],
          verificationMode: "characterization-parent",
        },
      ],
    },
    {
      ...profiles,
      profiles: [
        {
          ...profiles.profiles[1],
          baselineInput: "CHARACTERIZATION_SHA;process.exit(1)",
        },
      ],
    },
  ];
  for (const invalid of invalidProfiles) {
    assert.throws(() => validateReleaseProfiles(invalid), ReleaseProfileError);
  }
});
