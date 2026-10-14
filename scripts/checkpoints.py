"""Expected Desktop values calculated independently from CSV, not from DAX."""
import csv
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from f1lab.strategy import simulate, optimal_stop


def expected():
    with (ROOT/"data/sample/FactTelemetry.csv").open() as f:
        rows=[{k:float(v) for k,v in row.items()} for row in csv.DictReader(f)]
    checkpoints=[]
    for lap,driver in ((1,"NOR"),(2,"LEC")):
        points=[r for r in rows if r["LapId"]==lap]
        for seconds in (0,30,60,80):
            r=max((r for r in points if r["TimeMs"]<=seconds*1000),key=lambda r:r["Bin"])
            checkpoints.append({"driver":driver,"requested_s":seconds,"bin":int(r["Bin"]),
                "elapsed_s":r["TimeMs"]/1000,"speed_kmh":r["SpeedKmh"],
                "gear":int(r["Gear"]),"throttle_pct":r["ThrottlePct"],
                "brake":int(r["Brake"]),"progress_pct":r["Bin"]/5})
    scenarios=[]
    for stop,pit,mult in ((24,22,1),(35,22,1),(24,32,1),(24,22,2)):
        best=optimal_stop(pit_loss=pit,multiplier=mult)
        total=simulate(stop_lap=stop,pit_loss=pit,multiplier=mult)
        scenarios.append({"first":"MEDIUM","second":"HARD","stop_lap":stop,"pit_loss_s":pit,
            "degradation_multiplier":mult,"base_s":84,"total_s":total,"best_stop":best,
            "penalty_s":total-simulate(stop_lap=best,pit_loss=pit,multiplier=mult)})
    return {"notice":"Independent Python expectations; DAX and Desktop rendering still require local verification.",
            "replay":checkpoints,"comparison":{"A":"NOR","B":"LEC","delta_s":.134,
            "sector_deltas_s":[-.119,.153,.100]},"strategy":scenarios}


if __name__=="__main__":
    path=ROOT/"docs/validation/expected.json"; path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(expected(),indent=2)+"\n")
    print(path)
