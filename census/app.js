const tooltip = d3.select("#tooltip");

const STAGE_COLORS = {
  education_group: "#4cc9f0",
  work_status_group: "#f6c85f",
  marital_group: "#ff7f50",
  income_bucket: "#7cb34b",
};

const BAR_OPTIONS = {
  education: { key: "bar_by_education", label: "Education" },
  age: { key: "bar_by_age", label: "Age band" },
  work: { key: "bar_by_work_status", label: "Work status" },
  sex: { key: "bar_by_sex", label: "Sex" },
};

let activeBarKey = "education";

function showTooltip(event, html) {
  tooltip
    .style("display", "block")
    .style("left", `${event.pageX + 14}px`)
    .style("top", `${event.pageY + 14}px`)
    .html(html);
}

function moveTooltip(event) {
  tooltip
    .style("left", `${event.pageX + 14}px`)
    .style("top", `${event.pageY + 14}px`);
}

function hideTooltip() {
  tooltip.style("display", "none");
}

function formatMillions(value) {
  return `${d3.format(".1f")(value / 1_000_000)}M`;
}

function formatPercent(value) {
  return `${d3.format(".1%")(value)}`;
}

function buildSummaryCards(supporting) {
  const cards = [
    { label: "Raw records", value: d3.format(",")(supporting.records) },
    { label: "Weighted population", value: formatMillions(supporting.weighted_population) },
    { label: "Top story", value: "Pathways to $50K" },
    { label: "Main encoding", value: "Weighted flow" },
  ];

  const grid = d3.select("#summary-grid");
  grid.html("");

  cards.forEach((card) => {
    const div = grid.append("div").attr("class", "summary-card");
    div.append("div").attr("class", "summary-label").text(card.label);
    div.append("div").attr("class", "summary-value").text(card.value);
  });
}

function renderSankey(pathways, supporting) {
  const container = d3.select("#sankey-chart");
  container.html("");

  const width = 1080;
  const height = 560;

  const svg = container.append("svg")
    .attr("width", width)
    .attr("height", height);

  const graph = {
    nodes: pathways.nodes.map(d => ({ ...d })),
    links: pathways.links.map(d => ({ ...d })),
  };

  const sankey = d3.sankey()
    .nodeWidth(18)
    .nodePadding(18)
    .extent([[18, 18], [width - 18, height - 18]])
    .nodeAlign(d3.sankeyJustify);

  sankey(graph);

  svg.append("g")
    .selectAll("path")
    .data(graph.links)
    .enter()
    .append("path")
    .attr("class", "sankey-link")
    .attr("d", d3.sankeyLinkHorizontal())
    .attr("stroke", d => {
      const sourceNode = graph.nodes.find(n => n.index === d.source.index);
      return STAGE_COLORS[sourceNode.stage_key] || "#9aa5b1";
    })
    .attr("stroke-width", d => Math.max(1, d.width))
    .on("mouseenter", function(event, d) {
      showTooltip(
        event,
        `<strong>${d.source.name}</strong> → <strong>${d.target.name}</strong><br>` +
        `Weighted population: ${formatMillions(d.value)}`
      );
    })
    .on("mousemove", moveTooltip)
    .on("mouseleave", hideTooltip);

  const node = svg.append("g")
    .selectAll("g")
    .data(graph.nodes)
    .enter()
    .append("g")
    .attr("class", "sankey-node");

  node.append("rect")
    .attr("x", d => d.x0)
    .attr("y", d => d.y0)
    .attr("height", d => Math.max(1, d.y1 - d.y0))
    .attr("width", d => d.x1 - d.x0)
    .attr("fill", d => STAGE_COLORS[d.stage_key] || "#9aa5b1")
    .on("mouseenter", function(event, d) {
      showTooltip(
        event,
        `<strong>${d.name}</strong><br>` +
        `${d.stage_label}<br>` +
        `Weighted population touching node: ${formatMillions(d.value)}`
      );
    })
    .on("mousemove", moveTooltip)
    .on("mouseleave", hideTooltip);

  node.append("text")
    .attr("x", d => d.x0 < width / 2 ? d.x1 + 8 : d.x0 - 8)
    .attr("y", d => (d.y0 + d.y1) / 2)
    .attr("dy", "0.35em")
    .attr("text-anchor", d => d.x0 < width / 2 ? "start" : "end")
    .text(d => d.name);

  d3.select("#sankey-caption").text(
    `Weighted population represented: ${formatMillions(supporting.weighted_population)}. The thickest flow in the uploaded summary starts at less than high school → not in labor force → never married → <= $50K.`
  );
}

function renderBarControls(supporting) {
  const toolbar = d3.select("#bar-controls");
  toolbar.html("");

  Object.entries(BAR_OPTIONS).forEach(([id, meta]) => {
    toolbar.append("button")
      .attr("class", activeBarKey === id ? "active" : null)
      .text(meta.label)
      .on("click", () => {
        activeBarKey = id;
        renderBarControls(supporting);
        renderBarChart(supporting);
      });
  });
}

function getCategoryLabel(optionId) {
  if (optionId === "education") return "education_group";
  if (optionId === "age") return "age_band";
  if (optionId === "work") return "work_status_group";
  return "sex_group";
}

