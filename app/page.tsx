"use client";

import {
  Briefcase,
  CreditCard,
  ExternalLink,
  FileText,
  RotateCcw,
  Search,
  ShieldCheck,
  Wallet,
  X,
} from "lucide-react";
import Link from "next/link";
import { FormEvent, useMemo, useState } from "react";

type ResultStatus = "new" | "active" | "claimed";

type DemoRecord = {
  id: number;
  searchName: string;
  propertyType: string;
  holder: string;
  reportedAs: string;
  address: string;
  source: string;
  amount: number;
  status: ResultStatus;
  icon: "wallet" | "briefcase" | "card" | "refund" | "file";
};

const DEMO_RECORDS: DemoRecord[] = [
  {
    id: 101,
    searchName: "christa villarosa",
    propertyType: "Insurance payout",
    holder: "Pacific Life Insurance Company",
    reportedAs: "Christa Villarosa",
    address: "Victorville, CA",
    source: "California State Controller",
    amount: 1284.52,
    status: "new",
    icon: "file",
  },
  {
    id: 102,
    searchName: "christa villarosa",
    propertyType: "Bank balance",
    holder: "Wells Fargo Bank",
    reportedAs: "Christa M Villarosa",
    address: "Victorville, CA",
    source: "California State Controller",
    amount: 402.18,
    status: "active",
    icon: "wallet",
  },
  {
    id: 201,
    searchName: "boyd gainor",
    propertyType: "Uncashed check",
    holder: "State Compensation Insurance Fund",
    reportedAs: "Boyd Gainor",
    address: "San Francisco, CA",
    source: "California State Controller",
    amount: 842.75,
    status: "active",
    icon: "briefcase",
  },
  {
    id: 202,
    searchName: "boyd gainor",
    propertyType: "Refund",
    holder: "City and County of San Francisco",
    reportedAs: "Boyd L Gainor",
    address: "San Francisco, CA",
    source: "California State Controller",
    amount: 118.44,
    status: "claimed",
    icon: "refund",
  },
  {
    id: 301,
    searchName: "meena fernandes",
    propertyType: "Security deposit",
    holder: "Pacific Gas and Electric Company",
    reportedAs: "Meena Fernandes",
    address: "Sunnyvale, CA",
    source: "California State Controller",
    amount: 274.9,
    status: "new",
    icon: "card",
  },
  {
    id: 401,
    searchName: "williams dunshea",
    propertyType: "Bank balance",
    holder: "Bank of America",
    reportedAs: "Williams Dunshea",
    address: "Bakersfield, CA",
    source: "California State Controller",
    amount: 1567.33,
    status: "active",
    icon: "wallet",
  },
  {
    id: 501,
    searchName: "david b coulter",
    propertyType: "Payroll check",
    holder: "California Payroll Services",
    reportedAs: "David B Coulter",
    address: "California",
    source: "California State Controller",
    amount: 319.8,
    status: "active",
    icon: "briefcase",
  },
];

const claimUrl = "https://claimit.ca.gov/";

function normalize(value: string) {
  return value.trim().toLowerCase().replace(/\s+/g, " ");
}

function money(value: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(value);
}

function Icon({ name }: { name: DemoRecord["icon"] }) {
  const props = { size: 20, strokeWidth: 1.9 };
  if (name === "wallet") return <Wallet {...props} />;
  if (name === "briefcase") return <Briefcase {...props} />;
  if (name === "card") return <CreditCard {...props} />;
  if (name === "refund") return <RotateCcw {...props} />;
  return <FileText {...props} />;
}

