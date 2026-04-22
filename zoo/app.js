const CLASS_COLORS = {
  mammal: "#4cc9f0",
  bird: "#f6c85f",
  reptile: "#ff7f50",
  fish: "#6f4e7c",
  amphibian: "#43aa8b",
  insect: "#90be6d",
  invertebrate: "#9aa5b1",
};

const tooltip = d3.select("#tooltip");
let selectedPcaClasses = new Set();
let selectedFingerprintClasses = new Set();
let selectedConstellationClasses = new Set();

let pcaInitialized = false;
let fingerprintInitialized = false;
let constellationInitialized = false;

let lockedConstellationAnimal = null;

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

function titleCase(value) {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function renderToggleButtons(containerSelector, classes, selectedSet, onChange) {
  const container = d3.select(containerSelector);
  container.html("");

  container
    .append("button")
    .attr("class", selectedSet.size === classes.length ? "active" : null)
    .text("All")
    .on("click", function () {
      selectedSet.clear();
      classes.forEach((d) => selectedSet.add(d.class_name));
      onChange();
    });

  container
    .append("button")
    .attr("class", selectedSet.size === 0 ? "active" : null)
    .text("None")
    .on("click", function () {
      selectedSet.clear();
      onChange();
    });

  classes.forEach((item) => {
    container
      .append("button")
      .attr("class", selectedSet.has(item.class_name) ? "active" : null)
      .text(titleCase(item.class_name))
      .on("click", function () {
        if (selectedSet.has(item.class_name)) {
          selectedSet.delete(item.class_name);
        } else {
          selectedSet.add(item.class_name);
        }
        onChange();
      });
  });
}

function renderPcaChart(data) {
  const allPoints = data.pca_points;
  const classes = data.classes;

  if (!pcaInitialized) {
    classes.forEach((d) => selectedPcaClasses.add(d.class_name));
    pcaInitialized = true;
  }

  const container = d3.select("#pca-chart");
  container.html("");

  const width = 760;
  const height = 460;
  const margin = { top: 18, right: 26, bottom: 52, left: 62 };

  const svg = container
    .append("svg")
    .attr("width", width)
    .attr("height", height);

  const plotWidth = width - margin.left - margin.right;
  const plotHeight = height - margin.top - margin.bottom;

  const chart = svg
    .append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);

  const filteredPoints = allPoints.filter((d) =>
    selectedPcaClasses.has(d.class_name)
  );

  const x = d3
    .scaleLinear()
    .domain(d3.extent(allPoints, (d) => d.pc1))
    .nice()
    .range([0, plotWidth]);

  const y = d3
    .scaleLinear()
    .domain(d3.extent(allPoints, (d) => d.pc2))
    .nice()
    .range([plotHeight, 0]);

  chart
    .append("g")
    .attr("class", "axis")
    .attr("transform", `translate(0,${plotHeight})`)
    .call(d3.axisBottom(x).ticks(7));

  chart.append("g").attr("class", "axis").call(d3.axisLeft(y).ticks(7));

  chart
    .append("text")
    .attr("class", "plot-label")
    .attr("x", plotWidth / 2)
    .attr("y", plotHeight + 40)
    .attr("text-anchor", "middle")
    .text("PC1");

  chart
    .append("text")
    .attr("class", "plot-label")
    .attr("transform", "rotate(-90)")
    .attr("x", -plotHeight / 2)
    .attr("y", -42)
    .attr("text-anchor", "middle")
    .text("PC2");

  chart
    .selectAll(".pca-point")
    .data(filteredPoints)
    .enter()
    .append("circle")
    .attr("cx", (d) => x(d.pc1))
    .attr("cy", (d) => y(d.pc2))
    .attr("r", 4.2)
    .attr("fill", (d) => CLASS_COLORS[d.class_name] || "#cccccc")
    .attr("opacity", 0.8)
    .on("mouseenter", function (event, d) {
      d3.select(this).attr("r", 6.2).attr("stroke", "white").attr("stroke-width", 1.2);

      showTooltip(
        event,
        `<strong>${d.animal_name}</strong><br>` +
          `${titleCase(d.class_name)}<br>` +
          `PC1: ${d.pc1.toFixed(3)}<br>` +
          `PC2: ${d.pc2.toFixed(3)}<br>` +
          `Legs: ${d.legs}`
      );
    })
    .on("mousemove", moveTooltip)
    .on("mouseleave", function () {
      d3.select(this).attr("r", 4.2).attr("stroke", null);
      hideTooltip();
    });

  d3.select("#pca-caption").text(
    filteredPoints.length === 0
      ? "No classes are currently selected."
      : "Even with class filtering, the PCA projection still mixes several groups together. It works as a preview, but not as the main presentation."
  );

  renderToggleButtons("#pca-controls", classes, selectedPcaClasses, () =>
    renderPcaChart(data)
  );
}

