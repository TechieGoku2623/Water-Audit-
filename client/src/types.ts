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
  monthlyCost: number;
  efficiencyScore: number;
  breakdown: FixtureBreakdown[];
  recommendations: Recommendation[];
}

export interface FixtureInput {
  name: string;
  location: string;
  fixtureType: FixtureType;
  litersPerUse: number;
  usesPerDay: number;
}
