import { randomUUID } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import type { Fixture, FixtureInput, Settings, SettingsInput } from "./types.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const DATA_DIR =
  process.env.WATER_AUDIT_DATA_DIR ?? resolve(__dirname, "../../data");
const DATA_FILE =
  process.env.WATER_AUDIT_DATA_FILE ?? resolve(DATA_DIR, "fixtures.json");
const SETTINGS_FILE =
  process.env.WATER_AUDIT_SETTINGS_FILE ?? resolve(DATA_DIR, "settings.json");

const DEFAULT_SETTINGS: Settings = {
  costPerLiter: 0.002,
  currencySymbol: "$",
};

function seedFixtures(): Fixture[] {
  const now = new Date().toISOString();
  const base: Omit<Fixture, "id" | "createdAt">[] = [
    {
      name: "Master Bathroom Shower",
      location: "Master Bath",
      fixtureType: "shower",
      litersPerUse: 49,
      usesPerDay: 2,
    },
    {
      name: "Guest Toilet",
      location: "Hallway",
      fixtureType: "toilet",
      litersPerUse: 6,
      usesPerDay: 6,
    },
    {
      name: "Kitchen Faucet",
      location: "Kitchen",
      fixtureType: "faucet",
      litersPerUse: 4,
      usesPerDay: 11,
    },
  ];
  return base.map((f) => ({ ...f, id: randomUUID(), createdAt: now }));
}

function ensureFile(): void {
  const dir = dirname(DATA_FILE);
  if (!existsSync(dir)) {
    mkdirSync(dir, { recursive: true });
  }
  if (!existsSync(DATA_FILE)) {
    writeFileSync(DATA_FILE, JSON.stringify(seedFixtures(), null, 2), "utf8");
  }
}

function readAll(): Fixture[] {
  ensureFile();
  try {
    return JSON.parse(readFileSync(DATA_FILE, "utf8")) as Fixture[];
  } catch {
    return [];
  }
}

function writeAll(fixtures: Fixture[]): void {
  ensureFile();
  writeFileSync(DATA_FILE, JSON.stringify(fixtures, null, 2), "utf8");
}

export function listFixtures(): Fixture[] {
  return readAll();
}

export function createFixture(input: FixtureInput): Fixture {
  const fixtures = readAll();
  const fixture: Fixture = {
    ...input,
    id: randomUUID(),
    createdAt: new Date().toISOString(),
  };
  fixtures.push(fixture);
  writeAll(fixtures);
  return fixture;
}

export function updateFixture(id: string, input: FixtureInput): Fixture | null {
  const fixtures = readAll();
  const index = fixtures.findIndex((f) => f.id === id);
  if (index === -1) {
    return null;
  }
  const updated: Fixture = {
    ...fixtures[index],
    ...input,
    id: fixtures[index].id,
    createdAt: fixtures[index].createdAt,
  };
  fixtures[index] = updated;
  writeAll(fixtures);
  return updated;
}

export function deleteFixture(id: string): boolean {
  const fixtures = readAll();
  const next = fixtures.filter((f) => f.id !== id);
  if (next.length === fixtures.length) {
    return false;
  }
  writeAll(next);
  return true;
}

export function getSettings(): Settings {
  if (!existsSync(DATA_DIR)) {
    mkdirSync(DATA_DIR, { recursive: true });
  }
  if (!existsSync(SETTINGS_FILE)) {
    writeFileSync(SETTINGS_FILE, JSON.stringify(DEFAULT_SETTINGS, null, 2), "utf8");
    return { ...DEFAULT_SETTINGS };
  }
  try {
    const parsed = JSON.parse(readFileSync(SETTINGS_FILE, "utf8")) as Partial<Settings>;
    return { ...DEFAULT_SETTINGS, ...parsed };
  } catch {
    return { ...DEFAULT_SETTINGS };
  }
}

export function updateSettings(input: SettingsInput): Settings {
  const next: Settings = { ...getSettings(), ...input };
  if (!existsSync(DATA_DIR)) {
    mkdirSync(DATA_DIR, { recursive: true });
  }
  writeFileSync(SETTINGS_FILE, JSON.stringify(next, null, 2), "utf8");
  return next;
}