function renderHeatmap(data) {
  const heatmapRows = data.heatmap;
  const classNames = data.classes.map((d) => d.class_name);
  const traits = [...data.traits, ...data.numeric_traits];

  const container = d3.select("#heatmap-chart");
  container.html("");

  const cellSize = 32;
  const width = 220 + traits.length * cellSize;
  const height = 120 + classNames.length * cellSize;

  const svg = container
    .append("svg")
    .attr("width", width)
    .attr("height", height);

  const margin = { top: 90, right: 20, bottom: 20, left: 180 };
  const chart = svg
    .append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);

  const x = d3.scaleBand().domain(traits).range([0, traits.length * cellSize]).padding(0.05);
  const y = d3.scaleBand().domain(classNames).range([0, classNames.length * cellSize]).padding(0.05);

  const maxValue = d3.max(heatmapRows, (d) => d.value);
  const color = d3.scaleLinear().domain([0, maxValue]).range(["#2b313b", "#7cb34b"]);

  chart
    .selectAll(".heatmap-cell")
    .data(heatmapRows)
    .enter()
    .append("rect")
    .attr("class", "heatmap-cell")
    .attr("x", (d) => x(d.trait))
    .attr("y", (d) => y(d.class_name))
    .attr("width", x.bandwidth())
    .attr("height", y.bandwidth())
    .attr("fill", (d) => color(d.value))
    .on("mouseenter", function (event, d) {
      d3.select(this).attr("stroke", "white").attr("stroke-width", 1.5);
      showTooltip(
        event,
        `<strong>${titleCase(d.class_name)}</strong><br>` +
          `Trait: ${d.trait}<br>` +
          `Value: ${d.value.toFixed(2)}`
      );
    })
    .on("mousemove", moveTooltip)
    .on("mouseleave", function () {
      d3.select(this).attr("stroke", null).attr("stroke-width", null);
      hideTooltip();
    });

  chart
    .selectAll(".trait-label")
    .data(traits)
    .enter()
    .append("text")
    .attr("class", "heatmap-label")
    .attr("x", (d) => x(d) + x.bandwidth() / 2)
    .attr("y", -10)
    .attr("text-anchor", "start")
    .attr("transform", (d) => `rotate(-45, ${x(d) + x.bandwidth() / 2}, -10)`)
    .text((d) => d);

  chart
    .selectAll(".class-label")
    .data(classNames)
    .enter()
    .append("text")
    .attr("class", "heatmap-label")
    .attr("x", -12)
    .attr("y", (d) => y(d) + y.bandwidth() / 2)
    .attr("text-anchor", "end")
    .attr("dominant-baseline", "middle")
    .text((d) => titleCase(d));

  d3.select("#heatmap-caption").text(
    "This view is much more interpretable than the PCA preview because the trait structure stays visible and the classes can be compared directly."
  );
}

