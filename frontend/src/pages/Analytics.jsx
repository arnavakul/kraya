import { useState } from 'react';
import { Link } from 'react-router-dom';
import '../styles/analytics.css';

const TIME_RANGES = ['Last 30 Days', 'This Quarter', 'Year to Date', 'All Time'];

const METRIC_CARDS = [
  {
    title: 'Autonomous Spend',
    value: '₹1,42,80,000',
    delta: '+14.2%',
    sub: 'Routed through AI workflows',
    tone: 'positive',
    icon: '₹',
  },
  {
    title: 'Avg Sourcing Cycle',
    value: '1.4 Days',
    delta: '-77.4%',
    sub: 'Down from 6.2 manual days',
    tone: 'positive',
    icon: '⚡',
  },
  {
    title: 'Agent Autonomy Rate',
    value: '84.6%',
    delta: '+8.1%',
    sub: 'Zero manual intervention to RFQ',
    tone: 'positive',
    icon: '🤖',
  },
  {
    title: 'Audit-Ready Risk Score',
    value: '88.4 / 100',
    delta: '+5.2 pts',
    sub: 'TreeSHAP multi-factor verification',
    tone: 'positive',
    icon: '🛡️',
  },
];

const PIPELINE_FUNNEL = [
  { stage: '1. Requirement Validation', count: 64, pct: 100, desc: 'Extracted & verified by Intake Agent' },
  { stage: '2. Supplier Discovery', count: 59, pct: 92, desc: 'Matched across catalog & category rules' },
  { stage: '3. Quote Parsing & Assembly', count: 52, pct: 81, desc: 'Automated RFQs and quote extraction' },
  { stage: '4. XGBoost & TreeSHAP Scoring', count: 48, pct: 75, desc: 'Predictive risk & commercial rating' },
  { stage: '5. Recommendation & PO Draft', count: 44, pct: 69, desc: 'Presented for human sign-off' },
];

const SHAP_DRIVERS = [
  { feature: 'Price vs Budget Target', label: 'Commercial Alignment', impact: '+12.4 pts', positive: true, pct: 82 },
  { feature: 'Historical On-Time Delivery', label: 'Reliability Track Record', impact: '+8.6 pts', positive: true, pct: 68 },
  { feature: 'Extended Warranty Coverage', label: 'Contractual Protection', impact: '+4.8 pts', positive: true, pct: 45 },
  { feature: 'Delivery Lead Time Variance', label: 'Schedule Risk', impact: '-3.2 pts', positive: false, pct: 32 },
  { feature: 'Payment Terms Policy Deviation', label: 'Working Capital Impact', impact: '-2.1 pts', positive: false, pct: 24 },
];

const TOP_CATEGORIES = [
  { name: 'Laptops & IT Hardware', spend: '₹62,40,000', share: 44, count: 18 },
  { name: 'Cloud Infrastructure & SaaS', spend: '₹38,20,000', share: 27, count: 12 },
  { name: 'Office Ergonomics & Setup', spend: '₹24,10,000', share: 17, count: 8 },
  { name: 'Industrial Equipment & R&D', spend: '₹18,10,000', share: 12, count: 6 },
];

