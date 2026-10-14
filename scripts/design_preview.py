"""Render design previews from PBIR positions and actual CSV. Not Desktop screenshots."""
import csv
import json
import sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Wedge, Circle
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from f1lab.strategy import simulate,optimal_stop,COMPOUNDS

BG="#080e18"; PANEL="#101826"; MUTED="#a5b4cc"; WHITE="#eef4ff"; GREEN="#74f7ce"; RED="#ff544f"
plt.rcParams.update({"font.family":"DejaVu Sans","svg.fonttype":"none","svg.hashsalt":"f1lab-v02"})


def render():
    with (ROOT/"data/sample/FactTelemetry.csv").open() as f:
        raw=[{k:float(v) for k,v in row.items()} for row in csv.DictReader(f)]
    traces={i:[r for r in raw if r["LapId"]==i] for i in (1,2)}
    current=max((r for r in traces[1] if r["TimeMs"]<=30000),key=lambda r:r["Bin"])
    x=[r["Bin"]/5 for r in traces[1]]
    labels={"Replay heading":"F1 TELEMETRY LAB / PIT WALL","Data health":"2 tours | 1 002 points | FASTF1",
       "Replay subtitle":"MONZA 2024 / QUALIFICATIONS  ·  EXPLORER UN TOUR",
       "Comparison subtitle":"MONZA 2024 / QUALIFICATIONS  ·  TROUVER LES ÉCARTS",
       "Strategy subtitle":"MODÈLE PÉDAGOGIQUE / 53 TOURS  ·  TESTER UNE STRATÉGIE",
       "Replay instruction":"Déplacez le chrono : le point agrandi indique la position.",
       "Comparison instruction":"Delta B - A : positif = B plus lent ; négatif = B plus rapide.",
       "Comparison insight":"NOR gagne 0,134 s sur LEC",
       "Strategy status":"Simulation : un arrêt, deux composés, sans trafic, météo ni safety car.",
       "Strategy insight":"Arrêt choisi : tour 24 | meilleur candidat : tour 24 | écart : 0,00 s",
       "Lap time s":"79,327","Lap time A s":"79,327","Lap time B s":"79,461","Lap delta s":"+0,134",
       "Sector 1 delta s":"−0,119","Sector 2 delta s":"+0,153","Sector 3 delta s":"+0,100",
       "Current gear":str(int(current["Gear"])),"Current brake":str(int(current["Brake"])),
       "Current throttle pct":f'{current["ThrottlePct"]:.0f}',"Current elapsed s":f'{current["TimeMs"]/1000:.3f}',
       "Replay progress pct":f'{current["Bin"]/5:.1f}',"Best stop lap":"24","Penalty vs best s":"0,00",
       "Strategy time label":"75 min 14,4 s"}
    defaults={"driver":"NOR","lapA":"NOR","lapB":"LEC","cursor":"0 ───────────●────────── 80   /   30,0 s",
              "FirstCompound":"MEDIUM","SecondCompound":"HARD","StopLap":"24","PitLoss":"22","Degradation":"1,0","BasePace":"84"}
    best=optimal_stop()
    out=ROOT/"docs/previews"; out.mkdir(parents=True,exist_ok=True)
    for page in ("Replay","Comparison","Strategy"):
        fig=plt.figure(figsize=(16,9),dpi=100,facecolor=BG)
        canvas=fig.add_axes([0,0,1,1]); canvas.set_xlim(0,1600); canvas.set_ylim(910,0); canvas.axis("off")
        folder=ROOT/"powerbi/F1 Telemetry Lab.Report/definition/pages"/page
        for f in sorted((folder/"visuals").glob("*/visual.json")):
            v=json.loads(f.read_text()); p=v["position"]; cfg=v["visual"]; kind=cfg["visualType"]; name=v["name"]
            px,py,w,h=p["x"],p["y"],p["width"],p["height"]
            canvas.add_patch(FancyBboxPatch((px,py),w,h,boxstyle="round,pad=0,rounding_size=8",fc=PANEL,ec="#253146",lw=.6))
            title=cfg["visualContainerObjects"]["title"][0]["properties"]["text"]["expr"]["Literal"]["Value"][1:-1].replace("''","'")
            if title: canvas.text(px+14,py+20,title,color=MUTED,fontsize=9,weight="bold",va="center")
            roles=cfg.get("query",{}).get("queryState",{})
            metric=lambda role: roles[role]["projections"][0]["field"].get("Measure",{}).get("Property")
            if kind=="card":
                m=metric("Values")
                font=cfg["objects"]["labels"][0]["properties"]["fontSize"]["expr"]["Literal"]["Value"]
                size=float(font[:-1])*.72
                canvas.text(px+16,py+h*.60,labels.get(m,""),color=WHITE if m in labels and not m.endswith((" s","pct")) else GREEN,fontsize=size,va="center")
            elif kind=="slicer":
                canvas.text(px+14,py+55,defaults[name],color=WHITE,fontsize=13,va="center")
                if name!="cursor": canvas.text(px+w-25,py+55,"⌄",color=MUTED,fontsize=15,va="center")
            elif kind=="scatterChart":
                ax=fig.add_axes([(px+28)/1600,(900-py-h+35)/900,(w-56)/1600,(h-75)/900],facecolor=PANEL)
                rows=traces[1]; a=[r["X"] for r in rows]; b=[r["Y"] for r in rows]
                colors=[RED if r["Brake"] else GREEN if r["SpeedKmh"]>280 else "#ffce62" if r["SpeedKmh"]>180 else "#759bff" for r in rows]
                ax.scatter(a,b,c=colors,s=5); ax.scatter([current["X"]],[current["Y"]],s=160,c=WHITE,edgecolors=GREEN,linewidths=2)
                ax.set_aspect("equal"); ax.axis("off")
                canvas.text(px+w/2,py+h-15,"● Rapide    ● Intermédiaire    ● Lent    ● Freinage",color=MUTED,fontsize=9,ha="center")
            elif kind=="gauge":
                ax=fig.add_axes([(px+30)/1600,(900-py-h+15)/900,(w-60)/1600,(h-60)/900],facecolor=PANEL)
                speed=current["SpeedKmh"]; end=180*(1-speed/360)
                ax.add_patch(Wedge((0,0),1,0,180,width=.12,color="#253146"))
                ax.add_patch(Wedge((0,0),1,end,180,width=.12,color=GREEN))
                ax.text(0,.15,f"{speed:.0f}",color=WHITE,fontsize=40,ha="center")
                ax.text(0,-.05,"km/h",color=MUTED,fontsize=12,ha="center")
                ax.set_xlim(-1.15,1.15); ax.set_ylim(-.2,1.15); ax.set_aspect("equal"); ax.axis("off")
            elif kind=="tableEx":
                if name=="pedalbars":
                    for i,(label,value,color) in enumerate([("ACCÉLÉRATEUR",current["ThrottlePct"]/100,GREEN),("FREIN",current["Brake"],RED)]):
                        yy=py+55+i*55
                        canvas.text(px+14,yy+8,label,color=MUTED,fontsize=10,va="center")
                        canvas.add_patch(FancyBboxPatch((px+180,yy),300,20,boxstyle="round,pad=0,rounding_size=3",fc="#253146",ec="none"))
                        if value: canvas.add_patch(FancyBboxPatch((px+180,yy),300*value,20,boxstyle="round,pad=0,rounding_size=3",fc=color,ec="none"))
                        canvas.text(px+500,yy+10,f"{value*100:.0f}%" if i==0 else "ON" if value else "OFF",color=WHITE,fontsize=15,va="center")
                else:
                    split=24/53*(w-60)
                    canvas.text(px+30,py+55,"MEDIUM / 24 tours",color=WHITE,fontsize=15)
                    canvas.text(px+w-30,py+55,"HARD / 29 tours",color=WHITE,fontsize=15,ha="right")
                    canvas.add_patch(FancyBboxPatch((px+30,py+68),split,22,boxstyle="square,pad=0",fc="#ffce62",ec="none"))
                    canvas.add_patch(FancyBboxPatch((px+30+split,py+68),w-60-split,22,boxstyle="square,pad=0",fc=WHITE,ec="none"))
                    canvas.text(px+w/2,py+118,"ARRÊT APRÈS LE TOUR 24",color=MUTED,fontsize=10,ha="center")
            elif kind=="lineChart":
                ax=fig.add_axes([(px+55)/1600,(900-py-h+30)/900,(w-80)/1600,(h-70)/900],facecolor=PANEL)
                ax.tick_params(colors=MUTED,labelsize=7)
                for spine in ax.spines.values(): spine.set_visible(False)
                ax.grid(axis="y",alpha=.15,color=MUTED)
                if name in ("speedtrace","compare"):
                    ax.plot(x,[r["SpeedKmh"] for r in traces[1]],c=GREEN,lw=1.5)
                    if name=="compare": ax.plot(x,[r["SpeedKmh"] for r in traces[2]],c=RED,lw=1.3)
                    else: ax.scatter([current["Bin"]/5],[current["SpeedKmh"]],s=30,c=RED)
                elif name=="pedals":
                    ax.plot(x,[r["ThrottlePct"] for r in traces[1]],c=GREEN,lw=1)
                    ax.plot(x,[r["Brake"]*100 for r in traces[1]],c=RED,lw=1)
                elif name=="deltatrace":
                    ax.axhline(0,c=MUTED,lw=.7)
                    ax.plot(x,[(b["TimeMs"]-a["TimeMs"])/1000 for a,b in zip(traces[1],traces[2])],c=GREEN,lw=1.5)
                elif name=="stints":
                    def times(stop):
                        return [84+COMPOUNDS["MEDIUM" if i<=stop else "HARD"].offset+
                                (i-1 if i<=stop else i-stop-1)*COMPOUNDS["MEDIUM" if i<=stop else "HARD"].degradation+
                                (22 if i==stop else 0) for i in range(1,54)]
                    ax.plot(range(1,54),times(24),c=GREEN,lw=1.5)
                    ax.plot(range(1,54),times(best),c=RED,lw=1,ls="--")
                else:
                    costs=[simulate(stop_lap=i)-simulate(stop_lap=best) for i in range(1,53)]
                    ax.plot(range(1,53),costs,c=GREEN,lw=1.5)
                    ax.scatter([24],[costs[23]],s=35,c=RED)
        canvas.text(24,903,"APERÇU DE CONCEPTION • données CSV réelles • rendu Power BI Desktop à valider",color=MUTED,fontsize=8)
        fig.savefig(out/(page.lower()+".svg"),metadata={"Date":None},facecolor=BG)
        fig.savefig("/tmp/f1-"+page.lower()+".png",facecolor=BG)
        plt.close(fig)
    print(out)


if __name__=="__main__": render()