function drawAnimalGlyph(card, animal, options = {}) {
  const size = options.size || 92;
  const svg = card
    .append("svg")
    .attr("class", "animal-glyph-svg")
    .attr("width", size)
    .attr("height", size)
    .attr("viewBox", "0 0 92 92");

  const g = svg.append("g").attr("transform", "translate(46,44)");
  const classColor = CLASS_COLORS[animal.class_name] || "#cccccc";

  const headWidth = animal.traits.catsize ? 36 : 31;
  const headHeight = animal.traits.catsize ? 28 : 24;

  // Tail / fins / wings behind the head
  if (animal.traits.tail) {
    g.append("path")
      .attr("d", "M 22 18 C 35 18, 38 28, 30 34")
      .attr("fill", "none")
      .attr("stroke", classColor)
      .attr("stroke-width", 3)
      .attr("stroke-linecap", "round")
      .attr("opacity", 0.9);
  }

  if (animal.traits.airborne) {
    g.append("path")
      .attr("d", "M -28 -2 C -45 -16, -43 14, -26 10")
      .attr("fill", "none")
      .attr("stroke", classColor)
      .attr("stroke-width", 3)
      .attr("stroke-linecap", "round")
      .attr("opacity", 0.85);

    g.append("path")
      .attr("d", "M 28 -2 C 45 -16, 43 14, 26 10")
      .attr("fill", "none")
      .attr("stroke", classColor)
      .attr("stroke-width", 3)
      .attr("stroke-linecap", "round")
      .attr("opacity", 0.85);
  }

  if (animal.traits.aquatic || animal.traits.fins) {
    g.append("path")
      .attr("d", "M -24 10 L -38 20 L -24 24 Z")
      .attr("fill", classColor)
      .attr("opacity", 0.75);

    g.append("path")
      .attr("d", "M 24 10 L 38 20 L 24 24 Z")
      .attr("fill", classColor)
      .attr("opacity", 0.75);
  }

  // Ears for hairy animals
  if (animal.traits.hair) {
    g.append("path")
      .attr("d", `M ${-headWidth * 0.58} ${-headHeight * 0.48} L ${-headWidth * 0.2} ${-headHeight * 1.12} L ${-headWidth * 0.02} ${-headHeight * 0.3} Z`)
      .attr("fill", classColor)
      .attr("opacity", 0.9);

    g.append("path")
      .attr("d", `M ${headWidth * 0.58} ${-headHeight * 0.48} L ${headWidth * 0.2} ${-headHeight * 1.12} L ${headWidth * 0.02} ${-headHeight * 0.3} Z`)
      .attr("fill", classColor)
      .attr("opacity", 0.9);
  }

  // Crest for feathered animals
  if (animal.traits.feathers) {
    const crestData = [
      { x: -10, y: -headHeight - 5 },
      { x: 0, y: -headHeight - 12 },
      { x: 10, y: -headHeight - 5 },
    ];

    crestData.forEach((pt, i) => {
      g.append("path")
        .attr("d", `M ${pt.x - 4} ${-headHeight + 2} L ${pt.x} ${pt.y} L ${pt.x + 4} ${-headHeight + 2} Z`)
        .attr("fill", classColor)
        .attr("opacity", 0.9 - i * 0.1);
    });
  }

  // Main head
  g.append("ellipse")
    .attr("cx", 0)
    .attr("cy", 0)
    .attr("rx", headWidth)
    .attr("ry", headHeight)
    .attr("fill", "#39414d")
    .attr("class", "glyph-outline");

  // Backbone stripe for vertebrates
  if (animal.traits.backbone) {
    g.append("line")
      .attr("x1", 0)
      .attr("y1", -headHeight + 5)
      .attr("x2", 0)
      .attr("y2", headHeight - 6)
      .attr("stroke", "rgba(255,255,255,0.18)")
      .attr("stroke-width", 2)
      .attr("stroke-linecap", "round");
  }

  // Egg marker
  if (animal.traits.eggs) {
    g.append("ellipse")
      .attr("cx", 0)
      .attr("cy", -headHeight - 10)
      .attr("rx", 5)
      .attr("ry", 7)
      .attr("fill", "rgba(255,255,255,0.92)");
  }

  // Eyes
  const eyeY = -6;
  const eyeDX = animal.traits.predator ? 10 : 12;

  if (animal.traits.predator) {
    g.append("path")
      .attr("d", `M ${-eyeDX - 4} ${eyeY + 2} L ${-eyeDX + 4} ${eyeY - 1}`)
      .attr("stroke", "white")
      .attr("stroke-width", 2)
      .attr("stroke-linecap", "round");

    g.append("path")
      .attr("d", `M ${eyeDX - 4} ${eyeY - 1} L ${eyeDX + 4} ${eyeY + 2}`)
      .attr("stroke", "white")
      .attr("stroke-width", 2)
      .attr("stroke-linecap", "round");
  } else {
    g.append("circle")
      .attr("cx", -eyeDX)
      .attr("cy", eyeY)
      .attr("r", 3.2)
      .attr("fill", "white");

    g.append("circle")
      .attr("cx", eyeDX)
      .attr("cy", eyeY)
      .attr("r", 3.2)
      .attr("fill", "white");
  }

  g.append("circle")
    .attr("cx", -eyeDX)
    .attr("cy", eyeY)
    .attr("r", 1.3)
    .attr("fill", "#1f232b");

  g.append("circle")
    .attr("cx", eyeDX)
    .attr("cy", eyeY)
    .attr("r", 1.3)
    .attr("fill", "#1f232b");

  // Beak or snout
  if (animal.traits.feathers) {
    g.append("path")
      .attr("d", "M 0 2 L 10 8 L 0 12 L -2 7 Z")
      .attr("fill", classColor);
  } else {
    if (animal.traits.milk) {
      g.append("ellipse")
        .attr("cx", 0)
        .attr("cy", 8)
        .attr("rx", 10)
        .attr("ry", 7)
        .attr("fill", "rgba(255,255,255,0.08)")
        .attr("stroke", "rgba(255,255,255,0.18)")
        .attr("stroke-width", 1);
    }

    if (animal.traits.breathes) {
      g.append("circle").attr("cx", -3).attr("cy", 7).attr("r", 1.2).attr("fill", "#e8edf3");
      g.append("circle").attr("cx", 3).attr("cy", 7).attr("r", 1.2).attr("fill", "#e8edf3");
    }
  }

  // Whiskers
  if (animal.traits.hair) {
    [-1, 1].forEach((side) => {
      g.append("line")
        .attr("x1", 7 * side)
        .attr("y1", 10)
        .attr("x2", 20 * side)
        .attr("y2", 7)
        .attr("stroke", "rgba(255,255,255,0.7)")
        .attr("stroke-width", 1.2);

      g.append("line")
        .attr("x1", 7 * side)
        .attr("y1", 13)
        .attr("x2", 20 * side)
        .attr("y2", 13)
        .attr("stroke", "rgba(255,255,255,0.7)")
        .attr("stroke-width", 1.2);

      g.append("line")
        .attr("x1", 7 * side)
        .attr("y1", 16)
        .attr("x2", 20 * side)
        .attr("y2", 19)
        .attr("stroke", "rgba(255,255,255,0.7)")
        .attr("stroke-width", 1.2);
    });
  }

  // Mouth / teeth / fangs
  g.append("path")
    .attr("d", "M -8 15 Q 0 20 8 15")
    .attr("fill", "none")
    .attr("stroke", "white")
    .attr("stroke-width", 1.5)
    .attr("stroke-linecap", "round");

  if (animal.traits.toothed) {
    [-5, -1, 3].forEach((x) => {
      g.append("rect")
        .attr("x", x)
        .attr("y", 15)
        .attr("width", 2.3)
        .attr("height", 4)
        .attr("fill", "white");
    });
  }

  if (animal.traits.venomous) {
    g.append("path")
      .attr("d", "M -4 15 L -2 22 L 0 15")
      .attr("fill", classColor);

    g.append("path")
      .attr("d", "M 4 15 L 2 22 L 0 15")
      .attr("fill", classColor);
  }

  // Domestic collar
  if (animal.traits.domestic) {
    g.append("path")
      .attr("d", `M ${-headWidth * 0.68} ${headHeight * 0.38} Q 0 ${headHeight * 0.72} ${headWidth * 0.68} ${headHeight * 0.38}`)
      .attr("fill", "none")
      .attr("stroke", classColor)
      .attr("stroke-width", 3)
      .attr("stroke-linecap", "round");
  }

  // Legs badge
  g.append("circle")
    .attr("class", "glyph-badge")
    .attr("cx", 0)
    .attr("cy", 32)
    .attr("r", 11);

  g.append("text")
    .attr("class", "glyph-badge-text")
    .attr("x", 0)
    .attr("y", 32)
    .text(animal.legs);
}

