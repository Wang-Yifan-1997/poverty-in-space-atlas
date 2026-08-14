/* Poverty in Space — Descriptives. Data from window.DESC. */
(function () {
  "use strict";
  var D = window.DESC;
  if (!D) { document.getElementById("explore").innerHTML =
    "<p>Could not load manifest. Run <code>scripts/make_descriptives.py</code>.</p>"; return; }

  var cBy = {}; D.countries.forEach(function (c) { cBy[c.iso] = c; });
  var state = { country: D.countries[0].iso, dataset: "v3", tab: "density" };

  // ---- country dropdown (grouped by region) ----
  var sel = document.getElementById("country");
  var lastReg = null;
  D.countries.forEach(function (c) {
    if (c.region !== lastReg) {
      var og = document.createElement("optgroup"); og.label = c.region; sel.appendChild(og); lastReg = c.region;
    }
    var o = document.createElement("option"); o.value = c.iso; o.textContent = c.name;
    sel.lastChild.appendChild(o);
  });
  sel.value = state.country;
  sel.onchange = function () { state.country = sel.value; render(); };

  // ---- dataset seg ----
  var dsWrap = document.getElementById("dataset");
  D.datasets.forEach(function (d) {
    var b = document.createElement("button"); b.textContent = d.label; b._key = d.key;
    b.className = d.key === state.dataset ? "active" : "";
    b.onclick = function () { state.dataset = d.key; syncSeg(dsWrap); render(); };
    dsWrap.appendChild(b);
  });

  // ---- tabs ----
  var tabs = document.getElementById("desc-tabs");
  D.tabs.forEach(function (t) {
    var b = document.createElement("button"); b.setAttribute("role", "tab");
    b.textContent = t.label; b._key = t.key;
    b.className = t.key === state.tab ? "active" : "";
    b.onclick = function () { state.tab = t.key; syncTabs(); render(); };
    tabs.appendChild(b);
  });
  function syncTabs(){ [].forEach.call(tabs.children,function(b){ b.className = b._key===state.tab ? "active":""; }); }
  function syncSeg(g){ [].forEach.call(g.children,function(b){ b.classList.toggle("active", b._key===state.dataset); }); }

  var img = document.getElementById("desc-img"),
      cap = document.getElementById("desc-cap"),
      un  = document.getElementById("desc-unavailable"),
      dl  = document.getElementById("desc-dl"),
      note= document.getElementById("desc-note"),
      dsRow = dsWrap.parentElement;

  function figPath(){
    var c = state.country, t = state.tab;
    return t === "temporal" ? "figures/descriptives/temporal/" + c + ".png"
                            : "figures/descriptives/" + t + "/" + state.dataset + "/" + c + ".png";
  }
  function available(){
    var c = cBy[state.country];
    if (state.tab === "temporal") return c.temporal;
    return c.datasets.indexOf(state.dataset) > -1;
  }

  function render(){
    var c = cBy[state.country], t = state.tab, isTemp = (t === "temporal");
    // dataset selector only matters for non-temporal tabs
    dsRow.style.opacity = isTemp ? 0.4 : 1;
    [].forEach.call(dsWrap.children, function(b){ b.disabled = isTemp; });
    note.hidden = !isTemp;
    if (isTemp) note.innerHTML = "<strong>Temporal persistence</strong> uses the Google 2.5D panel (2016 → 2023), available for 12 countries. The Dataset selector doesn't apply here.";

    if (!available()){
      img.hidden = true; dl.hidden = true; cap.textContent = "";
      un.hidden = false;
      un.textContent = isTemp
        ? c.name + " is not in the 2.5D temporal panel — temporal persistence is available for 12 countries only."
        : c.name + " has no 2.5D data — the " + dsLabel(state.dataset) + " dataset covers 12 countries only. Switch Dataset to “Google v3”.";
      return;
    }
    un.hidden = true; img.hidden = false;
    var p = figPath();
    img.src = p; img.alt = c.name + " — " + tabLabel(t);
    cap.textContent = c.name + " · " + (isTemp ? "2.5D 2016→2023" : dsLabel(state.dataset)) + " · " + tabLabel(t);
    dl.hidden = false; dl.href = p; dl.download = "povertyinspace_desc_" + c.iso + "_" + t + (isTemp ? "" : "_" + state.dataset) + ".png";
  }
  function dsLabel(k){ var d = D.datasets.filter(function(x){return x.key===k;})[0]; return d ? d.label : k; }
  function tabLabel(k){ var t = D.tabs.filter(function(x){return x.key===k;})[0]; return t ? t.label : k; }

  render();
})();
