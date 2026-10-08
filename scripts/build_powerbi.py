"""Generate portable PBIP/PBIR/TMDL from a validated export."""
import argparse
import base64
import csv
import io
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from f1lab.data import validate
from f1lab.strategy import COMPOUNDS

SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/"


def dump(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")


def read_csv(path):
    with path.open(encoding="utf-8") as f: return list(csv.DictReader(f))


def q(name): return "'"+name.replace("'","''")+"'"


def table(folder, name, rows, types, measures=None):
    lines=[f"table {q(name)}", ""]
    for label,expr in (measures or {}).items():
        fence=chr(96)*3
        if "\n" in expr:
            lines += [f"\tmeasure {q(label)} = "+fence, *["\t\t\t"+s for s in expr.splitlines()], "\t\t\t"+fence]
        else:
            lines += [f"\tmeasure {q(label)} = "+expr]
        if label.endswith("SVG"): lines += ["\t\tdataCategory: ImageUrl"]
        elif label not in ("Data source", "Strategy status", "Selected driver", "Session label"):
            fmt = "0" if label in ("Current gear","Current brake","Selected bin","Best stop lap") else "0.000" if label.endswith(" s") else "0.00"
            lines += ['\t\tformatString: '+fmt]
        lines += [""]
    for col,typ in types.items():
        lines += [f"\tcolumn {q(col)}",f"\t\tdataType: {typ}",f"\t\tsourceColumn: {col}",
                  "\t\tsummarizeBy: none", ""]
    f=io.StringIO(newline="")
    w=csv.DictWriter(f,fieldnames=list(types)); w.writeheader(); w.writerows(rows)
    payload=base64.b64encode(f.getvalue().encode()).decode()
    mt={"string":"type text","int64":"Int64.Type","double":"type number","boolean":"type logical"}
    transforms=", ".join('{"'+c+'", '+mt[t]+'}' for c,t in types.items())
    lines += [f"\tpartition {q(name)} = m", "\t\tmode: import", "\t\tsource =", "\t\t\tlet",
              f'\t\t\t\tSource = Csv.Document(Binary.FromText("{payload}", BinaryEncoding.Base64), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
              '\t\t\t\tHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),',
              '\t\t\t\tTyped = Table.TransformColumnTypes(Headers, {'+transforms+'}, "en-US")',
              '\t\t\tin', '\t\t\t\tTyped', ""]
    (folder/(name+".tmdl")).write_text("\n".join(lines),encoding="utf-8")


def measures():
    m={
      "Selected bin":"SELECTEDVALUE(ReplayBin[Bin], 0)",
      "Selected driver":'SELECTEDVALUE(DimLap[Driver], "Select one driver")',
      "Data source":'CONCATENATEX(VALUES(DimLap[Source]), DimLap[Source], ", ")',
      "Session label":'CONCATENATEX(VALUES(DimLap[Session]), DimLap[Session], ", ")',
      "Lap time s":"VAR lap = SELECTEDVALUE(DimLap[LapId], 1)\nRETURN CALCULATE(MAX(DimLap[LapTimeS]), TREATAS({lap}, DimLap[LapId]))",
      "Speed trace":"VAR lap = SELECTEDVALUE(DimLap[LapId], 1)\nRETURN CALCULATE(AVERAGE(FactTelemetry[SpeedKmh]), TREATAS({lap}, DimLap[LapId]))",
      "Throttle trace":"VAR lap = SELECTEDVALUE(DimLap[LapId], 1)\nRETURN CALCULATE(AVERAGE(FactTelemetry[ThrottlePct]), TREATAS({lap}, DimLap[LapId]))",
      "Brake trace":"VAR lap = SELECTEDVALUE(DimLap[LapId], 1)\nRETURN 100 * CALCULATE(AVERAGE(FactTelemetry[Brake]), TREATAS({lap}, DimLap[LapId]))",
      "Replay progress pct":"[Selected bin] / 5",
    }
    for label,col in [("Current speed kmh","SpeedKmh"),("Current throttle pct","ThrottlePct"),
                      ("Current brake","Brake"),("Current gear","Gear"),("Current elapsed s","TimeMs")]:
        m[label]=f"VAR lap = SELECTEDVALUE(DimLap[LapId], 1)\nRETURN CALCULATE(MAX(FactTelemetry[{col}]), TREATAS({{lap}}, DimLap[LapId]), REMOVEFILTERS(DimDistance), TREATAS({{[Selected bin]}}, FactTelemetry[Bin]))"+(" / 1000" if col=="TimeMs" else "")
    for tag,sel in [("A","LapA"),("B","LapB")]:
        for label,col in [("Speed","SpeedKmh"),("Elapsed","TimeMs")]:
            m[f"{label} {tag}"]=f"VAR lap = SELECTEDVALUE({sel}[LapId], {1 if tag=='A' else 2})\nRETURN CALCULATE(MAX(FactTelemetry[{col}]), REMOVEFILTERS(DimLap), TREATAS({{lap}}, DimLap[LapId]))"+(" / 1000" if col=="TimeMs" else "")
        m[f"Lap time {tag} s"]=f"VAR lap = SELECTEDVALUE({sel}[LapId], {1 if tag=='A' else 2})\nRETURN CALCULATE(MAX(DimLap[LapTimeS]), REMOVEFILTERS(DimLap), TREATAS({{lap}}, DimLap[LapId]))"
        for n in (1,2,3):
            m[f"Sector {n} {tag} s"]=f"VAR lap = SELECTEDVALUE({sel}[LapId], {1 if tag=='A' else 2})\nRETURN CALCULATE(MAX(DimLap[S{n}]), REMOVEFILTERS(DimLap), TREATAS({{lap}}, DimLap[LapId]))"
    m["Delta B minus A s"]="[Elapsed B] - [Elapsed A]"
    m["Lap delta s"]="[Lap time B s] - [Lap time A s]"
    for n in (1,2,3): m[f"Sector {n} delta s"]=f"[Sector {n} B s] - [Sector {n} A s]"
    m["Strategy status"]='IF(SELECTEDVALUE(FirstCompound[Compound], "MEDIUM") = SELECTEDVALUE(SecondCompound[Compound], "HARD"), "INVALID: choose two distinct compounds", "EDUCATIONAL MODEL | dry race | one stop")'
    m["Strategy total s"]='''VAR first = SELECTEDVALUE(FirstCompound[Compound], "MEDIUM")
VAR second = SELECTEDVALUE(SecondCompound[Compound], "HARD")
VAR stop = SELECTEDVALUE(StopLap[Lap], 24)
VAR remaining = 53 - stop
VAR pit = SELECTEDVALUE(PitLoss[Seconds], 22)
VAR mult = SELECTEDVALUE(Degradation[Multiplier], 1)
VAR base = SELECTEDVALUE(BasePace[Seconds], 84)
VAR o1 = LOOKUPVALUE(Compound[Offset], Compound[Compound], first)
VAR o2 = LOOKUPVALUE(Compound[Offset], Compound[Compound], second)
VAR d1 = LOOKUPVALUE(Compound[Degradation], Compound[Compound], first) * mult
VAR d2 = LOOKUPVALUE(Compound[Degradation], Compound[Compound], second) * mult
RETURN IF(first <> second, stop*(base+o1) + d1*stop*(stop-1)/2 + remaining*(base+o2) + d2*remaining*(remaining-1)/2 + pit)'''
    m["Strategy total min"]="[Strategy total s] / 60"
    m["Candidate total s"]="VAR stop = SELECTEDVALUE(CandidateStop[Lap])\nRETURN IF(NOT ISBLANK(stop), CALCULATE([Strategy total s], REMOVEFILTERS(StopLap), TREATAS({stop}, StopLap[Lap])))"
    m["Best stop lap"]="VAR candidates = ADDCOLUMNS(ALL(CandidateStop[Lap]), \"Cost\", [Candidate total s])\nVAR best = TOPN(1, FILTER(candidates, NOT ISBLANK([Cost])), [Cost], ASC, CandidateStop[Lap], ASC)\nRETURN MAXX(best, CandidateStop[Lap])"
    m["Penalty vs best s"]="VAR candidates = ADDCOLUMNS(ALL(CandidateStop[Lap]), \"Cost\", [Candidate total s])\nRETURN IF(NOT ISBLANK([Strategy total s]), [Strategy total s] - MINX(candidates, [Cost]))"
    m["Simulated lap s"]='''VAR lap = SELECTEDVALUE(RaceLap[Lap])
VAR stop = SELECTEDVALUE(StopLap[Lap], 24)
VAR first = SELECTEDVALUE(FirstCompound[Compound], "MEDIUM")
VAR second = SELECTEDVALUE(SecondCompound[Compound], "HARD")
VAR compound = IF(lap <= stop, first, second)
VAR age = IF(lap <= stop, lap - 1, lap - stop - 1)
VAR base = SELECTEDVALUE(BasePace[Seconds], 84)
VAR mult = SELECTEDVALUE(Degradation[Multiplier], 1)
RETURN IF(first <> second && NOT ISBLANK(lap), base + LOOKUPVALUE(Compound[Offset], Compound[Compound], compound) + age * mult * LOOKUPVALUE(Compound[Degradation], Compound[Compound], compound) + IF(lap = stop, SELECTEDVALUE(PitLoss[Seconds], 22), 0))'''
    m["Track SVG"]='''VAR lap = SELECTEDVALUE(DimLap[LapId], 1)
VAR bin = [Selected bin]
VAR points = CALCULATETABLE(FactTelemetry, REMOVEFILTERS(DimDistance), TREATAS({lap}, DimLap[LapId]))
VAR track = CONCATENATEX(points, FORMAT(FactTelemetry[SVGX], "0.0", "en-US") & "," & FORMAT(FactTelemetry[SVGY], "0.0", "en-US"), " ", FactTelemetry[Bin], ASC)
VAR x = MAXX(FILTER(points, FactTelemetry[Bin] = bin), FactTelemetry[SVGX])
VAR y = MAXX(FILTER(points, FactTelemetry[Bin] = bin), FactTelemetry[SVGY])
VAR svg = "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 640 460'><rect width='640' height='460' fill='#101826'/><polyline points='" & track & "' fill='none' stroke='#29374c' stroke-width='16' stroke-linejoin='round'/><polyline points='" & track & "' fill='none' stroke='#74f7ce' stroke-width='3'/><circle cx='" & FORMAT(x,"0.0","en-US") & "' cy='" & FORMAT(y,"0.0","en-US") & "' r='9' fill='#ff544f' stroke='white' stroke-width='3'/></svg>"
RETURN IF(NOT ISBLANK(lap), "data:image/svg+xml;utf8," & SUBSTITUTE(svg, "#", "%23"))'''
    # Avoid collisions with the Compound table and potential function names.
    for name,text in m.items():
        for old,new in (("first","tyreOne"),("second","tyreTwo"),("compound","chosenTyre")):
            text=re.sub(r"\b"+old+r"\b",new,text)
        m[name]=text
    return m


def expr(t,c,measure=False):
    return {"Measure" if measure else "Column":{"Expression":{"SourceRef":{"Entity":t}},"Property":c}}


def projection(t,c,measure=False):
    return {"field":expr(t,c,measure),"queryRef":t+"."+c,"nativeQueryRef":c}


def literal(v):
    if isinstance(v,bool): v="true" if v else "false"
    elif isinstance(v,(int,float)): v=str(v)+"D"
    else: v="'"+v.replace("'","''")+"'"
    return {"expr":{"Literal":{"Value":v}}}


def obj(**kwargs): return [{"properties":{k:literal(v) for k,v in kwargs.items()}}]


def visual(page,name,kind,title,x,y,w,h,roles=None,objects=None):
    config={"visualType":kind,"drillFilterOtherVisuals":True,
        "visualContainerObjects":{
            "title":obj(show=True,text=title,fontColor="#eef4ff",fontSize=12,bold=True,fontFamily="Segoe UI"),
            "background":[{"properties":{"show":literal(True),"color":{"solid":{"color":literal("#101826")}},"transparency":literal(0)}}],
            "border":obj(show=True,color="#29374c",radius=8),
            "general":obj(altText=title)}}
    if roles: config["query"]={"queryState":{role:{"projections":ps} for role,ps in roles.items()}}
    if objects: config["objects"]=objects
    if kind=="lineChart" and roles and "Category" in roles:
        config["query"]["sortDefinition"]={"sort":[{"field":roles["Category"][0]["field"],"direction":"Ascending"}],"isDefaultSort":True}
    dump(page/"visuals"/name/"visual.json",{"$schema":SCHEMA+"visualContainer/2.1.0/schema.json", "name":name,
          "position":{"x":x,"y":y,"width":w,"height":h,"z":1,"tabOrder":len(list((page/"visuals").glob("*"))) if (page/"visuals").exists() else 0},"visual":config})


def card(page,name,measure,title,x,y,w=220,h=115):
    visual(page,name,"card",title,x,y,w,h,{"Values":[projection("Metrics",measure,True)]},
           {"labels":obj(color="#74f7ce",fontSize=30),"categoryLabels":obj(show=False)})


def slicer(page,name,t,c,title,x,y,w=220,h=85):
    visual(page,name,"slicer",title,x,y,w,h,{"Values":[projection(t,c)]},
        {"data":obj(mode="Dropdown"),"selection":obj(singleSelect=True,selectAllCheckboxEnabled=False),
         "items":obj(fontColor="#eef4ff",background="#101826"),"header":obj(show=False)})


def line(page,name,axis,ys,title,x,y,w,h):
    visual(page,name,"lineChart",title,x,y,w,h,{"Category":[projection(*axis)],"Y":[projection("Metrics",s,True) for s in ys]},
        {"categoryAxis":obj(labelColor="#a5b4cc",show=True),"valueAxis":obj(labelColor="#a5b4cc",show=True),
         "legend":obj(show=True,labelColor="#eef4ff"),"lineStyles":obj(strokeWidth=3)})


def build(data_dir,output):
    output.mkdir(parents=True,exist_ok=True)
    report=output/"F1 Telemetry Lab.Report"
    semantic=output/"F1 Telemetry Lab.SemanticModel"
    for p in [report/"definition",semantic/"definition"]:
        if p.exists(): shutil.rmtree(p)
    tables=semantic/"definition"/"tables"; tables.mkdir(parents=True)
    laps=read_csv(data_dir/"DimLap.csv"); tel=read_csv(data_dir/"FactTelemetry.csv")
    lt={"LapId":"int64","Driver":"string","LapNumber":"int64","LapTimeS":"double","S1":"double","S2":"double","S3":"double","Source":"string","Session":"string","Circuit":"string"}
    tt={c:("int64" if c in ("LapId","Bin","Brake","Gear","RPM","Sector") else "double") for c in tel[0]}
    numeric=lambda rows,types:[{k:(int(v) if types[k]=="int64" else float(v) if types[k]=="double" else v) for k,v in r.items()} for r in rows]
    laps=numeric(laps,lt); tel=numeric(tel,tt); validate(laps,tel)
    for lap_id in (1,2):
        points=[r for r in tel if r["LapId"]==lap_id]
        xmin,xmax=min(r["X"] for r in points),max(r["X"] for r in points)
        ymin,ymax=min(r["Y"] for r in points),max(r["Y"] for r in points)
        scale=min(560/max(1,xmax-xmin),380/max(1,ymax-ymin))
        for r in points:
            r["SVGX"]=round(320+(r["X"]-(xmin+xmax)/2)*scale,3)
            r["SVGY"]=round(230-(r["Y"]-(ymin+ymax)/2)*scale,3)
    tt.update(SVGX="double",SVGY="double")
    table(tables,"DimLap",laps,lt)
    table(tables,"FactTelemetry",tel,tt)
    table(tables,"DimDistance",[{"Bin":i,"ProgressPct":i/5} for i in range(501)],{"Bin":"int64","ProgressPct":"double"})
    table(tables,"ReplayBin",[{"Bin":i,"ProgressPct":i/5} for i in range(501)],{"Bin":"int64","ProgressPct":"double"})
    for n in ("LapA","LapB"): table(tables,n,[{"LapId":r["LapId"],"Driver":r["Driver"]} for r in laps],{"LapId":"int64","Driver":"string"})
    table(tables,"Compound",[{"Compound":c.name,"Offset":c.offset,"Degradation":c.degradation} for c in COMPOUNDS.values()],{"Compound":"string","Offset":"double","Degradation":"double"})
    for n in ("FirstCompound","SecondCompound"):
        table(tables,n,[{"Compound":c} for c in COMPOUNDS],{"Compound":"string"})
    for n,col,vals,typ in [("StopLap","Lap",range(1,53),"int64"),("CandidateStop","Lap",range(1,53),"int64"),
                           ("RaceLap","Lap",range(1,54),"int64"),("PitLoss","Seconds",range(15,36),"int64"),
                           ("BasePace","Seconds",range(75,96),"int64"),("Degradation","Multiplier",[i/10 for i in range(5,21)],"double")]:
        table(tables,n,[{col:v} for v in vals],{col:typ})
    table(tables,"Metrics",[{"Anchor":1}],{"Anchor":"int64"},measures())
    refs="\n".join("ref table "+q(p.stem) for p in sorted(tables.glob("*.tmdl")))
    (semantic/"definition"/"database.tmdl").write_text("database 'F1 Telemetry Lab'\n\tcompatibilityLevel: 1600\n\tcompatibilityMode: powerBI\n")
    (semantic/"definition"/"model.tmdl").write_text("model Model\n\tculture: en-US\n\tdefaultPowerBIDataSourceVersion: powerBI_V3\n\tsourceQueryCulture: en-US\n\tdataAccessOptions\n\t\tlegacyRedirects\n\t\treturnErrorValuesAsNull\n\n"+refs+"\n")
    (semantic/"definition"/"relationships.tmdl").write_text(
        "relationship lap_telemetry\n\tfromColumn: FactTelemetry.LapId\n\ttoColumn: DimLap.LapId\n\n"
        "relationship distance_telemetry\n\tfromColumn: FactTelemetry.Bin\n\ttoColumn: DimDistance.Bin\n")
    dump(semantic/"definition.pbism",{"$schema":"https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json","version":"4.2","settings":{}})
    dump(output/"F1 Telemetry Lab.pbip",{"$schema":"https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json","version":"1.0","artifacts":[{"report":{"path":"F1 Telemetry Lab.Report"}}],"settings":{"enableAutoRecovery":True}})
    dump(report/"definition.pbir",{"$schema":"https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json","version":"4.0","datasetReference":{"byPath":{"path":"../F1 Telemetry Lab.SemanticModel"}}})
    dump(report/"definition"/"version.json",{"$schema":SCHEMA+"versionMetadata/1.0.0/schema.json","version":"2.0.0"})
    theme={"name":"F1 Midnight","dataColors":["#74f7ce","#ff544f","#ffce62","#759bff"],"background":"#080e18","foreground":"#eef4ff","tableAccent":"#74f7ce"}
    dump(report/"StaticResources"/"RegisteredResources"/"F1Midnight.json",theme)
    dump(report/"definition"/"report.json",{"$schema":SCHEMA+"report/3.1.0/schema.json",
          "themeCollection":{"customTheme":{"name":"F1Midnight","reportVersionAtImport":{"visual":"2.1.0","report":"3.1.0","page":"1.0.0"},"type":"RegisteredResources"}},
          "resourcePackages":[{"name":"RegisteredResources","type":"RegisteredResources","items":[{"name":"F1Midnight","path":"F1Midnight.json","type":"CustomTheme"}]}]})
    names=["Replay","Comparison","Strategy"]
    dump(report/"definition"/"pages"/"pages.json",{"$schema":SCHEMA+"pagesMetadata/1.0.0/schema.json","pageOrder":names,"activePageName":"Replay"})
    for n,title in zip(names,["01 · Telemetry Replay","02 · Lap Performance","03 · Strategy Simulator"]):
        page=report/"definition"/"pages"/n
        dump(page/"page.json",{"$schema":SCHEMA+"page/1.0.0/schema.json","name":n,"displayName":title,"displayOption":"FitToPage","height":900,"width":1600,
              "objects":{"background":[{"properties":{"color":{"solid":{"color":literal("#080e18")}},"transparency":literal(0)}}]}})
        card(page,"source","Data source","F1 TELEMETRY LAB · "+title,24,18,1000,70)
        card(page,"session","Session label","SESSION / PROVENANCE",1040,18,536,70)
    p=report/"definition"/"pages"/"Replay"
    slicer(p,"driver","DimLap","Driver","SELECT ONE DRIVER",24,110,300)
    slicer(p,"cursor","ReplayBin","Bin","REPLAY CURSOR · bin 0–500",344,110,390)
    card(p,"speed","Current speed kmh","SPEED · km/h",754,110,260)
    card(p,"gear","Current gear","GEAR",1034,110,260)
    card(p,"elapsed","Current elapsed s","ELAPSED · seconds",1314,110,262)
    visual(p,"track","tableEx","CIRCUIT POSITION · SVG / DAX",24,245,710,480,{"Values":[projection("Metrics","Track SVG",True)]},
           {"grid":obj(imageHeight=420,outlineColor="#101826"),"columnHeaders":obj(show=False),"total":obj(totals=False)})
    line(p,"speedtrace",("DimDistance","ProgressPct"),["Speed trace"],"SPEED PROFILE · circuit progress %",754,245,822,230)
    line(p,"pedals",("DimDistance","ProgressPct"),["Throttle trace","Brake trace"],"THROTTLE / BRAKE · %",754,495,822,230)
    card(p,"throttle","Current throttle pct","THROTTLE · %",24,745,350)
    card(p,"brake","Current brake","BRAKE · 0 / 1",394,745,340)
    card(p,"laptime","Lap time s","LAP TIME · seconds",754,745,392)
    card(p,"progress","Replay progress pct","PROGRESS · %",1166,745,410)
    p=report/"definition"/"pages"/"Comparison"
    slicer(p,"lapA","LapA","Driver","REFERENCE A",24,110,350)
    slicer(p,"lapB","LapB","Driver","COMPARISON B",394,110,350)
    card(p,"timeA","Lap time A s","LAP A · seconds",764,110,250)
    card(p,"timeB","Lap time B s","LAP B · seconds",1034,110,250)
    card(p,"delta","Lap delta s","B − A · seconds",1304,110,272)
    line(p,"compare",("DimDistance","ProgressPct"),["Speed A","Speed B"],"SPEED OVERLAY · aligned at equal circuit progress",24,245,1552,300)
    line(p,"deltatrace",("DimDistance","ProgressPct"),["Delta B minus A s"],"DELTA B − A · positive = B slower",24,565,1060,300)
    for i in (1,2,3): card(p,"sector"+str(i),f"Sector {i} delta s",f"SECTOR {i} · B − A seconds",1104,565+(i-1)*100,472,90)
    p=report/"definition"/"pages"/"Strategy"
    for i,(t,c,title) in enumerate([("FirstCompound","Compound","STINT 1 TYRE"),("SecondCompound","Compound","STINT 2 TYRE"),
          ("StopLap","Lap","PIT AFTER LAP"),("PitLoss","Seconds","PIT LOSS · seconds"),("Degradation","Multiplier","DEGRADATION ×"),("BasePace","Seconds","BASE LAP · seconds")]):
        slicer(p,t,t,c,title,24+i*260,110,252)
    card(p,"status","Strategy status","MODEL ASSUMPTIONS · 53 laps / one stop",24,215,1552,80)
    card(p,"total","Strategy total min","RACE TOTAL · minutes",24,315,500)
    card(p,"optimal","Best stop lap","BEST STOP · selected assumptions",544,315,500)
    card(p,"penalty","Penalty vs best s","PENALTY VS BEST · seconds",1064,315,512)
    line(p,"stints",("RaceLap","Lap"),["Simulated lap s"],"SIMULATED LAP TIME · pit loss charged to in-lap",24,455,760,410)
    line(p,"candidates",("CandidateStop","Lap"),["Candidate total s"],"STRATEGY SWEEP · race seconds by stop lap",804,455,772,410)
    print(f"Generated portable PBIP at {output}")


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--data",type=Path,default=ROOT/"data"/"sample")
    p.add_argument("--output",type=Path,default=ROOT/"powerbi")
    a=p.parse_args(); build(a.data,a.output)
