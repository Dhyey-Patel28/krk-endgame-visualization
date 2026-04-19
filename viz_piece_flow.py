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


def build_piece_flow_section(piece_flow_payload: dict) -> dict:
    payload = payload_json(piece_flow_payload)

    css = """
    .piece-flow-wrap {
      max-width: 980px;
      margin: 0 auto;
      padding: 2rem 1rem 3rem 1rem;
    }

    .piece-flow-wrap h2 {
      color: var(--color-yellow);
      margin: 1.3rem auto 0.8rem auto;
      font-weight: 500;
      text-align: center;
    }

    .piece-flow-wrap p {
      margin: 0 auto 1rem auto;
      line-height: 1.68rem;
      color: var(--color-faded-gray);
      max-width: 42rem;
      text-align: center;
    }

    .controls {
      margin: 1.2rem auto 1.5rem auto;
      max-width: 42rem;
    }

    .control-row {
      display: flex;
      justify-content: center;
      align-items: center;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 10px;
    }

    .control-label {
      min-width: 88px;
      color: var(--color-faded-gray);
      font-size: 0.78rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }

    .caption {
      font-weight: bold;
      text-align: center;
      margin-bottom: 0.5rem;
    }

    #piece-flow-section #movepaths {
      display: flex;
      flex-direction: column;
      align-items: center;
      margin: 1.4rem 0 0.6rem 0;
    }

    #piece-flow-section .paths-main {
      width: 540px;
      display: flex;
      flex-direction: column;
      align-items: center;
    }

    #piece-flow-section .paths-side {
      width: 208px;
      height: 540px;
      display: flex;
      justify-content: center;
      align-items: center;
    }

    #piece-flow-section #movepaths-viz {
      width: 540px;
      display: flex;
      justify-content: center;
    }

    #piece-flow-section #piece-selector-viz {
      width: 208px;
      display: flex;
      justify-content: center;
    }

    #piece-flow-section .paths-layout {
      display: grid;
      grid-template-columns: 540px 208px;
      align-items: center;
      gap: 32px;
      justify-content: center;
    }

    #piece-flow-section .paths-board .square.light {
      color: #6c6c6c;
    }

    #piece-flow-section .paths-board .square.dark {
      color: #3c3c3c;
    }

    #piece-flow-section .paths-board .label {
      color: #fff;
      font-size: 12px;
    }

    #piece-flow-section .helper {
      max-width: 42rem;
      text-align: center;
      color: var(--color-faded-gray);
      margin: 0 auto 0.8rem auto;
    }

    #piece-flow-section .summary {
      max-width: 42rem;
      margin: 1.75rem auto 0 auto;
    }

    #piece-flow-section .summary h3 {
      color: var(--color-yellow);
      margin-bottom: 0.4rem;
      text-align: center;
    }

    #piece-flow-section .summary ul {
      margin: 0.4rem 0 0 1.2rem;
      color: var(--color-faded-gray);
    }

    #piece-flow-section .summary li {
      margin-bottom: 0.4rem;
    }

    #piece-flow-section .selector-board {
      background: #2b2f36;
      border: 1px solid rgba(255,255,255,0.08);
      border-radius: 6px;
    }

    #piece-flow-section .selector-cell {
      cursor: pointer;
    }

    #piece-flow-section .selector-cell.active rect {
      stroke: #ff4d4d;
      stroke-width: 3px;
    }

    #piece-flow-section .selector-label {
      fill: white;
      font-size: 11px;
      font-weight: 600;
      pointer-events: none;
    }

    #piece-flow-section .selector-piece {
      fill: white;
      font-size: 38px;
      pointer-events: none;
    }

    #piece-flow-section .selector-subtle {
      fill: rgba(255,255,255,0.70);
      font-size: 10px;
      pointer-events: none;
    }

    @media screen and (max-width: 900px) {
      #piece-flow-section .paths-layout {
        grid-template-columns: 1fr;
        gap: 24px;
      }

      #piece-flow-section .paths-main,
      #piece-flow-section #movepaths-viz {
        width: 100%;
      }

      #piece-flow-section .paths-side,
      #piece-flow-section #piece-selector-viz {
        width: 208px;
        margin: 0 auto;
      }
    }
    """

    html = """
    <section id="piece-flow-section" class="piece-flow-wrap">
      <h2>Abstract art</h2>
      <p class="helper">
        Each thin strand represents an aggregated move pattern. Stronger patterns appear brighter and thicker.
        Click a tile to explore the black king, white rook, white king, or all piece journeys.
      </p>

      <div id="movepaths">
        <div class="paths-layout">
          <div class="paths-main">
            <div class="caption" id="main-caption">Piece journeys</div>
            <div id="movepaths-viz"></div>
          </div>
          <div class="paths-side">
            <div id="piece-selector-viz"></div>
          </div>
        </div>
      </div>
      
      <div class="controls">
        <div class="control-row">
          <div class="control-label">Outcome</div>
          <div id="bucket-buttons"></div>
        </div>
      </div>

      <div class="summary">
        <h3>What this view is showing</h3>
        <ul id="top-moves-list"></ul>
      </div>
    </section>
    """

    js = f"""
    const pieceFlowData = {payload};

    (function() {{
      const bucketOrder = pieceFlowData.bucket_order;
      const bucketLabels = pieceFlowData.bucket_labels;
      const pieceLabels = pieceFlowData.piece_filter_labels;

      let selectedBucket = "draw";
      const BASE_PIECES = ["black_king", "white_rook", "white_king"];
      let selectedPieces = new Set(["black_king", "white_rook", "white_king"]);

      function selectedPieceKeys() {{
        return Array.from(selectedPieces);
      }}

      function allSelected() {{
        return BASE_PIECES.every(function(k) {{ return selectedPieces.has(k); }});
      }}

      function selectedLabel() {{
        const labels = selectedPieceKeys().map(function(k) {{ return pieceLabels[k]; }});
        if (allSelected()) return "All pieces";
        if (!labels.length) return "No pieces selected";
        return labels.join(" + ");
      }}

      function mergeEdges(edgeLists) {{
        const grouped = new Map();

        edgeLists.forEach(function(edges) {{
          edges.forEach(function(edge) {{
            const key = edge.from + "|" + edge.to + "|" + edge.piece;
            if (!grouped.has(key)) {{
              grouped.set(key, {{
                from: edge.from,
                to: edge.to,
                piece: edge.piece,
                count: 0
              }});
            }}
            grouped.get(key).count += edge.count;
          }});
        }});

        return Array.from(grouped.values()).sort(function(a, b) {{
          if (b.count !== a.count) return b.count - a.count;
          if (a.piece !== b.piece) return a.piece.localeCompare(b.piece);
          if (a.from !== b.from) return a.from.localeCompare(b.from);
          return a.to.localeCompare(b.to);
        }});
      }}

      function mergeTopMoves(moveLists) {{
        const grouped = new Map();

        moveLists.forEach(function(moves) {{
          moves.forEach(function(item) {{
            grouped.set(item.move, (grouped.get(item.move) || 0) + item.count);
          }});
        }});

        return Array.from(grouped.entries())
          .map(function(entry) {{
            return {{ move: entry[0], count: entry[1] }};
          }})
          .sort(function(a, b) {{
            if (b.count !== a.count) return b.count - a.count;
            return a.move.localeCompare(b.move);
          }});
      }}

      function currentEdges() {{
        const lists = selectedPieceKeys().map(function(key) {{
          return pieceFlowData.edges[key][selectedBucket] || [];
        }});
        return mergeEdges(lists);
      }}

      function currentTopMoves() {{
        const lists = selectedPieceKeys().map(function(key) {{
          return pieceFlowData.top_moves[key][selectedBucket] || [];
        }});
        return mergeTopMoves(lists);
      }}

      function currentCount() {{
        return selectedPieceKeys().reduce(function(total, key) {{
          return total + (pieceFlowData.counts[key][selectedBucket] || 0);
        }}, 0);
      }}

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

      function renderBucketButtons() {{
        renderButtonGroup(
          "#bucket-buttons",
          bucketOrder.map(function(bucket) {{
            return [bucket, bucketLabels[bucket]];
          }}),
          selectedBucket,
          function(key) {{
            selectedBucket = key;
            renderAll();
          }}
        );
      }}

      function squareCenter(square, cell, offsetX, offsetY) {{
        const file = square.charCodeAt(0) - 97;
        const rank = 8 - parseInt(square[1], 10);
        return {{
          x: offsetX + file * cell + cell / 2,
          y: offsetY + rank * cell + cell / 2
        }};
      }}

      function renderMovePaths() {{
        const container = d3.select("#movepaths-viz");
        container.html("");

        const edges = currentEdges();
        const topEdges = edges.slice(0, 180);

        d3.select("#main-caption").text(
          selectedLabel() + " in " + bucketLabels[selectedBucket]
        );

        const size = 540;
        const svg = container.append("svg")
          .attr("width", size)
          .attr("height", size);

        const boardSize = 540;
        const cell = boardSize / 8;
        const offsetX = 0;
        const offsetY = 0;

        const boardGroup = svg.append("g").attr("class", "paths-board");

        for (let row = 0; row < 8; row++) {{
          for (let col = 0; col < 8; col++) {{
            boardGroup.append("rect")
              .attr("class", "square " + (((row + col) % 2 === 0) ? "light" : "dark"))
              .attr("transform", "translate(" + (col * cell) + "," + (row * cell) + ")")
              .attr("width", cell)
              .attr("height", cell)
              .attr("fill", "currentColor");
          }}
        }}

        ["8","7","6","5","4","3","2","1"].forEach(function(rank, i) {{
          boardGroup.append("text")
            .attr("class", "rank label")
            .attr("transform", "translate(0," + (i * cell) + ")")
            .attr("dominant-baseline", "hanging")
            .attr("dy", "0.25em")
            .attr("dx", "0.25em")
            .attr("fill", "currentColor")
            .text(rank);
        }});

        ["a","b","c","d","e","f","g","h"].forEach(function(file, i) {{
          boardGroup.append("text")
            .attr("class", "file label")
            .attr("transform", "translate(" + ((i + 1) * cell) + "," + boardSize + ")")
            .attr("text-anchor", "end")
            .attr("dy", "-0.25em")
            .attr("dx", "-0.25em")
            .attr("fill", "currentColor")
            .text(file);
        }});

        if (!topEdges.length) {{
          return;
        }}

        const maxCount = d3.max(topEdges, d => d.count) || 1;
        const widthScale = d3.scaleLinear().domain([1, maxCount]).range([0.6, 3.8]);
        const opacityScale = d3.scaleLinear().domain([1, maxCount]).range([0.06, 0.42]);

        topEdges.forEach(function(edge) {{
          const fromPos = squareCenter(edge.from, cell, offsetX, offsetY);
          const toPos = squareCenter(edge.to, cell, offsetX, offsetY);

          const dx = toPos.x - fromPos.x;
          const dy = toPos.y - fromPos.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;

          const mx = (fromPos.x + toPos.x) / 2;
          const my = (fromPos.y + toPos.y) / 2;
          const nx = -dy / dist;
          const ny = dx / dist;
          const bend = Math.min(70, 14 + dist * 0.15);

          const cx = mx + nx * bend;
          const cy = my + ny * bend;

          svg.append("path")
            .attr("class", "move-path")
            .attr("d", "M " + fromPos.x + " " + fromPos.y + " Q " + cx + " " + cy + " " + toPos.x + " " + toPos.y)
            .attr("fill", "transparent")
            .attr("stroke", "white")
            .attr("stroke-width", widthScale(edge.count))
            .attr("opacity", opacityScale(edge.count));
        }});
      }}

      function selectorItems() {{
        return [
          {{ key: "white_king", label: "White king", symbol: "♔", row: 0, col: 0 }},
          {{ key: "all_toggle", label: "All pieces", symbol: "✦", row: 0, col: 1 }},
          {{ key: "black_king", label: "Black king", symbol: "♚", row: 1, col: 0 }},
          {{ key: "white_rook", label: "White rook", symbol: "♖", row: 1, col: 1 }}
        ];
      }}

      function renderPieceSelector() {{
        const container = d3.select("#piece-selector-viz");
        container.html("");

        const outerSize = 208;
        const padding = 12;
        const gap = 12;
        const cell = 86;

        const svg = container.append("svg")
          .attr("class", "selector-board")
          .attr("width", outerSize)
          .attr("height", outerSize);

        const items = selectorItems();

        items.forEach(function(item) {{
          const x = padding + item.col * (cell + gap);
          const y = padding + item.row * (cell + gap);

          let isActive = false;
          if (item.key === "all_toggle") {{
            isActive = allSelected();
          }} else {{
            isActive = selectedPieces.has(item.key);
          }}

          const group = svg.append("g")
            .attr("class", "selector-cell" + (isActive ? " active" : ""))
            .attr("transform", "translate(" + x + "," + y + ")")
            .on("click", function() {{
              if (item.key === "all_toggle") {{
                if (allSelected()) {{
                  selectedPieces = new Set();
                }} else {{
                  selectedPieces = new Set(BASE_PIECES);
                }}
              }} else {{
                if (selectedPieces.has(item.key)) {{
                  selectedPieces.delete(item.key);
                }} else {{
                  selectedPieces.add(item.key);
                }}
              }}
              renderAll();
            }});

          group.append("rect")
            .attr("width", cell)
            .attr("height", cell)
            .attr("rx", 4)
            .attr("ry", 4)
            .attr("fill", (item.row + item.col) % 2 === 0 ? "#6c6c6c" : "#3c3c3c")
            .attr("stroke", "rgba(255,255,255,0.18)")
            .attr("stroke-width", 1.25);

          group.append("text")
            .attr("class", "selector-piece")
            .attr("x", cell / 2)
            .attr("y", 34)
            .attr("text-anchor", "middle")
            .text(item.symbol);

          group.append("text")
            .attr("class", "selector-label")
            .attr("x", cell / 2)
            .attr("y", 58)
            .attr("text-anchor", "middle")
            .text(item.label);

          group.append("text")
            .attr("class", "selector-subtle")
            .attr("x", cell / 2)
            .attr("y", 74)
            .attr("text-anchor", "middle")
            .text(isActive ? "selected" : "click");
        }});
      }}

      function renderSummary() {{
        const list = d3.select("#top-moves-list");
        list.html("");

        list.append("li").text(
          selectedLabel() +
          " in " + bucketLabels[selectedBucket] +
          " contributes " + currentCount() + " engine-recommended moves."
        );

        const topMoves = currentTopMoves();
        if (!topMoves.length) {{
          list.append("li").text("No common move patterns for this selection.");
          return;
        }}

        topMoves.slice(0, 5).forEach(function(item, idx) {{
          list.append("li").text(
            "Common pattern " + (idx + 1) + ": " + item.move + " (" + item.count + " times)"
          );
        }});
      }}

      function renderAll() {{
        renderBucketButtons();
        renderMovePaths();
        renderPieceSelector();
        renderSummary();
      }}

      renderAll();
    }})();
    """

    return {
        "html": html,
        "css": css,
        "js": js,
    }