// Opt-in CLI adds --ref and --candidate-sha; it never grants workflow eligibility.
// `resolvedProfile` is data-only; the reader emits only these fixed metadata fields.
export const PROFILE_ENVIRONMENT_FIELDS = Object.freeze([
  "RELEASE_PROFILE_ID",
  "RELEASE_BASELINE_SHA",
  "RELEASE_BASELINE_CHECK",
  "RELEASE_CHARACTERIZATION_PARENT_SHA",
  "RELEASE_CANDIDATE_SHA",
]);

const INPUT_SHA_FIELDS = new Set([
  "CHARACTERIZATION_SHA",
  "VALIDATED_BASE_SHA",
  "RELEASE_SOURCE_SHA",
  "ISOLATION_SOURCE_SHA",
  "PLATFORM_MARKER_BASELINE_SHA",
]);
const SHA_PATTERN = /^[0-9a-f]{40}$/;
const PROFILE_ID_PATTERN = /^[a-z0-9]+(?:[.-][a-z0-9]+)*$/;
const REF_PATTERN = /^refs\/heads\/[A-Za-z0-9._/-]+$/;
const VERIFICATION_MODES = new Set([
  "characterization-parent",
  "ancestor",
]);
const PROFILE_REQUIRED_FIELDS = [
  "id",
  "ref",
  "previousStableSHA",
  "targetStableSHA",
  "verificationMode",
];
const PROFILE_OPTIONAL_FIELDS = [
  "baselineInput",
  "baselineSHA",
  "characterizedParentInput",
  "characterizedParentSHA",
];

export class ReleaseProfileError extends Error {}

function hasExactProfileKeys(profile) {
  const keys = Object.keys(profile).sort();
  const required = PROFILE_REQUIRED_FIELDS.slice().sort();
  const allowed = [...PROFILE_REQUIRED_FIELDS, ...PROFILE_OPTIONAL_FIELDS]
    .sort();
  return (
    PROFILE_REQUIRED_FIELDS.every((field) => Object.hasOwn(profile, field)) &&
    keys.every((field) => allowed.includes(field)) &&
    keys.length >= required.length
  );
}

function isValidGitBranchRef(ref) {
  if (
    typeof ref !== "string" ||
    !REF_PATTERN.test(ref) ||
    ref.includes("..") ||
    ref.includes("@{") ||
    ref.endsWith("/") ||
    ref.endsWith(".")
  ) {
    return false;
  }
  return ref.slice("refs/heads/".length).split("/").every(
    (component) =>
      component.length > 0 &&
      !component.startsWith(".") &&
      !component.toLowerCase().endsWith(".lock"),
  );
}

function validateProfile(profile) {
  if (
    !profile ||
    typeof profile !== "object" ||
    Array.isArray(profile) ||
    !hasExactProfileKeys(profile)
  ) {
    throw new ReleaseProfileError(
      "Release profile contains missing or unknown fields.",
    );
  }
  if (
    typeof profile.id !== "string" ||
    !PROFILE_ID_PATTERN.test(profile.id)
  ) {
    throw new ReleaseProfileError("Release profile id is invalid.");
  }
  if (!isValidGitBranchRef(profile.ref)) {
    throw new ReleaseProfileError("Release profile ref is not a safe branch ref.");
  }
  if (!profile.ref.startsWith("refs/heads/windows-parity/")) {
    throw new ReleaseProfileError(
      "Release profiles are restricted to Windows parity branches.",
    );
  }
  for (const field of ["previousStableSHA", "targetStableSHA"]) {
    if (typeof profile[field] !== "string" || !SHA_PATTERN.test(profile[field])) {
      throw new ReleaseProfileError(
        `Release profile ${field} must be a full lowercase Git SHA.`,
      );
    }
  }
  if (!VERIFICATION_MODES.has(profile.verificationMode)) {
    throw new ReleaseProfileError("Release profile verification mode is invalid.");
  }
  const baselineSources = ["baselineInput", "baselineSHA"].filter((field) =>
    Object.hasOwn(profile, field),
  );
  if (baselineSources.length !== 1) {
    throw new ReleaseProfileError(
      "Release profile must specify exactly one baseline input or SHA.",
    );
  }
  if (
    Object.hasOwn(profile, "baselineInput") &&
    !INPUT_SHA_FIELDS.has(profile.baselineInput)
  ) {
    throw new ReleaseProfileError("Release profile baseline input is invalid.");
  }
  if (
    Object.hasOwn(profile, "baselineSHA") &&
    (typeof profile.baselineSHA !== "string" || !SHA_PATTERN.test(profile.baselineSHA))
  ) {
    throw new ReleaseProfileError("Release profile baseline SHA is invalid.");
  }

  const parentSources = [
    "characterizedParentInput",
    "characterizedParentSHA",
  ].filter((field) => Object.hasOwn(profile, field));
  if (profile.verificationMode === "characterization-parent") {
    if (parentSources.length !== 1) {
      throw new ReleaseProfileError(
        "Characterization profiles require exactly one parent input or SHA.",
      );
    }
    if (
      Object.hasOwn(profile, "characterizedParentInput") &&
      !INPUT_SHA_FIELDS.has(profile.characterizedParentInput)
    ) {
      throw new ReleaseProfileError(
        "Release profile characterized parent input is invalid.",
      );
    }
    if (
      Object.hasOwn(profile, "characterizedParentSHA") &&
      (typeof profile.characterizedParentSHA !== "string" ||
        !SHA_PATTERN.test(profile.characterizedParentSHA))
    ) {
      throw new ReleaseProfileError(
        "Release profile characterized parent SHA is invalid.",
      );
    }
  } else if (parentSources.length !== 0) {
    throw new ReleaseProfileError(
      "Ancestor profiles cannot specify a characterization parent.",
    );
  }
}

