import cors from "cors";
import express from "express";
import { summarize } from "./audit.js";
import { createFixture, deleteFixture, listFixtures } from "./store.js";
import { parseFixtureInput } from "./validation.js";

const app = express();
const PORT = Number(process.env.PORT ?? 3001);

app.use(cors());
app.use(express.json());

app.get("/api/health", (_req, res) => {
  res.json({ status: "ok", service: "water-audit-api" });
});

app.get("/api/fixtures", (_req, res) => {
  res.json(listFixtures());
});

app.post("/api/fixtures", (req, res) => {
  try {
    const input = parseFixtureInput(req.body);
    const fixture = createFixture(input);
    res.status(201).json(fixture);
  } catch (err) {
    res.status(400).json({ error: (err as Error).message });
  }
});

app.delete("/api/fixtures/:id", (req, res) => {
  const removed = deleteFixture(req.params.id);
  if (!removed) {
    res.status(404).json({ error: "Fixture not found." });
    return;
  }
  res.status(204).end();
});

app.get("/api/summary", (_req, res) => {
  res.json(summarize(listFixtures()));
});

app.listen(PORT, () => {
  console.log(`[water-audit] API listening on http://localhost:${PORT}`);
});