export default function Home() {
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [city, setCity] = useState("");
  const [state, setState] = useState("CA");
  const [searched, setSearched] = useState(false);
  const [query, setQuery] = useState("");

  const matches = useMemo(() => {
    if (!searched) return [];

    const nameQuery = normalize(query);
    const cityQuery = normalize(city);
    const tokens = nameQuery.split(" ").filter(Boolean);

    if (state && state !== "CA") return [];

    return DEMO_RECORDS.filter((record) => {
      const name = normalize(record.searchName);
      const address = normalize(record.address);
      const nameMatches =
        tokens.length === 0 || tokens.every((token) => name.includes(token));
      const cityMatches = !cityQuery || address.includes(cityQuery);
      return nameMatches && cityMatches;
    }).sort((a, b) => {
      if (a.status === "claimed" && b.status !== "claimed") return 1;
      if (a.status !== "claimed" && b.status === "claimed") return -1;
      return b.amount - a.amount;
    });
  }, [city, query, searched, state]);

  const claimable = matches.filter((record) => record.status !== "claimed");
  const claimed = matches.filter((record) => record.status === "claimed");
  const total = claimable.reduce((sum, record) => sum + record.amount, 0);

  function runSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setQuery(`${firstName} ${lastName}`);
    setSearched(true);
  }

  function resetSearch() {
    setFirstName("");
    setLastName("");
    setCity("");
    setState("CA");
    setQuery("");
    setSearched(false);
  }

  return (
    <div className="shell">
      <header className="topbar">
        <div className="topbar-inner">
          <Link className="brand" href="/" aria-label="SmartCredit home">
            <span className="brand-name">smartcredit</span>
            <span className="brand-beta">BETA</span>
          </Link>
          <nav className="nav" aria-label="Product navigation">
            <a href="#search">Money</a>
            <span>Credit</span>
            <span>Reports</span>
            <span>Identity</span>
          </nav>
        </div>
      </header>

      <main className="main">
        <section className="hero">
          <div className="hero-copy">
            <p className="eyebrow">Hosted demo</p>
            <h1>
              Get My <span className="orange">Money Back</span>
            </h1>
            <p className="lead">
              Search sample California unclaimed-property records, review
              potential matches, and open the official state claim portal. The
              local Python prototype still powers the full DuckDB-backed search.
            </p>
          </div>

          <aside className="hero-panel" id="search" aria-label="Search demo">
            <div className="facts">
              <div className="fact">
                <strong>CA</strong>
                <span>Hosted demo coverage</span>
              </div>
              <div className="fact">
                <strong>{DEMO_RECORDS.length}</strong>
                <span>Demo records available</span>
              </div>
            </div>

            <form className="search-card" onSubmit={runSearch}>
              <h2>Run your search</h2>
              <p>
                Try Christa Villarosa, Boyd Gainor, Meena Fernandes, Williams
                Dunshea, or David B Coulter.
              </p>
              <div className="form-grid">
                <div>
                  <label htmlFor="firstName">First name</label>
                  <input
                    id="firstName"
                    autoComplete="given-name"
                    value={firstName}
                    onChange={(event) => setFirstName(event.target.value)}
                  />
                </div>
                <div>
                  <label htmlFor="lastName">Last name</label>
                  <input
                    id="lastName"
                    autoComplete="family-name"
                    value={lastName}
                    onChange={(event) => setLastName(event.target.value)}
                  />
                </div>
                <div>
                  <label htmlFor="city">City</label>
                  <input
                    id="city"
                    placeholder="Optional"
                    value={city}
                    onChange={(event) => setCity(event.target.value)}
                  />
                </div>
                <div>
                  <label htmlFor="state">State</label>
                  <select
                    id="state"
                    value={state}
                    onChange={(event) => setState(event.target.value)}
                  >
                    <option value="CA">California</option>
                    <option value="TX">Texas</option>
                    <option value="NY">New York</option>
                    <option value="FL">Florida</option>
                  </select>
                </div>
              </div>
              <div className="button-row">
                <button className="button button-primary" type="submit">
                  <Search size={18} strokeWidth={2.2} />
                  Search records
                </button>
                <button
                  className="button button-secondary"
                  type="button"
                  onClick={resetSearch}
                  aria-label="Clear search"
                >
                  <X size={18} strokeWidth={2.2} />
                </button>
              </div>
            </form>

            <div className="hero-note">
              SmartCredit is not affiliated with any state, never holds funds,
              and never charges a finder fee. Claims are filed free directly
              with the state.
            </div>
          </aside>
        </section>

        <section className="workflow" aria-label="How it works">
          <article className="step">
            <span className="step-number">1</span>
            <h3>Review</h3>
            <p>
              See the source, holder, address on file, and state-reported
              amount for each potential match.
            </p>
          </article>
          <article className="step">
            <span className="step-number">2</span>
            <h3>Claim</h3>
            <p>
              Use the official state portal. California claims typically process
              in about 30 to 180 days.
            </p>
          </article>
          <article className="step">
            <span className="step-number">3</span>
            <h3>Monitor</h3>
            <p>
              The local prototype compares state snapshots so newly reported and
              claimed records can be shown separately.
            </p>
          </article>
        </section>

        <section className="results-shell" aria-live="polite">
          <div className="results-header">
            <div>
              <p className="eyebrow">Results</p>
              <h2>
                {searched && claimable.length
                  ? `You may be owed ${money(total)}`
                  : searched
                    ? "No demo matches found"
                    : "Search results appear here"}
              </h2>
            </div>
            <p>
              {searched
                ? `${claimable.length} claimable demo record${
                    claimable.length === 1 ? "" : "s"
                  } and ${claimed.length} claimed-history record${
                    claimed.length === 1 ? "" : "s"
                  }.`
                : "Enter a demo name above to see the shareable Sites version in action."}
            </p>
          </div>

          {matches.length > 0 ? (
            <ul className="result-list">
              {matches.map((record) => (
                <li className="result-row" key={record.id}>
                  <div className="icon-cell" aria-hidden="true">
                    <Icon name={record.icon} />
                  </div>
                  <div>
                    <div className="row-title">
                      <strong>{record.propertyType}</strong>
                      {record.status === "new" ? (
                        <span className="badge">New</span>
                      ) : null}
                      {record.status === "claimed" ? (
                        <span className="badge">Claimed</span>
                      ) : null}
                    </div>
                    <div className="holder">{record.holder}</div>
                    <dl className="details">
                      <dt>Reported as</dt>
                      <dd>{record.reportedAs}</dd>
                      <dt>Address on file</dt>
                      <dd>{record.address}</dd>
                      <dt>Source</dt>
                      <dd>
                        <ShieldCheck size={14} strokeWidth={2} />{" "}
                        {record.source}
                      </dd>
                    </dl>
                  </div>
                  <div className="amount">
                    {money(record.amount)}
                    <span>Estimated</span>
                  </div>
                  <a
                    className="button button-primary"
                    href={claimUrl}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Claim
                    <ExternalLink size={16} strokeWidth={2.2} />
                  </a>
                </li>
              ))}
            </ul>
          ) : (
            <div className="empty">
              {searched
                ? "Try one of the demo names listed in the search panel, or choose California as the state."
                : "No search has been run yet."}
            </div>
          )}
        </section>
      </main>

      <footer className="footer">
        Hosted Sites demo for sharing. The local FastAPI prototype remains the
        source for full California data ingestion, DuckDB search, MaxAI, admin,
        and the live deck.
      </footer>
    </div>
  );
}