function renderFingerprintWall(data) {
  const classes = data.classes;
  const allAnimals = data.animals;

  if (!fingerprintInitialized) {
    classes.forEach((d) => selectedFingerprintClasses.add(d.class_name));
    fingerprintInitialized = true;
  }

  renderToggleButtons(
    "#fingerprint-controls",
    classes,
    selectedFingerprintClasses,
    () => renderFingerprintWall(data)
  );

  const grid = d3.select("#fingerprint-grid");
  grid.html("");

  const visibleClasses = classes.filter((d) =>
    selectedFingerprintClasses.has(d.class_name)
  );

  visibleClasses.forEach((classItem) => {
    const animals = allAnimals.filter((d) => d.class_name === classItem.class_name);

    const panel = grid.append("section").attr("class", "class-panel");

    panel.append("h3").text(titleCase(classItem.class_name));
    panel
      .append("div")
      .attr("class", "class-count")
      .text(`${classItem.count} animals`);

    const animalsWrap = panel.append("div").attr("class", "class-animals");

    animals.forEach((animal) => {
      const card = animalsWrap.append("div").attr("class", "animal-card");

      drawAnimalGlyph(card, animal);

      card
        .append("div")
        .attr("class", "animal-name")
        .text(animal.animal_name);

      card
        .append("div")
        .attr("class", "animal-legs")
        .text(`${animal.legs} legs`);

      card
        .on("mouseenter", function (event) {
          const activeTraits = animal.active_traits.length
            ? animal.active_traits.join(", ")
            : "none";

          showTooltip(
            event,
            `<strong>${animal.animal_name}</strong><br>` +
              `${titleCase(animal.class_name)}<br>` +
              `Legs: ${animal.legs}<br>` +
              `Traits: ${activeTraits}`
          );
        })
        .on("mousemove", moveTooltip)
        .on("mouseleave", hideTooltip);
    });
  });
}

