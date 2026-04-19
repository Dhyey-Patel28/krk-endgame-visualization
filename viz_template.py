def build_page(title: str, intro_html: str, sections: list[dict]) -> str:
    all_css = "\n".join(section["css"] for section in sections if section.get("css"))
    all_html = "\n".join(section["html"] for section in sections if section.get("html"))
    all_js = "\n".join(section["js"] for section in sections if section.get("js"))

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>

<style>
:root {{
  --color-dark-grey: #282c34;
  --color-light-grey: #333842;
  --color-yellow: #d19a66;
  --color-green: #7cb34b;
  --color-green-active: #638f3c;
  --color-faded-gray: #9eabb3;
  --color-white: white;
}}

html {{
  font-size: 18px;
}}

body {{
  background: var(--color-dark-grey);
  color: var(--color-white);
  margin: 0;
  font-size: 18px;
  font-family: Poppins, Arial, sans-serif;
}}

.wrap {{
  max-width: 1100px;
  margin: 0 auto;
  padding: 2rem 1rem 3rem 1rem;
}}

h1 {{
  color: var(--color-yellow);
  margin: 1rem auto 0.75rem auto;
  font-size: 3rem;
  font-weight: 300;
  text-align: center;
}}

button {{
  background: transparent;
  border: 1px solid var(--color-green);
  border-radius: 3px;
  color: var(--color-green);
  display: inline-block;
  font-size: 14px;
  padding: 3px 10px;
  cursor: pointer;
}}

button.active {{
  background-color: var(--color-green-active);
  color: #fff;
}}

.page-credit {{
  max-width: 58rem;
  margin: 2.5rem auto 0 auto;
  padding-top: 1rem;
  border-top: 1px solid rgba(255,255,255,0.08);
  color: var(--color-faded-gray);
  font-size: 0.95rem;
  line-height: 1.65rem;
  text-align: center;
}}

.page-credit a {{
  color: var(--color-green);
  text-decoration: none;
}}

.page-credit a:hover {{
  text-decoration: underline;
}}

{all_css}
</style>
</head>
<body>
  <div class="wrap">
    <h1>{title}</h1>
    {intro_html}
    {all_html}
    
    <div class="page-credit">
      <strong style="color:white;">Acknowledgment.</strong>
      This project’s interactive chess visual style was inspired by ebemunk’s
      <em>A Visual Look at 2 Million Chess Games</em> and the
      <em>chess-dataviz</em> library.
      The KRK dashboard uses its own preprocessing, engine analysis, and KRK-specific visual mappings.
      Original sources:
      <a href="https://blog.ebemunk.com/a-visual-look-at-2-million-chess-games/" target="_blank" rel="noopener noreferrer">blog post</a>,
      <a href="https://ebemunk.com/chess-dataviz/" target="_blank" rel="noopener noreferrer">library demo</a>,
      <a href="https://github.com/ebemunk/chess-dataviz" target="_blank" rel="noopener noreferrer">GitHub</a>.
    </div>
  </div>

  <script src="https://d3js.org/d3.v7.min.js"></script>
  <script>
  {all_js}
  </script>
</body>
</html>
"""