#!/usr/bin/env python3
r"""Descriptives subpage figures: per country × dataset. ONE panel per PNG (no composites).
  density_asinh : asinh(building density) histogram [zeros kept]
  density_log   : log(building density) histogram   [zeros dropped]
  wealth        : predicted-IWI histogram
  spatial_scatter / spatial_heat   : own vs neighbours' asinh density (scatter | 10×10 heatmap)
  temporal_scatter / temporal_heat : asinh density 2016 vs 2023 (scatter | 10×10 heatmap) [2.5D panel, 12 countries]

Density = arcsinh(count/area); neighbour = H3 ring-1 mean.
Datasets: v3 (hex_predictions_all_outcomes.csv, 52 countries) + 2.5D 2016/2023 (atlas_temporal, 12).
Figures -> figures/descriptives/{tab}/{dataset}/{ISO}.png  (temporal_*: figures/descriptives/{tab}/{ISO}.png)
Writes data/descriptives.json + assets/descriptives_manifest.js. Optional argv = restrict ISOs (test; skips manifest)."""
import os, sys, json, importlib.util, warnings
import numpy as np, pandas as pd, h3
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
warnings.filterwarnings("ignore")
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

ATLAS=r"C:\Users\wyf19\Dropbox\phd general\poverty-in-space-atlas"
TASK8=r"C:\Users\wyf19\Dropbox\phd general\poverty in space\new_code\01code\task8_demand_trap"
TEMP =r"D:\Google Building\data\temp\atlas_temporal"
FIGD =os.path.join(ATLAS,"figures","descriptives")
spec=importlib.util.spec_from_file_location("bm",os.path.join(ATLAS,"scripts","build_maps.py"))
bm=importlib.util.module_from_spec(spec); spec.loader.exec_module(bm)
NAMES=bm.NAMES; REGION=bm.REGION; MIN_HEX=bm.MIN_HEX
try: AREA7=h3.average_hexagon_area(7,"km^2")
except Exception: AREA7=5.1613
TEMP_ISOS=["BFA","BGD","CIV","CMR","GHA","GIN","KEN","LSO","MDG","MOZ","MWI","SEN"]
TEAL="#2b6777"; TEAL2="#6a51a3"; MAROON="#a3282b"; NAVY="#26456e"; GREEN="#1a7a3a"

def ensure(*p): d=os.path.join(FIGD,*p); os.makedirs(d,exist_ok=True); return d

def neighbour_mean(h3arr, val):
    idx={c:i for i,c in enumerate(h3arr)}; out=np.full(len(h3arr),np.nan)
    for c,i in idx.items():
        nn=[idx[x] for x in h3.grid_disk(c,1) if (x in idx and x!=c)]
        if nn: out[i]=val[nn].mean()
    return out

# ---- single-panel figures -------------------------------------------------
def fig_density(dens, name, out, mode):
    if mode=="asinh":
        v=np.arcsinh(dens); col=TEAL
        title=f"asinh(density) — zeros kept  ({(dens==0).mean()*100:.0f}% of hexes are zero)"
        xl="asinh( buildings / km² )"
    else:
        v=np.log(dens[dens>0]); col=TEAL2
        title=f"log(density) — zeros dropped  (n={len(v):,})"
        xl="log( buildings / km² )"
    fig,a=plt.subplots(figsize=(6.6,4.7))
    a.hist(v,bins=60,color=col,alpha=.9)
    a.set_xlabel(xl); a.set_ylabel("# hexes"); a.set_title(title,fontsize=10.5)
    fig.suptitle(f"{name} — building density",fontweight="bold",fontsize=13); fig.tight_layout(rect=[0,0,1,.95])
    fig.savefig(out,dpi=130,bbox_inches="tight"); plt.close(fig)

