#!/usr/bin/env python3
r"""Add two BUILDING-DENSITY layers to the atlas, for all 3 datasets already in the Period selector:
  bld_density : buildings/km² (log colour, scale shared across countries per dataset)
  bld_decile  : within-country equal-count decile 1–10

Datasets:  v3 (52 countries, from hex_predictions_all_outcomes.csv, border-clipped)
           2.5D 2016 & 2023 (12 countries, from atlas_temporal/predictions_{ISO}_{YEAR}.csv)

Figures land in the same trees as the other outcomes; 2 new outcomes are injected into the manifest.
Re-run after any build_maps.py / add_temporal.py rebuild (those rewrite the manifest without these).
Optional argv = restrict to ISO codes (test mode; skips manifest write)."""
import os, sys, json, importlib.util, warnings
import numpy as np, pandas as pd, h3
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import LogNorm
warnings.filterwarnings("ignore")
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

ATLAS = r"C:\Users\wyf19\Dropbox\phd general\poverty-in-space-atlas"
TASK8 = r"C:\Users\wyf19\Dropbox\phd general\poverty in space\new_code\01code\task8_demand_trap"
TEMP  = r"D:\Google Building\data\temp\atlas_temporal"
spec=importlib.util.spec_from_file_location("bm", os.path.join(ATLAS,"scripts","build_maps.py"))
bm=importlib.util.module_from_spec(spec); spec.loader.exec_module(bm)   # bsegs, NAMES, REGION, FIGD, MIN_HEX
FIGD=bm.FIGD; MIN_HEX=bm.MIN_HEX
try: AREA7=h3.average_hexagon_area(7,"km^2")
except Exception: AREA7=5.1613
TEMP_ISOS=["BFA","BGD","CIV","CMR","GHA","GIN","KEN","LSO","MDG","MOZ","MWI","SEN"]
YEARS=["2016","2023"]
VIRIDIS="#440154,#482878,#3e4989,#31688e,#26828e,#1f9e89,#35b779,#6ece58,#b5de2b,#fde725"
VIR=plt.get_cmap("viridis"); VIR10=plt.get_cmap("viridis",10)

def load_v3():
    d=pd.read_csv(os.path.join(TASK8,"hex_predictions_all_outcomes.csv"),usecols=["iso","h3","hex_lat","hex_lon","n_buildings"])
    d["dens"]=d.n_buildings/AREA7
    return d

def load_temp(year):
    parts=[]
    for iso in TEMP_ISOS:
        f=os.path.join(TEMP,f"predictions_{iso}_{year}.csv")
        if not os.path.exists(f): continue
        d=pd.read_csv(f,usecols=["h3","n_buildings","bld_density"]); d["iso"]=iso; parts.append(d)
    A=pd.concat(parts,ignore_index=True)
    ll=[h3.cell_to_latlng(x) for x in A.h3]
    A["hex_lat"]=[p[0] for p in ll]; A["hex_lon"]=[p[1] for p in ll]; A["dens"]=A.bld_density
    return A

def level_scale(d):
    s=d[d.n_buildings>=10]
    lo,hi=np.nanpercentile(s.dens,[2,98])
    return [round(float(max(lo,0.1)),2), round(float(hi),1)]

def render(s, cvals, name, segs, asp, ms, path_full, path_thumb, cmap, norm=None, vmin=None, vmax=None, ticks=None, ticklab=None):
    for kind,path,mss,dpi,txt in (("full",path_full,ms,150,True),("thumb",path_thumb,max(ms*0.5,1.0),72,False)):
        fig,a=plt.subplots(figsize=(6.6,6.4) if txt else (3.2,3.2))
        sc=a.scatter(s.hex_lon,s.hex_lat,c=cvals,s=mss,marker="h",linewidths=0,cmap=cmap,norm=norm,vmin=vmin,vmax=vmax,rasterized=True)
        if segs: a.add_collection(LineCollection(segs,colors="#33383d",linewidths=(.55 if txt else .45),alpha=.85))
        a.set_aspect(asp)
        if txt:
            a.set_xticks([]); a.set_yticks([])
            for sp in a.spines.values(): sp.set_visible(False)
            cb=fig.colorbar(sc,ax=a,shrink=.74,pad=.02); cb.ax.tick_params(labelsize=8.5); cb.outline.set_visible(False)
            if ticks is not None: cb.set_ticks(ticks)
            if ticklab is not None: cb.set_ticklabels(ticklab)
            fig.suptitle(name,fontweight="bold",fontsize=15,y=0.96); fig.tight_layout(rect=[0,0,1,0.95])
            fig.savefig(path,dpi=dpi,bbox_inches="tight")
        else:
            a.axis("off"); fig.savefig(path,dpi=dpi,bbox_inches="tight",transparent=True)
        plt.close(fig)

