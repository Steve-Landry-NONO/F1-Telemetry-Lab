"""Export a compact model with common distance bins for fair lap comparison."""
import csv
import hashlib
import json
import math
from pathlib import Path

TELEMETRY_COLUMNS = ["LapId", "Bin", "DistanceM", "TimeMs", "SpeedKmh", "ThrottlePct",
                     "Brake", "Gear", "RPM", "X", "Y", "Sector"]
# Stylised demonstration track only, not surveyed Monza geometry.
TRACK = [(0,0),(25,-145),(36,-220),(47,-228),(43,-245),(32,-249),(34,-270),
         (65,-315),(120,-342),(185,-350),(230,-330),(241,-300),(235,-278),
         (256,-260),(285,-250),(323,-218),(345,-173),(340,-133),(309,-118),
         (290,-95),(307,-68),(342,-20),(368,37),(361,76),(328,99),(278,101),
         (217,87),(164,70),(118,57),(72,40),(30,21),(0,0)]


def write_csv(path, rows, columns=None):
    rows = list(rows)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columns or list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def track_point(progress):
    lengths = [math.hypot(b[0]-a[0], b[1]-a[1]) for a,b in zip(TRACK,TRACK[1:])]
    target = progress * sum(lengths)
    for i, length in enumerate(lengths):
        if target <= length or i == len(lengths)-1:
            p = min(1, target/length)
            a,b = TRACK[i:i+2]
            return a[0]+p*(b[0]-a[0]), a[1]+p*(b[1]-a[1])
        target -= length


def demo(output):
    output = Path(output)
    laps, telemetry = [], []
    for lap_id, driver, advantage in [(1,"DEMO A",0), (2,"DEMO B",1.6)]:
        elapsed = 0.0
        previous_speed = None
        lap_rows = []
        for b in range(501):
            p = b/500
            speed = 326 - sum(depth*math.exp(-((p-center)/width)**2)
                for center,width,depth in [(0.15,.024,235),(.32,.025,210),(.47,.04,155),
                                           (.64,.03,200),(.87,.06,140)])
            speed += advantage*math.sin(p*math.pi*6)
            braking = previous_speed is not None and speed < previous_speed-2
            if b:
                elapsed += (5793/500) / ((speed+previous_speed)/2/3.6)
            x,y = track_point(p)
            lap_rows.append(dict(zip(TELEMETRY_COLUMNS,[lap_id,b,round(p*5793,3),
                round(elapsed*1000,3),round(speed,3),0 if braking else round(min(100,speed/2.8),2),
                int(braking),max(1,min(8,int(speed/43)+1)),round(6500+speed*18),
                round(x,3),round(y,3),min(3,int(p*3)+1)])))
            previous_speed = speed
        telemetry.extend(lap_rows)
        sectors = [lap_rows[167]["TimeMs"]/1000,
                   (lap_rows[334]["TimeMs"]-lap_rows[167]["TimeMs"])/1000,
                   (lap_rows[-1]["TimeMs"]-lap_rows[334]["TimeMs"])/1000]
        laps.append({"LapId":lap_id,"Driver":driver,"LapNumber":lap_id,
                     "LapTimeS":round(elapsed,6),"S1":sectors[0],"S2":sectors[1],"S3":sectors[2],
                     "Source":"SYNTHETIC DEMO", "Session":"Stylised Monza demo", "Circuit":"Monza (stylised)"})
    export(output, laps, telemetry, {"source":"synthetic", "description":
        "Deterministic invented telemetry and stylised geometry; not real drivers or race observations."})


def export(output, laps, telemetry, provenance):
    output = Path(output)
    validate(laps, telemetry)
    write_csv(output/"DimLap.csv",laps)
    write_csv(output/"FactTelemetry.csv",telemetry, TELEMETRY_COLUMNS)
    write_csv(output/"DimDistance.csv",[{"Bin":b,"ProgressPct":b/5} for b in range(501)])
    provenance["sha256"] = {p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                             for p in sorted(output.glob("*.csv"))}
    (output/"manifest.json").write_text(json.dumps(provenance,indent=2)+"\n")


