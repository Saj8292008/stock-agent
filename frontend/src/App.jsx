import { useCallback, useEffect, useRef, useState } from "react";
import {
  Area, AreaChart, CartesianGrid, ResponsiveContainer,
  Tooltip, XAxis, YAxis,
} from "recharts";
import { RefreshCw, TrendingDown, TrendingUp, Zap } from "lucide-react";

const API = "";

const fmt$ = (n) =>
  n == null ? "—" : `$${Number(n).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

const fmtPct = (n) =>
  n == null ? "—" : `${n >= 0 ? "+" : ""}${(n * 100).toFixed(2)}%`;

const pctColor = (n) =>
  n == null ? "text-slate-400" : n >= 0 ? "text-emerald-400" : "text-red-400";

// ── small stat card ────────────────────────────────────────────────────────

function StatCard({ label, value, sub, color = "text-white" }) {
  return (
    <div className="bg-slate-800 rounded-xl p-5 flex flex-col gap-1 border border-slate-700">
      <span className="text-xs text-slate-400 uppercase tracking-widest">{label}</span>
      <span className={`text-2xl font-bold tabular-nums ${color}`}>{value}</span>
      {sub && <span className="text-sm text-slate-400">{sub}</span>}
    </div>
  );
}

// ── stock price card ───────────────────────────────────────────────────────

function StockCard({ symbol, name, price, ref_price, pct_from_ref, holding }) {
  const signal =
    holding ? "HOLDING"
    : pct_from_ref != null && pct_from_ref <= -0.05 ? "BUY SIGNAL"
    : "watching";

  const signalColor =
    holding ? "bg-cyan-900 text-cyan-300"
    : signal === "BUY SIGNAL" ? "bg-emerald-900 text-emerald-300"
    : "bg-slate-700 text-slate-400";

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-4 flex flex-col gap-2">
      <div className="flex justify-between items-start">
        <div>
          <div className="font-bold text-white">{symbol}</div>
          <div className="text-xs text-slate-400">{name}</div>
        </div>
        <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${signalColor}`}>
          {signal}
        </span>
      </div>
      <div className="text-xl font-bold tabular-nums text-white">{fmt$(price)}</div>
      <div className="flex justify-between text-xs text-slate-400">
        <span>Ref {fmt$(ref_price)}</span>
        <span className={pctColor(pct_from_ref)}>{fmtPct(pct_from_ref)} from ref</span>
      </div>
    </div>
  );
}

// ── positions table ────────────────────────────────────────────────────────

