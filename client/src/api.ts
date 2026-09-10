import type { AuditSummary, Fixture, FixtureInput } from "./types.ts";

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    try {
      const body = (await res.json()) as { error?: string };
      if (body.error) message = body.error;
    } catch {
      // ignore parse errors
    }
    throw new Error(message);
  }
  return res.json() as Promise<T>;
}

export async function getFixtures(): Promise<Fixture[]> {
  return handle(await fetch("/api/fixtures"));
}

export async function getSummary(): Promise<AuditSummary> {
  return handle(await fetch("/api/summary"));
}

export async function createFixture(input: FixtureInput): Promise<Fixture> {
  return handle(
    await fetch("/api/fixtures", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
    }),
  );
}

export async function deleteFixture(id: string): Promise<void> {
  const res = await fetch(`/api/fixtures/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`Failed to delete fixture (${res.status})`);
}
