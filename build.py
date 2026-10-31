#!/usr/bin/env python3
"""Build the static rozkalns.design site from the design sources in src/.

Each src/*.dc.html is a page designed on the Claude Design canvas. This script
turns it into a plain HTML page with clean URLs, relative links, meta tags,
hreflang alternates and a small shared script. Output goes to dist/.

    python3 build.py            # production build into dist/
    python3 build.py --preview  # file-friendly build into preview/
"""
import os, re, shutil, html, sys
EXPLICIT = '--preview' in sys.argv  # link to .../index.html so the site works without a web server

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, 'src')
DIST = os.path.join(ROOT, 'preview' if EXPLICIT else 'dist')
DOMAIN = 'https://rozkalns.design'

SLUGS = {
    'IOS': 'instructor-operating-station', 'LoftHUB': 'lofthub', 'Brand': 'loft-dynamics-website-and-brand',
    'DNB': 'dnb', 'BankOfLatvia': 'bank-of-latvia', 'Vivi': 'vivi', 'Metrohm': 'metrohm', 'Roche': 'roche',
    'Theapolis': 'theapolis', 'HRG': 'human-rights-guide', 'Asya': 'asya', 'IIHF': 'iihf', 'Apple': 'apple-tv',
}

def route(name):
    """src file name -> site path (without language prefix), e.g. 'work/lofthub/'."""
    base = name.replace('-DE.dc.html', '').replace('.dc.html', '')
    if base == 'V4': return ''
    if base in ('Work', 'Approach', 'About', 'Contact', 'Imprint', 'Privacy', 'Reference'): return base.lower() + '/'
    m = re.match(r'Case-(\w+)$', base)
    return 'work/%s/' % SLUGS[m.group(1)]

def url_for(name):
    lang = 'de/' if name.endswith('-DE.dc.html') else ''
    return lang + route(name)

def rel(from_url, to_url):
    depth = from_url.count('/')
    return ('../' * depth or './') + to_url if to_url else ('../' * depth or './')

# YouTube embeds load only on click (privacy: nothing third-party until then)
YT_SCRIPT = '''
<script>
document.addEventListener('click',function(e){var b=e.target.closest('[data-yt]');if(!b)return;
var f=document.createElement('iframe');f.src='https://www.youtube-nocookie.com/embed/'+b.dataset.yt+'?autoplay=1&rel=0';
f.title=b.dataset.title||'Video';f.allow='autoplay; encrypted-media; picture-in-picture; fullscreen';f.allowFullscreen=true;
f.style.cssText='position:absolute;inset:0;width:100%;height:100%;border:0';b.parentNode.replaceChildren(f);});
</script>'''

MOTION_SCRIPT = '''
<script>
// every looping video gets a pause button; the choice is shared by all videos and remembered across pages
(function () {
  var vids = [].slice.call(document.querySelectorAll('video[loop]')); if (!vids.length) return;
  var de = document.documentElement.lang === 'de';
  var get = function () { try { return localStorage.getItem('rz-motion') === 'paused'; } catch (e) { return false; } };
  var paused = get(); window.rzPaused = function () { return paused; };
  var P = '<svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true"><path d="M4 2v10M10 2v10" stroke="#eeede9" stroke-width="2"/></svg>';
  var Y = '<svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true"><path d="M3.5 2l8 5-8 5z" fill="none" stroke="#eeede9" stroke-width="1.5" stroke-linejoin="round"/></svg>';
  var btns = [];
  var paint = function () { btns.forEach(function (b) { b.innerHTML = paused ? Y : P; b.setAttribute('aria-label', paused ? (de ? 'Videos abspielen' : 'Play videos') : (de ? 'Videos pausieren' : 'Pause videos')); b.setAttribute('aria-pressed', paused ? 'true' : 'false'); }); };
  var apply = function () { document.documentElement.classList.toggle('rz-paused', paused); vids.forEach(function (v) { if (paused) v.pause(); else if (v.dataset.inview !== '0') v.play().catch(function () {}); }); paint(); };
  vids.forEach(function (v) {
    var b = document.createElement('button'); b.type = 'button'; b.className = 'vctl';
    var link = v.closest('a'), host = link ? link.parentElement : v.parentElement;
    if (getComputedStyle(host).position === 'static') host.style.position = 'relative';
    if (v.classList.contains('hero-video')) { b.classList.add('vctl-hero'); var bar = host.querySelector('.bar'); var lift = function () { b.style.bottom = ((bar ? bar.offsetHeight : 0) + 16) + 'px'; }; lift(); window.addEventListener('resize', lift); window.addEventListener('load', lift); }
    if (link) { var place = function () { b.style.top = (link.offsetTop + link.offsetHeight - 52) + 'px'; b.style.left = (link.offsetLeft + link.offsetWidth - 52) + 'px'; b.style.right = 'auto'; b.style.bottom = 'auto'; }; place(); window.addEventListener('resize', place); window.addEventListener('load', place); }
    b.addEventListener('click', function () { paused = !paused; try { localStorage.setItem('rz-motion', paused ? 'paused' : 'play'); } catch (e) {} apply(); });
    host.appendChild(b); btns.push(b);
  });
  apply();
})();
</script>'''

