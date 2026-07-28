#!/usr/bin/env python3
r"""Poverty-in-Space Atlas (v3) figure builder.
7 outcomes × 2 screening levels × 49 countries, from hex_predictions_all_outcomes.csv.
Each map: hex scatter + ADM0 country border, NO subtitle (country name only), per-outcome shared scale.

Layout:
  figures/full/{screening}/{outcome}/{ISO}.png   - titled + colourbar (lightbox)
  figures/thumb/{screening}/{outcome}/{ISO}.png  - clean map only (grid)
Also writes data/countries.json + assets/manifest.js.
Optional argv = restrict to given ISO3 codes (for quick tests)."""
import os, sys, json, shutil, glob, time
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import ListedColormap
import warnings; warnings.filterwarnings("ignore")
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

PRED=r"C:\Users\wyf19\Dropbox\phd general\poverty in space\new_code\01code\task8_demand_trap\hex_predictions_all_outcomes.csv"
ATLAS=r"C:\Users\wyf19\Dropbox\phd general\poverty-in-space-atlas"
FIGD=os.path.join(ATLAS,"figures"); DATAD=os.path.join(ATLAS,"data")
BND=r"D:\Google Building\data\raw\open building v3\boundaries"
MIN_HEX=150

OUTCOMES=[
 dict(key="wealth",          label="Wealth",           sub="median IWI (0–100)",    kind="reg", cmap="RdYlGn", low="poorer",    high="richer"),
 dict(key="poverty_rate",    label="Poverty rate",     sub="% households IWI < 35", kind="reg", cmap="YlOrRd", low="less poor", high="more poor"),
 dict(key="extreme_rate",    label="Extreme poverty",  sub="% households IWI < 20", kind="reg", cmap="Reds",   low="less",      high="more"),
 dict(key="inequality_cv",   label="Inequality (CV)",  sub="within-hex CV of IWI",  kind="reg", cmap="Purples",low="equal",     high="unequal"),
 dict(key="gini",            label="Gini",             sub="within-hex Gini of IWI",kind="reg", cmap="Purples",low="equal",     high="unequal"),
 dict(key="poverty_dummy",   label="Poor (yes/no)",    sub="median IWI < 35",       kind="bin", cmap="YlOrRd", low="no", high="yes", yes="#bd0026"),
 dict(key="inequality_dummy",label="High inequality (yes/no)",sub="CV > 0.40",       kind="bin", cmap="Oranges",low="no", high="yes", yes="#d94801"),
]
PREDCOL={"wealth":"pred_wealth","poverty_rate":"pred_poverty_rate","extreme_rate":"pred_extreme_rate",
         "inequality_cv":"pred_cv","gini":"pred_gini","poverty_dummy":"prob_poor","inequality_dummy":"prob_unequal"}
GRAD={"RdYlGn":"#a50026,#d73027,#f46d43,#fdae61,#fee08b,#ffffbf,#d9ef8b,#a6d96a,#66bd63,#1a9850,#006837",
 "YlOrRd":"#ffffcc,#ffeda0,#fed976,#feb24c,#fd8d3c,#fc4e2a,#e31a1c,#bd0026,#800026",
 "Reds":"#fff5f0,#fee0d2,#fcbba1,#fc9272,#fb6a4a,#ef3b2c,#cb181d,#a50f15,#67000d",
 "Purples":"#fcfbfd,#efedf5,#dadaeb,#bcbddc,#9e9ac8,#807dba,#6a51a3,#54278f,#3f007d",
 "Oranges":"#fff5eb,#fee6ce,#fdd0a2,#fdae6b,#fd8d3c,#f16913,#d94801,#a63603,#7f2704"}
SCREENINGS=[dict(key="screened",label="Screened (≥10 buildings)",min_bld=10),
            dict(key="all",label="All buildings",min_bld=1)]

NAMES={"AGO":"Angola","BDI":"Burundi","BEN":"Benin","BFA":"Burkina Faso","BGD":"Bangladesh","BWA":"Botswana",
 "CAF":"Central African Republic","CIV":"Côte d'Ivoire","CMR":"Cameroon","COD":"DR Congo","COG":"Congo",
 "COM":"Comoros","CPV":"Cape Verde","DJI":"Djibouti","DZA":"Algeria","EGY":"Egypt","ERI":"Eritrea",
 "ETH":"Ethiopia","GAB":"Gabon","GHA":"Ghana","GIN":"Guinea","GMB":"Gambia","GNB":"Guinea-Bissau",
 "GNQ":"Equatorial Guinea","KEN":"Kenya","LBR":"Liberia","LBY":"Libya","LSO":"Lesotho","MAR":"Morocco",
 "MDG":"Madagascar","MLI":"Mali","MOZ":"Mozambique","MRT":"Mauritania","MUS":"Mauritius","MWI":"Malawi",
 "NAM":"Namibia","NER":"Niger","NGA":"Nigeria","RWA":"Rwanda","SDN":"Sudan","SEN":"Senegal","SLE":"Sierra Leone",
 "SOM":"Somalia","SSD":"South Sudan","STP":"São Tomé and Príncipe","SWZ":"Eswatini","SYC":"Seychelles",
 "TCD":"Chad","TGO":"Togo","TUN":"Tunisia","TZA":"Tanzania","UGA":"Uganda","ZAF":"South Africa",
 "ZMB":"Zambia","ZWE":"Zimbabwe"}
