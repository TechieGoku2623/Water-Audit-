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
  litersPerUse: number;
  usesPerDay: number;
  createdAt: string;
}

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

export interface AuditSummary {
  fixtureCount: number;
  totalDailyLiters: number;
  totalMonthlyLiters: number;
  totalYearlyLiters: number;
  monthlyCost: number;
  yearlyCost: number;
  efficiencyScore: number;
  costPerLiter: number;
  currencySymbol: string;
  breakdown: FixtureBreakdown[];
  recommendations: Recommendation[];
}

export interface Settings {
  costPerLiter: number;
  currencySymbol: string;
}

export interface FixtureInput {
  name: string;
  location: string;
  fixtureType: FixtureType;
  litersPerUse: number;
  usesPerDay: number;
}