MEET_SCRIPT = '''
<style>
.meet-ov{position:fixed;inset:0;z-index:200;background:#121211;display:flex;align-items:center;justify-content:center}
.meet-ov[hidden]{display:none !important}
.meet-bg,.meet-bg img,.meet-bg video{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;border-radius:0 !important}
.meet-bg::after{content:"";position:absolute;inset:0;background:rgba(18,18,17,.55)}
.meet-stage{position:relative;height:min(86vh,86svh,calc((100vw - 32px) * 16 / 9));aspect-ratio:9/16;border-radius:12px;overflow:hidden;background:#1c1c1b}
.meet-stage video{width:100%;height:100%;object-fit:cover;display:block;background:#000}
.meet-stage .ph{position:absolute;inset:0;padding:24px;text-align:center;font-family:"Geist Mono",ui-monospace,Menlo,monospace;font-size:13px;line-height:1.5;color:#8c8c89;border-radius:12px}
.meet-x{position:absolute;top:16px;right:16px;width:44px;height:44px;border:0;border-radius:8px;background:rgba(18,18,17,.78);cursor:pointer;display:flex;align-items:center;justify-content:center}
.meet-x:focus-visible{outline:2px solid #eeede9;outline-offset:2px}
@media (prefers-reduced-motion:reduce){.meet-bg video{display:none}}
</style>
<script>
// intro video: the card previews 2 s muted, then stops and shows the play button; play opens a portrait player over the blurred loop
(function () {
  var cards = [].slice.call(document.querySelectorAll('.meet')); if (!cards.length) return;
  var de = document.documentElement.lang === 'de';
  var still = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var paused = function () { return document.documentElement.classList.contains('rz-paused'); };
  var X = '<svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true"><path d="M3 3l14 14M17 3L3 17" stroke="#eeede9" stroke-width="1.5"/></svg>';
  cards.forEach(function (card) {
    var frame = card.querySelector('.meet-frame'), btn = card.querySelector('.meet-play'), d = card.dataset;
    var ready = d.ready === '1';
    if (ready) {
      var v = document.createElement('video'); v.muted = true; v.playsInline = true; v.setAttribute('playsinline', ''); v.preload = 'auto'; v.src = d.mv; if (d.mp) v.poster = d.mp; v.setAttribute('aria-hidden', 'true');
      var ph = frame.querySelector('.ph'); if (ph) ph.remove(); frame.insertBefore(v, btn);
      if (!still && 'IntersectionObserver' in window) {
        card.classList.add('previewing');
        var done = function () { v.pause(); card.classList.remove('previewing'); };
        v.addEventListener('timeupdate', function () { if (v.currentTime >= 2) done(); });
        var io = new IntersectionObserver(function (es) { es.forEach(function (e) { if (e.isIntersecting && e.intersectionRatio >= .5) { io.disconnect(); if (paused()) done(); else v.play().catch(done); } }); }, { threshold: [.5] });
        io.observe(card);
      }
    }
    var ov, last;
    var close = function () { if (!ov) return; var pv = ov.querySelector('.meet-stage video'); if (pv) pv.pause(); var bv = ov.querySelector('.meet-bg video'); if (bv) bv.pause(); ov.hidden = true; document.documentElement.style.overflow = ''; if (last) last.focus(); };
    var open = function () {
      last = document.activeElement;
      if (!ov) {
        ov = document.createElement('div'); ov.className = 'meet-ov'; ov.hidden = true; ov.setAttribute('role', 'dialog'); ov.setAttribute('aria-modal', 'true'); ov.setAttribute('aria-label', btn.textContent.trim());
        var bg = '<div class="meet-bg" aria-hidden="true"><img src="' + d.blurp + '" alt="">' + (still ? '' : '<video src="' + d.blur + '" muted loop playsinline></video>') + '</div>';
        var stage = ready ? '<video controls playsinline' + (d.mp ? ' poster="' + d.mp + '"' : '') + ' src="' + d.mv + '">' + (d.mt ? '<track kind="captions" src="' + d.mt + '" srclang="' + (de ? 'de' : 'en') + '" label="' + (de ? 'Deutsch' : 'English') + '" default>' : '') + '</video>' : card.querySelector('.meet-ph-big').outerHTML.replace('meet-ph-big', 'ph').replace(' hidden', '');
        ov.innerHTML = bg + '<div class="meet-stage">' + stage + '</div><button type="button" class="meet-x" aria-label="' + (de ? 'Schliessen' : 'Close') + '">' + X + '</button>';
        document.body.appendChild(ov);
        ov.querySelector('.meet-x').addEventListener('click', close);
        ov.addEventListener('click', function (e) { if (e.target === ov || e.target.closest('.meet-bg')) close(); });
        ov.addEventListener('keydown', function (e) {
          if (e.key === 'Escape') close();
          if (e.key === 'Tab') { var f = [].slice.call(ov.querySelectorAll('button,video[controls]')); var i = f.indexOf(document.activeElement); if (e.shiftKey && i <= 0) { e.preventDefault(); f[f.length - 1].focus(); } else if (!e.shiftKey && i === f.length - 1) { e.preventDefault(); f[0].focus(); } }
        });
      }
      ov.hidden = false; document.documentElement.style.overflow = 'hidden';
      var bv = ov.querySelector('.meet-bg video'); if (bv && !paused()) bv.play().catch(function () {});
      var pv = ov.querySelector('.meet-stage video'); if (pv) { pv.currentTime = 0; pv.muted = false; pv.play().catch(function () {}); }
      ov.querySelector('.meet-x').focus();
    };
    btn.addEventListener('click', open);
    frame.addEventListener('click', function (e) { if (e.target !== btn && !btn.contains(e.target)) open(); });
  });
})();
</script>'''