REGION={"DZA":"North Africa","EGY":"North Africa","LBY":"North Africa","MAR":"North Africa","TUN":"North Africa","SDN":"North Africa",
 "BEN":"West Africa","BFA":"West Africa","CIV":"West Africa","CPV":"West Africa","GMB":"West Africa","GHA":"West Africa",
 "GIN":"West Africa","GNB":"West Africa","LBR":"West Africa","MLI":"West Africa","MRT":"West Africa","NER":"West Africa",
 "NGA":"West Africa","SEN":"West Africa","SLE":"West Africa","TGO":"West Africa",
 "AGO":"Central Africa","CMR":"Central Africa","CAF":"Central Africa","TCD":"Central Africa","COG":"Central Africa",
 "COD":"Central Africa","GNQ":"Central Africa","GAB":"Central Africa","STP":"Central Africa",
 "BDI":"East Africa","COM":"East Africa","DJI":"East Africa","ERI":"East Africa","ETH":"East Africa","KEN":"East Africa",
 "MDG":"East Africa","MWI":"East Africa","MUS":"East Africa","MOZ":"East Africa","RWA":"East Africa","SYC":"East Africa",
 "SOM":"East Africa","SSD":"East Africa","TZA":"East Africa","UGA":"East Africa","ZMB":"East Africa","ZWE":"East Africa",
 "BWA":"Southern Africa","SWZ":"Southern Africa","LSO":"Southern Africa","NAM":"Southern Africa","ZAF":"Southern Africa",
 "BGD":"South Asia"}
REG_ORDER=["North Africa","West Africa","Central Africa","East Africa","Southern Africa","South Asia"]

_SEG={}
def bsegs(iso):
    if iso in _SEG: return _SEG[iso]
    p=os.path.join(BND,f"{iso}_ADM0.geojson"); segs=[]
    if os.path.exists(p):
        gj=json.load(open(p))
        def add(cc):
            for r in cc:
                a=np.asarray(r)
                if a.ndim==2 and len(a)>1: segs.append(a[:,:2])
        for f in gj.get("features",[gj]):
            g=f.get("geometry",f); t=g.get("type"); c=g.get("coordinates")
            if t=="Polygon": add(c)
            elif t=="MultiPolygon":
                for poly in c: add(poly)
    _SEG[iso]=segs; return segs

def fresh(d):
    import stat
    def onerr(fn,pp,exc):
        try: os.chmod(pp,stat.S_IWRITE); fn(pp)
        except Exception: pass
    if os.path.exists(d):
        for _ in range(10):
            try: shutil.rmtree(d,onerror=onerr)
            except Exception: pass
            if not os.path.exists(d): break
            time.sleep(1.0)
    os.makedirs(d,exist_ok=True)

def render(s, col, cmap, vmin, vmax, name, segs, asp, ms, path_full, path_thumb, is_bin=False):
    # full
    fig,a=plt.subplots(figsize=(6.6,6.4))
    sc=a.scatter(s.hex_lon,s.hex_lat,c=s[col],s=ms,marker="h",linewidths=0,cmap=cmap,vmin=vmin,vmax=vmax,rasterized=True)
    if segs: a.add_collection(LineCollection(segs,colors="#33383d",linewidths=.55,alpha=.85))
    a.set_aspect(asp); a.set_xticks([]); a.set_yticks([])
    for sp in a.spines.values(): sp.set_visible(False)
    cb=fig.colorbar(sc,ax=a,shrink=.74,pad=.02); cb.ax.tick_params(labelsize=8.5); cb.outline.set_visible(False)
    if is_bin: cb.set_ticks([0.25,0.75]); cb.set_ticklabels(["no","yes"])
    fig.suptitle(name,fontweight="bold",fontsize=15,y=0.96); fig.tight_layout(rect=[0,0,1,0.95])
    fig.savefig(path_full,dpi=150,bbox_inches="tight"); plt.close(fig)
    # thumb
    fig,a=plt.subplots(figsize=(3.2,3.2))
    a.scatter(s.hex_lon,s.hex_lat,c=s[col],s=max(ms*0.5,1.0),marker="h",linewidths=0,cmap=cmap,vmin=vmin,vmax=vmax,rasterized=True)
    if segs: a.add_collection(LineCollection(segs,colors="#33383d",linewidths=.45,alpha=.8))
    a.set_aspect(asp); a.axis("off")
    fig.savefig(path_thumb,dpi=72,bbox_inches="tight",transparent=True); plt.close(fig)

