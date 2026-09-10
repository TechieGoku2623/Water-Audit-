import { useEffect, useMemo, useState } from "react";
import {
  createFixture,
  deleteFixture,
  getSettings,
  getSummary,
  updateFixture,
  updateSettings,
} from "./api.ts";
import type { AuditSummary, FixtureType, Settings } from "./types.ts";

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
  const [settings, setSettings] = useState<Settings | null>(null);
  const [ratePer1000, setRatePer1000] = useState("");
  const [currency, setCurrency] = useState("");
  const [form, setForm] = useState(emptyForm);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function refresh() {
    const [s, cfg] = await Promise.all([getSummary(), getSettings()]);
    setSummary(s);
    setSettings(cfg);
    setRatePer1000((cfg.costPerLiter * 1000).toString());
    setCurrency(cfg.currencySymbol);
  }

  useEffect(() => {
    refresh()
      .catch((e) => setError((e as Error).message))
      .finally(() => setLoading(false));
  }, []);

  const cur = summary?.currencySymbol ?? "$";
  const money = (value: number) => `${cur}${value.toFixed(2)}`;

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      if (editingId) {
        await updateFixture(editingId, form);
      } else {
        await createFixture(form);
      }
      setForm(emptyForm);
      setEditingId(null);
      await refresh();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  function onEdit(id: string) {
    const f = summary?.breakdown.find((b) => b.id === id);
    if (!f) return;
    setEditingId(id);
    setForm({
      name: f.name,
      location: f.location,
      fixtureType: f.fixtureType,
      litersPerUse: f.litersPerUse,
      usesPerDay: f.usesPerDay,
    });
  }

  function onCancelEdit() {
    setEditingId(null);
    setForm(emptyForm);
  }

  async function onDelete(id: string) {
    setError(null);
    try {
      if (editingId === id) onCancelEdit();
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

  async function applySettings() {
    if (!settings) return;
    const perLiter = Number(ratePer1000) / 1000;
    const symbol = currency.trim() || "$";
    if (
      perLiter === settings.costPerLiter &&
      symbol === settings.currencySymbol
    ) {
      return;
    }
    setError(null);
    try {
      await updateSettings({ costPerLiter: perLiter, currencySymbol: symbol });
      await refresh();
    } catch (err) {
      setError((err as Error).message);
    }
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
            <span className="card-label">Cost</span>
            <span className="card-value">{money(summary.monthlyCost)}<small>/mo</small></span>
            <span className="card-sub">{money(summary.yearlyCost)}/yr</span>
          </div>
          <div className="card highlight">
            <span className="card-label">Efficiency score</span>
            <span className="card-value">{summary.efficiencyScore}/100</span>
          </div>
        </section>
      )}

      {settings && (
        <section className="panel settings-bar">
          <h2>Rate &amp; currency</h2>
          <div className="settings-fields">
            <label>
              Water rate (per 1,000 L)
              <input
                type="number"
                min="0"
                step="0.1"
                value={ratePer1000}
                onChange={(e) => setRatePer1000(e.target.value)}
                onBlur={applySettings}
                onKeyDown={(e) => e.key === "Enter" && applySettings()}
              />
            </label>
            <label>
              Currency symbol
              <input
                maxLength={3}
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
                onBlur={applySettings}
                onKeyDown={(e) => e.key === "Enter" && applySettings()}
              />
            </label>
            <p className="muted settings-hint">
              Changes apply to all cost estimates below.
            </p>
          </div>
        </section>
      )}

      <div className="grid">
        <section className="panel">
          <h2>{editingId ? "Edit fixture" : "Add a fixture"}</h2>
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
            <div className="form-actions">
              <button type="submit" className="primary">
                {editingId ? "Save changes" : "Add fixture"}
              </button>
              {editingId && (
                <button type="button" className="secondary" onClick={onCancelEdit}>
                  Cancel
                </button>
              )}
            </div>
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
                  <th className="num">{cur}/mo</th>
                  <th className="actions-col"></th>
                </tr>
              </thead>
              <tbody>
                {summary.breakdown.map((f) => (
                  <tr key={f.id} className={editingId === f.id ? "editing" : ""}>
                    <td>
                      <strong>{f.name}</strong>
                      {f.location && <span className="muted"> · {f.location}</span>}
                    </td>
                    <td className="muted">{f.fixtureType}</td>
                    <td className="num">{f.litersPerDay.toLocaleString()}</td>
                    <td className="num">{f.shareOfTotal}%</td>
                    <td className="num">{money(f.monthlyCost)}</td>
                    <td className="num actions-col">
                      <button
                        className="link"
                        onClick={() => onEdit(f.id)}
                        aria-label={`Edit ${f.name}`}
                      >
                        ✎
                      </button>
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

      {summary && summary.breakdown.length > 0 && (
        <section className="panel chart-panel">
          <h2>Usage by fixture</h2>
          <ul className="chart">
            {[...summary.breakdown]
              .sort((a, b) => b.litersPerDay - a.litersPerDay)
              .map((f) => (
                <li key={f.id} className="chart-row">
                  <span className="chart-label" title={f.name}>
                    {f.name}
                  </span>
                  <div className="chart-track">
                    <div
                      className="chart-bar"
                      style={{ width: `${Math.max(f.shareOfTotal, 2)}%` }}
                    >
                      <span className="chart-bar-value">
                        {f.litersPerDay.toLocaleString()} L/day
                      </span>
                    </div>
                  </div>
                  <span className="chart-share">{f.shareOfTotal}%</span>
                </li>
              ))}
          </ul>
        </section>
      )}

      {summary && summary.recommendations.length > 0 && (
        <section className="panel recommendations">
          <h2>
            Recommendations
            <span className="savings-pill">
              Save up to {money(recommendedSavings)}/mo
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
                  <span className="muted">{money(r.monthlyCostSaved)}/mo</span>
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