FIT_SCRIPT = '''
<style>.fitw :is(h1,h2,h3,h4,dd,p,.disp,.ttl){overflow-wrap:normal}.item>.txt{min-width:0;max-width:100%}</style>
<script>
// no hyphenation: a word that is too wide for its box makes the text a little smaller instead of breaking
(function () {
  var root = document.documentElement; root.classList.add('fitw');
  var els = [].slice.call(document.querySelectorAll('main :is(h1,h2,h3,h4,dd,p,.disp,.ttl), footer :is(h1,h2,h3,p)'));
  var fit = function () {
    els.forEach(function (e) {
      e.style.fontSize = '';
      if (!e.offsetWidth || e.scrollWidth <= e.clientWidth + 1) return;
      var s = parseFloat(getComputedStyle(e).fontSize), n = 0;
      while (e.scrollWidth > e.clientWidth + 1 && n++ < 30) { s *= .96; e.style.fontSize = s + 'px'; }
    });
    // section headings on one page share one size: the smallest one that fits
    var secs = [].slice.call(document.querySelectorAll('main h2.sec')).filter(function (e) { return e.offsetWidth; });
    var min = Math.min.apply(null, secs.map(function (e) { return parseFloat(getComputedStyle(e).fontSize); }));
    secs.forEach(function (e) { if (parseFloat(getComputedStyle(e).fontSize) > min + .1) e.style.fontSize = min + 'px'; });
  };
  var t; window.addEventListener('resize', function () { clearTimeout(t); t = setTimeout(fit, 120); });
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(fit); fit();
})();
</script>'''

