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


def build_heatmap_section(heatmap_payload: dict) -> dict:
    payload = payload_json(heatmap_payload)

    css = """
    .heatmap-wrap {
      max-width: 980px;
      margin: 0 auto;
      padding: 1rem 1rem 2rem 1rem;
    }

    .heatmap-wrap h2 {
      color: var(--color-yellow);
      margin: 1.3rem auto 0.8rem auto;
      font-weight: 500;
      text-align: center;
    }

    .heatmap-wrap p {
      margin: 0 auto 1rem auto;
      line-height: 1.68rem;
      color: var(--color-faded-gray);
      max-width: 42rem;
      text-align: center;
    }

    #heatmap-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      margin: 1rem 0 1.2rem 0;
    }

    #heatmap-chart {
      margin-bottom: 1rem;
      width: 520px;
      display: flex;
      justify-content: center;
      align-items: center;
    }

    .heatmap-caption {
      font-weight: bold;
      text-align: center;
      margin-bottom: 0.75rem;
    }

    .heatmap-toolbar {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 0.65rem;
      margin-bottom: 0.5rem;
    }

    .heatmap-bucket-row,
    .heatmap-mode-row,
    .heatmap-piece-row {
      display: flex;
      justify-content: center;
      align-items: center;
      flex-wrap: wrap;
      gap: 8px;
    }

    .heatmap-toolbar button {
      background: transparent;
      border: 1px solid var(--color-green);
      border-radius: 3px;
      color: var(--color-green);
      display: inline-block;
      font-size: 14px;
      height: 32px;
      line-height: 24px;
      padding: 3px 10px;
      text-align: center;
      white-space: nowrap;
      cursor: pointer;
    }

    .heatmap-toolbar button.active {
      background-color: var(--color-green-active);
      color: #fff;
    }

    .heatmap-select {
      border: 1px solid var(--color-green);
      border-radius: 3px;
      color: var(--color-green);
      background: transparent;
      display: inline-block;
      font-size: 14px;
      height: 32px;
      line-height: 24px;
      padding: 3px 10px;
      cursor: pointer;
      outline: none;
    }

    .heatmap-select option {
      background: var(--color-light-grey);
      color: white;
    }

    .heatmap-piece-group-label {
      color: var(--color-faded-gray);
      font-size: 0.8rem;
      margin-right: 4px;
      min-width: 70px;
      text-align: right;
    }

    .heatmap-summary {
      max-width: 42rem;
      margin: 0.75rem auto 0 auto;
      color: var(--color-faded-gray);
      text-align: center;
    }

    .heatmap-board-label {
      fill: #ffffff;
      font-size: 12px;
    }

    @media screen and (max-width: 700px) {
      #heatmap-chart {
        width: 100%;
      }

      .heatmap-piece-group-label {
        min-width: auto;
        text-align: center;
        margin-right: 0;
      }
    }
    """

    html = """
    <section id="heatmap-section" class="heatmap-wrap">
      <h2>Heatmaps</h2>
      <p>
        Heatmaps show which squares are used most often by engine-recommended moves. This is the quick,
        readable overview; the flow art below shows the same behavior as movement patterns.
      </p>

      <div id="heatmap-container">
        <div class="heatmap-caption" id="heatmap-caption">Heatmap</div>

        <div id="heatmap-chart"></div>

        <div class="heatmap-toolbar">
          <div class="heatmap-bucket-row" id="heatmap-bucket-buttons"></div>

          <div class="heatmap-mode-row">
            <select id="heatmap-mode-select" class="heatmap-select">
              <option value="destination">Square Utilization</option>
              <option value="origin">Move Squares</option>
            </select>
          </div>

          <div class="heatmap-piece-row">
            <span class="heatmap-piece-group-label">White / all</span>
            <div id="heatmap-piece-buttons-w"></div>
          </div>

          <div class="heatmap-piece-row">
            <span class="heatmap-piece-group-label">Black</span>
            <div id="heatmap-piece-buttons-b"></div>
          </div>
        </div>
      </div>

      <div class="heatmap-summary" id="heatmap-summary"></div>
    </section>
    """

    js = f"""
    const heatmapData = {payload};

    (function() {{
      const bucketOrder = heatmapData.bucket_order;
      const bucketLabels = heatmapData.bucket_labels;
      const pieceLabels = heatmapData.piece_filter_labels;

      let selectedBucket = "draw";
      let selectedPiece = "all";
      let selectedMode = "destination";

      function currentBoard() {{
        return heatmapData[selectedMode][selectedPiece][selectedBucket] || [];
      }}

      function currentCount() {{
        return heatmapData.counts[selectedPiece][selectedBucket] || 0;
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

      function renderControls() {{
        renderButtonGroup(
          "#heatmap-bucket-buttons",
          bucketOrder.map(function(bucket) {{
            return [bucket, bucketLabels[bucket]];
          }}),
          selectedBucket,
          function(key) {{
            selectedBucket = key;
            renderAll();
          }}
        );

        renderButtonGroup(
          "#heatmap-piece-buttons-w",
          [
            ["all", "All"],
            ["white_rook", "R"],
            ["white_king", "K"]
          ],
          selectedPiece,
          function(key) {{
            selectedPiece = key;
            renderAll();
          }}
        );

        renderButtonGroup(
          "#heatmap-piece-buttons-b",
          [
            ["black_king", "K"]
          ],
          selectedPiece,
          function(key) {{
            selectedPiece = key;
            renderAll();
          }}
        );

        d3.select("#heatmap-mode-select")
          .property("value", selectedMode)
          .on("change", function() {{
            selectedMode = this.value;
            renderAll();
          }});
      }}

      function squareName(row, col) {{
        const file = "abcdefgh"[col];
        const rank = String(8 - row);
        return file + rank;
      }}

      function drawBoard(boardValues) {{
        const container = d3.select("#heatmap-chart");
        container.html("");

        const size = 520;
        const svg = container.append("svg")
          .attr("width", size)
          .attr("height", size);

        const boardSize = 520;
        const cell = boardSize / 8;

        const flat = boardValues.flat();
        const maxValue = d3.max(flat) || 0;

        const sizeScale = d3.scaleLinear()
          .domain([0, maxValue || 1])
          .range([0, cell * 0.68]);

        const opacityScale = d3.scaleLinear()
          .domain([0, maxValue || 1])
          .range([0.0, 0.82]);

        for (let row = 0; row < 8; row++) {{
          for (let col = 0; col < 8; col++) {{
            const baseColor = (row + col) % 2 === 0 ? "#6c6c6c" : "#3c3c3c";

            svg.append("rect")
              .attr("x", col * cell)
              .attr("y", row * cell)
              .attr("width", cell)
              .attr("height", cell)
              .attr("fill", baseColor);

            const value = boardValues[row][col];
            const heatSize = sizeScale(value);

            if (value > 0 && heatSize > 0) {{
              svg.append("rect")
                .attr("class", "heat-square")
                .attr("x", col * cell + (cell - heatSize) / 2)
                .attr("y", row * cell + (cell - heatSize) / 2)
                .attr("width", heatSize)
                .attr("height", heatSize)
                .attr("fill", "white")
                .attr("opacity", opacityScale(value))
                .append("title")
                .text(squareName(row, col) + ": " + value.toFixed(4));
            }}
          }}
        }}

        ["8","7","6","5","4","3","2","1"].forEach(function(rank, i) {{
          svg.append("text")
            .attr("class", "heatmap-board-label")
            .attr("x", 4)
            .attr("y", i * cell + 14)
            .text(rank);
        }});

        ["a","b","c","d","e","f","g","h"].forEach(function(file, i) {{
          svg.append("text")
            .attr("class", "heatmap-board-label")
            .attr("x", i * cell + cell - 10)
            .attr("y", boardSize - 4)
            .text(file);
        }});
      }}

      function renderSummary() {{
        const modeLabel = selectedMode === "destination" ? "square utilization" : "move squares";

        d3.select("#heatmap-caption").text(
          pieceLabels[selectedPiece] + " — " + modeLabel + " in " + bucketLabels[selectedBucket]
        );

        d3.select("#heatmap-summary").text(
          pieceLabels[selectedPiece] +
          " contributes " + currentCount() +
          " engine-recommended moves in " + bucketLabels[selectedBucket] + "."
        );
      }}

      function renderAll() {{
        renderControls();
        drawBoard(currentBoard());
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