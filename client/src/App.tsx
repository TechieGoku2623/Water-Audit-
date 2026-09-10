import { useEffect, useMemo, useState } from "react";
import { createFixture, deleteFixture, getSummary } from "./api.ts";
import type { AuditSummary, FixtureType } from "./types.ts";

const FIXTURE_TYPES: { value: FixtureType; label: string; typicalLiters: number }[] = [
  { value: "shower", label: "Shower", typicalLiters: 65 },
  { value: "toilet", label: "Toilet", typicalLiters: 9 },
  { value: "faucet", label: "Faucet", typicalLiters: 6 },
  { value: "dishwasher", label: "Dishwasher", typicalLiters: 15 },
  { value: "washingMachine", label: "Washing Machine", typicalLiters: 60 },
  { value: "irrigation", label: "Irrigation", typicalLiters: 120 },
  { value: "other", label: "Other", typicalLiters: 10 },
];

const emptyForm = {
  name: "",
  location: "",
  fixtureType: "shower" as FixtureType,
  litersPerUse: 65,
  usesPerDay: 2,
};

export function App() {
  const [summary, setSummary] = useState<AuditSummary | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function refresh() {
    setSummary(await getSummary());
  }

  useEffect(() => {
    refresh()
      .catch((e) => setError((e as Error).message))
      .finally(() => setLoading(false));
  }, []);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await createFixture(form);
      setForm(emptyForm);
      await refresh();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function onDelete(id: string) {
    setError(null);
    try {
      await deleteFixture(id);
      await refresh();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  function onTypeChange(fixtureType: FixtureType) {
    const preset = FIXTURE_TYPES.find((t) => t.value === fixtureType);
    setForm((prev) => ({
      ...prev,
      fixtureType,
      litersPerUse: preset ? preset.typicalLiters : prev.litersPerUse,
    }));
  }

  const recommendedSavings = useMemo(
    () =>
      summary?.recommendations.reduce((sum, r) => sum + r.monthlyCostSaved, 0) ?? 0,
    [summary],
  );

  return (
    <div className="app">
      <header className="header">
        <div className="logo">
          <span className="drop" aria-hidden>
            💧
          </span>
          <div>
            <h1>Water Audit</h1>
            <p className="tagline">
              Track fixtures, estimate consumption &amp; cost, and find savings.
            </p>
          </div>
        </div>
      </header>

      {error && <div className="banner error">{error}</div>}
      {loading && <div className="banner">Loading…</div>}

      {summary && (
        <section className="cards">
          <div className="card">
            <span className="card-label">Fixtures</span>
            <span className="card-value">{summary.fixtureCount}</span>
          </div>
          <div className="card">
            <span className="card-label">Daily usage</span>
            <span className="card-value">
              {summary.totalDailyLiters.toLocaleString()} <small>L</small>
            </span>
          </div>
          <div className="card">
            <span className="card-label">Monthly usage</span>
            <span className="card-value">
              {summary.totalMonthlyLiters.toLocaleString()} <small>L</small>
            </span>
          </div>
          <div className="card">
            <span className="card-label">Monthly cost</span>
            <span className="card-value">${summary.monthlyCost.toFixed(2)}</span>
          </div>
          <div className="card highlight">
            <span className="card-label">Efficiency score</span>
            <span className="card-value">{summary.efficiencyScore}/100</span>
          </div>
        </section>
      )}

      <div className="grid">
        <section className="panel">
          <h2>Add a fixture</h2>
          <form onSubmit={onSubmit} className="fixture-form">
            <label>
              Name
              <input
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="e.g. Master Bathroom Shower"
                required
              />
            </label>
            <label>
              Location
              <input
                value={form.location}
                onChange={(e) => setForm({ ...form, location: e.target.value })}
                placeholder="e.g. Master Bath"
              />
            </label>
            <label>
              Type
              <select
                value={form.fixtureType}
                onChange={(e) => onTypeChange(e.target.value as FixtureType)}
              >
                {FIXTURE_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
            </label>
            <div className="row">
              <label>
                Liters / use
                <input
                  type="number"
                  min="0.1"
                  step="0.1"
                  value={form.litersPerUse}
                  onChange={(e) =>
                    setForm({ ...form, litersPerUse: Number(e.target.value) })
                  }
                  required
                />
              </label>
              <label>
                Uses / day
                <input
                  type="number"
                  min="0.1"
                  step="0.1"
                  value={form.usesPerDay}
                  onChange={(e) =>
                    setForm({ ...form, usesPerDay: Number(e.target.value) })
                  }
                  required
                />
              </label>
            </div>
            <button type="submit" className="primary">
              Add fixture
            </button>
          </form>
        </section>

        <section className="panel">
          <h2>Fixture breakdown</h2>
          {summary && summary.breakdown.length > 0 ? (
            <table className="breakdown">
              <thead>
                <tr>
                  <th>Fixture</th>
                  <th>Type</th>
                  <th className="num">L/day</th>
                  <th className="num">Share</th>
                  <th className="num">$/mo</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {summary.breakdown.map((f) => (
                  <tr key={f.id}>
                    <td>
                      <strong>{f.name}</strong>
                      {f.location && <span className="muted"> · {f.location}</span>}
                    </td>
                    <td className="muted">{f.fixtureType}</td>
                    <td className="num">{f.litersPerDay.toLocaleString()}</td>
                    <td className="num">{f.shareOfTotal}%</td>
                    <td className="num">${f.monthlyCost.toFixed(2)}</td>
                    <td className="num">
                      <button
                        className="link danger"
                        onClick={() => onDelete(f.id)}
                        aria-label={`Delete ${f.name}`}
                      >
                        ✕
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="muted">No fixtures yet. Add one to start your audit.</p>
          )}
        </section>
      </div>

      {summary && summary.recommendations.length > 0 && (
        <section className="panel recommendations">
          <h2>
            Recommendations
            <span className="savings-pill">
              Save up to ${recommendedSavings.toFixed(2)}/mo
            </span>
          </h2>
          <ul>
            {summary.recommendations.map((r) => (
              <li key={r.fixtureId}>
                <div>
                  <strong>{r.fixtureName}</strong>
                  <p className="muted">{r.message}</p>
                </div>
                <div className="rec-savings">
                  <span>{r.monthlyLitersSaved.toLocaleString()} L/mo</span>
                  <span className="muted">${r.monthlyCostSaved.toFixed(2)}/mo</span>
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