function renderBarChart(supporting) {
  const container = d3.select("#bar-chart");
  container.html("");

  const option = BAR_OPTIONS[activeBarKey];
  const field = getCategoryLabel(activeBarKey);
  const data = supporting[option.key];

  const width = 980;
  const height = 450;
  const margin = { top: 20, right: 30, bottom: 95, left: 70 };
  const plotWidth = width - margin.left - margin.right;
  const plotHeight = height - margin.top - margin.bottom;

  const svg = container.append("svg")
    .attr("width", width)
    .attr("height", height);

  const g = svg.append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);

  const x = d3.scaleBand()
    .domain(data.map(d => d[field]))
    .range([0, plotWidth])
    .padding(0.22);

  const y = d3.scaleLinear()
    .domain([0, d3.max(data, d => d.share_over_50k)]).nice()
    .range([plotHeight, 0]);

  g.append("g")
    .attr("class", "axis")
    .attr("transform", `translate(0,${plotHeight})`)
    .call(d3.axisBottom(x))
    .selectAll("text")
    .attr("transform", "rotate(-28)")
    .style("text-anchor", "end");

  g.append("g")
    .attr("class", "axis")
    .call(d3.axisLeft(y).tickFormat(d3.format(".0%")));

  g.selectAll(".bar")
    .data(data)
    .enter()
    .append("rect")
    .attr("class", "bar")
    .attr("x", d => x(d[field]))
    .attr("y", d => y(d.share_over_50k))
    .attr("width", x.bandwidth())
    .attr("height", d => plotHeight - y(d.share_over_50k))
    .attr("fill", (d, i) => i === 0 ? "#7cb34b" : "#4cc9f0")
    .on("mouseenter", function(event, d) {
      showTooltip(
        event,
        `<strong>${d[field]}</strong><br>` +
        `Weighted share over $50K: ${formatPercent(d.share_over_50k)}<br>` +
        `Weighted over $50K: ${formatMillions(d.weighted_over_50k)}<br>` +
        `Weighted total: ${formatMillions(d.total_weight)}`
      );
    })
    .on("mousemove", moveTooltip)
    .on("mouseleave", hideTooltip);

  g.selectAll(".bar-label")
    .data(data)
    .enter()
    .append("text")
    .attr("class", "label")
    .attr("x", d => x(d[field]) + x.bandwidth() / 2)
    .attr("y", d => y(d.share_over_50k) - 8)
    .attr("text-anchor", "middle")
    .text(d => formatPercent(d.share_over_50k));

  const best = data[0];
  d3.select("#bar-caption").text(
    `${option.label} view: ${best[field]} has the highest weighted share above $50K in the uploaded summary at ${formatPercent(best.share_over_50k)}.`
  );
}

function renderTopPathways(supporting) {
  const container = d3.select("#pathways-chart");
  container.html("");

  const data = supporting.top_pathways.slice(0, 12).map(d => ({
    label: `${d.education_group} → ${d.work_status_group} → ${d.marital_group} → ${d.income_bucket}`,
    weight: d.weight,
    income_bucket: d.income_bucket,
  }));

  const width = 1120;
  const rowHeight = 28;
  const height = 80 + data.length * rowHeight;
  const margin = { top: 16, right: 80, bottom: 16, left: 390 };
  const plotWidth = width - margin.left - margin.right;

  const svg = container.append("svg")
    .attr("width", width)
    .attr("height", height);

  const x = d3.scaleLinear()
    .domain([0, d3.max(data, d => d.weight)]).nice()
    .range([0, plotWidth]);

  const y = d3.scaleBand()
    .domain(data.map(d => d.label))
    .range([margin.top, height - margin.bottom])
    .padding(0.18);

  svg.append("g")
    .selectAll(".pathway-bar")
    .data(data)
    .enter()
    .append("rect")
    .attr("class", "pathway-bar")
    .attr("x", margin.left)
    .attr("y", d => y(d.label))
    .attr("height", y.bandwidth())
    .attr("width", d => x(d.weight))
    .attr("fill", d => d.income_bucket === "> $50K" ? "#7cb34b" : "#4cc9f0")
    .on("mouseenter", function(event, d) {
      showTooltip(
        event,
        `<strong>${d.label}</strong><br>` +
        `Weighted population: ${formatMillions(d.weight)}`
      );
    })
    .on("mousemove", moveTooltip)
    .on("mouseleave", hideTooltip);

  svg.append("g")
    .selectAll(".pathway-label")
    .data(data)
    .enter()
    .append("text")
    .attr("class", "pathway-label")
    .attr("x", margin.left - 10)
    .attr("y", d => y(d.label) + y.bandwidth() / 2)
    .attr("text-anchor", "end")
    .attr("dominant-baseline", "middle")
    .text(d => d.label);

  svg.append("g")
    .selectAll(".pathway-value")
    .data(data)
    .enter()
    .append("text")
    .attr("class", "pathway-value")
    .attr("x", d => margin.left + x(d.weight) + 8)
    .attr("y", d => y(d.label) + y.bandwidth() / 2)
    .attr("dominant-baseline", "middle")
    .text(d => formatMillions(d.weight));

  d3.select("#pathways-caption").text(
    "Most of the strongest weighted pathways in the uploaded summary still terminate in the <= $50K group, even when the path includes full-time work or marriage."
  );
}

Promise.all([
  d3.json("data/census_pathways.json"),
  d3.json("data/census_supporting.json"),
]).then(([pathways, supporting]) => {
  buildSummaryCards(supporting);
  renderSankey(pathways, supporting);
  renderBarControls(supporting);
  renderBarChart(supporting);
  renderTopPathways(supporting);
}).catch((error) => {
  console.error(error);
  d3.select("#summary-grid").html("<div class='summary-card'><div class='summary-label'>Error</div><div class='summary-value'>Data files not found</div></div>");
});