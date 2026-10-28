/* CommuteIQ: pure computations for the public, aggregated-data demo.
   "WALK" is a recommendation, never evidence that a journey occurred. */
(function(root) {
  "use strict";
  const sum = (values) => values.reduce((a, b) => a + Number(b || 0), 0);
  const filterRoute = (rows, route) => (rows || []).filter(r => route === "all" || String(r.route_id) === String(route));

  function summary(data, route = "all") {
    const actions = filterRoute(data.route_actions, route);
    const outcomes = filterRoute(data.outcomes, route);
    const events = sum(actions.map(r => r.events));
    const walk = sum(actions.filter(r => r.action === "WALK").map(r => r.events));
    return {
      events, walk, wait: events - walk,
      walkShare: events ? walk / events : 0,
      potentialSteps: sum(actions.map(r => r.potential_steps)),
      verified: sum(outcomes.map(r => r.verified_outcomes)),
      catches: sum(outcomes.map(r => r.verified_catches))
    };
  }

  function latestQuality(data) {
    const rows = data.quality_rules || [];
    const ids = rows.map(r => Number(r.run_id)).filter(Number.isFinite);
    const lastId = ids.length ? Math.max(...ids) : null;
    const latest = lastId === null ? [] : rows.filter(r => Number(r.run_id) === lastId);
    return {
      rules: latest,
      passed: latest.filter(r => r.status === "PASS").length,
      failed: latest.filter(r => r.status === "FAIL").length,
      affectedRuleRows: sum(latest.map(r => r.affected_records)),
      total: latest.length,
      source: latest[0]?.source_name || "No feed runs"
    };
  }

  function routeMix(data, route = "all") {
    const rows = filterRoute(data.route_actions, route);
    const groups = new Map();
    for (const row of rows) {
      const key = String(row.route_id);
      if (!groups.has(key)) groups.set(key, {route: key, walk: 0, wait: 0});
      groups.get(key)[row.action.toLowerCase()] += Number(row.events);
    }
    return [...groups.values()].sort((a, b) => a.route.localeCompare(b.route));
  }

  function hourlyActivity(data, route = "all") {
    const rows = filterRoute(data.hourly, route);
    const groups = new Map();
    for (const row of rows) {
      const hour = String(row.hour_utc).padStart(2, "0");
      groups.set(hour, (groups.get(hour) || 0) + Number(row.events));
    }
    return [...groups.entries()].sort((a, b) => a[0].localeCompare(b[0]))
      .map(([hour, events]) => ({hour, events}));
  }

  function reasonSummary(data, route = "all") {
    const rows = filterRoute(data.decision_reasons, route);
    const groups = new Map();
    for (const row of rows) {
      const label = row.action === "WALK" ? "Feasible walk suggested" : row.decision_reason;
      groups.set(label, (groups.get(label) || 0) + Number(row.events));
    }
    return [...groups.entries()].sort((a, b) => b[1] - a[1])
      .map(([reason, count]) => ({reason, count}));
  }

  function evaluateScenario(params) {
    const {currentEta, nextEta, walking, buffer, wantsSteps, sameVehicle,
           nextStopServed, accessiblePath, feedAge} = params;
    const finiteNonnegative = [currentEta, nextEta, walking, buffer, feedAge]
      .every(v => typeof v === "number" && Number.isFinite(v) && v >= 0);
    if (!finiteNonnegative) return {action: "WAIT", reason: "Missing or invalid inputs", margin: null};
    const margin = nextEta - walking - buffer;
    if (!accessiblePath) return {action: "WAIT", reason: "Walking path not verified accessible", margin};
    if (!nextStopServed) return {action: "WAIT", reason: "Next stop is not verified on this trip", margin};
    if (!sameVehicle) return {action: "WAIT", reason: "Same vehicle not verified at both stops", margin};
    if (feedAge > 90) return {action: "WAIT", reason: "Arrival estimates are stale", margin};
    if (!wantsSteps) return {action: "WAIT", reason: "Walking is disabled", margin};
    if (currentEta <= walking) return {action: "WAIT", reason: "Current-stop ETA is too close", margin};
    if (margin <= 0) return {action: "WAIT", reason: "Insufficient buffer to reach next stop", margin};
    return {action: "WALK", reason: "Feasible under the assumed predictions; not guaranteed", margin};
  }

  const api = {summary, latestQuality, routeMix, hourlyActivity, reasonSummary, evaluateScenario};
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  root.CommuteLogic = api;
})(typeof window !== "undefined" ? window : globalThis);