MNAV_SCRIPT = '''
<script>
// mobile: the menu hides behind a two-line button and opens full screen; the lines turn into an X
(function () {
  var head = document.querySelector('header.head'); if (!head) return;
  var de = document.documentElement.lang === 'de';
  var L = de ? ['Menü öffnen', 'Menü schliessen'] : ['Open menu', 'Close menu'];
  var mk = function () { var b = document.createElement('button'); b.type = 'button'; b.className = 'burger'; b.setAttribute('aria-label', L[0]); b.setAttribute('aria-expanded', 'false'); b.setAttribute('aria-controls', 'mnav'); b.innerHTML = '<span></span><span></span>'; return b; };
  head.appendChild(mk());
  var nav = head.querySelector('nav.main'), lang = head.querySelector('div > a[lang]'), who = head.querySelector('.who a');
  var o = document.createElement('div'); o.id = 'mnav'; o.className = 'mnav'; o.setAttribute('role', 'dialog'); o.setAttribute('aria-modal', 'true'); o.setAttribute('aria-label', de ? 'Menü' : 'Menu'); o.hidden = true;
  var row = document.createElement('div'); row.className = 'mrow';
  if (who) { var w = who.cloneNode(true); w.className = 'mwho'; w.removeAttribute('style'); row.appendChild(w); }
  var x = mk(); x.setAttribute('aria-label', L[1]); x.setAttribute('aria-expanded', 'true'); row.appendChild(x); o.appendChild(row);
  var list = document.createElement('nav'); list.className = 'mlinks'; list.setAttribute('aria-label', de ? 'Hauptnavigation' : 'Main');
  if (nav) nav.querySelectorAll('a').forEach(function (a) { var c = a.cloneNode(true); c.removeAttribute('style'); list.appendChild(c); });
  o.appendChild(list);
  if (lang) { var l = lang.cloneNode(true); l.className = 'mlang'; l.removeAttribute('style'); o.appendChild(l); }
  document.body.appendChild(o);
  var opener = null;
  var open = function (btn) { opener = btn; o.hidden = false; document.documentElement.classList.add('mnav-open'); requestAnimationFrame(function () { requestAnimationFrame(function () { o.classList.add('open'); }); }); document.querySelectorAll('.burger').forEach(function (b) { if (b !== x) b.setAttribute('aria-expanded', 'true'); }); setTimeout(function () { x.focus(); }, 50); };
  var close = function () { o.classList.remove('open'); document.documentElement.classList.remove('mnav-open'); document.querySelectorAll('.burger').forEach(function (b) { if (b !== x) b.setAttribute('aria-expanded', 'false'); }); setTimeout(function () { o.hidden = true; }, 350); if (opener && opener.offsetParent) opener.focus(); };
  document.addEventListener('click', function (e) { var b = e.target.closest('.burger'); if (!b) return; if (b === x) close(); else open(b); });
  o.addEventListener('click', function (e) { if (e.target.closest('.mlinks a, .mlang, .mwho')) close(); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && o.classList.contains('open')) close(); });
  window.addEventListener('resize', function () { if (window.innerWidth > 768 && o.classList.contains('open')) close(); });
})();
</script>'''

PIN_SCRIPT = '''
<script>
// scrolling up brings the menu back as a bar pinned to the top; scrolling down hides it again
(function () {
  var head = document.querySelector('header.head'); if (!head) return;
  var bar = document.createElement('div'); bar.className = 'pinbar'; bar.setAttribute('aria-hidden', 'true'); bar.inert = true;
  var c = head.cloneNode(true); c.removeAttribute('id'); c.querySelectorAll('[id]').forEach(function (n) { n.removeAttribute('id'); });
  c.style.position = 'static'; var cs = getComputedStyle(head.parentNode); ['fontFamily', 'fontSize', 'lineHeight', 'letterSpacing', 'color', 'fontFeatureSettings'].forEach(function (k) { bar.style[k] = cs[k]; }); bar.appendChild(c); document.body.appendChild(bar);
  var last = window.scrollY, shown = false;
  var set = function (v) { if (v === shown) return; shown = v; bar.classList.toggle('on', v); bar.inert = !v; if (v) bar.removeAttribute('aria-hidden'); else bar.setAttribute('aria-hidden', 'true'); };
  window.addEventListener('scroll', function () {
    var y = window.scrollY, past = y > head.offsetTop + head.offsetHeight, d = y - last;
    if (!past) set(false); else if (d < -4) set(true); else if (d > 4) set(false);
    if (Math.abs(d) > 4) last = y;
  }, { passive: true });
})();
</script>'''

