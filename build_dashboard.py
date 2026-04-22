from pathlib import Path

from viz_data import (
    load_engine_df,
    build_piece_flow_payload,
    build_heatmap_payload,
    build_endgame_sunburst_payload,
)
from viz_previsualization import (
    load_previsualization_df,
    build_previsualization_section,
)
from viz_piece_flow import build_piece_flow_section
from viz_heatmap import build_heatmap_section
from viz_endgame_sunburst import build_endgame_sunburst_section
from viz_template import build_page


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "krk"
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_HTML = OUTPUT_DIR / "index.html"


def main():
    pre_df = load_previsualization_df()
    engine_df = load_engine_df()

    heatmap_payload = build_heatmap_payload(engine_df)
    piece_flow_payload = build_piece_flow_payload(engine_df)
    sunburst_payload = build_endgame_sunburst_payload(
        engine_df,
        max_depth=5,
        max_examples_per_signature=18,
        max_children_per_node=48,
        min_bucket_fraction=0.0003,
    )

    sections = [
        build_previsualization_section(pre_df),
        build_endgame_sunburst_section(sunburst_payload),
        build_heatmap_section(heatmap_payload),
        build_piece_flow_section(piece_flow_payload),
    ]

    intro_html = """
        <p style="max-width:46rem;margin:0 auto 1rem auto;line-height:1.68rem;color:var(--color-faded-gray);text-align:center;">
        This dashboard is organized as a progression. First, it shows the KRK data in generic supporting views
        so the limitations are visible. Then it moves to board-native visualizations that better match the structure
        of the problem.
        </p>

        <p style="max-width:52rem;margin:0 auto 1.5rem auto;line-height:1.68rem;color:var(--color-faded-gray);text-align:center;font-size:0.95rem;">
        <strong style="color:white;">Acknowledgment.</strong>
        The interactive chessboard visual design in this project was inspired by
        <em>A Visual Look at 2 Million Chess Games</em> and the
        <em>chess-dataviz</em> library by ebemunk.
        This KRK project uses a different dataset and custom endgame-specific transformations,
        but the presentation style, interaction ideas, and board-centric storytelling were informed by that work.
        Please see the original sources:
        <a href="https://blog.ebemunk.com/a-visual-look-at-2-million-chess-games/" target="_blank" rel="noopener noreferrer" style="color:#7cb34b;">blog post</a>,
        <a href="https://ebemunk.com/chess-dataviz/" target="_blank" rel="noopener noreferrer" style="color:#7cb34b;">library demo</a>,
        and
        <a href="https://github.com/ebemunk/chess-dataviz" target="_blank" rel="noopener noreferrer" style="color:#7cb34b;">GitHub repository</a>.
        </p>
    """

    html = build_page(
        title="King Rook King Visualization Dashboard",
        intro_html=intro_html,
        sections=sections,
    )

    OUTPUT_HTML.write_text(html, encoding="utf-8")
    print(f"Saved: {OUTPUT_HTML}")


if __name__ == "__main__":
    main()