import pathlib
import shutil
import streamlit as st

GA_SCRIPT = """
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-Z8WYXRFL78"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'G-Z8WYXRFL78');
</script>
<!-- Recover from stale code-split chunks after a redeploy -->
<script id="chunk_reload_handler">
  (function () {
    // After a deploy, a cached index.html may reference JS chunk hashes
    // that no longer exist on the server, throwing "Failed to fetch
    // dynamically imported module". Reload once to pull fresh HTML.
    // Guard with a short cooldown so a genuinely broken deploy can't loop.
    function shouldReload() {
      try {
        var last = parseInt(sessionStorage.getItem('chunk_reload_at') || '0', 10);
        if (Date.now() - last < 10000) return false;   // reloaded < 10s ago
        sessionStorage.setItem('chunk_reload_at', String(Date.now()));
        return true;
      } catch (e) {
        return true;
      }
    }
    function isChunkError(msg) {
      msg = msg || '';
      return msg.indexOf('Failed to fetch dynamically imported module') !== -1 ||
             msg.indexOf('Importing a module script failed') !== -1 ||
             msg.indexOf('error loading dynamically imported module') !== -1;
    }
    window.addEventListener('unhandledrejection', function (event) {
      var msg = (event && event.reason && event.reason.message) || '';
      if (isChunkError(msg) && shouldReload()) {
        console.warn('Stale chunk detected - reloading for fresh assets.');
        window.location.reload();
      }
    });
    window.addEventListener('error', function (event) {
      if (isChunkError(event && event.message) && shouldReload()) {
        console.warn('Stale chunk detected - reloading for fresh assets.');
        window.location.reload();
      }
    });
  })();
</script>
"""


def inject_ga():

    index_path = pathlib.Path(st.__file__).parent / "static" / "index.html"
    bck_index = index_path.with_suffix('.bck')

    # Keep a pristine copy of Streamlit's original index.html the first time we
    # run, then always re-derive from it. This makes injection idempotent: no
    # matter how many times this runs, the result is the clean file + exactly
    # one copy of our scripts.
    if not bck_index.exists():
        shutil.copy(index_path, bck_index)

    html = bck_index.read_text()
    new_html = html.replace('<head>', '<head>\n' + GA_SCRIPT)
    index_path.write_text(new_html)


inject_ga()
