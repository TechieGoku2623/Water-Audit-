CREATE TABLE IF NOT EXISTS facilities (
    facility_id TEXT PRIMARY KEY,
    company TEXT NOT NULL,
    name TEXT NOT NULL,
    region TEXT NOT NULL,
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    it_capacity_mw DOUBLE PRECISION,
    cooling_type TEXT,
    source_url TEXT NOT NULL CHECK (source_url <> '')
);

CREATE TABLE IF NOT EXISTS disclosures (
    facility_id TEXT NOT NULL REFERENCES facilities(facility_id),
    year INTEGER NOT NULL CHECK (year >= 1900),
    wue_l_per_kwh DOUBLE PRECISION,
    pue DOUBLE PRECISION,
    source_url TEXT NOT NULL CHECK (source_url <> ''),
    PRIMARY KEY (facility_id, year)
);

CREATE TABLE IF NOT EXISTS permits (
    facility_id TEXT NOT NULL REFERENCES facilities(facility_id),
    permit_id TEXT NOT NULL,
    withdrawal_limit_gpd DOUBLE PRECISION,
    discharge_limit_gpd DOUBLE PRECISION,
    issuing_agency TEXT,
    source_url TEXT NOT NULL CHECK (source_url <> ''),
    PRIMARY KEY (facility_id, permit_id)
);

CREATE TABLE IF NOT EXISTS climate (
    region TEXT NOT NULL,
    month INTEGER NOT NULL CHECK (month BETWEEN 1 AND 12),
    avg_temp_f DOUBLE PRECISION,
    avg_humidity_pct DOUBLE PRECISION,
    source_url TEXT NOT NULL CHECK (source_url <> ''),
    PRIMARY KEY (region, month)
);

CREATE INDEX IF NOT EXISTS idx_facilities_region ON facilities(region);
CREATE INDEX IF NOT EXISTS idx_facilities_cooling_type ON facilities(cooling_type);
CREATE INDEX IF NOT EXISTS idx_disclosures_year ON disclosures(year);
CREATE INDEX IF NOT EXISTS idx_permits_facility ON permits(facility_id);
