# Water Audit

A small full-stack app to audit household/facility water use: register fixtures
(showers, toilets, faucets, appliances, irrigation), estimate daily/monthly
consumption and cost, and get efficiency recommendations with projected savings.

## Stack

- **Server** (`server/`): Node + Express + TypeScript REST API. Fixtures are
  persisted to a JSON file (`data/fixtures.json`), seeded on first run.
- **Client** (`client/`): React + Vite + TypeScript dashboard.
- npm workspaces tie the two together from the repo root.

## Prerequisites

- Node.js >= 20 (developed on Node 22)

## Getting started

```bash
npm install        # installs both workspaces
npm run dev        # runs the API (:3001) and web client (:5173) together
```

Then open http://localhost:5173. The Vite dev server proxies `/api/*` to the
API on port 3001.

### Individual commands

```bash
npm run dev:server   # API only (tsx watch)
npm run dev:client   # web client only (vite)
npm run build        # type-check + build server and client
npm run typecheck    # type-check both workspaces
```

## API

| Method | Path                 | Description                                    |
| ------ | -------------------- | ---------------------------------------------- |
| GET    | `/api/health`        | Health check                                   |
| GET    | `/api/fixtures`      | List fixtures                                  |
| POST   | `/api/fixtures`      | Create a fixture                               |
| PUT    | `/api/fixtures/:id`  | Update a fixture                               |
| DELETE | `/api/fixtures/:id`  | Delete a fixture                               |
| GET    | `/api/settings`      | Get water rate + currency settings             |
| PUT    | `/api/settings`      | Update water rate and/or currency symbol       |
| GET    | `/api/summary`       | Usage/cost breakdown + savings recommendations |

Fixture payload:

```json
{
  "name": "Master Bathroom Shower",
  "location": "Master Bath",
  "fixtureType": "shower",
  "litersPerUse": 75,
  "usesPerDay": 2
}
```

`fixtureType` is one of `shower`, `toilet`, `faucet`, `dishwasher`,
`washingMachine`, `irrigation`, `other`.

Settings payload (either field is optional):

```json
{
  "costPerLiter": 0.002,
  "currencySymbol": "$"
}
```

The configured `costPerLiter` drives all cost and savings figures in
`/api/summary`. Fixtures and settings are stored as JSON files under `data/`.

## Cloud Agent environment

`.cursor/environment.json` installs dependencies with `npm install` and runs two
terminals (`api`, `web`) exposing ports 3001 and 5173.