def fig_wealth(w, name, out):
    w=w[~np.isnan(w)]
    fig,a=plt.subplots(figsize=(6.6,4.7))
    a.hist(w,bins=60,color=GREEN,alpha=.9)
    a.axvline(35,color=MAROON,ls="--",lw=1.5,label="poverty line (IWI 35)")
    a.set_xlabel("predicted wealth (IWI, 0–100)"); a.set_ylabel("# hexes"); a.legend(fontsize=9)
    a.set_title(f"mean {w.mean():.1f} · median {np.median(w):.1f} · {(w<35).mean()*100:.0f}% below 35",fontsize=10.5)
    fig.suptitle(f"{name} — wealth distribution",fontweight="bold",fontsize=13); fig.tight_layout(rect=[0,0,1,.95])
    fig.savefig(out,dpi=130,bbox_inches="tight"); plt.close(fig)

def fig_scatter(x, y, xlab, ylab, name, sub, out, dotcol):
    m=~(np.isnan(x)|np.isnan(y)); x=x[m]; y=y[m]; n=len(x)
    b=np.polyfit(x,y,1); r=np.corrcoef(x,y)[0,1]
    fig,a=plt.subplots(figsize=(6.6,4.8))
    rs=np.random.RandomState(1); sel=rs.choice(n,min(8000,n),replace=False)
    a.scatter(x[sel],y[sel],s=5,alpha=.12,c=dotcol,linewidths=0)
    lo=min(x.min(),y.min()); hi=max(x.max(),y.max()); xs=np.linspace(x.min(),x.max(),40)
    a.plot(xs,np.polyval(b,xs),color=MAROON,lw=2,label=f"slope {b[0]:.2f} · R²={r**2:.2f}")
    a.plot([lo,hi],[lo,hi],"--",c="#999",lw=1); a.set_xlabel(xlab); a.set_ylabel(ylab)
    a.legend(fontsize=9,loc="upper left")
    fig.suptitle(f"{name} — {sub} · scatter (8k sample)",fontweight="bold",fontsize=12.5); fig.tight_layout(rect=[0,0,1,.95])
    fig.savefig(out,dpi=130,bbox_inches="tight"); plt.close(fig)

def fig_heat(x, y, xlab, ylab, name, sub, out):
    m=~(np.isnan(x)|np.isnan(y)); x=x[m]; y=y[m]
    fig,a=plt.subplots(figsize=(6.6,4.8))
    H,xe,ye=np.histogram2d(x,y,bins=10)
    im=a.imshow(H.T,origin="lower",aspect="auto",extent=[xe[0],xe[-1],ye[0],ye[-1]],
                cmap="magma",norm=LogNorm(vmin=1,vmax=max(H.max(),2)))
    a.plot([xe[0],xe[-1]],[xe[0],xe[-1]],"--",c="#fff",lw=1,alpha=.6)
    a.set_xlabel(xlab); a.set_ylabel(ylab)
    cb=fig.colorbar(im,ax=a,shrink=.85); cb.set_label("# hexes",fontsize=9)
    fig.suptitle(f"{name} — {sub} · 10×10 bins (hex count)",fontweight="bold",fontsize=12.5); fig.tight_layout(rect=[0,0,1,.95])
    fig.savefig(out,dpi=130,bbox_inches="tight"); plt.close(fig)

# ---- generators -----------------------------------------------------------
def gen_snapshot(dataset, only, avail):
    """dataset: 'v3' | '2016' | '2023'. Builds density(asinh/log)/wealth/spatial(scatter/heat) per country."""
    if dataset=="v3":
        D=pd.read_csv(os.path.join(TASK8,"hex_predictions_all_outcomes.csv"),
                      usecols=["iso","h3","n_buildings","pred_wealth"]).rename(columns={"pred_wealth":"w"})
        D["dens"]=D.n_buildings/AREA7; isos=sorted(D.iso.unique())
        getc=lambda iso: D[D.iso==iso]
    else:
        isos=TEMP_ISOS
        def getc(iso):
            f=os.path.join(TEMP,f"predictions_{iso}_{dataset}.csv")
            d=pd.read_csv(f,usecols=["h3","bld_density","wealth"]).rename(columns={"bld_density":"dens","wealth":"w"})
            d["iso"]=iso; return d
    for iso in isos:
        if only and iso not in only: continue
        s=getc(iso)
        if len(s)<MIN_HEX: continue
        nm=NAMES.get(iso,iso)
        dens=s.dens.to_numpy(float); asinh=np.arcsinh(dens)
        fig_density(dens, nm, os.path.join(ensure("density_asinh",dataset),f"{iso}.png"), "asinh")
        fig_density(dens, nm, os.path.join(ensure("density_log",dataset),f"{iso}.png"),   "log")
        fig_wealth(s.w.to_numpy(float), nm, os.path.join(ensure("wealth",dataset),f"{iso}.png"))
        nb=neighbour_mean(s.h3.to_numpy(), asinh)
        fig_scatter(nb, asinh, "neighbours' asinh density", "own asinh density", nm, "spatial persistence",
                    os.path.join(ensure("spatial_scatter",dataset),f"{iso}.png"), NAVY)
        fig_heat(nb, asinh, "neighbours' asinh density", "own asinh density", nm, "spatial persistence",
                 os.path.join(ensure("spatial_heat",dataset),f"{iso}.png"))
        avail.setdefault(iso,{"iso":iso,"name":nm,"region":REGION.get(iso,"Africa"),"datasets":[],"temporal":False})
        if dataset not in avail[iso]["datasets"]: avail[iso]["datasets"].append(dataset)
        print(f"  [{dataset}] {iso} n={len(s):,}",flush=True)

