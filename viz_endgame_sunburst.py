"""
Visualization note:
This module was developed for a KRK endgame visualization project and was
inspired in part by ebemunk's chess visualization work:

- https://blog.ebemunk.com/a-visual-look-at-2-million-chess-games/
- https://ebemunk.com/chess-dataviz/
- https://github.com/ebemunk/chess-dataviz

This implementation uses a different dataset, custom preprocessing, and
KRK-specific interaction logic rather than reproducing the original project.
"""
from viz_data import payload_json


def build_endgame_sunburst_section(sunburst_payload: dict) -> dict:
    payload = payload_json(sunburst_payload)

    css = """
    .sunburst-wrap {
      max-width: 1020px;
      margin: 0 auto;
      padding: 1.2rem 1rem 2.2rem 1rem;
    }

    .sunburst-wrap h2 {
      color: var(--color-yellow);
      margin: 1.3rem auto 0.8rem auto;
      font-weight: 500;
      text-align: center;
    }

    .sunburst-wrap p {
      margin: 0 auto 1rem auto;
      line-height: 1.68rem;
      color: var(--color-faded-gray);
      max-width: 48rem;
      text-align: center;
    }

    .sunburst-controls {
      margin: 1rem auto 1rem auto;
      max-width: 48rem;
    }

    .sunburst-control-row {
      display: flex;
      justify-content: center;
      align-items: center;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 10px;
    }

    .sunburst-panel {
      display: flex;
      justify-content: center;
      align-items: center;
      margin-top: 0.4rem;
    }

    #sunburst-chart {
      width: 820px;
      display: flex;
      justify-content: center;
      align-items: center;
    }

    .sunburst-summary {
      max-width: 52rem;
      margin: 1rem auto 0.2rem auto;
      color: var(--color-faded-gray);
      text-align: center;
      min-height: 1.6rem;
      line-height: 1.6rem;
    }

    .sunburst-helper {
      max-width: 52rem;
      margin: 0.15rem auto 0 auto;
      color: #94a3b8;
      text-align: center;
      font-size: 0.92rem;
    }

    .sunburst-arc {
      stroke: rgba(15, 15, 15, 0.62);
      stroke-width: 0.8px;
      cursor: pointer;
      transition: opacity 120ms ease;
    }

    .sunburst-arc.dimmed {
      opacity: 0.26;
    }

    .sunburst-arc.active {
      stroke: white;
      stroke-width: 2.2px;
    }

    .sunburst-arc.ancestor {
      stroke: rgba(255,255,255,0.86);
      stroke-width: 1.6px;
    }

    .sunburst-label {
      fill: white;
      font-size: 12px;
      pointer-events: none;
      text-anchor: middle;
      user-select: none;
    }

    .sunburst-center-ring {
      fill: rgba(21, 28, 40, 0.95);
    }

    .board-piece-image {
      pointer-events: none;
    }

    .center-status {
      fill: white;
      font-size: 11px;
      font-weight: 600;
      text-anchor: middle;
      letter-spacing: 0.03em;
    }

    @media screen and (max-width: 860px) {
      #sunburst-chart {
        width: 100%;
      }
    }
    """

    html = """
    <section id="sunburst-section" class="sunburst-wrap">
      <h2>Endgame tree</h2>
      <p>
        This view adapts an openings sunburst to KRK endgames. Hover a branch to select a representative
        continuation. Then move inward or outward across the rings to scrub through the line move by move.
        Click a branch to pin it.
      </p>

      <div class="sunburst-controls">
        <div class="sunburst-control-row" id="sunburst-bucket-buttons"></div>
      </div>

      <div class="sunburst-panel">
        <div id="sunburst-chart"></div>
      </div>

      <div class="sunburst-summary" id="sunburst-summary"></div>
      <div class="sunburst-helper" id="sunburst-helper"></div>
    </section>
    """

    js = f"""
    const endgameSunburstData = {payload};

    (function() {{
      const bucketOrder = endgameSunburstData.bucket_order;
      const bucketLabels = endgameSunburstData.bucket_labels;

      const DEFAULT_CENTER_FEN = "4k3/8/8/8/8/8/8/4K2R w - - 0 1";

      let selectedBucket = "draw";
      let pinnedNode = null;
      let hoveredNode = null;

      function renderButtonGroup(containerId, options, selectedValue, onClick) {{
        const wrap = d3.select(containerId);
        wrap.html("");

        options.forEach(function(item) {{
          const key = item[0];
          const label = item[1];

          wrap.append("button")
            .attr("class", key === selectedValue ? "active" : null)
            .text(label)
            .on("click", function() {{
              onClick(key);
            }});
        }});
      }}

      function currentTree() {{
        return endgameSunburstData.trees[selectedBucket];
      }}

      function svgToDataUri(svgText) {{
        return "data:image/svg+xml;utf8," + encodeURIComponent(svgText);
      }}

      function pieceAsset(piece) {{
        const whiteKing = `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 45 45">
  <g fill="none" fill-rule="evenodd" stroke="#000" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
    <path d="M22.5 11.63V6"/>
    <path d="M20 8h5"/>
    <path d="M22.5 25S27 17.5 25.5 14.5c0 0-1-2.5-3-2.5s-3 2.5-3 2.5C18 17.5 22.5 25 22.5 25z" fill="#fff"/>
    <path d="M12.5 37c5.5 3.5 14.5 3.5 20 0V30s9-4.5 6-10.5C34.5 13 25 16 22.5 23.5V27v-3.5C20 16 10.5 13 6.5 19.5 3.5 25.5 12.5 30 12.5 30v7z" fill="#fff"/>
    <path d="M12.5 30c5.5-3 14.5-3 20 0"/>
    <path d="M12.5 33.5c5.5-3 14.5-3 20 0"/>
    <path d="M12.5 37c5.5-3 14.5-3 20 0"/>
  </g>
</svg>`;

        const blackKing = `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 45 45">
  <g fill="none" fill-rule="evenodd" stroke="#000" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
    <path d="M22.5 11.63V6"/>
    <path d="M20 8h5"/>
    <path d="M22.5 25S27 17.5 25.5 14.5c0 0-1-2.5-3-2.5s-3 2.5-3 2.5C18 17.5 22.5 25 22.5 25z" fill="#000"/>
    <path d="M12.5 37c5.5 3.5 14.5 3.5 20 0V30s9-4.5 6-10.5C34.5 13 25 16 22.5 23.5V27v-3.5C20 16 10.5 13 6.5 19.5 3.5 25.5 12.5 30 12.5 30v7z" fill="#000"/>
    <path d="M32 29.5s8.5-4 6.03-9.65C34.15 14 25 18 22.5 24.5v2.1-2.1C20 18 10.85 14 6.97 19.85 4.5 25.5 13 29.5 13 29.5" stroke="#fff"/>
    <path d="M12.5 30c5.5-3 14.5-3 20 0" stroke="#fff"/>
    <path d="M12.5 33.5c5.5-3 14.5-3 20 0" stroke="#fff"/>
    <path d="M12.5 37c5.5-3 14.5-3 20 0" stroke="#fff"/>
  </g>
</svg>`;

        const whiteRook = `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 45 45">
  <g fill="#fff" fill-rule="evenodd" stroke="#000" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
    <path d="M9 39h27v-3H9v3z" stroke-linecap="butt"/>
    <path d="M12 36v-4h21v4H12z" stroke-linecap="butt"/>
    <path d="M11 14V9h4v2h5V9h5v2h5V9h4v5" stroke-linecap="butt"/>
    <path d="M34 14l-3 3H14l-3-3"/>
    <path d="M31 17v12.5H14V17" stroke-linecap="butt" stroke-linejoin="miter"/>
    <path d="M31 29.5l1.5 2.5h-20L14 29.5"/>
    <path d="M11 14h23"/>
  </g>
</svg>`;

        const assets = {{
          "K": svgToDataUri(whiteKing),
          "k": svgToDataUri(blackKing),
          "R": svgToDataUri(whiteRook),
        }};

        return assets[piece] || null;
      }}

      function parseFenBoard(fen) {{
        const boardPart = fen.split(" ")[0];
        const rows = boardPart.split("/");
        const board = [];

        rows.forEach(function(row) {{
          const expanded = [];
          row.split("").forEach(function(ch) {{
            if ("12345678".includes(ch)) {{
              const n = parseInt(ch, 10);
              for (let i = 0; i < n; i++) expanded.push("");
            }} else {{
              expanded.push(ch);
            }}
          }});
          board.push(expanded);
        }});

        return board;
      }}

      function cloneBoard(board) {{
        return board.map(function(row) {{ return row.slice(); }});
      }}

      function squareToRC(square) {{
        const col = square.charCodeAt(0) - 97;
        const row = 8 - parseInt(square[1], 10);
        return {{ row, col }};
      }}

      function applyUciMove(board, uci) {{
        if (!uci || uci.length < 4) return board;

        const from = squareToRC(uci.slice(0, 2));
        const to = squareToRC(uci.slice(2, 4));

        const next = cloneBoard(board);
        const piece = next[from.row][from.col];
        next[from.row][from.col] = "";
        next[to.row][to.col] = piece;
        return next;
      }}

      function drawCenterBoard(boardLayer, boardState, centerX, centerY, boardSize, statusText) {{
        boardLayer.html("");

        const boardGroup = boardLayer.append("g")
          .attr("transform", "translate(" + (centerX - boardSize / 2) + "," + (centerY - boardSize / 2) + ")");

        const cell = boardSize / 8;

        boardGroup.append("rect")
          .attr("x", -10)
          .attr("y", -10)
          .attr("width", boardSize + 20)
          .attr("height", boardSize + 20)
          .attr("rx", 10)
          .attr("fill", "rgba(22, 29, 42, 0.95)");

        for (let row = 0; row < 8; row++) {{
          for (let col = 0; col < 8; col++) {{
            const baseColor = (row + col) % 2 === 0 ? "#f0d9b5" : "#b58863";

            boardGroup.append("rect")
              .attr("x", col * cell)
              .attr("y", row * cell)
              .attr("width", cell)
              .attr("height", cell)
              .attr("fill", baseColor);
          }}
        }}

        for (let row = 0; row < 8; row++) {{
          for (let col = 0; col < 8; col++) {{
            const piece = boardState[row][col];
            if (!piece) continue;

            const href = pieceAsset(piece);
            if (!href) continue;

            const pad = cell * 0.03;

            boardGroup.append("image")
              .attr("class", "board-piece-image")
              .attr("href", href)
              .attr("x", col * cell + pad)
              .attr("y", row * cell + pad)
              .attr("width", cell - 2 * pad)
              .attr("height", cell - 2 * pad);
          }}
        }}

        if (statusText) {{
          boardLayer.append("text")
            .attr("class", "center-status")
            .attr("x", centerX)
            .attr("y", centerY - boardSize / 2 - 18)
            .text(statusText);
        }}
      }}

      function pathMoves(node) {{
        return node && node.data ? (node.data.san_path || []) : [];
      }}

      function pathUci(node) {{
        return node && node.data ? (node.data.uci_path || []) : [];
      }}

      function representativeFen(node) {{
        return node && node.data ? (node.data.fen || null) : null;
      }}

      function colorForRootMove(name) {{
        const palette = {{
          "R": "#3aa0f3",
          "K": "#ffa52f",
        }};

        const key = name && name.startsWith("R") ? "R" : "K";
        return palette[key] || "#7f7f7f";
      }}

      function nodeColor(d) {{
        const ancestors = d.ancestors().reverse();
        const depth1 = ancestors.length > 1 ? ancestors[1].data.name : d.data.name;
        const base = d3.color(colorForRootMove(depth1)) || d3.color("#777");
        const factor = Math.max(0, d.depth - 1) * 0.11;
        return d3.interpolateRgb(base.brighter(0.18), "#111")(factor);
      }}

      function ancestorChain(node) {{
        return node.ancestors().reverse().slice(1);
      }}

      function movesUpToDepth(node, hoverDepth) {{
        const full = pathUci(node);
        return full.slice(0, hoverDepth);
      }}

      function sanMovesUpToDepth(node, hoverDepth) {{
        const full = pathMoves(node);
        return full.slice(0, hoverDepth);
      }}

      function boardFromNodeAtDepth(node, hoverDepth) {{
        const fen = representativeFen(node);
        let boardState = fen ? parseFenBoard(fen) : parseFenBoard(DEFAULT_CENTER_FEN);

        const partial = movesUpToDepth(node, hoverDepth);
        partial.forEach(function(mv) {{
          boardState = applyUciMove(boardState, mv);
        }});

        return boardState;
      }}

      function renderSunburst() {{
        const container = d3.select("#sunburst-chart");
        container.html("");

        const treeData = currentTree();
        if (!treeData) {{
          d3.select("#sunburst-summary").text("No tree available for this bucket.");
          d3.select("#sunburst-helper").text("");
          return;
        }}

        pinnedNode = null;
        hoveredNode = null;

        const width = 820;
        const height = 820;
        const radius = 300;
        const boardSize = 240;
        const ringOffset = boardSize / 2 + 14;

        const svg = container.append("svg")
          .attr("width", width)
          .attr("height", height)
          .attr("viewBox", "0 0 " + width + " " + height);

        const centerX = width / 2;
        const centerY = height / 2;

        const chartLayer = svg.append("g")
          .attr("transform", "translate(" + centerX + "," + centerY + ")");

        const arcLayer = chartLayer.append("g");
        const labelLayer = chartLayer.append("g");
        const boardLayer = chartLayer.append("g");

        const root = d3.hierarchy(treeData)
          .sum(function(d) {{ return d.count; }})
          .sort(function(a, b) {{ return b.value - a.value; }});

        d3.partition().size([2 * Math.PI, radius])(root);

        const arc = d3.arc()
          .startAngle(function(d) {{ return d.x0; }})
          .endAngle(function(d) {{ return d.x1; }})
          .innerRadius(function(d) {{ return d.y0 + ringOffset; }})
          .outerRadius(function(d) {{ return d.y1 + ringOffset; }});

        const baseBoard = parseFenBoard(DEFAULT_CENTER_FEN);
        drawCenterBoard(boardLayer, baseBoard, 0, 0, boardSize, bucketLabels[selectedBucket]);

        const nodes = root.descendants().filter(function(d) {{ return d.depth > 0; }});

        const arcs = arcLayer.selectAll(".sunburst-arc")
          .data(nodes)
          .enter()
          .append("path")
          .attr("class", "sunburst-arc")
          .attr("d", arc)
          .attr("fill", function(d) {{ return nodeColor(d); }});

        function clearArcState() {{
          arcs
            .classed("dimmed", false)
            .classed("active", false)
            .classed("ancestor", false);
        }}

        function highlightChain(node) {{
          if (!node) {{
            clearArcState();
            return;
          }}

          const chain = new Set(node.ancestors().slice(1));
          arcs
            .classed("dimmed", function(d) {{ return !chain.has(d); }})
            .classed("active", function(d) {{ return d === node; }})
            .classed("ancestor", function(d) {{ return chain.has(d) && d !== node; }});
        }}

        function depthFromRadius(node, localRadius) {{
          const chain = ancestorChain(node);
          for (let i = 0; i < chain.length; i++) {{
            const ringInner = chain[i].y0 + ringOffset;
            const ringOuter = chain[i].y1 + ringOffset;
            if (localRadius >= ringInner && localRadius <= ringOuter) {{
              return i + 1;
            }}
          }}
          return chain.length;
        }}

        function updateSummary(node, hoverDepth) {{
          if (!node) {{
            d3.select("#sunburst-summary").text(
              "Move through a branch ring by ring to replay a representative continuation."
            );
            d3.select("#sunburst-helper").text(
              "Hover selects a line. Moving inward or outward changes how many moves are shown. Click pins the line."
            );
            return;
          }}

          const partialSan = sanMovesUpToDepth(node, hoverDepth);
          const prefix = partialSan.length ? partialSan.join(" ") : "starting position";

          d3.select("#sunburst-summary").text(
            bucketLabels[selectedBucket] +
            " — " + prefix +
            " | depth " + hoverDepth +
            " of " + pathMoves(node).length +
            " | branch count: " + node.value
          );

          d3.select("#sunburst-helper").text(
            pinnedNode
              ? "Branch pinned. Click the same branch again to unpin, or click another branch to switch."
              : "Hover over a branch, then move across rings to scrub through the continuation."
          );
        }}

        function drawNodeAtDepth(node, hoverDepth) {{
          if (!node) {{
            drawCenterBoard(boardLayer, baseBoard, 0, 0, boardSize, bucketLabels[selectedBucket]);
            updateSummary(null, 0);
            return;
          }}

          const boardState = boardFromNodeAtDepth(node, hoverDepth);
          drawCenterBoard(
            boardLayer,
            boardState,
            0,
            0,
            boardSize,
            bucketLabels[selectedBucket] + " • ply " + hoverDepth
          );
          updateSummary(node, hoverDepth);
        }}

        function activeNode() {{
          return pinnedNode || hoveredNode;
        }}

        arcs
          .on("mouseenter", function(event, d) {{
            if (pinnedNode && pinnedNode !== d) return;
            hoveredNode = d;
            highlightChain(activeNode());
            drawNodeAtDepth(d, 1);
          }})
          .on("mousemove", function(event, d) {{
            if (pinnedNode && pinnedNode !== d) return;

            hoveredNode = d;

            const active = activeNode();
            highlightChain(active);

            const pointer = d3.pointer(event, svg.node());
            const dx = pointer[0] - centerX;
            const dy = pointer[1] - centerY;
            const localRadius = Math.sqrt(dx * dx + dy * dy);

            const hoverDepth = depthFromRadius(d, localRadius);
            drawNodeAtDepth(d, hoverDepth);
          }})
          .on("mouseleave", function() {{
            if (pinnedNode) {{
              highlightChain(pinnedNode);
              drawNodeAtDepth(pinnedNode, pathMoves(pinnedNode).length > 0 ? 1 : 0);
              return;
            }}

            hoveredNode = null;
            clearArcState();
            drawNodeAtDepth(null, 0);
          }})
          .on("click", function(event, d) {{
            if (pinnedNode === d) {{
              pinnedNode = null;
              hoveredNode = d;
              highlightChain(d);
              drawNodeAtDepth(d, 1);
              return;
            }}

            pinnedNode = d;
            hoveredNode = d;
            highlightChain(d);
            drawNodeAtDepth(d, 1);
          }});

        labelLayer.selectAll(".sunburst-label")
          .data(nodes.filter(function(d) {{ return (d.x1 - d.x0) > 0.17; }}))
          .enter()
          .append("text")
          .attr("class", "sunburst-label")
          .attr("transform", function(d) {{
            const angle = ((d.x0 + d.x1) / 2) * 180 / Math.PI - 90;
            const r = ((d.y0 + d.y1) / 2) + ringOffset;
            const flip = angle < 90 ? 0 : 180;
            return "rotate(" + angle + ") translate(" + r + ",0) rotate(" + flip + ")";
          }})
          .attr("dy", "0.35em")
          .text(function(d) {{ return d.data.name; }});

        drawNodeAtDepth(null, 0);

        svg.on("mouseleave", function() {{
          if (!pinnedNode) {{
            hoveredNode = null;
            clearArcState();
            drawNodeAtDepth(null, 0);
          }}
        }});
      }}

      function renderControls() {{
        renderButtonGroup(
          "#sunburst-bucket-buttons",
          bucketOrder.map(function(bucket) {{
            return [bucket, bucketLabels[bucket]];
          }}),
          selectedBucket,
          function(key) {{
            selectedBucket = key;
            pinnedNode = null;
            hoveredNode = null;
            renderAll();
          }}
        );
      }}

      function renderAll() {{
        renderControls();
        renderSunburst();
      }}

      renderAll();
    }})();
    """

    return {
        "html": html,
        "css": css,
        "js": js,
    }