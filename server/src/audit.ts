import type {
  AuditSummary,
  Fixture,
  FixtureBreakdown,
  FixtureType,
  Recommendation,
  Settings,
} from "./types.js";

const DAYS_PER_MONTH = 30;
const DAYS_PER_YEAR = 365;

/** Default cost of water in USD per liter (roughly $7.60 per 1000 gallons). */
export const DEFAULT_COST_PER_LITER = 0.002;

/**
 * Per-use liter benchmarks for an efficient fixture. Anything meaningfully
 * above the benchmark is flagged with a recommendation and estimated savings.
 */
const EFFICIENT_LITERS_PER_USE: Partial<Record<FixtureType, number>> = {
  shower: 40,
  toilet: 6,
  faucet: 4,
  dishwasher: 12,
  washingMachine: 50,
};

function round(value: number, decimals = 2): number {
  const factor = 10 ** decimals;
  return Math.round(value * factor) / factor;
}

export function summarize(fixtures: Fixture[], settings: Settings): AuditSummary {
  const costPerLiter = settings.costPerLiter;
  const breakdown: FixtureBreakdown[] = fixtures.map((f) => {
    const litersPerDay = f.litersPerUse * f.usesPerDay;
    const litersPerMonth = litersPerDay * DAYS_PER_MONTH;
    return {
      ...f,
      litersPerDay: round(litersPerDay),
      litersPerMonth: round(litersPerMonth),
      monthlyCost: round(litersPerMonth * costPerLiter),
      shareOfTotal: 0,
    };
  });

  const totalDailyLiters = breakdown.reduce((sum, f) => sum + f.litersPerDay, 0);
  const totalMonthlyLiters = totalDailyLiters * DAYS_PER_MONTH;

  for (const f of breakdown) {
    f.shareOfTotal =
      totalDailyLiters > 0 ? round((f.litersPerDay / totalDailyLiters) * 100, 1) : 0;
  }

  const recommendations: Recommendation[] = [];
  for (const f of fixtures) {
    const benchmark = EFFICIENT_LITERS_PER_USE[f.fixtureType];
    if (benchmark === undefined || f.litersPerUse <= benchmark * 1.1) {
      continue;
    }
    const litersSavedPerDay = (f.litersPerUse - benchmark) * f.usesPerDay;
    const monthlyLitersSaved = round(litersSavedPerDay * DAYS_PER_MONTH);
    recommendations.push({
      fixtureId: f.id,
      fixtureName: f.name,
      message: `Uses ${f.litersPerUse} L per use vs. an efficient benchmark of ${benchmark} L. Consider a low-flow ${f.fixtureType} to cut usage.`,
      monthlyLitersSaved,
      monthlyCostSaved: round(monthlyLitersSaved * costPerLiter),
    });
  }
  recommendations.sort((a, b) => b.monthlyLitersSaved - a.monthlyLitersSaved);

  const totalPotentialSavings = recommendations.reduce(
    (sum, r) => sum + r.monthlyLitersSaved,
    0,
  );
  const efficiencyScore =
    totalMonthlyLiters > 0
      ? round(
          Math.max(
            0,
            Math.min(100, (1 - totalPotentialSavings / totalMonthlyLiters) * 100),
          ),
          0,
        )
      : 100;

  const totalYearlyLiters = totalDailyLiters * DAYS_PER_YEAR;

  return {
    fixtureCount: fixtures.length,
    totalDailyLiters: round(totalDailyLiters),
    totalMonthlyLiters: round(totalMonthlyLiters),
    totalYearlyLiters: round(totalYearlyLiters),
    monthlyCost: round(totalMonthlyLiters * costPerLiter),
    yearlyCost: round(totalYearlyLiters * costPerLiter),
    efficiencyScore,
    costPerLiter,
    currencySymbol: settings.currencySymbol,
    breakdown,
    recommendations,
  };
}
