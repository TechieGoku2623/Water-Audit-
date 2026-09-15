<div align="center">

# Water Audit

**See which fixture is driving the bill — and what a low-flow swap would save**

A household or small-facility dashboard that turns fixture use into daily liters, monthly cost, and concrete savings at *your* water rate. Not a generic conservation PDF.

[![Node](https://img.shields.io/badge/Node-20+-339933?logo=node.js&logoColor=white)](#getting-started)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white)](#repository-map)
[![React](https://img.shields.io/badge/React-Vite-61DAFB?logo=react&logoColor=black)](#getting-started)
[![Demo](https://img.shields.io/badge/Demo-plays%20on%20this%20page-2B6CB0)](#watch-the-demo)

</div>

---

## The problem

Most water “audits” dump the same advice on every building: shorter showers, fix leaks, install aerators. That does not answer the questions that change behavior:

- Which fixture is actually using the water?
- What does that cost at this site’s rate?
- If I swap this shower for a 40 L/use head, how many liters and dollars per month do I get back?

Without those numbers, conservation stays abstract. With them, a facility manager or homeowner can prioritize the one fixture that dominates the bill.

## What this software does

You register each fixture (shower, toilet, faucet, dishwasher, washer, irrigation, other) with **liters per use** and **uses per day**. The API multiplies those by your **cost per liter**, compares each fixture to an efficient benchmark, and returns:

- Daily and monthly volume
- Monthly and annual cost
- Share of total use
- An efficiency score (0–100)
- Recommendations with liters and currency saved if you hit the benchmark

The React dashboard and the Express API share one model. Change a shower from 65 L to 40 L and the KPIs, breakdown table, bar chart, and recommendation move together.

These are **estimates from the values you enter**, not smart-meter telemetry.

---

## Watch the demo

The walkthrough **plays on this page**.

<p align="center">
  <img src="docs/demo.gif" alt="Water Audit dashboard walkthrough — plays inline" width="920"/>
</p>

| In the clip | Why it matters |
| --- | --- |
| Header KPIs | Fixtures, daily L, monthly L, cost, efficiency |
| Fixture table | Which fixture owns the bill |
| Edit / cancel | Writes go through the API; cancel is safe |
| Recommendations | Savings use the same rate as the cost column |

---

## How the numbers are built

```text
liters/use × uses/day     →  daily L
daily L × 30              →  monthly L
monthly L × costPerLiter  →  monthly cost

If liters/use is well above the efficient benchmark:
  savings = (actual − benchmark) × uses/day × 30
```

| Fixture type | Efficient benchmark (L / use) |
| --- | ---: |
| Shower | 40 |
| Toilet | 6 |
| Faucet | 4 |
| Dishwasher | 12 |
| Washing machine | 50 |

Irrigation and `other` are tracked in totals; they do not currently emit benchmark savings. Rate is stored as cost per liter (the UI shows a rate per 1,000 L). First run seeds an efficient household so the demo starts near **90/100**.

### Repository map

```text
water-audit-/
├── client/                 React + Vite + TypeScript   (:5173)
├── server/                 Express + TypeScript        (:3001)
│   └── src/
│       ├── index.ts        REST routes
│       ├── store.ts        JSON persistence
│       ├── audit.ts        Totals + savings
│       └── validation.ts
├── data/                   fixtures + settings (created at runtime)
├── docs/demo.gif
└── package.json            npm workspaces
```

Persistence is local JSON (`data/`). There is no login or multi-tenant cloud.

---

## Getting started

Node.js **20+**.

```bash
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173). Vite proxies `/api` to port **3001**.

| Command | What it does |
| --- | --- |
| `npm run dev:server` | API only |
| `npm run dev:client` | Web client only |
| `npm run build` | Type-check and build both |
| `npm run typecheck` | Type-check both workspaces |

### API

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/api/health` | Health check |
| `GET` / `POST` | `/api/fixtures` | List / create |
| `PUT` / `DELETE` | `/api/fixtures/:id` | Update / delete |
| `GET` / `PUT` | `/api/settings` | Rate and currency |
| `GET` | `/api/summary` | Usage, cost, recommendations |

```json
{
  "name": "Master Bathroom Shower",
  "location": "Master Bath",
  "fixtureType": "shower",
  "litersPerUse": 75,
  "usesPerDay": 2
}
```

Optional env: `PORT`, `WATER_AUDIT_DATA_DIR`, `WATER_AUDIT_DATA_FILE`.

---

<p align="center"><sub>Water Audit · measure the fixture, then save against the bill</sub></p>
