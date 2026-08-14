/* Poverty in Space — Descriptives. Atlas-style grid: dataset × variable (→ optional sub-view) → all countries.
   window.DESC: tabs may carry `subs` (asinh/log, scatter/heat) and `temporal:true`. Folder = key or key_sub. */
(function () {
  "use strict";
  var D = window.DESC;
  if (!D) { document.getElementById("grid").innerHTML =
    "<p>Could not load manifest. Run <code>scripts/make_descriptives.py</code>.</p>"; return; }

  var state = { dataset: "v3", tab: "density", sub: null, region: "all" };
  function curTab(){ return D.tabs.filter(function(t){ return t.key===state.tab; })[0] || D.tabs[0]; }
  function tabIsTemporal(){ return !!curTab().temporal; }
  function tabSubs(){ return curTab().subs || null; }
  function folder(){ var t=curTab(); return (t.subs && state.sub) ? t.key + "_" + state.sub : t.key; }

  // ---- dataset seg ----
  var dsWrap = document.getElementById("dataset");
  D.datasets.forEach(function (d) {
    var b = document.createElement("button"); b.textContent = d.label; b._key = d.key;
    b.className = d.key === state.dataset ? "active" : "";
    b.onclick = function () { state.dataset = d.key; syncSeg(dsWrap, d.key); render(); };
    dsWrap.appendChild(b);
  });

  // ---- primary variable tabs ----
  var tabs = document.getElementById("desc-tabs");
  D.tabs.forEach(function (t) {
    var b = document.createElement("button"); b.setAttribute("role", "tab");
    b.textContent = t.label; b._key = t.key;
    b.className = t.key === state.tab ? "active" : "";
    b.onclick = function () {
      state.tab = t.key;
      state.sub = (t.subs && t.subs.length) ? t.subs[0].key : null;   // default to first sub-view
      syncTabs(); buildSubtabs(); render();
    };
    tabs.appendChild(b);
  });
  function syncTabs(){ [].forEach.call(tabs.children,function(b){ b.className = b._key===state.tab ? "active":""; }); }
  function syncSeg(g,key){ [].forEach.call(g.children,function(b){ b.classList.toggle("active", b._key===key); }); }

  // ---- secondary sub-view tabs (built per primary tab) ----
  var subWrap = document.getElementById("desc-subtabs");
  function buildSubtabs(){
    subWrap.innerHTML = "";
    var subs = tabSubs();
    if (!subs){ subWrap.hidden = true; return; }
    subWrap.hidden = false;
    subs.forEach(function(s){
      var b=document.createElement("button"); b.setAttribute("role","tab");
      b.textContent = s.label; b._key = s.key;
      b.className = s.key===state.sub ? "active":"";
      b.onclick = function(){ state.sub = s.key; syncSubtabs(); render(); };
      subWrap.appendChild(b);
    });
  }
  function syncSubtabs(){ [].forEach.call(subWrap.children,function(b){ b.className = b._key===state.sub ? "active":""; }); }

  // ---- region filter ----
  var present = D.regions.filter(function(r){ return D.countries.some(function(c){ return c.region===r; }); });
  var rf = document.getElementById("region-filter");
  [["all","All regions"]].concat(present.map(function(r){ return [r,r]; })).forEach(function(p){
    var b=document.createElement("button"); b.textContent=p[1]; b._key=p[0];
    b.className = p[0]===state.region ? "active":"";
    b.onclick=function(){ state.region=p[0]; syncSeg(rf,p[0]); render(); };
    rf.appendChild(b);
  });

  var dsRow = dsWrap.parentElement, note = document.getElementById("desc-note");
  var grid = document.getElementById("grid");

  function has(c){ return tabIsTemporal() ? c.temporal : c.datasets.indexOf(state.dataset) > -1; }
  function figPath(iso){
    return tabIsTemporal() ? "figures/descriptives/" + folder() + "/" + iso + ".png"
                           : "figures/descriptives/" + folder() + "/" + state.dataset + "/" + iso + ".png";
  }
  function dsLabel(k){ var d=D.datasets.filter(function(x){return x.key===k;})[0]; return d?d.label:k; }
  function tabLabel(){ var t=curTab(); var s=(t.subs&&state.sub)?" · "+(t.subs.filter(function(x){return x.key===state.sub;})[0]||{}).label:""; return t.label+s; }

  var visible = [];
  function currentList(){
    return D.countries.filter(function(c){ return (state.region==="all"||c.region===state.region) && has(c); });
  }
  function render(){
    var isTemp = tabIsTemporal();
    dsRow.style.opacity = isTemp ? 0.4 : 1;
    [].forEach.call(dsWrap.children,function(b){ b.disabled = isTemp; });
    note.hidden = !isTemp;
    if (isTemp) note.innerHTML = "<strong>Temporal persistence</strong> (2016 → 2023) uses the Google 2.5D panel — 12 countries. The Dataset selector doesn't apply.";

    visible = currentList();
    grid.innerHTML = "";
    if (!visible.length){ grid.innerHTML = '<p class="empty">No countries for this selection.</p>'; return; }
    visible.forEach(function(c,i){
      var card=document.createElement("div"); card.className="card";
      card.innerHTML =
        '<div class="card-img desc-thumb"><img loading="lazy" alt="'+c.name+' '+tabLabel()+'" src="'+figPath(c.iso)+'"></div>'+
        '<div class="card-body"><span class="card-name">'+c.name+'</span></div>';
      card.onclick=function(){ openLightbox(i); };
      grid.appendChild(card);
    });
  }

  // ---- lightbox ----
  var lb=document.getElementById("lightbox"), lbImg=document.getElementById("lb-img"),
      lbCap=document.getElementById("lb-cap"), lbDl=document.getElementById("lb-dl"), idx=0;
  function openLightbox(i){ idx=i; show(); lb.hidden=false; document.body.style.overflow="hidden"; }
  function show(){
    var c=visible[idx], isTemp=tabIsTemporal(), p=figPath(c.iso);
    lbImg.src=p; lbImg.alt=c.name+" "+tabLabel();
    lbCap.innerHTML="<strong>"+c.name+" — "+tabLabel()+"</strong>"+(isTemp?"2.5D 2016 → 2023":dsLabel(state.dataset))+" · "+c.region;
    lbDl.href=p; lbDl.download="povertyinspace_desc_"+c.iso+"_"+folder()+(isTemp?"":"_"+state.dataset)+".png";
  }
  function step(d){ idx=(idx+d+visible.length)%visible.length; show(); }
  function close(){ lb.hidden=true; document.body.style.overflow=""; }
  document.getElementById("lb-close").onclick=close;
  document.getElementById("lb-prev").onclick=function(e){ e.stopPropagation(); step(-1); };
  document.getElementById("lb-next").onclick=function(e){ e.stopPropagation(); step(1); };
  lb.onclick=function(e){ if(e.target===lb) close(); };
  document.addEventListener("keydown",function(e){
    if(lb.hidden) return;
    if(e.key==="Escape") close(); else if(e.key==="ArrowLeft") step(-1); else if(e.key==="ArrowRight") step(1);
  });

  // init: default primary tab's first sub-view
  var t0 = curTab(); state.sub = (t0.subs && t0.subs.length) ? t0.subs[0].key : null;
  buildSubtabs();
  render();
})();