TOP_SCRIPT = '''<script>
(function () {
  // a link to a page always opens it at the top (back/forward keeps the browser's own position)
  var nav = performance.getEntriesByType && performance.getEntriesByType('navigation')[0];
  if (location.hash || (nav && nav.type === 'back_forward')) return;
  if ('scrollRestoration' in history) history.scrollRestoration = 'manual';
  var top = function () { var d = document.documentElement; d.style.scrollBehavior = 'auto'; window.scrollTo(0, 0); try { d.scrollIntoView({ block: 'start', behavior: 'instant' }); } catch (e) {} d.style.scrollBehavior = ''; };
  var moved = false; ['wheel', 'touchstart', 'keydown'].forEach(function (e) { window.addEventListener(e, function () { moved = true; }, { once: true, passive: true }); });
  top(); window.addEventListener('load', function () { if (!moved) top(); });
})();

// photos marked data-fade fade in once loaded
(function () {
  document.querySelectorAll('img[data-fade]').forEach(function (img) {
    var show = function () { requestAnimationFrame(function () { img.classList.add('in'); }); };
    if (img.complete && img.naturalWidth) show(); else { img.addEventListener('load', show); img.addEventListener('error', show); }
  });
})();
// videos start only when they scroll into view, and pause when they leave it
(function () {
  var vids = document.querySelectorAll('video.loop');
  if (!vids.length) return;
  var still = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  vids.forEach(function (v) { v.removeAttribute('autoplay'); v.autoplay = false; try { v.pause(); } catch (e) {} });
  if (still) return;
  if (!('IntersectionObserver' in window)) { vids.forEach(function (v) { v.play().catch(function () {}); }); return; }
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (en) {
      var v = en.target;
      v.dataset.inview = en.isIntersecting ? '1' : '0';
      if (en.isIntersecting) { if (!v.dataset.started) { v.dataset.started = '1'; try { v.currentTime = 0; } catch (e) {} } if (!(window.rzPaused && window.rzPaused())) v.play().catch(function () {}); }
      else v.pause();
    });
  }, { threshold: 0.35 });
  vids.forEach(function (v) { io.observe(v); });
})();
</script>'''

SCRIPT = '''<script>
(function () {
  // a link to a page always opens it at the top (back/forward keeps the browser's own position)
  var nav = performance.getEntriesByType && performance.getEntriesByType('navigation')[0];
  if (location.hash || (nav && nav.type === 'back_forward')) return;
  if ('scrollRestoration' in history) history.scrollRestoration = 'manual';
  var top = function () { var d = document.documentElement; d.style.scrollBehavior = 'auto'; window.scrollTo(0, 0); try { d.scrollIntoView({ block: 'start', behavior: 'instant' }); } catch (e) {} d.style.scrollBehavior = ''; };
  var moved = false; ['wheel', 'touchstart', 'keydown'].forEach(function (e) { window.addEventListener(e, function () { moved = true; }, { once: true, passive: true }); });
  top(); window.addEventListener('load', function () { if (!moved) top(); });
})();

// photos marked data-fade fade in once loaded
(function () {
  document.querySelectorAll('img[data-fade]').forEach(function (img) {
    var show = function () { requestAnimationFrame(function () { img.classList.add('in'); }); };
    if (img.complete && img.naturalWidth) show(); else { img.addEventListener('load', show); img.addEventListener('error', show); }
  });
})();
// videos start only when they scroll into view, and pause when they leave it
(function () {
  var vids = document.querySelectorAll('video.loop');
  if (!vids.length) return;
  var still = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  vids.forEach(function (v) { v.removeAttribute('autoplay'); v.autoplay = false; try { v.pause(); } catch (e) {} });
  if (still) return;
  if (!('IntersectionObserver' in window)) { vids.forEach(function (v) { v.play().catch(function () {}); }); return; }
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (en) {
      var v = en.target;
      v.dataset.inview = en.isIntersecting ? '1' : '0';
      if (en.isIntersecting) { if (!v.dataset.started) { v.dataset.started = '1'; try { v.currentTime = 0; } catch (e) {} } if (!(window.rzPaused && window.rzPaused())) v.play().catch(function () {}); }
      else v.pause();
    });
  }, { threshold: 0.35 });
  vids.forEach(function (v) { io.observe(v); });
})();
document.querySelectorAll('[data-track-wrap]').forEach(function (wrap) {
  var track = wrap.querySelector('[data-track]');
  wrap.querySelectorAll('[data-step]').forEach(function (b) {
    b.addEventListener('click', function () { track.scrollBy({ left: (+wrap.dataset.trackWrap || 340) * +b.dataset.step, behavior: 'smooth' }); });
  });
});
</script>'''