def validate(laps, telemetry):
    ids = {int(r["LapId"]) for r in laps}
    if len(ids) != 2 or len(laps) != 2:
        raise ValueError("MVP requires exactly two unique laps")
    for lap in laps:
        rows = [r for r in telemetry if int(r["LapId"]) == int(lap["LapId"])]
        if [int(r["Bin"]) for r in rows] != list(range(501)):
            raise ValueError("Each lap must contain 501 ordered, unique common-distance bins")
        if abs(float(rows[-1]["TimeMs"])/1000-float(lap["LapTimeS"])) > .05:
            raise ValueError("Final telemetry time does not match lap time")
        for i,r in enumerate(rows):
            if not all(math.isfinite(float(r[c])) for c in TELEMETRY_COLUMNS):
                raise ValueError("Non-finite telemetry")
            if not (0 <= r["ThrottlePct"] <= 100 and r["Brake"] in (0,1)
                    and 0 <= r["Gear"] <= 8 and 0 <= r["SpeedKmh"] <= 400):
                raise ValueError("Telemetry outside physical bounds")
            if i and (r["TimeMs"] <= rows[i-1]["TimeMs"] or r["DistanceM"] <= rows[i-1]["DistanceM"]):
                raise ValueError("Time and distance must increase")
    if {r["LapId"] for r in telemetry} != ids:
        raise ValueError("Unknown lap foreign key")


def real(output, year=2024, event="Italy", session_code="Q", drivers=("NOR","LEC"), cache=".cache/fastf1"):
    import fastf1
    import numpy as np
    Path(cache).mkdir(parents=True,exist_ok=True)
    fastf1.Cache.enable_cache(cache)
    session = fastf1.get_session(year,event,session_code)
    session.load(weather=False,messages=False)
    selected = [session.laps.pick_drivers(d).pick_fastest() for d in drivers]
    if any(lap is None or not bool(lap["IsAccurate"]) for lap in selected):
        raise ValueError("Two accurate fastest laps required")
    raw = [lap.get_telemetry().add_distance() for lap in selected]
    # Normalize distance per lap: comparison is at equal circuit progress.
    telemetry,laps = [],[]
    for lap_id,(driver,lap,tel) in enumerate(zip(drivers,selected,raw),1):
        t = tel["Time"].dt.total_seconds().to_numpy()
        lap_time = lap["LapTime"].total_seconds()
        # Retain samples strictly within lap; add exact endpoint times before interpolation.
        mask=(t>=0)&(t<=lap_time)
        tel=tel.loc[mask].copy(); t=t[mask]
        dist=tel["Distance"].to_numpy()
        unique=np.r_[True,np.diff(dist)>0]
        tel=tel.iloc[np.flatnonzero(unique)]; t=t[unique]; dist=dist[unique]
        if len(dist)<50 or dist[-1]<=dist[0]:
            raise ValueError("Insufficient monotonic telemetry")
        p=(dist-dist[0])/(dist[-1]-dist[0])
        grid=np.linspace(0,1,501)
        times=np.interp(grid,p,t)
        # Scale elapsed time to exact official lap endpoints, preserve interior shape.
        times=(times-times[0])/(times[-1]-times[0])*lap_time
        channels={}
        for col in ["Speed","Throttle","RPM","X","Y"]:
            channels[col]=np.interp(grid,p,tel[col].to_numpy(dtype=float))
        nearest=np.searchsorted(p,grid).clip(0,len(p)-1)
        s1,s2,s3=[lap[f"Sector{i}Time"].total_seconds() for i in (1,2,3)]
        for b in range(501):
            telemetry.append(dict(zip(TELEMETRY_COLUMNS,[lap_id,b,round(grid[b]*5793,3),
                round(times[b]*1000,3),round(channels["Speed"][b],3),round(channels["Throttle"][b],3),
                int(bool(tel.iloc[nearest[b]]["Brake"])),int(tel.iloc[nearest[b]]["nGear"]),
                round(channels["RPM"][b]),round(channels["X"][b],3),round(channels["Y"][b],3),
                1 if times[b]<s1 else 2 if times[b]<s1+s2 else 3])))
        laps.append({"LapId":lap_id,"Driver":driver,"LapNumber":int(lap["LapNumber"]),
                     "LapTimeS":lap_time,"S1":s1,"S2":s2,"S3":s3,"Source":"FASTF1 HISTORICAL",
                     "Session":f"{year} {event} {session_code}","Circuit":"Monza"})
    export(output,laps,telemetry,{"source":"fastf1", "year":year,"event":event,
        "session":session_code,"drivers":list(drivers),"fastf1_version":fastf1.__version__,
        "processing":"501 normalized-distance bins; linear continuous channels, next-sample discrete channels; elapsed time endpoint correction; nominal Monza distance 5793m"})