def render_dataset(d, year, lvl, only):
    floor=max(lvl[0],0.1); lognorm=LogNorm(vmin=floor,vmax=lvl[1],clip=True)
    for scrkey,minb in (("screened",10),("all",1)):
        sub=d[d.n_buildings>=minb]
        for iso in sorted(sub.iso.unique()):
            if only and iso not in only: continue
            s=sub[sub.iso==iso].copy()
            if len(s)<MIN_HEX: continue
            r=s.dens.rank(method="first"); s["dec"]=np.ceil(r/len(s)*10).clip(1,10).astype(int)
            mlat=float(s.hex_lat.mean()); asp=1/np.cos(np.radians(mlat))
            ms=1.6 if len(s)>80000 else (3.0 if len(s)>20000 else 6.0)
            segs=bm.bsegs(iso); nm=bm.NAMES.get(iso,iso)
            def paths(out):
                if year:  # matches app figPath: figures/temporal/{kind}/{screening}/{year}/{outcome}/{ISO}.png
                    fd=os.path.join(FIGD,"temporal","full",scrkey,year,out); td=os.path.join(FIGD,"temporal","thumb",scrkey,year,out)
                else:
                    fd=os.path.join(FIGD,"full",scrkey,out); td=os.path.join(FIGD,"thumb",scrkey,out)
                os.makedirs(fd,exist_ok=True); os.makedirs(td,exist_ok=True)
                return os.path.join(fd,f"{iso}.png"), os.path.join(td,f"{iso}.png")
            fL,tL=paths("bld_density")
            render(s, np.clip(s.dens.values,floor,None), nm, segs, asp, ms, fL, tL, cmap=VIR, norm=lognorm)
            fD,tD=paths("bld_decile")
            render(s, s.dec.values, nm, segs, asp, ms, fD, tD, cmap=VIR10, vmin=0.5, vmax=10.5, ticks=list(range(1,11)))
        print(f"  {'temporal '+year if year else 'v3'} [{scrkey}] rendered", flush=True)

def inject_manifest(sc_v3, sc_t):
    mpath=os.path.join(ATLAS,"data","countries.json"); m=json.load(open(mpath,encoding="utf-8"))
    m["outcomes"]=[o for o in m["outcomes"] if o["key"] not in ("bld_density","bld_decile")]
    m["outcomes"].append(dict(key="bld_density",label="Building density",sub="buildings / km² (log)",kind="reg",low="sparse",high="dense",scale=sc_v3,grad=VIRIDIS))
    m["outcomes"].append(dict(key="bld_decile",label="Density decile",sub="within-country rank 1–10",kind="reg",low="1 (sparsest)",high="10 (densest)",scale=[1,10],grad=VIRIDIS))
    if "temporal" in m:
        m["temporal"]["scales"]["bld_density"]=sc_t; m["temporal"]["scales"]["bld_decile"]=[1,10]
    json.dump(m,open(mpath,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
    open(os.path.join(ATLAS,"assets","manifest.js"),"w",encoding="utf-8").write("window.ATLAS = "+json.dumps(m,ensure_ascii=False)+";\n")
    print(f"manifest: +bld_density {sc_v3} (v3) / {sc_t} (2.5D) +bld_decile [1,10]", flush=True)

def main():
    only=set(a.upper() for a in sys.argv[1:])
    dv3=load_v3(); sc_v3=level_scale(dv3)
    print(f"v3 density scale (buildings/km2, 2-98pct): {sc_v3}", flush=True)
    render_dataset(dv3, None, sc_v3, only)
    dt={y:load_temp(y) for y in YEARS}
    sc_t=level_scale(pd.concat(dt.values(),ignore_index=True))
    print(f"2.5D density scale: {sc_t}", flush=True)
    for y in YEARS: render_dataset(dt[y], y, sc_t, only)
    if only: print("\nTEST render done (manifest not written).", flush=True); return
    inject_manifest(sc_v3, sc_t)
    print("\nDONE: building-density level + decile layers added.", flush=True)

if __name__=="__main__": main()
