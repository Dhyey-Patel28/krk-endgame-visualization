from pathlib import Path
from typing import Dict, List

import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from viz_data import payload_json


BASE_DIR = Path(__file__).resolve().parent
BASELINE_CSV = BASE_DIR / "data" / "krk_baseline.csv"

BUCKET_ORDER = ["draw", "win_0_2", "win_3_5", "win_6_9", "win_10_plus"]
BUCKET_LABELS = {
    "draw": "Draw",
    "win_0_2": "Win in 0–2",
    "win_3_5": "Win in 3–5",
    "win_6_9": "Win in 6–9",
    "win_10_plus": "Win in 10+",
}

PCA_FEATURES = [
    "wk_file", "wk_rank",
    "wr_file", "wr_rank",
    "bk_file", "bk_rank",
    "bk_edge_dist",
    "bk_corner_dist",
    "bk_center_dist",
    "wk_bk_chebyshev",
    "wr_bk_manhattan",
    "wk_wr_chebyshev",
    "wk_bk_euclidean",
    "wr_bk_euclidean",
    "wr_bk_aligned",
    "wk_support_close",
    "bk_on_edge",
    "bk_in_corner",
]


def load_previsualization_df(path: Path = BASELINE_CSV) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "target_bucket" in df.columns:
        df["target_bucket"] = pd.Categorical(
            df["target_bucket"],
            categories=BUCKET_ORDER,
            ordered=True,
        )
    return df


def _balanced_sample(df: pd.DataFrame, n_per_bucket: int = 260, random_state: int = 42) -> pd.DataFrame:
    parts = []
    for bucket in BUCKET_ORDER:
        block = df[df["target_bucket"] == bucket]
        if len(block) == 0:
            continue
        take = min(n_per_bucket, len(block))
        parts.append(block.sample(n=take, random_state=random_state))
    return pd.concat(parts, ignore_index=True)


def _bucket_random_pools(df: pd.DataFrame, max_per_bucket: int = 50, random_state: int = 42) -> Dict[str, List[dict]]:
    pools: Dict[str, List[dict]] = {}

    for bucket in BUCKET_ORDER:
        block = df[df["target_bucket"] == bucket]
        if len(block) == 0:
            pools[bucket] = []
            continue

        take = min(max_per_bucket, len(block))
        chosen = block.sample(n=take, random_state=random_state)

        bucket_rows = []
        for _, row in chosen.iterrows():
            bucket_rows.append({
                "position_id": int(row["position_id"]) if "position_id" in row else None,
                "target_bucket": str(row["target_bucket"]),
                "target_raw": str(row.get("target_raw", "")),
                "wk_square": str(row.get("wk_square", "")),
                "wr_square": str(row.get("wr_square", "")),
                "bk_square": str(row.get("bk_square", "")),
                "fen": str(row.get("fen", "")),
            })
        pools[bucket] = bucket_rows

    return pools


def build_previsualization_payload(df: pd.DataFrame) -> dict:
    sampled = _balanced_sample(df, n_per_bucket=260, random_state=42).copy()

    missing = [col for col in PCA_FEATURES if col not in sampled.columns]
    if missing:
        raise ValueError(
            "Previsualization dataframe is missing PCA feature columns: "
            + ", ".join(missing)
        )

    feature_frame = sampled[PCA_FEATURES].copy().fillna(0)
    scaled = StandardScaler().fit_transform(feature_frame)
    coords = PCA(n_components=2, random_state=42).fit_transform(scaled)

    sampled["pc1"] = coords[:, 0]
    sampled["pc2"] = coords[:, 1]

    pca_points = []
    for _, row in sampled.iterrows():
        pca_points.append({
            "pc1": float(row["pc1"]),
            "pc2": float(row["pc2"]),
            "target_bucket": str(row["target_bucket"]),
            "wk_square": str(row.get("wk_square", "")),
            "wr_square": str(row.get("wr_square", "")),
            "bk_square": str(row.get("bk_square", "")),
            "target_raw": str(row.get("target_raw", "")),
        })

    return {
        "bucket_order": BUCKET_ORDER,
        "bucket_labels": BUCKET_LABELS,
        "pca_points": pca_points,
        "sample_pools": _bucket_random_pools(df, max_per_bucket=50, random_state=42),
    }


