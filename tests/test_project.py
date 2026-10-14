import base64
import csv
import io
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
sys.path.insert(0,str(ROOT/"scripts"))
from f1lab.data import demo, validate
from f1lab.strategy import COMPOUNDS, simulate, optimal_stop
from build_powerbi import build, measures
from checkpoints import expected


class DataTests(unittest.TestCase):
    def test_demo_reproducible(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            demo(a); demo(b)
            for f in Path(a).glob("*"):
                self.assertEqual(f.read_bytes(), (Path(b)/f.name).read_bytes())

    def test_real_sample_endpoints_and_sector_totals(self):
        with (ROOT/"data/sample/DimLap.csv").open() as f:
            laps=list(csv.DictReader(f))
        with (ROOT/"data/sample/FactTelemetry.csv").open() as f:
            tel=list(csv.DictReader(f))
        for lap in laps:
            rows=[r for r in tel if r["LapId"]==lap["LapId"]]
            self.assertEqual(len(rows),501)
            self.assertAlmostEqual(float(rows[0]["TimeMs"]),0)
            self.assertAlmostEqual(float(rows[-1]["TimeMs"])/1000,float(lap["LapTimeS"]),places=5)
            self.assertAlmostEqual(sum(float(lap[f"S{i}"]) for i in (1,2,3)),float(lap["LapTimeS"]),places=5)
            self.assertTrue(all(float(a["TimeMs"])<float(b["TimeMs"]) for a,b in zip(rows,rows[1:])))
        self.assertAlmostEqual(float(laps[1]["LapTimeS"])-float(laps[0]["LapTimeS"]),.134)

    def test_quality_gate_rejects_missing_bins(self):
        with tempfile.TemporaryDirectory() as d:
            demo(d)
            with (Path(d)/"DimLap.csv").open() as f:
                laps=[{k:(float(v) if k in ("LapId","LapTimeS","S1","S2","S3","LapNumber") else v) for k,v in r.items()} for r in csv.DictReader(f)]
            with (Path(d)/"FactTelemetry.csv").open() as f:
                tel=[{k:float(v) for k,v in r.items()} for r in csv.DictReader(f)]
            with self.assertRaises(ValueError): validate(laps,tel[:-1])


class StrategyTests(unittest.TestCase):
    def test_closed_form_matches_sum_of_laps(self):
        for stop in (1,24,52):
            for first,second in (("SOFT","MEDIUM"),("MEDIUM","HARD"),("HARD","SOFT")):
                for mult in (.5,1,2):
                    total=0
                    for lap in range(1,54):
                        c=COMPOUNDS[first if lap<=stop else second]
                        age=lap-1 if lap<=stop else lap-stop-1
                        total+=84+c.offset+c.degradation*mult*age+(22 if lap==stop else 0)
                    self.assertAlmostEqual(simulate(stop_lap=stop,first=first,second=second,multiplier=mult),total)

    def test_pit_loss_is_charged_once(self):
        self.assertAlmostEqual(simulate(pit_loss=32)-simulate(pit_loss=22),10)

    def test_best_stop_exhaustive_and_nonnegative_penalty(self):
        best=optimal_stop()
        best_cost=simulate(stop_lap=best)
        self.assertTrue(all(simulate(stop_lap=s)>=best_cost for s in range(1,53)))

    def test_invalid_scenarios(self):
        for args in ({"stop_lap":0},{"stop_lap":53},{"pit_loss":-1},{"first":"HARD","second":"HARD"}):
            with self.assertRaises(ValueError): simulate(**args)


class ReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        cls.output=Path(cls.tmp.name)
        build(ROOT/"data/sample",cls.output)

    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()

    def test_visual_bindings_and_canvas(self):
        tables={p.stem:p.read_text() for p in (self.output/"F1 Telemetry Lab.SemanticModel/definition/tables").glob("*.tmdl")}
        m=measures()
        for f in self.output.rglob("visual.json"):
            v=json.loads(f.read_text()); pos=v["position"]
            self.assertLessEqual(pos["x"]+pos["width"],1600)
            self.assertLessEqual(pos["y"]+pos["height"],900)
            for role in v["visual"].get("query",{}).get("queryState",{}).values():
                for p in role["projections"]:
                    typ,node=next(iter(p["field"].items()))
                    t=node["Expression"]["SourceRef"]["Entity"]; c=node["Property"]
                    self.assertIn(t,tables)
                    if typ=="Measure": self.assertIn(c,m)
                    else: self.assertIn("column '"+c+"'",tables[t])

    def test_embedded_data_roundtrip(self):
        path=self.output/"F1 Telemetry Lab.SemanticModel/definition/tables/FactTelemetry.tmdl"
        encoded=re.search(r'Binary.FromText\("([^"]+)"',path.read_text()).group(1)
        rows=list(csv.DictReader(io.StringIO(base64.b64decode(encoded).decode())))
        self.assertEqual(len(rows),1002)
        self.assertEqual({r["LapId"] for r in rows},{"1","2"})
        self.assertTrue(all(0<=float(r["SVGX"])<=640 and 0<=float(r["SVGY"])<=460 for r in rows))

    def test_measures_reference_existing_measures(self):
        m=measures()
        for text in m.values():
            for ref in re.findall(r"(?<![\w'])\[([^\]]+)\]",text):
                self.assertTrue(ref in m or ref=="Cost",ref)

    def test_model_relationships_are_single_direction_star(self):
        text=(self.output/"F1 Telemetry Lab.SemanticModel/definition/relationships.tmdl").read_text()
        self.assertEqual(text.count("relationship "),2)
        self.assertNotIn("bothDirections",text)

    def test_dax_variables_do_not_collide_with_tables(self):
        tables={p.stem.lower() for p in (self.output/"F1 Telemetry Lab.SemanticModel/definition/tables").glob("*.tmdl")}
        for text in measures().values():
            for name in re.findall(r"\bVAR\s+(\w+)",text):
                self.assertNotIn(name.lower(),tables)

    def test_defaults_are_saved_in_slicers(self):
        defaults={"driver":"NOR","lapA":"NOR","lapB":"LEC","FirstCompound":"MEDIUM","SecondCompound":"HARD",
                  "StopLap":"24L","PitLoss":"22L","Degradation":"1L","BasePace":"84L"}
        for path in self.output.rglob("visual.json"):
            v=json.loads(path.read_text())
            if v["name"] not in defaults: continue
            filt=v["visual"]["objects"]["general"][0]["properties"]["filter"]["filter"]
            value=filt["Where"][0]["Condition"]["In"]["Values"][0][0]["Literal"]["Value"].strip("'")
            self.assertEqual(value,defaults[v["name"]])

    def test_slider_uses_elapsed_time_and_before_filter(self):
        v=json.loads((self.output/"F1 Telemetry Lab.Report/definition/pages/Replay/visuals/cursor/visual.json").read_text())
        self.assertEqual(v["visual"]["objects"]["data"][0]["properties"]["mode"]["expr"]["Literal"]["Value"],"'Before'")
        cond=v["visual"]["objects"]["general"][0]["properties"]["filter"]["filter"]["Where"][0]["Condition"]["Comparison"]
        self.assertEqual(cond["ComparisonKind"],4)
        self.assertIn("ReplayTime[Seconds]",measures()["Replay time request s"])
        self.assertIn("FactTelemetry[TimeMs] <= timeLimit",measures()["Selected bin"])

    def test_independent_replay_checkpoints(self):
        states=expected()["replay"]
        for driver in ("NOR","LEC"):
            points=[p for p in states if p["driver"]==driver]
            self.assertEqual(points[0]["bin"],0)
            self.assertEqual(points[-1]["bin"],500)
            for p in points:
                self.assertLessEqual(p["elapsed_s"],p["requested_s"])
        self.assertEqual(states[1]["bin"],183)

    def test_no_visuals_overlap(self):
        for p in (self.output/"F1 Telemetry Lab.Report/definition/pages").glob("*/page.json"):
            visuals=[json.loads(f.read_text()) for f in (p.parent/"visuals").glob("*/visual.json")]
            for i,a in enumerate(visuals):
                for b in visuals[i+1:]:
                    x,y=a["position"],b["position"]
                    overlap=(x["x"]<y["x"]+y["width"] and y["x"]<x["x"]+x["width"]
                             and x["y"]<y["y"]+y["height"] and y["y"]<x["y"]+x["height"])
                    self.assertFalse(overlap,(p.parent.name,a["name"],b["name"]))

    def test_charts_do_not_filter_controls(self):
        for path in (self.output/"F1 Telemetry Lab.Report/definition/pages").glob("*/page.json"):
            page=json.loads(path.read_text())
            self.assertTrue(page["visualInteractions"])
            self.assertTrue(all(i["type"]=="NoFilter" for i in page["visualInteractions"]))


if __name__=="__main__": unittest.main()
