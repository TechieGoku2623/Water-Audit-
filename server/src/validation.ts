import type { FixtureInput, FixtureType, SettingsInput } from "./types.js";

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

export function parseSettingsInput(body: unknown): SettingsInput {
  if (typeof body !== "object" || body === null) {
    throw new Error("Request body must be a JSON object.");
  }
  const b = body as Record<string, unknown>;
  const input: SettingsInput = {};

  if (b.costPerLiter !== undefined) {
    const costPerLiter = Number(b.costPerLiter);
    if (!Number.isFinite(costPerLiter) || costPerLiter < 0) {
      throw new Error("`costPerLiter` must be a non-negative number.");
    }
    input.costPerLiter = costPerLiter;
  }

  if (b.currencySymbol !== undefined) {
    const currencySymbol =
      typeof b.currencySymbol === "string" ? b.currencySymbol.trim() : "";
    if (!currencySymbol || currencySymbol.length > 3) {
      throw new Error("`currencySymbol` must be a 1-3 character string.");
    }
    input.currencySymbol = currencySymbol;
  }

  if (input.costPerLiter === undefined && input.currencySymbol === undefined) {
    throw new Error("Provide at least one of `costPerLiter` or `currencySymbol`.");
  }

  return input;
}