def main():
    only=set(a.upper() for a in sys.argv[1:])
    A=pd.read_csv(PRED)
    S=A[A.n_buildings>=10]
    scales={}
    for o in OUTCOMES:
        c=PREDCOL[o["key"]]
        scales[o["key"]]=[0.0,1.0] if o["kind"]!="reg" else [round(float(x),2) for x in np.nanpercentile(S[c],[2,98])]
    isos=sorted(A.iso.unique())
    if not only:  # wipe whole figures tree (also clears the old v2 flat layout)
        fresh(os.path.join(FIGD,"full")); fresh(os.path.join(FIGD,"thumb"))
    for scr in SCREENINGS:
        for o in OUTCOMES:
            os.makedirs(os.path.join(FIGD,"full",scr["key"],o["key"]),exist_ok=True)
            os.makedirs(os.path.join(FIGD,"thumb",scr["key"],o["key"]),exist_ok=True)
    os.makedirs(DATAD,exist_ok=True)

    # per-country stats for manifest
    cinfo={}
    for iso in isos:
        s_all=A[A.iso==iso]; s_scr=s_all[s_all.n_buildings>=10]
        cinfo[iso]={"n_all":int(len(s_all)),"n_screened":int(len(s_scr)),
                    "val":{o["key"]:round(float(s_scr[PREDCOL[o["key"]]].mean()),2) if len(s_scr) else None for o in OUTCOMES}}

    t0=time.time(); nfig=0
    for scr in SCREENINGS:
        sub=A[A.n_buildings>=scr["min_bld"]]
        for iso in isos:
            if only and iso not in only: continue
            s=sub[sub.iso==iso]
            if len(s)<MIN_HEX: continue
            mlat=float(s.hex_lat.mean()); asp=1/np.cos(np.radians(mlat))
            ms=1.6 if len(s)>80000 else (3.0 if len(s)>20000 else 6.0)
            segs=bsegs(iso)
            for o in OUTCOMES:
                vmin,vmax=scales[o["key"]]; col=PREDCOL[o["key"]]
                is_bin=o["kind"]=="bin"; cmap=ListedColormap(["#e4e7e7",o["yes"]]) if is_bin else o["cmap"]
                render(s,col,cmap,vmin,vmax,NAMES.get(iso,iso),segs,asp,ms,
                       os.path.join(FIGD,"full",scr["key"],o["key"],f"{iso}.png"),
                       os.path.join(FIGD,"thumb",scr["key"],o["key"],f"{iso}.png"),is_bin)
                nfig+=2
            print(f"  [{scr['key']}] {iso} {NAMES.get(iso,iso):20s} {len(s):>7,} hexes ({time.time()-t0:.0f}s, {nfig} figs)",flush=True)

    if only:
        print(f"\nTEST render done ({nfig} figs).",flush=True); return

    countries=[dict(iso=iso,name=NAMES.get(iso,iso),region=REGION.get(iso,"Africa"),
                    n_all=cinfo[iso]["n_all"],n_screened=cinfo[iso]["n_screened"],val=cinfo[iso]["val"])
               for iso in isos if cinfo[iso]["n_all"]>=MIN_HEX]
    countries.sort(key=lambda r:(REG_ORDER.index(r["region"]) if r["region"] in REG_ORDER else 9, r["name"]))
    ometa=[]
    for o in OUTCOMES:
        e=dict(key=o["key"],label=o["label"],sub=o["sub"],kind=o["kind"],low=o["low"],high=o["high"],scale=scales[o["key"]])
        if o["kind"]=="bin": e["no"]="#e4e7e7"; e["yes"]=o["yes"]
        else: e["grad"]=GRAD[o["cmap"]]
        ometa.append(e)
    meta={"outcomes":ometa,
          "screenings":[dict(key=s["key"],label=s["label"],min_bld=s["min_bld"]) for s in SCREENINGS],
          "regions":REG_ORDER,
          "model":{"name":"HistGradientBoosting (buildings-only)","unit":"H3 res-7 hex (~5 km)"},
          "countries":countries}
    json.dump(meta,open(os.path.join(DATAD,"countries.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
    open(os.path.join(ATLAS,"assets","manifest.js"),"w",encoding="utf-8").write("window.ATLAS = "+json.dumps(meta,ensure_ascii=False)+";\n")
    print(f"\nDONE: {nfig} figures, {len(countries)} countries -> atlas",flush=True)

if __name__=="__main__": main()
