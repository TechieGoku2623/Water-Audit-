import { randomUUID } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import type { Fixture, FixtureInput } from "./types.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const DATA_FILE =
  process.env.WATER_AUDIT_DATA_FILE ??
  resolve(__dirname, "../../data/fixtures.json");

function seedFixtures(): Fixture[] {
  const now = new Date().toISOString();
  const base: Omit<Fixture, "id" | "createdAt">[] = [
    {
      name: "Master Bathroom Shower",
      location: "Master Bath",
      fixtureType: "shower",
      litersPerUse: 75,
      usesPerDay: 2,
    },
    {
      name: "Guest Toilet",
      location: "Hallway",
      fixtureType: "toilet",
      litersPerUse: 11,
      usesPerDay: 8,
    },
    {
      name: "Kitchen Faucet",
      location: "Kitchen",
      fixtureType: "faucet",
      litersPerUse: 6,
      usesPerDay: 12,
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

export function deleteFixture(id: string): boolean {
  const fixtures = readAll();
  const next = fixtures.filter((f) => f.id !== id);
  if (next.length === fixtures.length) {
    return false;
  }
  writeAll(next);
  return true;
}