export function validateReleaseProfiles(profiles) {
  if (!profiles || typeof profiles !== "object" || Array.isArray(profiles)) {
    throw new ReleaseProfileError("Release profiles must be an object.");
  }
  const keys = Object.keys(profiles).sort();
  if (keys.join("\n") !== ["profiles", "schemaVersion"].join("\n")) {
    throw new ReleaseProfileError(
      "Release profiles contain missing or unknown fields.",
    );
  }
  if (profiles.schemaVersion !== 1) {
    throw new ReleaseProfileError("Release profiles schemaVersion must be 1.");
  }
  if (!Array.isArray(profiles.profiles) || profiles.profiles.length === 0) {
    throw new ReleaseProfileError("Release profiles must be a non-empty array.");
  }
  const ids = new Set();
  const refs = new Set();
  for (const profile of profiles.profiles) {
    validateProfile(profile);
    if (ids.has(profile.id) || refs.has(profile.ref)) {
      throw new ReleaseProfileError(
        "Release profile ids and refs must be unique.",
      );
    }
    ids.add(profile.id);
    refs.add(profile.ref);
  }
  return profiles;
}

function inputSHA(inputs, field) {
  const value = inputs[field];
  if (typeof value !== "string" || !SHA_PATTERN.test(value)) {
    throw new ReleaseProfileError(
      `Resolved release input ${field} must be a full lowercase Git SHA.`,
    );
  }
  return value;
}

export function resolveReleaseProfile(profiles, inputs, { ref, candidateSha }) {
  validateReleaseProfiles(profiles);
  if (!isValidGitBranchRef(ref)) {
    throw new ReleaseProfileError("Requested ref is not a safe branch ref.");
  }
  if (typeof candidateSha !== "string" || !SHA_PATTERN.test(candidateSha)) {
    throw new ReleaseProfileError(
      "Candidate SHA must be a full lowercase Git SHA.",
    );
  }
  if (!inputs || typeof inputs !== "object" || Array.isArray(inputs)) {
    throw new ReleaseProfileError("Release inputs must be an object.");
  }
  const profile = profiles.profiles.find((item) => item.ref === ref);
  if (!profile) {
    throw new ReleaseProfileError("No release profile matches the requested ref.");
  }
  const baselineSHA = Object.hasOwn(profile, "baselineInput")
    ? inputSHA(inputs, profile.baselineInput)
    : profile.baselineSHA;
  const resolvedProfile = {
    id: profile.id,
    ref: profile.ref,
    previousStableSHA: profile.previousStableSHA,
    targetStableSHA: profile.targetStableSHA,
    baselineSHA,
    baselineCheck: profile.verificationMode,
    candidateSHA: candidateSha,
  };
  if (profile.verificationMode === "characterization-parent") {
    resolvedProfile.characterizedParentSHA = Object.hasOwn(
      profile,
      "characterizedParentInput",
    )
      ? inputSHA(inputs, profile.characterizedParentInput)
      : profile.characterizedParentSHA;
  }
  return resolvedProfile;
}
