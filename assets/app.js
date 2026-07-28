/* Poverty in Space — Atlas: period × screening × outcome selectors. Data from window.ATLAS. */
(function () {
  "use strict";
  var A = window.ATLAS;
  if (!A) { document.getElementById("grid").innerHTML =
    "<p>Could not load manifest. Run <code>scripts/build_maps.py</code>.</p>"; return; }

  var MIN_HEX = 150;
  var oBy = {}; A.outcomes.forEach(function (o) { oBy[o.key] = o; });
  var state = { period: "v3", screening: A.screenings[0].key, outcome: A.outcomes[0].key, region: "all", sort: "name" };
  function fmt(n){ return n.toLocaleString("en-US"); }
  function set(id,v){ var el=document.getElementById(id); if(el) el.textContent=v; }

  // ---- period-aware accessors ----
  function isTemp(){ return state.period !== "v3"; }
  function curCountries(){ return isTemp() ? A.temporal.countries : A.countries; }
  function scaleOf(o){ return isTemp() ? A.temporal.scales[o.key] : o.scale; }
  function availN(c){
    if (isTemp()){ var n=c.n[state.period]; return state.screening==="all" ? n[0] : n[1]; }
    return state.screening==="all" ? c.n_all : c.n_screened;
  }
  function valOf(c,ok){ return isTemp() ? ((c.val[state.period]||{})[ok]) : (c.val||{})[ok]; }
  function figPath(kind,c){
    return isTemp()
      ? "figures/temporal/"+kind+"/"+state.screening+"/"+state.period+"/"+state.outcome+"/"+c.iso+".png"
      : "figures/"+kind+"/"+state.screening+"/"+state.outcome+"/"+c.iso+".png";
  }

  // ---- hero (headline = v3) ----
  set("stat-countries", A.countries.length);
  set("s-countries", A.countries.length);
  set("s-points", fmt(A.countries.reduce(function(s,c){ return s+c.n_all; }, 0)));
  set("s-outcomes", A.outcomes.length);

  // ---- period seg ----
  var pf = document.getElementById("period");
  var periods = [{key:"v3", label:"2023 · v3"}];
  if (A.temporal) A.temporal.years.forEach(function(y){ periods.push({key:y, label:y+" · 2.5D"}); });
  periods.forEach(function(p){
    var b=document.createElement("button"); b.textContent=p.label;
    b.className = p.key===state.period ? "active":"";
    b.onclick=function(){ state.period=p.key; syncSeg(pf,b); updateNote(); updateLegend(); render(); };
    pf.appendChild(b);
  });
  function updateNote(){
    var el=document.getElementById("period-note"); if(!el) return;
    if(isTemp() && A.temporal){ el.innerHTML="<strong>"+state.period+" · Google 2.5D temporal panel.</strong> "+A.temporal.model.note; el.hidden=false; }
    else el.hidden=true;
  }

  // ---- screening seg ----
  var scr = document.getElementById("screening");
  A.screenings.forEach(function(s){
    var b=document.createElement("button");
    b.textContent = s.label; b.className = s.key===state.screening ? "active" : "";
    b.onclick=function(){ state.screening=s.key; syncSeg(scr,b); render(); };
    scr.appendChild(b);
  });

  // ---- outcome tabs ----
  var tabs = document.getElementById("outcome-tabs");
  A.outcomes.forEach(function(o){
    var b=document.createElement("button"); b.setAttribute("role","tab");
    b.innerHTML = o.label + "<small>" + o.sub + "</small>";
    b.className = o.key===state.outcome ? "active" : ""; b._key=o.key;
    b.onclick=function(){ state.outcome=o.key; syncTabs(); updateLegend(); render(); };
    tabs.appendChild(b);
  });
  function syncTabs(){ [].forEach.call(tabs.children,function(b){ b.className = b._key===state.outcome ? "active":""; }); }

  // ---- region filter ----
  var present = A.regions.filter(function(r){ return A.countries.some(function(c){ return c.region===r; }); });
  var rf = document.getElementById("region-filter");
  [["all","All regions"]].concat(present.map(function(r){ return [r,r]; })).forEach(function(p){
    var b=document.createElement("button"); b.textContent=p[1];
    b.className = p[0]===state.region ? "active":"";
    b.onclick=function(){ state.region=p[0]; syncSeg(rf,b); render(); };
    rf.appendChild(b);
  });

  var sb = document.getElementById("sort-by");
  [].forEach.call(sb.children,function(b){ b.onclick=function(){ state.sort=b.getAttribute("data-sort"); syncSeg(sb,b); render(); }; });
  function syncSeg(g,a){ [].forEach.call(g.children,function(b){ b.classList.toggle("active",b===a); }); }

  // ---- legend ----
  function updateLegend(){
    var o=oBy[state.outcome], sc=scaleOf(o), lg=document.getElementById("legend");
    if (o.kind==="bin"){
      lg.innerHTML =
        '<span class="swatch" style="background:'+o.no+'"></span><span class="legend-label">no</span>'+
        '<span class="swatch" style="background:'+o.yes+'"></span><span class="legend-label">yes</span>'+
        '<span class="legend-cap">'+o.sub+' &nbsp;(dummy: yes / no)</span>';
    } else {
      lg.innerHTML =
        '<span class="legend-label">'+(Math.round(sc[0]*100)/100)+'</span>'+
        '<span class="legend-bar" style="background:linear-gradient(90deg,'+o.grad+')"></span>'+
        '<span class="legend-label">'+(Math.round(sc[1]*100)/100)+'</span>'+
        '<span class="legend-cap">'+o.low+' → '+o.high+' &nbsp;('+o.sub+', shared scale)</span>';
    }
  }

  // ---- grid ----
  var grid = document.getElementById("grid");
  var visible = [];
  function currentList(){
    var l = curCountries().filter(function(c){ return (state.region==="all"||c.region===state.region) && availN(c)>=MIN_HEX; });
    var ok=state.outcome;
    if (state.sort==="value") l.sort(function(a,b){ return (valOf(b,ok)||0)-(valOf(a,ok)||0); });
    else if (state.sort==="n") l.sort(function(a,b){ return availN(b)-availN(a); });
    else l.sort(function(a,b){ return a.name.localeCompare(b.name); });
    return l;
  }
  function render(){
    visible = currentList();
    grid.innerHTML = "";
    if (!visible.length){ grid.innerHTML='<p class="empty">No countries at this selection.</p>'; return; }
    var o=oBy[state.outcome];
    visible.forEach(function(c,i){
      var card=document.createElement("div"); card.className="card";
      card.innerHTML =
        '<div class="card-img"><img loading="lazy" alt="'+c.name+' '+o.label+'" src="'+figPath("thumb",c)+'"></div>'+
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
    var c=visible[idx], o=oBy[state.outcome], full=figPath("full",c);
    lbImg.src=full; lbImg.alt=c.name+" "+o.label;
    var extra = isTemp() ? " · "+state.period+" (2.5D · "+c.status+")" : "";
    lbCap.innerHTML="<strong>"+c.name+" — "+o.label+"</strong>"+o.sub+" · "+c.region+extra+" · "+fmt(availN(c))+" hexes";
    lbDl.href=full; lbDl.download="povertyinspace_"+c.iso+"_"+state.outcome+"_"+state.screening+(isTemp()?"_"+state.period:"")+".png";
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

  updateNote(); updateLegend(); render();
})();