function animalSimilarity(a, b) {
  const traitKeys = Object.keys(a.traits);
  let binaryMatches = 0;

  traitKeys.forEach((key) => {
    if (a.traits[key] === b.traits[key]) binaryMatches += 1;
  });

  const binaryScore = binaryMatches / traitKeys.length;
  const legDiff = Math.abs(a.legs - b.legs);
  const legScore = 1 - Math.min(legDiff, 8) / 8;

  return 0.82 * binaryScore + 0.18 * legScore;
}

function buildConstellationData(data) {
  const visibleAnimals = data.animals.filter((d) =>
    selectedConstellationClasses.has(d.class_name)
  );

  const nodes = visibleAnimals.map((d) => ({ ...d }));
  const linkMap = new Map();

  nodes.forEach((animal) => {
    const neighbors = nodes
      .filter((other) => other.animal_name !== animal.animal_name)
      .map((other) => ({
        target: other,
        score: animalSimilarity(animal, other),
      }))
      .filter((item) => item.score >= 0.74)
      .sort((a, b) => b.score - a.score)
      .slice(0, 4);

    neighbors.forEach((neighbor) => {
      const key = [animal.animal_name, neighbor.target.animal_name]
        .sort()
        .join("||");

      if (!linkMap.has(key) || linkMap.get(key).value < neighbor.score) {
        linkMap.set(key, {
          source: animal.animal_name,
          target: neighbor.target.animal_name,
          value: neighbor.score,
        });
      }
    });
  });

  return {
    nodes,
    links: Array.from(linkMap.values()),
  };
}

function dragStarted(simulation) {
  return function (event, d) {
    if (!event.active) simulation.alphaTarget(0.2).restart();
    d.fx = d.x;
    d.fy = d.y;
  };
}

function dragged(event, d) {
  d.fx = event.x;
  d.fy = event.y;
}

function dragEnded(simulation) {
  return function (event, d) {
    if (!event.active) simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
  };
}

