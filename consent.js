/* Cookie consent and ads, shared by the game and the site pages.
   Settings live in config.js (PG_CONFIG.ads):
     client    AdSense publisher ID ("ca-pub-…"). Empty = no ads: the ad spaces stay hidden.
     slots     AdSense ad unit IDs for each space: side (PC, beside the game), foot (PC, above the footer),
               rail (very wide screens), phone (phones, above the footer), page (site pages).
     cmp       "own" = this banner. "google" = the banner set up in AdSense > Privacy & messaging
               (Google-certified, needed for personalised ads in the EU/UK); this banner then stays off.
     h5        true once the site is accepted into H5 Games Ads: full-screen ads between Boosters.
     analytics Cloudflare Web Analytics token (no cookies, no consent needed). Empty = none.
   Add ?ads=preview to any address to see where the ad spaces are, without loading any ad. */
(function(){
  var CFG = (window.PG_CONFIG || {}).ads || {};
  var KEY = 'pg_consent', VERSION = 1, MAX_AGE = 180 * 864e5;   // ask again after 6 months
  var PREVIEW = /[?&]ads=preview\b/.test(location.search);
  var GOOGLE_CMP = CFG.cmp === 'google' && !!CFG.client;
  var waiting = [], decided = false, adsLoaded = false, blocked = false, banner = null;

  /* ---------- stored choice ---------- */
  function read(){
    try{
      var c = JSON.parse(localStorage.getItem(KEY));
      if(c && c.v === VERSION && Date.now() - c.at < MAX_AGE) return c;
    }catch(e){}
    return null;
  }
  function save(ads){
    var c = {v: VERSION, ads: !!ads, at: Date.now()};
    try{ localStorage.setItem(KEY, JSON.stringify(c)); }catch(e){}
    return c;
  }

  /* ---------- Google consent signals (Consent Mode v2) ---------- */
  window.dataLayer = window.dataLayer || [];
  function gtag(){ window.dataLayer.push(arguments); }
  gtag('consent', 'default', {ad_storage: 'denied', ad_user_data: 'denied', ad_personalization: 'denied', analytics_storage: 'denied', wait_for_update: 500});
  function signal(ads){
    var v = ads ? 'granted' : 'denied';
    gtag('consent', 'update', {ad_storage: v, ad_user_data: v, ad_personalization: v});
  }

  /* ---------- styles (banner and ad spaces) ---------- */
  var css = ''
  + '.adslot{margin:0 auto;text-align:center}'
  + '.adslot[hidden]{display:none!important}'
  + '.adslot .adlabel{display:block;font:600 11px/1.6 var(--body,system-ui,sans-serif);letter-spacing:.06em;text-transform:uppercase;color:var(--muted,#53647F)}'
  + '.adslot .adbox{margin:0 auto;max-width:100%;overflow:hidden}'
  + '.adslot ins.adsbygoogle{display:block;margin:0 auto}'
  + '.adslot:has(ins[data-ad-status="unfilled"]){display:none!important}'
  + '.adslot[data-ad="side"] .adbox{width:300px;height:250px}'
  + '.adslot[data-ad="foot"] .adbox{width:728px;height:90px}'
  + '.adslot[data-ad="rail"] .adbox{width:160px;height:600px}'
  + '.adslot[data-ad="phone"] .adbox{width:100%;max-width:336px;height:100px}'
  + '.adslot[data-ad="page"] .adbox{width:100%;min-height:100px}'
  + '.adslot[data-ad="side"],.adslot[data-ad="foot"],.adslot[data-ad="rail"]{display:none}'
  + '@media (min-width:1000px){.adslot[data-ad="side"],.adslot[data-ad="foot"]{display:block}.adslot[data-ad="phone"]{display:none}}'
  + '@media (min-width:1640px){.adslot[data-ad="rail"]{display:block}}'
  + '.adslot.preview .adbox{display:flex;align-items:center;justify-content:center;border:2px dashed var(--line,#B6C5DB);border-radius:12px;background:var(--surface-2,#EEF3FA);color:var(--muted,#53647F);font:700 14px/1.3 var(--body,system-ui,sans-serif);box-sizing:border-box}'
  + '.pgc{position:fixed;left:50%;transform:translateX(-50%);bottom:calc(var(--pgc-bottom,16px) + env(safe-area-inset-bottom,0px));z-index:60;width:min(560px,calc(100% - 24px));box-sizing:border-box;'
  +   'background:var(--surface,#fff);color:var(--ink,#13203D);border-radius:18px;padding:18px 18px 16px;box-shadow:0 18px 50px rgba(8,18,40,.35),inset 0 0 0 1.5px var(--line,#B6C5DB);'
  +   'font:15px/1.5 var(--body,system-ui,sans-serif);max-height:calc(100dvh - var(--pgc-bottom,16px) - 24px);overflow:auto;animation:pgcIn .25s ease-out}'
  + '@keyframes pgcIn{from{opacity:0;transform:translate(-50%,16px)}}'
  + '@media (prefers-reduced-motion:reduce){.pgc{animation:none}}'
  + '.pgc h2{margin:0 0 6px;font:800 19px/1.2 var(--display,system-ui,sans-serif);font-stretch:110%;border:0;padding:0}'
  + '.pgc p{margin:0 0 12px;font-size:14px;color:var(--ink,#13203D)}'
  + '.pgc a{color:inherit;text-decoration-color:var(--gold-deep,#D9A90E);text-underline-offset:2px}'
  + '.pgc .pgcrow{display:flex;gap:10px;flex-wrap:wrap}'
  + '.pgc .pgcrow button{flex:1 1 140px;min-height:46px;border-radius:12px;border:0;font:700 15px/1.2 var(--body,system-ui,sans-serif);cursor:pointer;'
  +   'background:var(--gold,#F2C230);color:#2E2300;box-shadow:inset 0 -3px 0 var(--gold-deep,#D9A90E)}'
  + '.pgc .pgcmore{display:block;margin:10px auto 0;background:none;border:0;padding:6px;font:600 14px/1.2 var(--body,system-ui,sans-serif);color:var(--muted,#53647F);text-decoration:underline;text-underline-offset:3px;cursor:pointer}'
  + '.pgc .pgcopts{margin:0 0 12px;display:flex;flex-direction:column;gap:8px}'
  + '.pgc .pgcopt{display:flex;gap:12px;align-items:flex-start;background:var(--surface-2,#EEF3FA);border-radius:12px;padding:10px 12px}'
  + '.pgc .pgcopt input{width:22px;height:22px;margin:2px 0 0;flex:none;accent-color:var(--gold-deep,#D9A90E)}'
  + '.pgc .pgcopt b{display:block;font-size:15px}'
  + '.pgc .pgcopt span{font-size:13px;color:var(--muted,#53647F)}'
  + '.pgc :focus-visible{outline:3px solid var(--focus,#2457D6);outline-offset:2px}'
  + '.pgchoices{background:none;border:0;padding:0;font:inherit;color:inherit;font-weight:700;cursor:pointer;text-decoration:none}'
  + '.pgchoices:hover{text-decoration:underline;text-decoration-color:var(--gold-deep,#D9A90E);text-underline-offset:3px}';
  var st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);

  /* ---------- ad spaces ---------- */
  function slots(){ return Array.prototype.slice.call(document.querySelectorAll('.adslot[data-ad]')); }
  var SIZES = {side: '300 × 250', foot: '728 × 90', rail: '160 × 600', phone: 'up to 336 × 100', page: 'responsive'};
  function visible(el){ return el.offsetParent !== null || getComputedStyle(el).position === 'fixed'; }
  function showSlots(){
    slots().forEach(function(el){
      var name = el.getAttribute('data-ad');
      if(PREVIEW){
        el.hidden = false; el.classList.add('preview');
        el.querySelector('.adbox').textContent = 'Ad space · ' + SIZES[name];
      }else if(CFG.client && (CFG.slots || {})[name] && !blocked){
        el.hidden = false;
      }
    });
  }
  function fillSlots(){
    if(!adsLoaded || blocked) return;
    slots().forEach(function(el){
      if(el.hidden || el.getAttribute('data-filled') || !visible(el)) return;
      var name = el.getAttribute('data-ad'), box = el.querySelector('.adbox');
      var ins = document.createElement('ins');
      ins.className = 'adsbygoogle';
      ins.setAttribute('data-ad-client', CFG.client);
      ins.setAttribute('data-ad-slot', CFG.slots[name]);
      if(name === 'page' || name === 'phone'){ ins.setAttribute('data-ad-format', name === 'page' ? 'auto' : 'horizontal'); ins.setAttribute('data-full-width-responsive', 'true'); ins.style.cssText = 'display:block;width:100%;height:100%'; }
      else ins.style.cssText = 'display:inline-block;width:100%;height:100%';
      box.appendChild(ins);
      el.setAttribute('data-filled', '1');
      try{ (window.adsbygoogle = window.adsbygoogle || []).push({}); }catch(e){}
    });
  }
  function loadAds(personal){
    if(adsLoaded || !CFG.client || PREVIEW) return;
    adsLoaded = true;
    window.adsbygoogle = window.adsbygoogle || [];
    if(!GOOGLE_CMP && !personal) window.adsbygoogle.requestNonPersonalizedAds = 1;
    var s = document.createElement('script');
    s.async = true; s.crossOrigin = 'anonymous';
    s.src = 'https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=' + encodeURIComponent(CFG.client);
    if(CFG.h5) s.setAttribute('data-ad-frequency-hint', '120s');
    s.onerror = function(){ blocked = true; slots().forEach(function(el){ if(!el.classList.contains('preview')) el.hidden = true; }); };
    document.head.appendChild(s);
    if(CFG.h5){ window.adBreak = window.adConfig = function(o){ window.adsbygoogle.push(o); }; window.adConfig({preloadAdBreaks: 'on'}); }
    fillSlots();
  }
  var rt = null;
  window.addEventListener('resize', function(){ clearTimeout(rt); rt = setTimeout(fillSlots, 300); });

  /* ---------- the banner ---------- */
  function el(tag, attrs, text){
    var e = document.createElement(tag);
    for(var k in attrs || {}) e.setAttribute(k, attrs[k]);
    if(text != null) e.textContent = text;
    return e;
  }
  function markDecided(){ if(decided) return; decided = true; var w = waiting; waiting = []; w.forEach(function(f){ try{ f(); }catch(e){} }); }
  function closeBanner(){ if(banner){ banner.remove(); banner = null; } }
  function decide(ads){
    var before = read(), c = save(ads);
    signal(c.ads);
    closeBanner();
    /* the ad library can't switch between personalised and not once loaded: reload to apply a change */
    if(adsLoaded && before && before.ads !== c.ads){ location.reload(); return; }
    loadAds(c.ads);
    markDecided();
  }
  function cookiesHref(){
    var a = document.querySelector('a[href$="privacy.html"]');
    return a ? a.getAttribute('href').replace('privacy.html', 'cookies.html') : 'cookies.html';
  }
  function openBanner(custom){
    closeBanner();
    var cur = read();
    banner = el('section', {'class': 'pgc', role: 'dialog', 'aria-modal': 'false', 'aria-labelledby': 'pgcT', 'aria-describedby': 'pgcD'});
    banner.appendChild(el('h2', {id: 'pgcT'}, 'Cookies and ads'));
    var p = el('p', {id: 'pgcD'});
    p.appendChild(document.createTextNode('PokeguessTCG is free thanks to ads. With your consent, Google and its partners use cookies to show ads based on your interests and to measure them. If you refuse, you\'ll still see ads, but not personalised ones. You can change your choice at any time from "Privacy choices" at the bottom of the page. '));
    var a = el('a', {href: cookiesHref()}, 'Cookie Policy'); p.appendChild(a); p.appendChild(document.createTextNode('.'));
    banner.appendChild(p);
    var box = null;
    if(custom){
      var opts = el('div', {'class': 'pgcopts'});
      var o1 = el('label', {'class': 'pgcopt'}); var c1 = el('input', {type: 'checkbox', checked: '', disabled: ''}); o1.appendChild(c1);
      var t1 = el('div'); t1.appendChild(el('b', null, 'Needed to play')); t1.appendChild(el('span', null, 'Your games, settings and sign-in, kept in this browser. Always on.')); o1.appendChild(t1);
      var o2 = el('label', {'class': 'pgcopt'}); box = el('input', {type: 'checkbox', id: 'pgcAds'}); if(cur && cur.ads) box.checked = true; o2.appendChild(box);
      var t2 = el('div'); t2.appendChild(el('b', null, 'Personalised ads')); t2.appendChild(el('span', null, 'Google and its partners use cookies to choose ads based on your interests and to measure them.')); o2.appendChild(t2);
      opts.appendChild(o1); opts.appendChild(o2); banner.appendChild(opts);
    }
    var row = el('div', {'class': 'pgcrow'});
    var no = el('button', {type: 'button', 'data-c': 'reject'}, 'Reject all');
    var yes = el('button', {type: 'button', 'data-c': 'accept'}, 'Accept all');
    no.onclick = function(){ decide(false); };
    yes.onclick = function(){ decide(true); };
    row.appendChild(no); row.appendChild(yes); banner.appendChild(row);
    var more = el('button', {type: 'button', 'class': 'pgcmore', 'data-c': custom ? 'save' : 'custom'}, custom ? 'Save my choices' : 'Customise');
    more.onclick = custom ? function(){ decide(box.checked); } : function(){ openBanner(true); };
    banner.appendChild(more);
    document.body.insertBefore(banner, document.body.firstChild);
    if(custom) box.focus();
  }

  /* ---------- "Privacy choices" links ---------- */
  function openChoices(){
    if(GOOGLE_CMP){
      window.googlefc = window.googlefc || {}; window.googlefc.callbackQueue = window.googlefc.callbackQueue || [];
      window.googlefc.callbackQueue.push(function(){ window.googlefc.showRevocationMessage(); });
    }else openBanner(true);
  }
  document.addEventListener('click', function(e){
    var b = e.target.closest && e.target.closest('[data-privacy-choices]');
    if(b){ e.preventDefault(); openChoices(); }
  });

  /* ---------- analytics without cookies ---------- */
  if(CFG.analytics && !PREVIEW){
    var cf = document.createElement('script'); cf.defer = true;
    cf.src = 'https://static.cloudflareinsights.com/beacon.min.js';
    cf.setAttribute('data-cf-beacon', JSON.stringify({token: CFG.analytics}));
    document.head.appendChild(cf);
  }

  /* ---------- start ---------- */
  function start(){
    showSlots();
    if(GOOGLE_CMP){ markDecided(); loadAds(true); return; }
    var c = read();
    if(c){ signal(c.ads); loadAds(c.ads); markDecided(); }
    else openBanner(false);
  }
  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();

  window.PG_ADS = {
    /* run f once the visitor has answered the banner (straight away if they already had) */
    whenDecided: function(f){ if(decided) f(); else waiting.push(f); },
    openChoices: openChoices,
    /* full-screen ad between games (H5 Games Ads), then go on; without it, go on straight away */
    adBreak: function(name, then){
      if(!(CFG.h5 && adsLoaded && !blocked && typeof window.adBreak === 'function')){ then(); return; }
      var done = false, t = setTimeout(go, 4000);   // no answer from the ad library: never leave the player stuck
      function go(){ clearTimeout(t); if(!done){ done = true; then(); } }
      try{ window.adBreak({type: 'next', name: name, beforeAd: function(){ clearTimeout(t); }, adBreakDone: go}); }catch(e){ go(); }
    }
  };
})();
