"use client";

import {
  ArrowRight,
  Briefcase,
  Check,
  CreditCard,
  ExternalLink,
  FileText,
  RotateCcw,
  Search,
  Shield,
  ShieldCheck,
  Wallet,
  X,
  Zap,
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

function ResultIcon({ name }: { name: DemoRecord["icon"] }) {
  const props = { size: 20, strokeWidth: 1.8 };
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
  const [searchOpen, setSearchOpen] = useState(false);

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

  const potentialMatches = matches.filter((record) => record.status !== "claimed");
  const claimedMatches = matches.filter((record) => record.status === "claimed");
  const claimableTotal = potentialMatches.reduce(
    (sum, record) => sum + record.amount,
    0,
  );

  function runSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setQuery(`${firstName} ${lastName}`);
    setSearched(true);
    setSearchOpen(false);
    window.setTimeout(() => {
      document.getElementById("results")?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }, 80);
  }

  return (
    <div className="page-shell">
      <header className="site-header">
        <div className="site-header-inner">
          <div className="brand-group">
            <Link className="brand-link" href="/" aria-label="SmartCredit home">
              <span className="brand-name">smartcredit</span>
              <span className="brand-beta">
                BETA
                <span className="brand-star" aria-hidden="true">
                  *
                </span>
              </span>
            </Link>
            <div className="partner-strip">
              <span>Partnered with</span>
              <strong className="tu">TransUnion</strong>
              <span>·</span>
              <strong className="experian">Experian</strong>
              <span>·</span>
              <strong className="equifax">EQUIFAX</strong>
            </div>
          </div>
          <nav className="main-nav" aria-label="Product navigation">
            <span>Credit</span>
            <span>Reports</span>
            <span>Identity</span>
            <a href="#results" className="nav-active">
              Money
            </a>
          </nav>
        </div>
      </header>

      <main className="content">
        <section className="hero-card">
          <div className="hero-grid">
            <div>
              <h1>
                Get My <span>Money Back</span>
              </h1>
              <p className="hero-copy">
                Every year, banks, employers, and insurers turn billions in
                forgotten money over to the state - old paychecks, deposits,
                refunds, and account balances. We check those official records
                for you and surface any potential matches, free.
              </p>
            </div>

            <div className="common-card">
              <p className="mini-label">Commonly unclaimed</p>
              <ul className="common-grid">
                <li>
                  <span>
                    <CreditCard size={18} />
                  </span>
                  Forgotten bank balances
                </li>
                <li>
                  <span>
                    <Briefcase size={18} />
                  </span>
                  Uncashed paychecks
                </li>
                <li>
                  <span>
                    <Zap size={18} />
                  </span>
                  Utility &amp; security deposits
                </li>
                <li>
                  <span>
                    <Shield size={18} />
                  </span>
                  Insurance &amp; refund payouts
                </li>
              </ul>
            </div>
          </div>
        </section>

        <section className="steps-grid" aria-label="How it works">
          <article>
            <div>
              <span>1</span>
              <h2>Review</h2>
            </div>
            <p>
              See any potential matches reported in your name, with the source,
              amount, and the address the state has on file.
            </p>
          </article>
          <article>
            <div>
              <span>2</span>
              <h2>Claim</h2>
            </div>
            <p>
              We guide you to file directly with the state. Most California
              claims are processed in about <strong>30-180 days</strong>.
            </p>
            <a href={claimUrl} target="_blank" rel="noreferrer">
              See the step-by-step filing guide <ArrowRight size={15} />
            </a>
          </article>
          <article>
            <div>
              <span>3</span>
              <h2>Monitor</h2>
            </div>
            <p>
              We keep watching. As states publish new records, we re-check your
              name and alert you the moment a new match appears.
            </p>
          </article>
        </section>

        <section id="results" className="results-section">
          {searched && matches.length > 0 ? (
            <Results
              claimableTotal={claimableTotal}
              potentialMatches={potentialMatches}
              claimedMatches={claimedMatches}
            />
          ) : searched ? (
            <div className="empty-card solid">
              <div className="empty-icon">
                <Search size={28} />
              </div>
              <p className="mini-label">No matches yet</p>
              <h2>Nothing found in the hosted demo data.</h2>
              <p>
                Try Christa Villarosa, Boyd Gainor, Meena Fernandes, Williams
                Dunshea, or David B Coulter. The full California dataset still
                runs in the local Python prototype.
              </p>
            </div>
          ) : (
            <div className="empty-card">
              <div className="empty-icon">
                <Search size={22} />
              </div>
              <p>
                Tap <strong>Run your search</strong> (top right), enter your
                name, and run a search to see potential matches here.
              </p>
            </div>
          )}
        </section>
      </main>

      <footer className="footer">
        Prototype - funds data sourced from state unclaimed-property programs.
        SmartCredit is not affiliated with any state, never holds your funds, and
        never charges a finder&apos;s fee. Claims are filed for free directly
        with the respective state.
      </footer>

      {!searchOpen ? (
        <button
          className="search-fab"
          type="button"
          onClick={() => setSearchOpen(true)}
          aria-label="Run your search"
        >
          <Search size={18} />
          <span>Run your search</span>
        </button>
      ) : null}

      <div
        className={`search-overlay ${searchOpen ? "is-open" : ""}`}
        onClick={() => setSearchOpen(false)}
      />

      <aside className={`search-popout ${searchOpen ? "is-open" : ""}`}>
        <div className="search-popout-header">
          <div>
            <strong>Run your search</strong>
            <span>Search by name; add a city to narrow it</span>
          </div>
          <button
            type="button"
            onClick={() => setSearchOpen(false)}
            aria-label="Close search"
          >
            <X size={20} />
          </button>
        </div>

        <form className="search-form" onSubmit={runSearch}>
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
              placeholder="e.g. Los Angeles"
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
              <option value="">All states</option>
              <option value="CA">California</option>
              <option value="TX">Texas</option>
              <option value="NY">New York</option>
              <option value="FL">Florida</option>
              <option value="GA">Georgia</option>
              <option value="IL">Illinois</option>
              <option value="OH">Ohio</option>
              <option value="PA">Pennsylvania</option>
              <option value="NJ">New Jersey</option>
              <option value="AZ">Arizona</option>
            </select>
          </div>
          <button className="submit-search" type="submit">
            Search records <ArrowRight size={17} />
          </button>
          <p className="demo-note">
            Hosted demo data includes the curated California names from the
            prototype README.
          </p>
        </form>
      </aside>
    </div>
  );
}