def build_previsualization_section(df: pd.DataFrame) -> dict:
    payload = payload_json(build_previsualization_payload(df))

    css = """
    .previs-wrap {
      max-width: 1020px;
      margin: 0 auto;
      padding: 1rem 1rem 2rem 1rem;
    }

    .previs-wrap h2 {
      color: var(--color-yellow);
      margin: 1.2rem auto 0.7rem auto;
      font-weight: 500;
      text-align: center;
    }

    .previs-wrap p {
      margin: 0 auto 1rem auto;
      line-height: 1.68rem;
      color: var(--color-faded-gray);
      max-width: 48rem;
      text-align: center;
    }

    .previs-toolbar {
      display: flex;
      justify-content: center;
      align-items: center;
      flex-wrap: wrap;
      gap: 8px;
      margin: 0.8rem 0 1rem 0;
    }

    .previs-toolbar button,
    .previs-board-toolbar button {
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

    .previs-toolbar button.active,
    .previs-board-toolbar button.active {
      background-color: var(--color-green-active);
      color: #fff;
    }

    #pca-preview-chart {
      display: flex;
      justify-content: center;
      align-items: center;
      width: 100%;
    }

    .previs-caption {
      text-align: center;
      color: var(--color-faded-gray);
      margin-top: 0.75rem;
      font-size: 0.95rem;
      line-height: 1.45rem;
      min-height: 2.9rem;
    }

    .previs-board-toolbar {
      display: flex;
      justify-content: center;
      align-items: center;
      flex-wrap: wrap;
      gap: 8px;
      margin: 1rem 0 1rem 0;
    }

    #single-sample-board {
      display: flex;
      justify-content: center;
      align-items: center;
      width: 100%;
    }

    .previs-board-meta {
      margin-top: 0.8rem;
      text-align: center;
      color: var(--color-faded-gray);
      line-height: 1.5rem;
      min-height: 3rem;
    }

    .previs-board-svg {
      display: block;
    }

    .board-piece-image {
      pointer-events: none;
    }

    .previs-tooltip {
      position: absolute;
      background-color: #282c34;
      border: 1px solid grey;
      color: #fff;
      padding: 6px 8px;
      display: none;
      flex-direction: column;
      align-items: flex-start;
      pointer-events: none;
      z-index: 20;
      font-size: 12px;
      line-height: 1.35rem;
      border-radius: 6px;
      max-width: 260px;
    }
    """

    html = """
    <section id="previsualization-section" class="previs-wrap">
      <h2>Previsualization</h2>
      <p>
        These supporting views show why generic visualization is not enough for KRK.
        The PCA plot is only a supporting preview, and the board below shows that each row is a single static position.
      </p>

      <h3 style="text-align:center;color:white;margin:0.8rem 0 0.5rem 0;">PCA 2D preview</h3>
      <div class="previs-toolbar" id="pca-filter-buttons"></div>
      <div id="pca-preview-chart"></div>
      <div class="previs-caption" id="pca-preview-caption"></div>

      <h3 style="text-align:center;color:white;margin:1.6rem 0 0.5rem 0;">Sample static positions</h3>
      <div class="previs-board-toolbar" id="sample-position-buttons"></div>
      <div id="single-sample-board"></div>
      <div class="previs-board-meta" id="single-sample-meta"></div>

      <div class="previs-tooltip" id="previs-tooltip"></div>
    </section>
    """

    js = f"""
    const previsData = {payload};

    (function() {{
      const colorMap = {{
        "draw": "#9aa5b1",
        "win_0_2": "#ff7f50",
        "win_3_5": "#f6c85f",
        "win_6_9": "#6f4e7c",
        "win_10_plus": "#4cc9f0"
      }};

      let selectedBuckets = new Set(previsData.bucket_order);
      let selectedBoardBucket = previsData.bucket_order[0];
      let selectedBoardSample = null;

      const tooltip = d3.select("#previs-tooltip");

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
    <path d="M12.5 37c5.5 3.5 14.5 3.5 20 0V30s9-4.5 6-10.5C34.5 13 25 16 22.5 23.5V27v-3.5C20 16 10.5 13 6.5 19.5 3.5 25.5 13 29.5 13 29.5" fill="#000"/>
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

      function randomChoice(items) {{
        if (!items || items.length === 0) return null;
        const index = Math.floor(Math.random() * items.length);
        return items[index];
      }}

      function renderPcaButtons() {{
        const wrap = d3.select("#pca-filter-buttons");
        wrap.html("");

        wrap.append("button")
          .attr("class", selectedBuckets.size === previsData.bucket_order.length ? "active" : null)
          .text("All")
          .on("click", function() {{
            if (selectedBuckets.size === previsData.bucket_order.length) {{
              selectedBuckets = new Set();
            }} else {{
              selectedBuckets = new Set(previsData.bucket_order);
            }}
            renderPcaButtons();
            renderPcaPreview();
          }});

        previsData.bucket_order.forEach(function(bucket) {{
          wrap.append("button")
            .attr("class", selectedBuckets.has(bucket) ? "active" : null)
            .text(previsData.bucket_labels[bucket])
            .on("click", function() {{
              if (selectedBuckets.has(bucket)) {{
                selectedBuckets.delete(bucket);
              }} else {{
                selectedBuckets.add(bucket);
              }}
              renderPcaButtons();
              renderPcaPreview();
            }});
        }});
      }}

      function showTooltip(event, d) {{
        tooltip
          .style("display", "flex")
          .style("left", (event.pageX + 14) + "px")
          .style("top", (event.pageY + 14) + "px")
          .html(
            "<strong>" + previsData.bucket_labels[d.target_bucket] + "</strong><br>" +
            "PC1: " + d.pc1.toFixed(3) + "<br>" +
            "PC2: " + d.pc2.toFixed(3) + "<br>" +
            "White King " + d.wk_square + " · White Rook " + d.wr_square + " · Black King " + d.bk_square + "<br>"
          );
      }}

      function hideTooltip() {{
        tooltip.style("display", "none");
      }}

      function renderPcaPreview() {{
        const container = d3.select("#pca-preview-chart");
        container.html("");

        const width = 620;
        const height = 420;
        const margin = {{ top: 14, right: 20, bottom: 46, left: 54 }};

        const svg = container.append("svg")
          .attr("width", width)
          .attr("height", height);

        const plotWidth = width - margin.left - margin.right;
        const plotHeight = height - margin.top - margin.bottom;

        const g = svg.append("g")
          .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

        const allPoints = previsData.pca_points;
        const points = allPoints.filter(d => selectedBuckets.has(d.target_bucket));

        const x = d3.scaleLinear()
          .domain(d3.extent(allPoints, d => d.pc1))
          .nice()
          .range([0, plotWidth]);

        const y = d3.scaleLinear()
          .domain(d3.extent(allPoints, d => d.pc2))
          .nice()
          .range([plotHeight, 0]);

        g.append("g")
          .attr("transform", "translate(0," + plotHeight + ")")
          .call(d3.axisBottom(x).ticks(6))
          .selectAll("text")
          .attr("fill", "#d7dee5");

        g.append("g")
          .call(d3.axisLeft(y).ticks(6))
          .selectAll("text")
          .attr("fill", "#d7dee5");

        g.selectAll(".domain,.tick line")
          .attr("stroke", "rgba(255,255,255,0.2)");

        g.append("text")
          .attr("x", plotWidth / 2)
          .attr("y", plotHeight + 36)
          .attr("text-anchor", "middle")
          .attr("fill", "#d7dee5")
          .text("PC1");

        g.append("text")
          .attr("transform", "rotate(-90)")
          .attr("x", -plotHeight / 2)
          .attr("y", -38)
          .attr("text-anchor", "middle")
          .attr("fill", "#d7dee5")
          .text("PC2");

        g.selectAll(".pca-point")
          .data(points)
          .enter()
          .append("circle")
          .attr("cx", d => x(d.pc1))
          .attr("cy", d => y(d.pc2))
          .attr("r", 4.0)
          .attr("fill", d => colorMap[d.target_bucket] || "#cccccc")
          .attr("opacity", 0.76)
          .on("mousemove", function(event, d) {{
            showTooltip(event, d);
          }})
          .on("mouseleave", hideTooltip);

        if (points.length === 0) {{
          g.append("text")
            .attr("x", plotWidth / 2)
            .attr("y", plotHeight / 2)
            .attr("text-anchor", "middle")
            .attr("fill", "#9fb0c0")
            .attr("font-size", 16)
            .text("No buckets selected");
        }}

        d3.select("#pca-preview-caption").text(
          points.length === 0
            ? "All PCA filters are currently off."
            : "Use the buttons above to compare outcome buckets. Even after filtering, the PCA projection still overlaps heavily, which is why it is only used here as a supporting preview."
        );
      }}

      function parseFenBoard(fen) {{
        const boardPart = fen.split(" ")[0];
        const rows = boardPart.split("/");
        const board = [];

        rows.forEach(function(row) {{
          const expanded = [];
          row.split("").forEach(function(ch) {{
            if ("12345678".includes(ch)) {{
              for (let i = 0; i < parseInt(ch, 10); i++) expanded.push("");
            }} else {{
              expanded.push(ch);
            }}
          }});
          board.push(expanded);
        }});

        return board;
      }}

      function drawSingleBoard(sample) {{
        const container = d3.select("#single-sample-board");
        container.html("");

        const size = 360;
        const cell = size / 8;

        const svg = container.append("svg")
          .attr("class", "previs-board-svg")
          .attr("width", size)
          .attr("height", size);

        for (let row = 0; row < 8; row++) {{
          for (let col = 0; col < 8; col++) {{
            svg.append("rect")
              .attr("x", col * cell)
              .attr("y", row * cell)
              .attr("width", cell)
              .attr("height", cell)
              .attr("fill", (row + col) % 2 === 0 ? "#f0d9b5" : "#b58863");
          }}
        }}

        const board = parseFenBoard(sample.fen);
        for (let row = 0; row < 8; row++) {{
          for (let col = 0; col < 8; col++) {{
            const piece = board[row][col];
            if (!piece) continue;

            const href = pieceAsset(piece);
            if (!href) continue;

            const pad = cell * 0.05;

            svg.append("image")
              .attr("class", "board-piece-image")
              .attr("href", href)
              .attr("x", col * cell + pad)
              .attr("y", row * cell + pad)
              .attr("width", cell - 2 * pad)
              .attr("height", cell - 2 * pad);
          }}
        }}

        d3.select("#single-sample-meta").html(
          "<strong>" + (previsData.bucket_labels[sample.target_bucket] || sample.target_bucket) + "</strong><br>" +
          "White King " + sample.wk_square + " · White Rook " + sample.wr_square + " · Black King " + sample.bk_square
        );
      }}

      function chooseRandomBoardSample(bucket) {{
        const pool = previsData.sample_pools[bucket] || [];
        const choice = randomChoice(pool);
        if (choice) {{
          selectedBoardSample = choice;
          drawSingleBoard(choice);
        }}
      }}

      function renderBoardButtons() {{
        const wrap = d3.select("#sample-position-buttons");
        wrap.html("");

        previsData.bucket_order.forEach(function(bucket) {{
          wrap.append("button")
            .attr("class", bucket === selectedBoardBucket ? "active" : null)
            .text(previsData.bucket_labels[bucket])
            .on("click", function() {{
              selectedBoardBucket = bucket;
              chooseRandomBoardSample(bucket);
              renderBoardButtons();
            }});
        }});
      }}

      renderPcaButtons();
      renderPcaPreview();
      renderBoardButtons();
      chooseRandomBoardSample(selectedBoardBucket);
    }})();
    """

    return {
        "html": html,
        "css": css,
        "js": js,
    }