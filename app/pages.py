"""Server-rendered pages for GI LINK."""

import json
from typing import Optional

BASE_URL = "https://gilinkdl.vercel.app"
ASSET_VERSION = "18"


def render_layout(
    title: str,
    description: str,
    canonical_path: str,
    content_html: str,
    schema_json: Optional[dict] = None,
    extra_scripts: str = f'<script src="/static/app.js?v={ASSET_VERSION}" defer></script>',
) -> str:
    canonical_url = f"{BASE_URL}{canonical_path}"
    schema_tag = ""
    if schema_json:
        schema = json.dumps(schema_json, ensure_ascii=False).replace("<", "\\u003c")
        schema_tag = f'<script type="application/ld+json">{schema}</script>'
    history_action = (
        '<button class="history-trigger" id="historyBtn" type="button">History</button>'
        if not canonical_path else ""
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#f7f8fa">
  <meta name="description" content="{description}">
  <meta name="robots" content="index,follow">
  <meta name="google-site-verification" content="Du_RVrnTwPBjSXPQjQ-RlDluCuEo0A4QMPz9vAWXjDY">
  <meta name="google-adsense-account" content="ca-pub-6837969928640726">
  <link rel="canonical" href="{canonical_url}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{canonical_url}">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{description}">
  <meta property="og:image" content="{BASE_URL}/icon-512.png">
  <meta property="og:site_name" content="GI LINK">
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="{title}">
  <meta name="twitter:description" content="{description}">
  <meta name="twitter:image" content="{BASE_URL}/icon-512.png">
  <link rel="icon" type="image/png" sizes="192x192" href="/icon-192.png">
  <link rel="apple-touch-icon" href="/icon-192.png">
  <link rel="manifest" href="/manifest.json">
  <link rel="stylesheet" href="/static/style.css?v={ASSET_VERSION}">
  <title>{title}</title>
  {schema_tag}
</head>
<body data-ui-mode="classic">
  <a class="skip-link" href="#main">Skip to content</a>
  <header class="site-header">
    <div class="container header-inner">
      <a class="brand" href="/" aria-label="GI LINK home">
        <img class="brand-icon" src="/icon-192.png" alt="" width="31" height="31">
        <span>GI<span class="brand-light">LINK</span></span>
      </a>
      <button class="ui-mode-toggle" id="uiModeToggle" type="button" aria-pressed="true" aria-label="Switch to modern interface">Classic UI</button>
      <button class="menu-toggle" id="menuToggle" type="button" aria-expanded="false" aria-controls="primaryNav" aria-label="Open menu">
        <span></span><span></span>
      </button>
      <nav class="primary-nav" id="primaryNav" aria-label="Main navigation">
        <a href="/">Home</a>
        <a href="/#platforms">Platforms</a>
        <a href="/#how-it-works">How it works</a>
        <a href="/about">About</a>
        <a href="/contact">Contact</a>
        {history_action}
        <a class="nav-cta" href="/#downloader">Download media <span aria-hidden="true">↗</span></a>
      </nav>
    </div>
  </header>
  {content_html}
  <footer class="site-footer">
    <div class="container footer-main">
      <div class="footer-brand">
        <a class="brand" href="/" aria-label="GI LINK home">
          <img class="brand-icon" src="/icon-192.png" alt="" width="31" height="31">
          <span>GI<span class="brand-light">LINK</span></span>
        </a>
        <p>Tools for working with public media links.</p>
      </div>
      <nav class="footer-nav" aria-label="Footer navigation">
        <a href="/about">About</a>
        <a href="/privacy">Privacy</a>
        <a href="/terms">Terms</a>
        <a href="/dmca">Copyright</a>
        <a href="/contact">Contact</a>
      </nav>
    </div>
    <div class="container footer-bottom">
      <span>Created by Ghalib Kamal</span>
      <span>Only download media you have permission to use.</span>
    </div>
  </footer>
  {extra_scripts}
</body>
</html>"""


def get_home_html() -> str:
    return """
  <main id="main">
    <section class="hero">
      <div class="container hero-grid">
        <div class="hero-copy">
          <p class="eyebrow"><span class="eyebrow-dot"></span> A straightforward media tool</p>
          <h1>
            <span class="modern-headline">Bring your media<br><span>with you.</span></span>
            <span class="classic-headline">Download <span>Video &amp; Audio</span> Online</span>
          </h1>
          <p class="hero-description">Get a downloadable file from a public video or audio link. Choose an available format and save it to your device.</p>
          <div class="trust-notes">
            <span><span class="check-mark">✓</span> No account required</span>
            <span><span class="check-mark">✓</span> Choose the file format</span>
          </div>
        </div>

        <section class="download-panel" id="downloader" aria-labelledby="download-title">
          <div class="panel-heading">
            <span class="panel-step">01</span>
            <div>
              <h2 id="download-title">Start with a link</h2>
              <p>Paste a public media URL to see available downloads.</p>
            </div>
          </div>
          <form id="urlForm" novalidate>
            <label for="urlInput">Media URL</label>
            <div class="url-control" id="urlControl">
              <span class="url-symbol" aria-hidden="true">↗</span>
              <input id="urlInput" name="url" type="url" inputmode="url" autocomplete="url" placeholder="https://www.youtube.com/…" required aria-describedby="urlHint formError">
              <button class="paste-button" id="pasteBtn" type="button">Paste</button>
            </div>
            <p class="field-hint" id="urlHint">Use a public link to a post or media page.</p>
            <p class="form-error" id="formError" role="alert" hidden></p>
            <button class="button button-primary submit-button" id="fetchBtn" type="submit">
              <span class="button-label">Find downloads</span>
              <span class="button-spinner" aria-hidden="true"></span>
              <span aria-hidden="true">→</span>
            </button>
          </form>
          <p class="panel-footnote"><span aria-hidden="true">i</span> GI LINK only works with content you’re authorized to download.</p>
          <section class="result-panel" id="mediaCard" aria-live="polite" hidden>
            <div class="result-header">
              <div class="thumbnail-wrap">
                <img id="mediaThumb" alt="" hidden>
                <span class="thumbnail-fallback" id="thumbnailFallback" aria-hidden="true">GI</span>
              </div>
              <div class="result-meta">
                <p class="result-platform" id="mediaPlatform"></p>
                <h3 id="mediaTitle"></h3>
                <p class="result-byline" id="mediaByline"></p>
              </div>
            </div>
            <div class="result-options">
              <div class="options-heading">
                <h3>Available downloads</h3>
                <span id="formatCount"></span>
              </div>
              <div id="formatPresets" class="format-list"></div>
            </div>
            <p class="download-status" id="downloadStatus" role="status" hidden></p>
          </section>
          <section class="error-panel" id="errorCard" role="alert" hidden>
            <span class="error-indicator" aria-hidden="true">!</span>
            <div><h3>Couldn’t load that link</h3><p id="errorMessage"></p></div>
          </section>
        </section>
      </div>
      <div class="hero-bottom container">
        <span>Public links only</span><span>Files processed on request</span><span>Formats shown before download</span>
      </div>
    </section>

    <section class="section platforms-section" id="platforms">
      <div class="container">
        <div class="section-heading">
          <p class="eyebrow">SUPPORTED SOURCES</p>
          <h2>Works with links from</h2>
          <p>Support depends on the public page and the source platform’s availability.</p>
        </div>
        <ul class="platform-list" aria-label="Supported media sources">
          <li><span class="platform-glyph youtube">▶</span>YouTube</li>
          <li><span class="platform-glyph instagram">◎</span>Instagram</li>
          <li><span class="platform-glyph tiktok">♪</span>TikTok</li>
          <li><span class="platform-glyph facebook">f</span>Facebook</li>
          <li><span class="platform-glyph x-mark">𝕏</span>X</li>
          <li><span class="platform-glyph reddit">r/</span>Reddit</li>
          <li><span class="platform-glyph pinterest">p</span>Pinterest</li>
          <li><span class="platform-glyph vimeo">v</span>Vimeo</li>
          <li><span class="platform-glyph soundcloud">≋</span>SoundCloud</li>
        </ul>
      </div>
    </section>

    <section class="section how-section" id="how-it-works">
      <div class="container how-grid">
        <div class="section-heading how-intro">
          <p class="eyebrow">A SIMPLE WORKFLOW</p>
          <h2>From link<br>to file.</h2>
          <p>GI LINK checks the source, then shows the formats it can retrieve. Nothing downloads until you choose an option.</p>
        </div>
        <ol class="steps-list">
          <li><span class="step-number">01</span><div><h3>Paste a public link</h3><p>Enter a link to a supported post or media page.</p></div></li>
          <li><span class="step-number">02</span><div><h3>Review the options</h3><p>Check the available media details and file formats.</p></div></li>
          <li><span class="step-number">03</span><div><h3>Save what you need</h3><p>Choose a download. The file is sent to your browser.</p></div></li>
        </ol>
      </div>
    </section>

    <section class="section faq-section" id="faq">
      <div class="container faq-grid">
        <div class="section-heading">
          <p class="eyebrow">GOOD TO KNOW</p>
          <h2>Questions,<br>answered.</h2>
        </div>
        <div class="faq-list">
          <details><summary>Which links can I use?<span aria-hidden="true">+</span></summary><p>GI LINK uses yt-dlp to support a broad range of public media pages, including the sources listed above. A particular post may still be unavailable because of its privacy, region, account, or platform restrictions.</p></details>
          <details><summary>Will every audio download be MP3?<span aria-hidden="true">+</span></summary><p>No. MP3 is offered when the server can convert the source audio. Otherwise, the original audio format is identified before you download.</p></details>
          <details><summary>Where does the file go?<span aria-hidden="true">+</span></summary><p>Your browser handles the download and uses its normal download location or save prompt.</p></details>
          <details><summary>Can I download private content?<span aria-hidden="true">+</span></summary><p>No. GI LINK is intended for public content you have permission to download. It does not provide access to private posts.</p></details>
        </div>
      </div>
    </section>
    <section class="responsible-use">
      <div class="container responsible-inner">
        <span class="responsible-icon" aria-hidden="true">↗</span>
        <p><strong>Use media responsibly.</strong> You are responsible for having permission to download and use the content. Respect copyright and the source platform’s terms.</p>
        <a href="/terms">Read the terms <span aria-hidden="true">→</span></a>
      </div>
    </section>
    <dialog class="history-dialog" id="historyModal" aria-labelledby="historyTitle">
      <button class="history-backdrop" type="button" data-history-close aria-label="Close recent links"></button>
      <section class="history-sheet">
        <div class="history-heading"><div><p class="eyebrow">ON THIS DEVICE</p><h2 id="historyTitle">Recent links</h2></div><button id="closeHistoryBtn" class="icon-button" type="button" aria-label="Close history">×</button></div>
        <div id="historyList" class="history-list"></div>
        <div class="history-actions"><p>History stays in this browser.</p><button id="clearHistoryBtn" class="text-button" type="button">Clear history</button></div>
      </section>
    </dialog>
  </main>
"""


def _information_page(title: str, eyebrow: str, intro: str, sections: str) -> str:
    return f"""
  <main class="content-page" id="main">
    <div class="container content-container">
      <a class="back-link" href="/">← <span>Back to GI LINK</span></a>
      <header class="content-heading"><p class="eyebrow">{eyebrow}</p><h1>{title}</h1><p>{intro}</p></header>
      <div class="prose-content">{sections}</div>
    </div>
  </main>
"""


def get_about_html() -> str:
    return _information_page(
        "A simpler way to save public media.",
        "ABOUT GI LINK",
        "GI LINK is a web interface for retrieving media from public links. It combines a FastAPI service with yt-dlp and lets you choose from the formats available for a source.",
        """
      <section><h2>How it works</h2><p>When you submit a link, GI LINK asks its media extractor for details and available formats. When you select a download, the server retrieves the selected media and streams it to your browser. Temporary files created for a download are removed after the response is sent.</p></section>
      <section><h2>Built with</h2><ul><li>FastAPI for the web application and API.</li><li>yt-dlp for media information and downloads.</li><li>Vercel for the current deployment.</li></ul></section>
      <section><h2>Responsible use</h2><p>Use GI LINK only for public content you own or are authorized to download. Respect copyright and each source platform’s terms. GI LINK does not unlock private posts.</p></section>
      <section><h2>Project</h2><p>GI LINK is maintained by Ghalib Kamal. The source code is available on <a href="https://github.com/ghalibkamal7/gilink" target="_blank" rel="noopener noreferrer">GitHub</a>.</p></section>
""",
    )


def get_privacy_html() -> str:
    return _information_page(
        "Privacy policy",
        "YOUR PRIVACY",
        "This page describes the information GI LINK handles when you use the website.",
        """
      <section><h2>Links and downloads</h2><p>When you submit a URL, the service processes it to retrieve media information or a download. The URL and the media request are sent to the source platform and to the hosting provider as needed to fulfill the request. GI LINK does not maintain a user account or a persistent download library.</p></section>
      <section><h2>Temporary files</h2><p>Some downloads are temporarily written to server storage before they are streamed to your browser. The application removes those files after the response completes. Temporary storage may be affected by interrupted requests or hosting-provider lifecycle behavior.</p></section>
      <section><h2>Browser history</h2><p>Recent links, when shown, are kept in the current page’s memory only. They are not saved to a GI LINK account and are cleared when the page is closed or refreshed.</p></section>
      <section><h2>Hosting and third parties</h2><p>The hosting provider may process standard operational data, such as request information, to deliver and secure the service. Source platforms and your browser may also apply their own privacy policies and settings.</p></section>
      <section><h2>Questions</h2><p>For privacy questions, use the project’s <a href="https://github.com/ghalibkamal7/gilink/issues" target="_blank" rel="noopener noreferrer">GitHub issue tracker</a>.</p></section>
""",
    )


def get_terms_html() -> str:
    return _information_page(
        "Terms of service",
        "USING GI LINK",
        "By using GI LINK, you agree to use the service lawfully and responsibly.",
        """
      <section><h2>Permitted use</h2><p>Use the service only with public media and only when you own the content or have permission to download it. You are responsible for complying with applicable laws, copyright, and the source platform’s terms.</p></section>
      <section><h2>Access restrictions</h2><p>GI LINK does not provide access to private content or bypass account, payment, or other access controls. Do not use the service to interfere with platforms or infringe another person’s rights.</p></section>
      <section><h2>Availability</h2><p>Media extraction depends on third-party websites and software that can change without notice. GI LINK may be unavailable or unable to retrieve a particular link. The service is provided without a guarantee of uninterrupted availability.</p></section>
      <section><h2>Third-party content</h2><p>Media remains hosted by its source platform. GI LINK does not claim ownership of third-party content. You are responsible for how you use any file you download.</p></section>
      <section><h2>Changes</h2><p>These terms may be updated as the service changes. Continued use after an update means you accept the revised terms.</p></section>
""",
    )


def get_dmca_html() -> str:
    return _information_page(
        "Copyright & takedown requests",
        "RESPECTING COPYRIGHT",
        "GI LINK is a tool for processing links submitted by users. It does not operate a catalog of media or host a public media library.",
        """
      <section><h2>Report a concern</h2><p>If you believe a link is being used to infringe your rights, submit a report through the <a href="https://github.com/ghalibkamal7/gilink/issues" target="_blank" rel="noopener noreferrer">GI LINK GitHub issue tracker</a>. Include the relevant source URL, identify the work, explain your relationship to the rights holder, and provide contact details so the report can be reviewed.</p></section>
      <section><h2>What GI LINK can do</h2><p>Media is retrieved from the third-party source supplied in a request. GI LINK does not control that source or remove its content. A request to block a link can be reviewed for changes to GI LINK’s processing behavior.</p></section>
      <section><h2>Responsible use</h2><p>Do not download or use copyrighted material unless you have the right to do so. Respect applicable copyright laws and the terms of the source platform.</p></section>
""",
    )


def get_contact_html() -> str:
    return _information_page(
        "Get in touch",
        "CONTACT",
        "The most reliable way to report a bug, suggest an improvement, or ask about the project is through GitHub.",
        """
      <section class="contact-card"><h2>GI LINK on GitHub</h2><p>Share a reproducible bug report or feature suggestion. Please avoid posting private links, personal information, or secrets in a public issue.</p><a class="button button-primary" href="https://github.com/ghalibkamal7/gilink/issues" target="_blank" rel="noopener noreferrer">Open the issue tracker <span aria-hidden="true">↗</span></a></section>
""",
    )


HOME_SCRIPTS = f'<script src="/static/app.js?v={ASSET_VERSION}" defer></script>'
SUBPAGE_SCRIPTS = f'<script src="/static/app.js?v={ASSET_VERSION}" defer></script>'
