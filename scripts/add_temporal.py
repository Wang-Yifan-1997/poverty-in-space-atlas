#!/usr/bin/env python3
r"""Incorporate the Google 2.5D TEMPORAL atlas (2016 & 2023, 12 countries) into the website.
- Copies the pre-rendered 672 PNGs into figures/temporal/{full,thumb}/{screening}/{year}/{outcome}/{ISO}.png
- Reads scales.json + training_metrics.csv + per-country/year predictions
- Injects a `temporal` block into data/countries.json + assets/manifest.js (leaves the v3 core intact).

Re-run this after any v3 rebuild (build_maps.py), since that rewrites the manifest without `temporal`."""
import os, sys, json, shutil, time, stat
import numpy as np, pandas as pd
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

SRC   = r"D:\Google Building\data\temp\atlas_temporal"
ATLAS = r"C:\Users\wyf19\Dropbox\phd general\poverty-in-space-atlas"
FIGD  = os.path.join(ATLAS, "figures", "temporal")
YEARS = ["2016", "2023"]
OUTKEYS = ["wealth","poverty_rate","extreme_rate","inequality_cv","gini","poverty_dummy","inequality_dummy"]
BINKEYS = {"poverty_dummy","inequality_dummy"}
ISOS  = ["BFA","BGD","CIV","CMR","GHA","GIN","KEN","LSO","MDG","MOZ","MWI","SEN"]
IN_TRAIN = {"GIN","KEN","LSO","MDG","MOZ","MWI","SEN"}
NAMES = {"BFA":"Burkina Faso","BGD":"Bangladesh","CIV":"Côte d'Ivoire","CMR":"Cameroon","GHA":"Ghana",
         "GIN":"Guinea","KEN":"Kenya","LSO":"Lesotho","MDG":"Madagascar","MOZ":"Mozambique","MWI":"Malawi","SEN":"Senegal"}
REGION = {"BFA":"West Africa","BGD":"South Asia","CIV":"West Africa","CMR":"Central Africa","GHA":"West Africa",
          "GIN":"West Africa","KEN":"East Africa","LSO":"Southern Africa","MDG":"East Africa","MOZ":"East Africa",
          "MWI":"East Africa","SEN":"West Africa"}

def lock_rmtree(d):
    def onerr(fn,pp,exc):
        try: os.chmod(pp,stat.S_IWRITE); fn(pp)
        except Exception: pass
    if os.path.exists(d):
        for _ in range(10):
            try: shutil.rmtree(d,onerror=onerr)
            except Exception: pass
            if not os.path.exists(d): break
            time.sleep(1.0)

def copy_figs():
    lock_rmtree(FIGD)
    shutil.copytree(os.path.join(SRC,"atlas","figures"), FIGD)
    n=sum(len(f) for _,_,f in os.walk(FIGD))
    print(f"copied {n} temporal PNGs -> {FIGD}", flush=True)

def build_temporal():
    scales=json.load(open(os.path.join(SRC,"atlas","scales.json"),encoding="utf-8"))
    scales={k:[round(float(v[0]),3),round(float(v[1]),3)] for k,v in scales.items()}
    tm=pd.read_csv(os.path.join(SRC,"training_metrics.csv"))
    metrics={r.outcome:{"metric":r.metric,"score":round(float(r.score),3)} for r in tm.itertuples()}
    countries=[]
    for iso in ISOS:
        rec={"iso":iso,"name":NAMES[iso],"region":REGION[iso],
             "status":("in training" if iso in IN_TRAIN else "extrapolated"),
             "n":{}, "val":{}}
        for yr in YEARS:
            d=pd.read_csv(os.path.join(SRC,f"predictions_{iso}_{yr}.csv"),
                          usecols=["n_buildings"]+OUTKEYS)
            scr=d[d.n_buildings>=10]
            rec["n"][yr]=[int(len(d)),int(len(scr))]
            rec["val"][yr]={k:(round(float(scr[k].mean()),3)) for k in OUTKEYS}
        countries.append(rec)
        print(f"  {iso} {NAMES[iso]:14s} 2016 n={rec['n']['2016']}  2023 n={rec['n']['2023']}", flush=True)
    countries.sort(key=lambda r:(r["region"], r["name"]))
    return {"years":YEARS,
            "model":{"name":"Google Open Buildings 2.5D temporal panel",
                     "note":"Retrained on count, density, built-up fraction and building HEIGHT only — the 2.5D product has no footprint-size features, so accuracy is a little lower than the v3 atlas. Scales are held fixed across countries and both years, so 2016 and 2023 are directly comparable.",
                     "n_train":4092},
            "metrics":metrics, "scales":scales, "countries":countries}

def main():
    copy_figs()
    temporal=build_temporal()
    mpath=os.path.join(ATLAS,"data","countries.json")
    m=json.load(open(mpath,encoding="utf-8"))
    m["temporal"]=temporal
    json.dump(m,open(mpath,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
    open(os.path.join(ATLAS,"assets","manifest.js"),"w",encoding="utf-8").write(
        "window.ATLAS = "+json.dumps(m,ensure_ascii=False)+";\n")
    print(f"\nDONE: temporal block added ({len(temporal['countries'])} countries × {len(YEARS)} years)", flush=True)

if __name__=="__main__": main()