def gen_temporal(only, avail):
    for iso in TEMP_ISOS:
        if only and iso not in only: continue
        a=pd.read_csv(os.path.join(TEMP,f"predictions_{iso}_2016.csv"),usecols=["h3","bld_density"]).rename(columns={"bld_density":"d16"})
        b=pd.read_csv(os.path.join(TEMP,f"predictions_{iso}_2023.csv"),usecols=["h3","bld_density"]).rename(columns={"bld_density":"d23"})
        m=a.merge(b,on="h3",how="inner")
        if len(m)<MIN_HEX: continue
        nm=NAMES.get(iso,iso)
        x=np.arcsinh(m.d16.to_numpy(float)); y=np.arcsinh(m.d23.to_numpy(float))
        fig_scatter(x,y,"asinh density 2016","asinh density 2023",nm,"temporal persistence (2016 → 2023)",
                    os.path.join(ensure("temporal_scatter"),f"{iso}.png"), TEAL)
        fig_heat(x,y,"asinh density 2016","asinh density 2023",nm,"temporal persistence (2016 → 2023)",
                 os.path.join(ensure("temporal_heat"),f"{iso}.png"))
        if iso in avail: avail[iso]["temporal"]=True
        print(f"  [temporal] {iso} n={len(m):,}",flush=True)

def main():
    only=set(a.upper() for a in sys.argv[1:]); avail={}
    for ds in ("v3","2016","2023"): gen_snapshot(ds, only, avail)
    gen_temporal(only, avail)
    if only: print("\nTEST done (manifest not written).",flush=True); return
    REG_ORDER=["North Africa","West Africa","Central Africa","East Africa","Southern Africa","South Asia"]
    countries=sorted(avail.values(), key=lambda r:(REG_ORDER.index(r["region"]) if r["region"] in REG_ORDER else 9, r["name"]))
    meta={"datasets":[{"key":"v3","label":"Google v3 (2023)"},{"key":"2016","label":"2.5D 2016"},{"key":"2023","label":"2.5D 2023"}],
          "tabs":[{"key":"density_asinh","label":"Density (asinh)"},
                  {"key":"density_log","label":"Density (log)"},
                  {"key":"wealth","label":"Wealth"},
                  {"key":"spatial_scatter","label":"Spatial · scatter"},
                  {"key":"spatial_heat","label":"Spatial · heatmap"},
                  {"key":"temporal_scatter","label":"Temporal · scatter"},
                  {"key":"temporal_heat","label":"Temporal · heatmap"}],
          "regions":REG_ORDER,"countries":countries}
    os.makedirs(os.path.join(ATLAS,"data"),exist_ok=True)
    json.dump(meta,open(os.path.join(ATLAS,"data","descriptives.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
    open(os.path.join(ATLAS,"assets","descriptives_manifest.js"),"w",encoding="utf-8").write("window.DESC = "+json.dumps(meta,ensure_ascii=False)+";\n")
    print(f"\nDONE: descriptives for {len(countries)} countries.",flush=True)

if __name__=="__main__": main()