def convert(name, src):
    me = url_for(name)
    de = name.endswith('-DE.dc.html')
    lang = 'de' if de else 'en'
    title = re.search(r'<title>(.*?)</title>', src).group(1)
    if name.startswith('V4'):
        title = 'Markus Rozkalns — ' + ('KI-beschleunigter UX/UI Designer' if de else 'AI-accelerated UX/UI designer')
    helmet = re.search(r'<helmet>([\s\S]*?)</helmet>', src).group(1).strip()
    # self-hosted fonts instead of Google Fonts (no third-party requests)
    fp = '../' * me.count('/')
    helmet = re.sub(r'<link[^>]*fonts\.googleapis\.com[^>]*>\n?', '', helmet)
    helmet = (f'<link rel="preload" href="{fp}fonts/Geist-Regular.woff2" as="font" type="font/woff2" crossorigin>\n<style>\n' +
              ''.join(f'@font-face{{font-family:"{fam}";src:url("{fp}fonts/{file}.woff2") format("woff2");font-weight:{w};font-style:normal;font-display:swap}}\n'
                      for fam, file, w in [('Geist', 'Geist-Regular', 400), ('Geist', 'Geist-Medium', 500), ('Geist Mono', 'GeistMono-Regular', 400), ('Geist Mono', 'GeistMono-Medium', 500)]) +
              '.js img[data-fade]{opacity:0;transition:opacity .9s ease}.js img[data-fade].in{opacity:1}@media (prefers-reduced-motion:reduce){.js img[data-fade]{opacity:1;transition:none}}\n' +
              '.skip{position:absolute;left:16px;top:-80px;z-index:100;background:#eeede9;color:#121211 !important;padding:10px 16px;border-radius:8px;font-size:16px;background-image:none !important}.skip:focus{top:16px}main:focus{outline:none}\n' +
              '.vctl{position:absolute;right:16px;bottom:16px;z-index:4;width:40px;height:40px;display:flex;align-items:center;justify-content:center;padding:0;border:1px solid rgba(238,237,233,.3);border-radius:8px;background:transparent;cursor:pointer;transition:border-color .3s ease}.vctl:hover{border-color:#eeede9}.vctl:focus-visible{outline:2px solid #eeede9;outline-offset:3px}.vctl-hero{right:16px;left:auto}@media (prefers-reduced-motion:reduce){.vctl{display:none}}\n' +
              '.burger{display:none;position:relative;width:44px;height:44px;margin:-10px -10px -10px 0;padding:0;border:0;background:none;cursor:pointer;-webkit-tap-highlight-color:transparent}.burger span{position:absolute;left:10px;right:10px;height:1.5px;background:#eeede9;transition:transform .35s cubic-bezier(.2,.7,.2,1)}.burger span:nth-child(1){top:18px}.burger span:nth-child(2){top:25px}.burger:focus-visible{outline:2px solid #eeede9;outline-offset:2px}' +
              '.mnav[hidden]{display:none !important}.mnav{position:fixed;inset:0;z-index:80;background:#121211;color:#eeede9;font-family:"Geist","Helvetica Neue",Helvetica,Arial,sans-serif;font-size:18px;line-height:1.5;display:flex;flex-direction:column;padding:20px 16px 32px;opacity:0;transition:opacity .3s ease;overflow-y:auto}.mnav.open{opacity:1}.mnav .mrow{display:flex;justify-content:space-between;align-items:center}.mnav .burger{display:block}.mnav.open .burger span:nth-child(1){transform:translateY(3.5px) rotate(45deg)}.mnav.open .burger span:nth-child(2){transform:translateY(-3.5px) rotate(-45deg)}' +
              '.mnav .mwho{font-weight:500;font-size:22px;letter-spacing:-.015em;background-image:none;padding-bottom:0}.mnav .mlinks{display:flex;flex-direction:column;align-items:flex-start;gap:14px;margin-top:88px}.mnav .mlinks a{font-weight:500;font-size:52px;line-height:1.05;letter-spacing:-.04em;--t:2px}.mnav .mlang{margin-top:auto;align-self:flex-start;font-size:20px;color:#a3a3a3}.mnav-open,.mnav-open body{overflow:hidden}' +
              '@media (max-width:768px){header.head{display:flex !important;justify-content:space-between;align-items:center;padding:20px 16px !important}header.head>div:first-child,header.head nav.main{display:none !important}header.head .who{margin:0 !important}header.head .burger{display:block}.band>.sticky{margin-bottom:64px !important}}' +
              '@media (prefers-reduced-motion:reduce){.mnav,.burger span{transition:none}}\n' +
              '.pinbar{position:fixed;top:0;left:0;right:0;z-index:50;background:#121211;transform:translateY(-100%);transition:transform .5s cubic-bezier(.2,.7,.2,1)}.pinbar.on{transform:none}@media (prefers-reduced-motion:reduce){.pinbar{transition:none}}\n' +
              '</style>\n' + helmet)
    body = src[src.index('</helmet>') + 9:src.index('</x-dc>')].strip()
    # description: first lead sentence on the page, else the home intro
    m = re.search(r'class="lead[^"]*"[^>]*>(.*?)</p>', body) or re.search(r'id="intro"[\s\S]*?<p[^>]*>(.*?)</p>', body)
    desc = html.unescape(re.sub(r'<[^>]+>', '', m.group(1))).strip() if m else ''
    # canvas-only bindings -> plain attributes
    body = body.replace('ref="{{trackRef}}"', 'data-track').replace('ref="{{galleryRef}}"', 'data-track')
    body = body.replace('onClick="{{gPrev}}"', 'data-step="-1"').replace('onClick="{{gNext}}"', 'data-step="1"')
    body = body.replace('onClick="{{prev}}"', 'data-step="-1"').replace('onClick="{{next}}"', 'data-step="1"')
    body = body.replace('<section id="approach" ', '<section id="approach" data-track-wrap ', 1)
    # internal links
    def link(mm):
        target, anchor = mm.group(1), mm.group(2) or ''
        return 'href="%s%s%s"' % (rel(me, url_for(target)), 'index.html' if EXPLICIT else '', anchor)
    body = re.sub(r'href="((?:V4|Work|About|Approach|Contact|Imprint|Privacy|Reference|Case-\w+?)(?:-DE)?\.dc\.html)(#[^"]*)?"', link, body)
    # hero fills the viewport on the real site (the canvas previews it at 900px)
    body = body.replace('<section id="top" style="position: relative; height: 900px;', '<section id="top" style="position: relative; height: 100vh; height: 100svh; min-height: 560px;')
    # strip autoplay: videos start when scrolled into view (script below)
    body = re.sub(r'(<video class="loop"[^>]*?) autoplay', r'\1', body)
    # lazy photos fade in once loaded (script below)
    body = re.sub(r'<img (?![^>]*data-fade)([^>]*loading="lazy")', r'<img data-fade \1', body)
    body = re.sub(r'(src|poster|data-m[vpt]|data-blurp?)="img/', lambda m: '%s="%simg/' % (m.group(1), '../' * me.count('/')), body)
    body = re.sub(r'href="files/', 'target="_blank" rel="noopener" href="%sfiles/' % ('../' * me.count('/')), body)
    # main landmark and a skip link (WCAG 2.4.1)
    if '<section id="top"' in body and body.index('<header') > body.index('<section id="top"'):
        body = body.replace('<section id="top"', '<main id="main">\n<section id="top"', 1)
        body = re.sub(r'(<h1 [^>]*class="[^"]*hero-h1)', r'\1" id="content" tabindex="-1" data-x="', body, count=1)
        skip = '#content'
    else:
        body = body.replace('</header>', '</header>\n<main id="main" tabindex="-1">', 1)
        skip = '#main'
    body = body.replace('<footer class="site-foot"', '</main>\n<footer class="site-foot"', 1)
    body = ('<a class="skip" href="%s">%s</a>\n' % (skip, 'Zum Inhalt springen' if de else 'Skip to content')) + body
    # external links open in a new tab
    body = re.sub(r'<a href="(https?://[^"]+)"', r'<a href="\1" target="_blank" rel="noopener"', body)
    other = name.replace('-DE.dc.html', '.dc.html') if de else name.replace('.dc.html', '-DE.dc.html')
    en_url, de_url = (url_for(other), me) if de else (me, url_for(other))
    head = f'''<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<script>document.documentElement.classList.add('js')</script>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{html.escape(desc, quote=True)}">
<meta name="theme-color" content="#121211">
<link rel="canonical" href="{DOMAIN}/{me}">
<link rel="alternate" hreflang="en" href="{DOMAIN}/{en_url}">
<link rel="alternate" hreflang="de" href="{DOMAIN}/{de_url}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{html.escape(desc, quote=True)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{DOMAIN}/{me}">
<meta property="og:image" content="{DOMAIN}/img/og.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{fp}favicon.ico" sizes="any">
<link rel="icon" type="image/png" href="{fp}img/favicon-32.png">
<link rel="apple-touch-icon" href="{fp}img/apple-touch-icon.png">
{helmet}
</head>
<body>
'''
    yt = YT_SCRIPT if 'data-yt' in body else ''
    yt += MEET_SCRIPT if 'class="meet"' in body else ''
    mo = MOTION_SCRIPT if re.search(r'<video[^>]* loop', body) else ''
    return head + body + '\n' + (SCRIPT if 'data-track' in body else TOP_SCRIPT) + FIT_SCRIPT + MNAV_SCRIPT + PIN_SCRIPT + mo + yt + '\n</body>\n</html>\n'