function renderConstellationFeature(animal, neighbors) {
  const feature = d3.select("#constellation-feature");
  feature.html("");

  if (!animal) {
    feature
      .attr("class", "constellation-feature empty")
      .text("Hover over an animal to inspect it. Click a node to lock the selection.");
    return;
  }

  feature.attr("class", "constellation-feature");

  const glyphWrap = feature.append("div").attr("class", "feature-glyph-wrap");
  drawAnimalGlyph(glyphWrap, animal, { size: 118 });

  const copy = feature.append("div").attr("class", "feature-copy");

  copy.append("div").attr("class", "feature-title").text(animal.animal_name);

  copy
    .append("div")
    .attr("class", "feature-meta")
    .text(`${titleCase(animal.class_name)} · ${animal.legs} legs`);

  copy
    .append("div")
    .attr("class", "feature-traits")
    .text(
      animal.active_traits.length
        ? `Active traits: ${animal.active_traits.join(", ")}`
        : "No active binary traits."
    );

  copy.append("div").attr("class", "feature-neighbor-title").text("Closest neighbors");

  const list = copy.append("ul").attr("class", "feature-neighbor-list");

  if (!neighbors.length) {
    list.append("li").text("No strong neighbors in the current selection.");
  } else {
    neighbors.forEach((n) => {
      list.append("li").text(`${n.name} (${n.score.toFixed(2)})`);
    });
  }
}

