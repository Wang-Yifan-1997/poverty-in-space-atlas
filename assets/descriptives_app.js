/* Poverty in Space — Descriptives. Atlas-style grid: dataset × variable → all countries. window.DESC. */
(function () {
  "use strict";
  var D = window.DESC;
  if (!D) { document.getElementById("grid").innerHTML =
    "<p>Could not load manifest. Run <code>scripts/make_descriptives.py</code>.</p>"; return; }

  var state = { dataset: "v3", tab: "density", region: "all" };
  function tabIsTemporal(){ return state.tab === "temporal"; }

  // ---- dataset seg ----
  var dsWrap = document.getElementById("dataset");
  D.datasets.forEach(function (d) {
    var b = document.createElement("button"); b.textContent = d.label; b._key = d.key;
    b.className = d.key === state.dataset ? "active" : "";
    b.onclick = function () { state.dataset = d.key; syncSeg(dsWrap, d.key); render(); };
    dsWrap.appendChild(b);
  });

  // ---- variable tabs ----
  var tabs = document.getElementById("desc-tabs");
  D.tabs.forEach(function (t) {
    var b = document.createElement("button"); b.setAttribute("role", "tab");
    b.textContent = t.label; b._key = t.key;
    b.className = t.key === state.tab ? "active" : "";
    b.onclick = function () { state.tab = t.key; syncTabs(); render(); };
    tabs.appendChild(b);
  });
  function syncTabs(){ [].forEach.call(tabs.children,function(b){ b.className = b._key===state.tab ? "active":""; }); }
  function syncSeg(g,key){ [].forEach.call(g.children,function(b){ b.classList.toggle("active", b._key===key); }); }

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
    return tabIsTemporal() ? "figures/descriptives/temporal/" + iso + ".png"
                           : "figures/descriptives/" + state.tab + "/" + state.dataset + "/" + iso + ".png";
  }
  function dsLabel(k){ var d=D.datasets.filter(function(x){return x.key===k;})[0]; return d?d.label:k; }
  function tabLabel(k){ var t=D.tabs.filter(function(x){return x.key===k;})[0]; return t?t.label:k; }

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
        '<div class="card-img desc-thumb"><img loading="lazy" alt="'+c.name+' '+tabLabel(state.tab)+'" src="'+figPath(c.iso)+'"></div>'+
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
    lbImg.src=p; lbImg.alt=c.name+" "+tabLabel(state.tab);
    lbCap.innerHTML="<strong>"+c.name+" — "+tabLabel(state.tab)+"</strong>"+(isTemp?"2.5D 2016 → 2023":dsLabel(state.dataset))+" · "+c.region;
    lbDl.href=p; lbDl.download="povertyinspace_desc_"+c.iso+"_"+state.tab+(isTemp?"":"_"+state.dataset)+".png";
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

  render();
})();
