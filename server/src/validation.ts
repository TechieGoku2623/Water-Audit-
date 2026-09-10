import type { FixtureInput, FixtureType } from "./types.js";

const FIXTURE_TYPES: FixtureType[] = [
  "shower",
  "toilet",
  "faucet",
  "dishwasher",
  "washingMachine",
  "irrigation",
  "other",
];

export function parseFixtureInput(body: unknown): FixtureInput {
  if (typeof body !== "object" || body === null) {
    throw new Error("Request body must be a JSON object.");
  }
  const b = body as Record<string, unknown>;

  const name = typeof b.name === "string" ? b.name.trim() : "";
  if (!name) {
    throw new Error("`name` is required.");
  }

  const location = typeof b.location === "string" ? b.location.trim() : "";

  const fixtureType = b.fixtureType as FixtureType;
  if (!FIXTURE_TYPES.includes(fixtureType)) {
    throw new Error(`\`fixtureType\` must be one of: ${FIXTURE_TYPES.join(", ")}.`);
  }

  const litersPerUse = Number(b.litersPerUse);
  if (!Number.isFinite(litersPerUse) || litersPerUse <= 0) {
    throw new Error("`litersPerUse` must be a positive number.");
  }

  const usesPerDay = Number(b.usesPerDay);
  if (!Number.isFinite(usesPerDay) || usesPerDay <= 0) {
    throw new Error("`usesPerDay` must be a positive number.");
  }

  return { name, location, fixtureType, litersPerUse, usesPerDay };
}
