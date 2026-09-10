export type FixtureType =
  | "shower"
  | "toilet"
  | "faucet"
  | "dishwasher"
  | "washingMachine"
  | "irrigation"
  | "other";

export interface Fixture {
  id: string;
  name: string;
  location: string;
  fixtureType: FixtureType;
  /** Liters consumed by a single use of this fixture. */
  litersPerUse: number;
  /** Average number of uses per day. */
  usesPerDay: number;
  createdAt: string;
}

export type FixtureInput = Omit<Fixture, "id" | "createdAt">;

export interface FixtureBreakdown extends Fixture {
  litersPerDay: number;
  litersPerMonth: number;
  monthlyCost: number;
  shareOfTotal: number;
}

export interface Recommendation {
  fixtureId: string;
  fixtureName: string;
  message: string;
  monthlyLitersSaved: number;
  monthlyCostSaved: number;
}

export interface Settings {
  /** Cost of water in the chosen currency per liter. */
  costPerLiter: number;
  /** Symbol used when formatting costs, e.g. "$" or "€". */
  currencySymbol: string;
}

export type SettingsInput = Partial<Settings>;

export interface AuditSummary {
  fixtureCount: number;
  totalDailyLiters: number;
  totalMonthlyLiters: number;
  totalYearlyLiters: number;
  monthlyCost: number;
  yearlyCost: number;
  /** 0-100, higher means more efficient relative to benchmarks. */
  efficiencyScore: number;
  costPerLiter: number;
  currencySymbol: string;
  breakdown: FixtureBreakdown[];
  recommendations: Recommendation[];
}