function renderConstellation(data) {
  const classes = data.classes;

  if (!constellationInitialized) {
    classes.forEach((d) => selectedConstellationClasses.add(d.class_name));
    constellationInitialized = true;
  }

  renderToggleButtons(
    "#constellation-controls",
    classes,
    selectedConstellationClasses,
    () => renderConstellation(data)
  );

  const container = d3.select("#constellation-chart");
  container.html("");

  const visibleAnimals = data.animals.filter((d) =>
    selectedConstellationClasses.has(d.class_name)
  );

  if (visibleAnimals.length === 0) {
    d3.select("#constellation-caption").text("No classes are currently selected.");
    renderConstellationFeature(null, []);
    return;
  }

  if (
    lockedConstellationAnimal &&
    !visibleAnimals.some((d) => d.animal_name === lockedConstellationAnimal)
  ) {
    lockedConstellationAnimal = null;
  }

  const visibleData = {
    ...data,
    animals: visibleAnimals,
  };

  const { nodes, links } = buildConstellationData(visibleData);

  const width = 980;
  const height = 620;
  const centerX = width / 2;
  const centerY = height / 2;
  const radius = Math.min(width, height) * 0.28;

  const svg = container
    .append("svg")
    .attr("class", "constellation-svg")
    .attr("width", width)
    .attr("height", height);

  svg
    .append("rect")
    .attr("class", "constellation-bg")
    .attr("width", width)
    .attr("height", height)
    .on("click", function () {
      lockedConstellationAnimal = null;
      resetFocus();
      hideTooltip();
    });

  const stars = d3.range(120).map(() => ({
    x: Math.random() * width,
    y: Math.random() * height,
    r: Math.random() * 1.7 + 0.35,
    o: Math.random() * 0.35 + 0.08,
  }));

  const starSelection = svg
    .append("g")
    .selectAll(".constellation-star")
    .data(stars)
    .enter()
    .append("circle")
    .attr("class", "constellation-star")
    .attr("cx", (d) => d.x)
    .attr("cy", (d) => d.y)
    .attr("r", (d) => d.r)
    .attr("opacity", (d) => d.o);

  starSelection.each(function (d) {
    const star = d3.select(this);

    (function twinkle() {
      star
        .transition()
        .duration(1000 + Math.random() * 1400)
        .attr("opacity", Math.min(0.65, d.o + Math.random() * 0.28))
        .transition()
        .duration(1000 + Math.random() * 1600)
        .attr("opacity", d.o)
        .on("end", twinkle);
    })();
  });

  const visibleClasses = classes.filter((d) =>
    selectedConstellationClasses.has(d.class_name)
  );

  const classCenters = new Map();

  if (visibleClasses.length === 1) {
    classCenters.set(visibleClasses[0].class_name, { x: centerX, y: centerY });
  } else {
    visibleClasses.forEach((item, index) => {
      const angle = (Math.PI * 2 * index) / visibleClasses.length - Math.PI / 2;
      classCenters.set(item.class_name, {
        x: centerX + Math.cos(angle) * radius,
        y: centerY + Math.sin(angle) * radius,
      });
    });
  }

  svg
    .append("g")
    .selectAll(".constellation-class-label")
    .data(visibleClasses)
    .enter()
    .append("text")
    .attr("class", "constellation-class-label")
    .attr("x", (d) => classCenters.get(d.class_name).x)
    .attr("y", (d) => classCenters.get(d.class_name).y - 56)
    .text((d) => titleCase(d.class_name));

  const linkLayer = svg.append("g");
  const nodeLayer = svg.append("g");

  const simulation = d3
    .forceSimulation(nodes)
    .force(
      "link",
      d3
        .forceLink(links)
        .id((d) => d.animal_name)
        .distance((d) => 118 - d.value * 54)
        .strength((d) => 0.09 + d.value * 0.24)
    )
    .force("charge", d3.forceManyBody().strength(-92))
    .force(
      "collision",
      d3.forceCollide().radius((d) => (d.traits.catsize ? 14 : 11))
    )
    .force(
      "x",
      d3.forceX((d) => classCenters.get(d.class_name).x).strength(0.095)
    )
    .force(
      "y",
      d3.forceY((d) => classCenters.get(d.class_name).y).strength(0.095)
    );

  const link = linkLayer
    .selectAll(".constellation-link")
    .data(links)
    .enter()
    .append("line")
    .attr("class", "constellation-link")
    .attr("stroke-width", (d) => 0.55 + (d.value - 0.7) * 2.8)
    .attr("opacity", 0.2);

  const halo = nodeLayer
    .selectAll(".constellation-halo")
    .data(nodes)
    .enter()
    .append("circle")
    .attr("class", "constellation-halo")
    .attr("r", (d) => (d.traits.catsize ? 14 : 11))
    .attr("fill", (d) => CLASS_COLORS[d.class_name] || "#cccccc")
    .attr("opacity", 0.16);

  const node = nodeLayer
    .selectAll(".constellation-node")
    .data(nodes)
    .enter()
    .append("circle")
    .attr("class", "constellation-node")
    .attr("r", (d) => (d.traits.catsize ? 7.4 : 5.8))
    .attr("fill", (d) => CLASS_COLORS[d.class_name] || "#cccccc")
    .call(
      d3
        .drag()
        .on("start", dragStarted(simulation))
        .on("drag", dragged)
        .on("end", dragEnded(simulation))
    );

  const nodeByName = new Map(nodes.map((n) => [n.animal_name, n]));

  function nodeName(x) {
    return typeof x === "object" ? x.animal_name : x;
  }

  function incidentNames(linkDatum) {
    return [nodeName(linkDatum.source), nodeName(linkDatum.target)];
  }

  function topNeighborsByName(animalName) {
    return links
      .filter((l) => {
        const [a, b] = incidentNames(l);
        return a === animalName || b === animalName;
      })
      .map((l) => {
        const [a, b] = incidentNames(l);
        return {
          name: a === animalName ? b : a,
          score: l.value,
        };
      })
      .sort((a, b) => b.score - a.score)
      .slice(0, 4);
  }

  function applyFocus(animalName) {
    const focused = nodeByName.get(animalName);

    if (!focused) {
      resetFocus();
      return;
    }

    const neighbors = topNeighborsByName(animalName);
    const neighborSet = new Set([animalName, ...neighbors.map((n) => n.name)]);

    link
      .attr("opacity", (l) => {
        const [a, b] = incidentNames(l);
        return a === animalName || b === animalName ? 0.92 : 0.05;
      })
      .attr("stroke", (l) => {
        const [a, b] = incidentNames(l);
        return a === animalName || b === animalName
          ? "rgba(255,255,255,0.65)"
          : "rgba(255,255,255,0.10)";
      })
      .attr("stroke-width", (l) => {
        const [a, b] = incidentNames(l);
        return a === animalName || b === animalName
          ? 1.4 + (l.value - 0.7) * 3.4
          : 0.45;
      });

    halo
      .attr("opacity", (n) => {
        if (n.animal_name === animalName) return 0.34;
        if (neighborSet.has(n.animal_name)) return 0.24;
        return 0.05;
      })
      .attr("r", (n) => {
        if (n.animal_name === animalName) return n.traits.catsize ? 20 : 17;
        if (neighborSet.has(n.animal_name)) return n.traits.catsize ? 16 : 13;
        return n.traits.catsize ? 14 : 11;
      });

    node
      .attr("opacity", (n) => (neighborSet.has(n.animal_name) ? 1 : 0.14))
      .attr("r", (n) => {
        if (n.animal_name === animalName) return 10.8;
        if (neighborSet.has(n.animal_name)) return n.traits.catsize ? 8.5 : 6.9;
        return n.traits.catsize ? 7.4 : 5.8;
      });

    renderConstellationFeature(focused, neighbors);
  }

  function resetFocus() {
    link
      .attr("opacity", 0.2)
      .attr("stroke", "rgba(255,255,255,0.16)")
      .attr("stroke-width", (d) => 0.55 + (d.value - 0.7) * 2.8);

    halo
      .attr("opacity", 0.16)
      .attr("r", (d) => (d.traits.catsize ? 14 : 11));

    node
      .attr("opacity", 0.95)
      .attr("r", (d) => (d.traits.catsize ? 7.4 : 5.8));

    renderConstellationFeature(null, []);
  }

  node
    .on("mouseenter", function (event, d) {
      if (!lockedConstellationAnimal) {
        applyFocus(d.animal_name);
      }

      const neighbors = topNeighborsByName(d.animal_name);
      const neighborText = neighbors.length
        ? neighbors.map((n) => `${n.name} (${n.score.toFixed(2)})`).join("<br>")
        : "No strong neighbors";

      showTooltip(
        event,
        `<strong>${d.animal_name}</strong><br>` +
          `${titleCase(d.class_name)}<br>` +
          `Legs: ${d.legs}<br>` +
          `Top neighbors:<br>${neighborText}`
      );
    })
    .on("mousemove", moveTooltip)
    .on("mouseleave", function () {
      if (!lockedConstellationAnimal) {
        resetFocus();
      }
      hideTooltip();
    })
    .on("click", function (event, d) {
      event.stopPropagation();

      if (lockedConstellationAnimal === d.animal_name) {
        lockedConstellationAnimal = null;
        resetFocus();
      } else {
        lockedConstellationAnimal = d.animal_name;
        applyFocus(d.animal_name);
      }

      hideTooltip();
    });

  simulation.on("tick", () => {
    link
      .attr("x1", (d) => d.source.x)
      .attr("y1", (d) => d.source.y)
      .attr("x2", (d) => d.target.x)
      .attr("y2", (d) => d.target.y);

    halo
      .attr("cx", (d) => d.x)
      .attr("cy", (d) => d.y);

    node
      .attr("cx", (d) => d.x)
      .attr("cy", (d) => d.y);
  });

  if (lockedConstellationAnimal) {
    applyFocus(lockedConstellationAnimal);
  } else {
    resetFocus();
  }

  d3.select("#constellation-caption").text(
    "Animals are linked to their strongest trait-neighbors. Dense neighborhoods reveal familiar groups, while unusual animals become bridges between regions."
  );
}

function renderDashboard(data) {
  renderPcaChart(data);
  renderHeatmap(data);
  renderFingerprintWall(data);
  renderConstellation(data);
}

d3.json("data/zoo_dashboard.json")
  .then(renderDashboard)
  .catch((error) => {
    console.error("Could not load zoo_dashboard.json", error);

    d3.select("#pca-caption").text("Could not load data/zoo_dashboard.json");
    d3.select("#heatmap-caption").text("Could not load data/zoo_dashboard.json");
    d3.select("#fingerprint-grid")
      .append("div")
      .style("text-align", "center")
      .style("color", "#aab6c2")
      .style("padding", "2rem 0")
      .text("Could not load data/zoo_dashboard.json");
  });