def main():
    if os.path.isdir(DIST): shutil.rmtree(DIST)
    for d in ('img', 'fonts', 'files'):
        if os.path.isdir(os.path.join(SRC, d)): shutil.copytree(os.path.join(SRC, d), os.path.join(DIST, d))
    names = sorted(n for n in os.listdir(SRC) if n.endswith('.dc.html'))
    for n in names:
        out = os.path.join(DIST, url_for(n), 'index.html')
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(os.path.join(SRC, n), encoding='utf-8') as f:
            page = convert(n, f.read())
        with open(out, 'w', encoding='utf-8') as f:
            f.write(page)
    nf = os.path.join(SRC, 'NotFound.html')
    if os.path.exists(nf):
        shutil.copy(nf, os.path.join(DIST, '404.html'))
    if os.path.exists(os.path.join(SRC, 'img', 'favicon.ico')):
        shutil.copy(os.path.join(SRC, 'img', 'favicon.ico'), os.path.join(DIST, 'favicon.ico'))
    urls = [url_for(n) for n in names]
    with open(os.path.join(DIST, 'sitemap.xml'), 'w') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for u in sorted(urls): f.write(f'  <url><loc>{DOMAIN}/{u}</loc></url>\n')
        f.write('</urlset>\n')
    with open(os.path.join(DIST, 'robots.txt'), 'w') as f:
        f.write(f'User-agent: *\nAllow: /\nSitemap: {DOMAIN}/sitemap.xml\n')
    print('built %d pages into %s/' % (len(names), os.path.basename(DIST)))

if __name__ == '__main__':
    main()
