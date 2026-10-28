(() => {
  "use strict";
  const $ = id => document.getElementById(id);
  let report;
  const n = value => Number(value || 0);
  const number = value => n(value).toLocaleString("en-CA");
  const element = (tag, className, text) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = String(text);
    return node;
  };
  const mount = (target, elements) => $(target).replaceChildren(...elements);
  const sum = (rows, field) => rows.reduce((acc, row) => acc + n(row[field]), 0);
  function card(label, figure, detail) {
    const root = element("article", "kpi");
    root.append(element("p", "kpi-label", label),
      element("p", "kpi-value", figure), element("p", "kpi-foot", detail));
    return root;
  }

  function barRows(target, rows, key, metric, count = 12) {
    const top = rows.slice().sort((a,b) => n(b[metric])-n(a[metric])).slice(0,count);
    const max = Math.max(1,...top.map(item => n(item[metric])));
    if (!top.length) {
      mount(target, [element("p", "empty-chart", "No records for this selection.")]);
      return;
    }
    mount(target, top.map(item => {
      const row = element("div", "route-row");
      const label = element("strong", "", String(item[key]));
      const meter = element("div", "route-meter");
      const fill = element("span");
      fill.style.width = (100*n(item[metric])/max)+"%";
      meter.setAttribute("aria-label", item[key]+": "+number(item[metric])+" incidents");
      meter.append(fill);
      row.append(label, meter, element("span", "number", number(item[metric])));
      return row;
    }));
  }

  function chart(target, rows, x, y, labelFn = value => value) {
    const items = rows.slice().sort((a,b)=>String(a[x]).localeCompare(String(b[x])));
    if (!items.length) {
      mount(target,[element("p","empty-chart","No records for this route.")]);
      return;
    }
    const max = Math.max(1,...items.map(row => n(row[y])));
    const root = element("div", "series-bars");
    for (const row of items) {
      const slot = element("div", "series-item");
      const bar = element("div", "series-bar");
      bar.style.height = Math.max(2, n(row[y])/max*168)+"px";
      bar.title = labelFn(row[x])+" · "+number(row[y])+" logged incidents";
      slot.append(bar, element("span", "series-label", labelFn(row[x])));
      root.append(slot);
    }
    mount(target,[root]);
  }

  function render(route = "all") {
    const routeRows = report.routes.filter(r=>route === "all" || String(r.route)===route);
    const total = sum(routeRows,"recorded_incidents");
    const positive = sum(routeRows,"positive_delay_incidents");
    const duration = sum(routeRows,"total_recorded_delay_minutes");
    const isAll = route === "all";
    mount("real-kpis",[
      card("Recorded incidents",number(total),"TTC event logs; not rider trips"),
      card("With positive delay",number(positive),"Cases where Min Delay > 0"),
      card("Recorded delay minutes",number(Math.round(duration)),"Sum across logged incident values"),
      card("Routes in scope",number(routeRows.length),isAll?"With validated records":"Selected route")
    ]);
    barRows("routes-chart", routeRows, "route", "recorded_incidents",12);
    // Only monthly totals for all routes: route-by-month data not supplied.
    if (isAll) {
      chart("monthly-chart",report.monthly,"month","recorded_incidents",x=>String(x).slice(2));
    } else {
      mount("monthly-chart",[element("p","empty-chart",
        "Route-level monthly history has not been exported. Select All routes to view verified monthly counts.")]);
    }
    const hourly = isAll ? report.hourly : report.route_by_hour.filter(r=>String(r.route)===route);
    chart("hour-chart",hourly,"hour","recorded_incidents",hour=>String(hour).padStart(2,"0"));
    const meta = report.meta;
    const summary = report.summary;
    mount("coverage",[
      element("p","kpi-label","Original source records"),
      element("p","kpi-value",number(meta.rows_in_source)),
      element("p","kpi-label","Validated 2025+ observations"),
      element("p","kpi-value",number(meta.rows_valid_2025_onward)),
      element("p","muted-note",number(meta.rows_dropped_invalid_or_before_2025)+" source rows omitted for invalid fields or dates before 2025."),
      element("p","muted-note","Positive-delay median across ALL routes: "+
        (summary.median_positive_delay_minutes === null ? "Unavailable" : summary.median_positive_delay_minutes+" min"))
    ]);
  }

  function attachTabs() {
    document.querySelectorAll("[data-tab]").forEach(button => button.addEventListener("click",()=>{
      for(const tab of document.querySelectorAll("[data-tab]")) {
        const active=tab === button;
        tab.classList.toggle("active",active);
        tab.setAttribute("aria-selected",String(active));
        $("view-"+tab.dataset.tab).hidden=!active;
      }
    }));
  }

  function fact(label,value) {
    const root = element("div","source-fact");
    root.append(element("span","",label),element("strong","",value));
    return root;
  }

  async function main() {
    attachTabs();
    try {
      // No synthetic fallback. A missing real snapshot is an explicit error.
      const result = await fetch("./real_data.json",{cache:"no-cache"});
      if (!result.ok) throw new Error("Verified data unavailable: HTTP "+result.status);
      report = await result.json();
      if (report.meta?.origin!=="REAL" || report.meta?.data_kind?.indexOf("Historical") !== 0 ||
          !report.meta.source_sha256 || !Array.isArray(report.routes) ||
          !Array.isArray(report.monthly) || !Array.isArray(report.hourly)) {
        throw new Error("Real TTC provenance validation failed. No demo records displayed.");
      }
      $("data-status").textContent = "TTC historical streetcar incident logs: "+
        report.meta.first_record+" to "+report.meta.last_record+
        " · Not live arrival times · "+report.meta.retrieval;
      const filter=$("route-filter");
      for(const row of report.routes){
        const opt=document.createElement("option");
        opt.value=String(row.route);
        opt.textContent="Route "+row.route;
        filter.append(opt);
      }
      filter.disabled=false;
      filter.addEventListener("change",()=>render(filter.value));
      mount("source-facts",[
        fact("Dataset","TTC Streetcar Delay Data, City of Toronto"),
        fact("Date coverage",report.meta.first_record+" — "+report.meta.last_record),
        fact("Acquisition",report.meta.retrieval),
        fact("Raw-source SHA256",report.meta.source_sha256),
        fact("Original CSV source",report.meta.source),
        fact("Aggregate generated",report.meta.generated_utc)
      ]);
      render();
    } catch(error) {
      $("data-status").textContent="Real TTC data not available";
      $("data-error").hidden=false;
      $("data-error").textContent=error.message+
        ". No synthetic substitute is used. See the project README for the official source ingestion instructions.";
      for(const id of ["real-kpis","routes-chart","monthly-chart","hour-chart","coverage"]){
        mount(id,[element("p","empty-chart","Verified data not yet available.")]);
      }
    }
  }
  main();
})();