export default function Analytics() {
  const [selectedRange, setSelectedRange] = useState('Last 30 Days');

  return (
    <div className="analytics-page">
      {/* Header */}
      <div className="analytics-header">
        <div>
          <h1 className="analytics-title">Procurement & Agent Analytics</h1>
          <p className="analytics-subtitle">
            Explainable AI sourcing performance, XGBoost risk evaluation, and TreeSHAP multi-factor attributions.
          </p>
        </div>
        <div className="analytics-controls">
          <div className="analytics-range-picker">
            {TIME_RANGES.map((range) => (
              <button
                key={range}
                type="button"
                className={`analytics-range-btn ${selectedRange === range ? 'active' : ''}`}
                onClick={() => setSelectedRange(range)}
              >
                {range}
              </button>
            ))}
          </div>
          <Link to="/agents" className="btn">
            Open Agent Chat →
          </Link>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="analytics-kpis">
        {METRIC_CARDS.map((card) => (
          <div key={card.title} className="analytics-kpi-card">
            <div className="analytics-kpi-top">
              <span className="analytics-kpi-label">{card.title}</span>
              <span className="analytics-kpi-icon">{card.icon}</span>
            </div>
            <strong className="analytics-kpi-value">{card.value}</strong>
            <div className="analytics-kpi-footer">
              <span className={`analytics-kpi-delta analytics-kpi-delta--${card.tone}`}>
                {card.delta}
              </span>
              <span className="analytics-kpi-sub">{card.sub}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Grid: Funnel + TreeSHAP */}
      <div className="analytics-grid">
        {/* Agent Conversion Funnel */}
        <section className="card analytics-card">
          <div className="analytics-card-header">
            <div>
              <h2 className="analytics-card-title">Agent Pipeline Conversion</h2>
              <p className="analytics-card-sub">Autonomous transition efficiency across procurement states</p>
            </div>
            <span className="analytics-badge-pill">68.8% End-to-End</span>
          </div>

          <div className="analytics-funnel">
            {PIPELINE_FUNNEL.map((f) => (
              <div key={f.stage} className="analytics-funnel-row">
                <div className="analytics-funnel-meta">
                  <strong className="analytics-funnel-stage">{f.stage}</strong>
                  <span className="analytics-funnel-desc">{f.desc}</span>
                </div>
                <div className="analytics-funnel-bar-wrap">
                  <div className="analytics-funnel-bar" style={{ width: `${f.pct}%` }} />
                </div>
                <div className="analytics-funnel-stat">
                  <strong>{f.count} reqs</strong>
                  <span>({f.pct}%)</span>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* TreeSHAP Explainable Risk Factors */}
        <section className="card analytics-card">
          <div className="analytics-card-header">
            <div>
              <h2 className="analytics-card-title">TreeSHAP Explainable Risk Drivers</h2>
              <p className="analytics-card-sub">Multi-factor point contributions to quote risk scores (0–100)</p>
            </div>
            <span className="analytics-badge-pill">Audit-Ready ML</span>
          </div>

          <div className="analytics-shap-list">
            {SHAP_DRIVERS.map((item) => (
              <div key={item.feature} className="analytics-shap-item">
                <div className="analytics-shap-head">
                  <div>
                    <strong className="analytics-shap-feature">{item.feature}</strong>
                    <span className="analytics-shap-label">{item.label}</span>
                  </div>
                  <span className={`analytics-shap-impact ${item.positive ? 'positive' : 'negative'}`}>
                    {item.impact}
                  </span>
                </div>
                <div className="analytics-shap-bar-bg">
                  <div
                    className={`analytics-shap-bar ${item.positive ? 'positive' : 'negative'}`}
                    style={{ width: `${item.pct}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>

      {/* Grid: Category Spend & Actionable Intelligence */}
      <div className="analytics-grid">
        {/* Category Spend Distribution */}
        <section className="card analytics-card">
          <div className="analytics-card-header">
            <div>
              <h2 className="analytics-card-title">Category Spend Distribution</h2>
              <p className="analytics-card-sub">Capital deployment across active procurement categories</p>
            </div>
            <Link to="/requests" className="analytics-link">
              View Requests →
            </Link>
          </div>

          <div className="analytics-cat-list">
            {TOP_CATEGORIES.map((cat) => (
              <div key={cat.name} className="analytics-cat-row">
                <div className="analytics-cat-info">
                  <strong>{cat.name}</strong>
                  <span>{cat.count} total procurement orders</span>
                </div>
                <div className="analytics-cat-spend">
                  <strong>{cat.spend}</strong>
                  <span>{cat.share}% of total spend</span>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* AI Recommendations & Opportunities */}
        <section className="card analytics-card">
          <div className="analytics-card-header">
            <div>
              <h2 className="analytics-card-title">Autonomous Recommendations</h2>
              <p className="analytics-card-sub">Actionable intelligence generated by the procurement agent</p>
            </div>
            <span className="analytics-badge-pill green">3 Opportunities</span>
          </div>

          <div className="analytics-recommendations">
            <div className="analytics-rec-card">
              <span className="analytics-rec-tag">Volume Aggregation</span>
              <strong className="analytics-rec-title">Consolidate Q4 Laptop Procurement</strong>
              <p className="analytics-rec-p">
                3 separate departments have open laptop requests. Aggregating 45 units could unlock an estimated
                <strong> 11.5% bulk supplier discount (₹3,40,000)</strong>.
              </p>
            </div>

            <div className="analytics-rec-card">
              <span className="analytics-rec-tag">Supplier Diversification</span>
              <strong className="analytics-rec-title">Expand Tier-2 Hardware Suppliers</strong>
              <p className="analytics-rec-p">
                IT hardware currently relies on 2 vendors. Onboarding 2 additional verified vendors in SE Asia will reduce single-source delivery risk.
              </p>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