function Results({
  claimableTotal,
  potentialMatches,
  claimedMatches,
}: {
  claimableTotal: number;
  potentialMatches: DemoRecord[];
  claimedMatches: DemoRecord[];
}) {
  return (
    <div>
      <div className="results-summary">
        <p className="mini-label">Your results</p>
        <h2>
          {potentialMatches.length > 0 ? (
            <>
              You may be owed about{" "}
              <span className="money-text">{money(claimableTotal)}</span>
            </>
          ) : (
            "Match history for your name"
          )}
        </h2>
        <p>
          {potentialMatches.length} claimable demo record
          {potentialMatches.length === 1 ? "" : "s"}.
          {claimedMatches.length > 0
            ? ` ${claimedMatches.length} record${
                claimedMatches.length === 1 ? "" : "s"
              } previously in your name ${
                claimedMatches.length === 1 ? "has" : "have"
              } since been claimed.`
            : ""}{" "}
          Amounts are state-reported estimates and may differ from the actual
          payout.
        </p>
      </div>

      {potentialMatches.length > 0 ? (
        <ResultGroup
          title="Potential matches"
          tone="green"
          records={potentialMatches}
        />
      ) : null}

      {claimedMatches.length > 0 ? (
        <ResultGroup
          title="Claimed history"
          tone="slate"
          subcopy="Previously reported in your name but no longer in the state's file - typically already claimed. Shown for your records."
          records={claimedMatches}
        />
      ) : null}

      <p className="result-disclaimer">
        Click <strong>Claim</strong> to be guided to the state&apos;s official
        portal - at no cost. You can always claim free directly with the state.
      </p>
    </div>
  );
}

function ResultGroup({
  title,
  subcopy,
  records,
  tone,
}: {
  title: string;
  subcopy?: string;
  records: DemoRecord[];
  tone: "green" | "slate";
}) {
  return (
    <section className="result-group">
      <div className="result-group-heading">
        <span className={`dot ${tone}`} />
        <h3>{title}</h3>
        <span className="count">{records.length}</span>
      </div>
      {subcopy ? <p className="result-subcopy">{subcopy}</p> : null}
      <ul>
        {records.map((record) => (
          <li key={record.id}>
            <ResultRow record={record} />
          </li>
        ))}
      </ul>
    </section>
  );
}

function ResultRow({ record }: { record: DemoRecord }) {
  const claimable = record.status !== "claimed";

  return (
    <article className={`result-row ${claimable ? "" : "is-claimed"}`}>
      <div className="result-icon" aria-hidden="true">
        <ResultIcon name={record.icon} />
      </div>
      <div className="result-main">
        <div className="result-title">
          <strong>{record.propertyType}</strong>
          {record.status === "new" ? <span className="new-badge">New</span> : null}
        </div>
        <p className="holder">{record.holder}</p>
        <dl>
          <dt>Reported as</dt>
          <dd>{record.reportedAs}</dd>
          <dt>Address on file</dt>
          <dd>{record.address}</dd>
          <dt>Source</dt>
          <dd className="source">
            <ShieldCheck size={13} /> {record.source}
          </dd>
        </dl>
      </div>
      <div className={`amount ${claimable ? "" : "is-claimed"}`}>
        {money(record.amount)}
        <span>Estimated</span>
      </div>
      <div>
        {claimable ? (
          <>
            <a
              className="claim-button"
              href={claimUrl}
              target="_blank"
              rel="noreferrer"
            >
              Claim <ExternalLink size={14} />
            </a>
            <button type="button" className="not-me">
              Not me <ArrowRight size={12} />
            </button>
          </>
        ) : (
          <>
            <span className="claimed-pill">
              <Check size={14} /> Claimed
            </span>
            <a
              className="verify-link"
              href={claimUrl}
              target="_blank"
              rel="noreferrer"
            >
              Verify on state portal <ArrowRight size={12} />
            </a>
          </>
        )}
      </div>
    </article>
  );
}
