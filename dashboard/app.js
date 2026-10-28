/* CommuteIQ read-only BI dashboard. Displays aggregated SQL exports only. */
(() => {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const fmt = (n) => Number(n || 0).toLocaleString("en-CA");
  let data = null;
  const make = (tag, cls, text) => {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined && text !== null) e.textContent = String(text);
    return e;
  };
  const replace = (node, children) => {
    node.replaceChildren(...children);
  };

  function kpi(label, value, foot) {
    const card = make("article", "kpi");
    card.append(make("div", "kpi-label", label),
      make("div", "kpi-value", value), make("div", "kpi-foot", foot));
    return card;
  }

  function renderMix(route) {
    const root = $("mix-chart");
    const groups = CommuteLogic.routeMix(data, route);
    if (!groups.length) {
      replace(root, [make("div", "empty-chart", "No decision events for this filter.")]);
      return;
    }
    const max = Math.max(...groups.map(r => r.walk + r.wait), 1);
    const cards = groups.map(r => {
      const row = make("div", "grouped-bar");
      const label = make("div", "group-label", r.route);
      const track = make("div", "bar-track");
      const walkBar = make("div", "bar-walk");
      const waitBar = make("div", "bar-wait");
      // Full track is scaled to the route's total, segment split is relative.
      const total = r.walk + r.wait;
      track.style.width = Math.max(2, (total / max) * 100) + "%";
      walkBar.style.width = (total ? r.walk / total * 100 : 0) + "%";
      waitBar.style.width = (total ? r.wait / total * 100 : 0) + "%";
      track.setAttribute("aria-label", r.route + ": " + r.walk + " WALK, " + r.wait + " WAIT");
      track.append(walkBar, waitBar);
      row.append(label, track, make("div", "bar-value", fmt(total)));
      return row;
    });
    replace(root, cards);
  }

  function renderHours(route) {
    const root = $("hour-chart");
    const hours = CommuteLogic.hourlyActivity(data, route);
    if (!hours.length) {
      replace(root, [make("div", "empty-chart", "No recorded decision hours.")]);
      return;
    }
    const chart = make("div", "hour-bars");
    const max = Math.max(...hours.map(r => r.events), 1);
    for (const row of hours) {
      const slot = make("div", "hour-slot");
      const bar = make("div", "hour-bar");
      bar.style.height = Math.max(4, 100 * row.events / max) + "%";
      bar.append(make("span", "hour-count", fmt(row.events)));
      const hour = make("span", "hour-title", row.hour + ":00");
      bar.append(hour);
      slot.append(bar);
      chart.append(slot);
    }
    replace(root, [chart]);
  }

  function renderReasons(route) {
    const root = $("reason-chart");
    const groups = CommuteLogic.reasonSummary(data, route).slice(0, 6);
    if (!groups.length) {
      replace(root, [make("div", "empty-chart", "No recommendation reasons.")]);
      return;
    }
    const max = Math.max(...groups.map(r => r.count), 1);
    const rows = groups.map(r => {
      const row = make("div", "reason-row");
      const name = make("div", "reason-name");
      name.append(make("span", "", r.reason), make("strong", "", fmt(r.count)));
      const track = make("div", "reason-track");
      const fill = make("div", "reason-fill");
      fill.style.width = (r.count / max * 100) + "%";
      track.append(fill);
      row.append(name, track);
      return row;
    });
    replace(root, rows);
  }

  function renderQuality() {
    const q = CommuteLogic.latestQuality(data);
    const percent = q.total ? Math.round(100 * q.passed / q.total) : 0;
    $("qa-gauge").style.setProperty("--progress", percent + "%");
    $("qa-percent").textContent = percent + "%";
    const trust = $("trust-stats");
    replace(trust, [
      trustItem(fmt(q.passed), "PASSED RULES"),
      trustItem(fmt(q.failed), "FAILED RULES"),
      trustItem(fmt(q.affectedRuleRows), "RULE VIOLATIONS")
    ]);
    replace($("quality-summary"), [
      kpi("Rules checked", fmt(q.total), "Latest simulated feed QA run"),
      kpi("Failed rules", fmt(q.failed), "Not necessarily distinct records"),
      kpi("Pass rate", percent + "%", "Rule count, not service reliability")
    ]);
    $("qa-source").textContent = q.source;
    const sorted = q.rules.slice().sort((a, b) =>
      (a.status === "FAIL" ? -1 : 1) - (b.status === "FAIL" ? -1 : 1) ||
      a.rule_id.localeCompare(b.rule_id));
    replace($("qa-rows"), sorted.map(r => {
      const tr = document.createElement("tr");
      tr.append(make("td", "", r.rule_id), make("td", "", r.severity));
      const statusTd = document.createElement("td");
      statusTd.append(make("span", "status-tag " + r.status.toLowerCase(), r.status));
      tr.append(statusTd, make("td", "right", fmt(r.affected_records)));
      return tr;
    }));
  }

  function trustItem(value, label) {
    const wrap = make("div", "trust-item");
    wrap.append(make("strong", "", value), make("span", "", label));
    return wrap;
  }

  function render() {
    if (!data) return;
    const route = $("route-filter").value;
    const s = CommuteLogic.summary(data, route);
    const share = s.events ? Math.round(s.walkShare * 100) + "%" : "—";
    const verified = s.verified
      ? fmt(s.catches) + " / " + fmt(s.verified) : "Not measured";
    replace($("kpis"), [
      kpi("Decision events", fmt(s.events), "Simulated recommendations"),
      kpi("Walk recommendation rate", share, fmt(s.walk) + " suggested WALK"),
      kpi("Potential steps", fmt(s.potentialSteps), "Estimates, not steps taken"),
      kpi("Verified catches", verified, "No real trip outcomes in demo")
    ]);
    renderMix(route);
    renderHours(route);
    renderReasons(route);
    renderQuality();
  }

  function renderScenario() {
    const value = id => Number($(id).value);
    const currentEta = value("eta-current");
    const nextEta = value("eta-next");
    const walking = value("walk-duration");
    const buffer = value("buffer-duration");
    $("val-current").textContent = currentEta + " min";
    $("val-next").textContent = nextEta + " min";
    $("val-walk").textContent = walking + " min";
    $("val-buffer").textContent = buffer + " min";
    const decision = CommuteLogic.evaluateScenario({
      currentEta, nextEta, walking, buffer,
      sameVehicle: $("same-vehicle").checked,
      nextStopServed: $("next-served").checked,
      accessiblePath: $("accessible-path").checked,
      wantsSteps: $("wants-steps").checked,
      feedAge: 0 // Simulated fresh prediction; not an actual real-time feed.
    });
    const action = $("decision-action");
    action.textContent = decision.action;
    action.classList.toggle("waiting", decision.action === "WAIT");
    $("decision-title").textContent = decision.action === "WALK" ?
      "Walk may be feasible." : "Waiting is safer.";
    $("decision-reason").textContent = decision.reason;
    $("decision-margin").textContent = decision.margin === null
      ? "Unknown" : (decision.margin > 0 ? "+" : "") + decision.margin + " min";
    $("decision-steps").textContent = "≈" + fmt(walking * 110) + " if walked";
  }

  function wireTabs() {
    document.querySelectorAll("[data-tab]").forEach(button => {
      button.addEventListener("click", () => {
        document.querySelectorAll("[data-tab]").forEach(tab => {
          const active = tab === button;
          tab.classList.toggle("active", active);
          tab.setAttribute("aria-selected", String(active));
          $("view-" + tab.dataset.tab).hidden = !active;
        });
      });
    });
  }

  function wireScenario() {
    ["eta-current", "eta-next", "walk-duration", "buffer-duration",
      "same-vehicle", "next-served", "accessible-path", "wants-steps"]
      .forEach(id => $(id).addEventListener("input", renderScenario));
    renderScenario();
  }

  async function start() {
    wireTabs();
    wireScenario();
    try {
      const response = await fetch("./data.json", {cache: "no-store"});
      if (!response.ok) throw new Error("HTTP " + response.status);
      data = await response.json();
      if (!data.meta || !Array.isArray(data.route_actions) ||
          !Array.isArray(data.quality_rules) || !Array.isArray(data.hourly)) {
        throw new Error("Unexpected analytics data shape");
      }
      const demo = data.meta.origin === "DEMO";
      $("origin-pill").textContent = demo ? "SYNTHETIC DATA" : "USER-SUPPLIED DATA";
      $("provenance-msg").textContent = (demo ? "DEMO ONLY · " : "LOCAL SOURCE · ") +
        String(data.meta.note || "Data provenance not supplied.") +
        " Recommendations are not completed trips. Hours are in UTC.";
      const routes = [...new Set(data.route_actions.map(x => String(x.route_id)))].sort();
      for (const route of routes) {
        const option = document.createElement("option");
        option.value = route;
        option.textContent = "Route " + route;
        $("route-filter").append(option);
      }
      $("route-filter").addEventListener("change", render);
      render();
    } catch (err) {
      $("error").hidden = false;
      $("error").textContent =
        "Dashboard data could not be loaded. Serve the dashboard folder over HTTP " +
        "(python3 -m http.server 8000 --directory dashboard), then verify data.json exists. " +
        "Details: " + err.message;
    }
  }

  start();
})();