function PositionsTable({ holdings }) {
  if (!holdings?.length)
    return <p className="text-slate-400 text-sm py-4">No open positions.</p>;

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-slate-400 border-b border-slate-700">
            {["Symbol", "Shares", "Avg Cost", "Current", "Value", "P&L", "P&L %"].map((h) => (
              <th key={h} className="pb-2 pr-4 font-medium">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {holdings.map((h) => (
            <tr key={h.symbol} className="border-b border-slate-800 hover:bg-slate-800/50">
              <td className="py-2 pr-4 font-bold text-cyan-400">{h.symbol}</td>
              <td className="py-2 pr-4 tabular-nums">{h.shares.toFixed(4)}</td>
              <td className="py-2 pr-4 tabular-nums">{fmt$(h.avg_cost)}</td>
              <td className="py-2 pr-4 tabular-nums">{fmt$(h.current_price)}</td>
              <td className="py-2 pr-4 tabular-nums">{fmt$(h.current_value)}</td>
              <td className={`py-2 pr-4 tabular-nums font-semibold ${pctColor(h.pnl)}`}>
                {fmt$(h.pnl)}
              </td>
              <td className={`py-2 pr-4 tabular-nums font-semibold ${pctColor(h.pnl_pct)}`}>
                {fmtPct(h.pnl_pct)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ── trade history ──────────────────────────────────────────────────────────

function TradeHistory({ trades }) {
  if (!trades?.length)
    return <p className="text-slate-400 text-sm py-4">No trades yet.</p>;

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-slate-400 border-b border-slate-700">
            {["Time", "Action", "Symbol", "Shares", "Price", "Total", "Reason"].map((h) => (
              <th key={h} className="pb-2 pr-4 font-medium">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {trades.map((t, i) => (
            <tr key={i} className="border-b border-slate-800 hover:bg-slate-800/50">
              <td className="py-2 pr-4 text-slate-400">{t.timestamp.slice(0, 19).replace("T", " ")}</td>
              <td className={`py-2 pr-4 font-bold ${t.action === "BUY" ? "text-emerald-400" : "text-red-400"}`}>
                {t.action}
              </td>
              <td className="py-2 pr-4 font-bold text-cyan-400">{t.symbol}</td>
              <td className="py-2 pr-4 tabular-nums">{t.shares.toFixed(4)}</td>
              <td className="py-2 pr-4 tabular-nums">{fmt$(t.price)}</td>
              <td className="py-2 pr-4 tabular-nums">{fmt$(t.total)}</td>
              <td className="py-2 pr-4 text-slate-400">{t.reason}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ── price chart ────────────────────────────────────────────────────────────

function PriceChart({ symbol }) {
  const [data, setData] = useState([]);
  const [period, setPeriod] = useState("1mo");

  useEffect(() => {
    fetch(`${API}/api/history/${symbol}?period=${period}`)
      .then((r) => r.json())
      .then(setData)
      .catch(() => {});
  }, [symbol, period]);

  const periods = ["5d", "1mo", "3mo", "6mo", "1y"];

  return (
    <div>
      <div className="flex gap-2 mb-3">
        {periods.map((p) => (
          <button
            key={p}
            onClick={() => setPeriod(p)}
            className={`px-2 py-0.5 rounded text-xs font-medium transition-colors ${
              period === p ? "bg-indigo-600 text-white" : "bg-slate-700 text-slate-300 hover:bg-slate-600"
            }`}
          >
            {p}
          </button>
        ))}
      </div>
      <ResponsiveContainer width="100%" height={200}>
        <AreaChart data={data}>
          <defs>
            <linearGradient id="cg" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor="#6366f1" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#6366f1" stopOpacity={0}   />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis dataKey="date" tick={{ fill: "#64748b", fontSize: 11 }} tickLine={false} axisLine={false} />
          <YAxis tick={{ fill: "#64748b", fontSize: 11 }} tickLine={false} axisLine={false}
            tickFormatter={(v) => `$${v.toFixed(0)}`} domain={["auto", "auto"]} />
          <Tooltip
            contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
            labelStyle={{ color: "#94a3b8" }}
            formatter={(v) => [`$${v.toFixed(2)}`, "Close"]}
          />
          <Area type="monotone" dataKey="close" stroke="#6366f1" strokeWidth={2}
            fill="url(#cg)" dot={false} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

// ── main app ───────────────────────────────────────────────────────────────

export default function App() {
  const [portfolio, setPortfolio] = useState(null);
  const [trades,    setTrades]    = useState([]);
  const [loading,   setLoading]   = useState(false);
  const [cycling,   setCycling]   = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [chartSymbol, setChartSymbol] = useState("NVDA");
  const intervalRef = useRef(null);

  const fetchAll = useCallback(async () => {
    try {
      const [pRes, tRes] = await Promise.all([
        fetch(`${API}/api/portfolio`),
        fetch(`${API}/api/trades?limit=30`),
      ]);
      setPortfolio(await pRes.json());
      setTrades(await tRes.json());
      setLastUpdate(new Date().toLocaleTimeString());
    } catch {
      // backend may not be running
    }
  }, []);

  const refresh = useCallback(async () => {
    setLoading(true);
    await fetchAll();
    setLoading(false);
  }, [fetchAll]);

  const runCycle = useCallback(async () => {
    setCycling(true);
    try {
      await fetch(`${API}/api/run-cycle`, { method: "POST" });
      await fetchAll();
    } finally {
      setCycling(false);
    }
  }, [fetchAll]);

  useEffect(() => {
    refresh();
    intervalRef.current = setInterval(refresh, 60_000);
    return () => clearInterval(intervalRef.current);
  }, [refresh]);

  const stocks   = portfolio?.stocks || {};
  const prices   = portfolio?.prices || {};
  const refs     = portfolio?.refs   || {};
  const holdings = portfolio?.holdings || [];
  const heldSet  = new Set(holdings.map((h) => h.symbol));

  return (
    <div className="min-h-screen bg-[#0f1117] text-slate-100 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Zap className="text-indigo-400" size={24} /> Stock Agent
          </h1>
          <p className="text-slate-400 text-sm mt-0.5">Paper Trading Dashboard</p>
        </div>
        <div className="flex items-center gap-3">
          {lastUpdate && (
            <span className="text-xs text-slate-500">Updated {lastUpdate}</span>
          )}
          <button
            onClick={runCycle}
            disabled={cycling}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50
                       text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
          >
            <TrendingUp size={15} />
            {cycling ? "Running…" : "Run Trade Cycle"}
          </button>
          <button
            onClick={refresh}
            disabled={loading}
            className="p-2 rounded-lg bg-slate-700 hover:bg-slate-600 transition-colors"
          >
            <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
          </button>
        </div>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <StatCard
          label="Portfolio Value"
          value={fmt$(portfolio?.total_value)}
          color="text-emerald-400"
        />
        <StatCard
          label="Cash"
          value={fmt$(portfolio?.cash)}
          color="text-cyan-400"
        />
        <StatCard
          label="Invested"
          value={fmt$(holdings.reduce((s, h) => s + h.current_value, 0))}
          color="text-yellow-400"
        />
        <StatCard
          label="Total P&L"
          value={fmt$(portfolio?.total_pnl)}
          sub={portfolio?.total_pnl != null && portfolio.total_pnl >= 0
            ? "▲ Unrealized gain"
            : "▼ Unrealized loss"}
          color={pctColor(portfolio?.total_pnl)}
        />
      </div>

      {/* Stock grid */}
      <div className="mb-8">
        <h2 className="text-lg font-semibold mb-3 text-white">Tracked Stocks</h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          {Object.entries(stocks).map(([sym, name]) => (
            <div key={sym} onClick={() => setChartSymbol(sym)}
              className="cursor-pointer transition-transform hover:scale-105">
              <StockCard
                symbol={sym}
                name={name}
                price={prices[sym]}
                ref_price={refs[sym]?.ref_price}
                pct_from_ref={refs[sym]?.pct_from_ref}
                holding={heldSet.has(sym)}
              />
            </div>
          ))}
        </div>
      </div>

      {/* Chart */}
      <div className="bg-slate-800 border border-slate-700 rounded-xl p-5 mb-8">
        <h2 className="text-lg font-semibold mb-4 text-white">
          {chartSymbol} — Price History
          <span className="text-slate-400 text-sm font-normal ml-2">(click any card to change)</span>
        </h2>
        <PriceChart symbol={chartSymbol} />
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Positions */}
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-5">
          <h2 className="text-lg font-semibold mb-4 text-white flex items-center gap-2">
            <TrendingUp size={18} className="text-emerald-400" /> Open Positions
            <span className="ml-auto text-sm font-normal text-slate-400">{holdings.length} stocks</span>
          </h2>
          <PositionsTable holdings={holdings} />
        </div>

        {/* Trade history */}
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-5">
          <h2 className="text-lg font-semibold mb-4 text-white flex items-center gap-2">
            <TrendingDown size={18} className="text-red-400" /> Trade History
            <span className="ml-auto text-sm font-normal text-slate-400">{trades.length} trades</span>
          </h2>
          <TradeHistory trades={trades} />
        </div>
      </div>
    </div>
  );
}
