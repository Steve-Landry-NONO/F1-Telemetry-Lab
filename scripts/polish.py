"""Native Power BI pit-wall layout and analytical measures."""


def additional_measures():
    return {
        "Replay time request s": "IF(ISFILTERED(ReplayTime[Seconds]), MAX(ReplayTime[Seconds]), 30)",
        "Selected bin": """VAR chosenLap = SELECTEDVALUE(DimLap[LapId], 1)
VAR timeLimit = [Replay time request s] * 1000
VAR samples = CALCULATETABLE(FactTelemetry, REMOVEFILTERS(DimDistance), REMOVEFILTERS(FactTelemetry[SpeedBand]), TREATAS({chosenLap}, DimLap[LapId]))
RETURN COALESCE(MAXX(FILTER(samples, FactTelemetry[TimeMs] <= timeLimit), FactTelemetry[Bin]), 0)""",
        "Selected driver": """VAR chosenLap = SELECTEDVALUE(DimLap[LapId], 1)
RETURN CALCULATE(SELECTEDVALUE(DimLap[Driver]), TREATAS({chosenLap}, DimLap[LapId]))""",
        "Data health": """VAR n = COUNTROWS(ALL(FactTelemetry))
RETURN IF(n = 1002, "2 tours | 1 002 points | " & CONCATENATEX(ALL(DimLap[Source]), DimLap[Source], ", "), "Actualiser pour charger les 2 tours")""",
        "Replay subtitle": '"MONZA 2024 / QUALIFICATIONS  ·  EXPLORER UN TOUR"',
        "Comparison subtitle": '"MONZA 2024 / QUALIFICATIONS  ·  TROUVER LES ÉCARTS"',
        "Strategy subtitle": '"MODÈLE PÉDAGOGIQUE / 53 TOURS  ·  TESTER UNE STRATÉGIE"',
        "Track X": """VAR chosenLap = SELECTEDVALUE(DimLap[LapId], 1)
RETURN CALCULATE(AVERAGE(FactTelemetry[SVGX]), TREATAS({chosenLap}, DimLap[LapId]))""",
        "Track Y": """VAR chosenLap = SELECTEDVALUE(DimLap[LapId], 1)
VAR coordinate = CALCULATE(AVERAGE(FactTelemetry[SVGY]), TREATAS({chosenLap}, DimLap[LapId]))
RETURN IF(NOT ISBLANK(coordinate), 460 - coordinate)""",
        "Track marker size": "IF(NOT ISBLANK([Track X]), IF(SELECTEDVALUE(DimDistance[Bin]) = [Selected bin], 80, 2))",
        "Replay speed cursor": "IF(SELECTEDVALUE(DimDistance[Bin]) = [Selected bin], [Speed trace])",
        "Elapsed trace s": """VAR chosenLap = SELECTEDVALUE(DimLap[LapId], 1)
RETURN CALCULATE(MAX(FactTelemetry[TimeMs]), TREATAS({chosenLap}, DimLap[LapId])) / 1000""",
        "Top speed kmh": """VAR chosenLap = SELECTEDVALUE(DimLap[LapId], 1)
RETURN CALCULATE(MAX(FactTelemetry[SpeedKmh]), REMOVEFILTERS(DimDistance), TREATAS({chosenLap}, DimLap[LapId]))""",
        "Replay instruction": '"Déplacez le chrono : le point agrandi indique la position. Les couleurs distinguent freinage et vitesse."',
        "Replay heading": '"F1 TELEMETRY LAB / PIT WALL"',
        "Comparison insight": """VAR gap = [Lap delta s]
VAR driverA = SELECTEDVALUE(LapA[Driver], "NOR")
VAR driverB = SELECTEDVALUE(LapB[Driver], "LEC")
RETURN IF(ISBLANK(gap), "Actualiser les données", IF(driverA = driverB, "Même pilote : courbes superposées, écarts nuls.", IF(gap >= 0, driverA & " gagne " & FORMAT(gap, "0.000", "fr-FR") & " s sur " & driverB, driverB & " gagne " & FORMAT(-gap, "0.000", "fr-FR") & " s sur " & driverA)))""",
        "Comparison instruction": '"Delta B - A : positif = B plus lent ; négatif = B plus rapide. Comparaison au même pourcentage du circuit."',
        "Strategy status": 'IF(SELECTEDVALUE(FirstCompound[Compound], "MEDIUM") = SELECTEDVALUE(SecondCompound[Compound], "HARD"), "Choisissez deux composés distincts pour ce scénario de course sèche.", "Simulation : un arrêt, deux composés, sans trafic, météo ni safety car.")',
        "Strategy insight": """VAR selectedStop = SELECTEDVALUE(StopLap[Lap], 24)
VAR loss = [Penalty vs best s]
RETURN IF(ISBLANK([Strategy total s]), "Scénario invalide : deux composés distincts sont requis.", "Arrêt choisi : tour " & selectedStop & " | meilleur candidat : tour " & FORMAT([Best stop lap], "0") & " | écart : " & FORMAT(loss, "0.00", "fr-FR") & " s")""",
        "Strategy time label": """VAR total = [Strategy total s]
RETURN IF(NOT ISBLANK(total), FORMAT(INT(total / 60), "0") & " min " & FORMAT(MOD(total, 60), "00.0", "fr-FR") & " s")""",
        "Optimal simulated lap s": """VAR bestLap = [Best stop lap]
RETURN IF(NOT ISBLANK(bestLap), CALCULATE([Simulated lap s], REMOVEFILTERS(StopLap), TREATAS({bestLap}, StopLap[Lap])))""",
        "Candidate penalty s": "IF(NOT ISBLANK([Candidate total s]), [Candidate total s] - ([Strategy total s] - [Penalty vs best s]))",
        "Chosen stop penalty s": "IF(SELECTEDVALUE(CandidateStop[Lap]) = SELECTEDVALUE(StopLap[Lap], 24), [Candidate penalty s])",
        "Pedals SVG": """VAR throttle = COALESCE([Current throttle pct], 0)
VAR braking = COALESCE([Current brake], 0)
VAR svg = "<svg xmlns='http://www.w3.org/2000/svg' width='600' height='118' viewBox='0 0 600 118'><rect width='600' height='118' fill='#101826'/><g font-family='Segoe UI,Arial' fill='#a5b4cc' font-size='15'><text x='18' y='25'>ACCÉLÉRATEUR</text><text x='18' y='83'>FREIN</text></g><rect x='165' y='10' width='330' height='26' rx='5' fill='#253146'/><rect x='165' y='10' width='" & FORMAT(throttle * 3.3, "0.0", "en-US") & "' height='26' rx='5' fill='#74f7ce'/><rect x='165' y='68' width='330' height='26' rx='5' fill='#253146'/><rect x='165' y='68' width='" & FORMAT(braking * 330, "0.0", "en-US") & "' height='26' rx='5' fill='#ff544f'/><g font-family='Segoe UI,Arial' fill='white' font-size='24' font-weight='bold'><text x='515' y='32'>" & FORMAT(throttle, "0") & "%</text><text x='515' y='92'>" & IF(braking = 1, "ON", "OFF") & "</text></g></svg>"
RETURN IF(COUNTROWS(ALL(FactTelemetry)) > 0, "data:image/svg+xml;utf8," & SUBSTITUTE(svg, "#", "%23"))""",
        "Stint plan SVG": """VAR tyreOne = SELECTEDVALUE(FirstCompound[Compound], "MEDIUM")
VAR tyreTwo = SELECTEDVALUE(SecondCompound[Compound], "HARD")
VAR selectedStop = SELECTEDVALUE(StopLap[Lap], 24)
VAR split = 1140 * selectedStop / 53
VAR colorOne = SWITCH(tyreOne, "SOFT", "#ff544f", "MEDIUM", "#ffce62", "#eef4ff")
VAR colorTwo = SWITCH(tyreTwo, "SOFT", "#ff544f", "MEDIUM", "#ffce62", "#eef4ff")
VAR svg = "<svg xmlns='http://www.w3.org/2000/svg' width='1200' height='108' viewBox='0 0 1200 108'><rect width='1200' height='108' fill='#101826'/><g font-family='Segoe UI,Arial' font-size='20' fill='white'><text x='30' y='28'>" & tyreOne & " / " & selectedStop & " tours</text><text x='1170' y='28' text-anchor='end'>" & tyreTwo & " / " & (53-selectedStop) & " tours</text></g><rect x='30' y='43' width='" & FORMAT(split, "0.0", "en-US") & "' height='23' fill='" & colorOne & "'/><rect x='" & FORMAT(30+split, "0.0", "en-US") & "' y='43' width='" & FORMAT(1140-split, "0.0", "en-US") & "' height='23' fill='" & colorTwo & "'/><line x1='" & FORMAT(30+split, "0.0", "en-US") & "' x2='" & FORMAT(30+split, "0.0", "en-US") & "' y1='35' y2='77' stroke='#759bff' stroke-width='4'/><g font-family='Segoe UI,Arial' font-size='15' fill='#a5b4cc'><text x='30' y='97'>DÉPART / TOUR 1</text><text x='600' y='97' text-anchor='middle'>ARRÊT APRÈS LE TOUR " & selectedStop & "</text><text x='1170' y='97' text-anchor='end'>ARRIVÉE / TOUR 53</text></g></svg>"
RETURN IF(tyreOne <> tyreTwo, "data:image/svg+xml;utf8," & SUBSTITUTE(svg, "#", "%23"))""",
    }


def render_layout(report, api, drivers):
    dump, visual, card, slicer, line, projection, obj, literal = api
    schema = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/"
    pages = report/"definition"/"pages"
    names=["Replay","Comparison","Strategy"]
    subtitles=["Replay subtitle","Comparison subtitle","Strategy subtitle"]
    titles=["01 · Pit Wall","02 · Duel de pilotes","03 · Stratégie"]
    dump(pages/"pages.json",{"$schema":schema+"pagesMetadata/1.0.0/schema.json","pageOrder":names,"activePageName":"Replay"})

    def text_card(p,name,measure,title,x,y,w,h=64,size=17):
        card(p,name,measure,title,x,y,w,h,font_size=size)

    def svg(p,name,measure,title,x,y,w,h,image_height=118):
        visual(p,name,"tableEx",title,x,y,w,h,{"Values":[projection("Metrics",measure,True)]},
               {"grid":obj(imageHeight=image_height,imageWidth=w-32,rowPadding=0,outlineColor="#101826"),
                "columnHeaders":obj(show=False),"total":obj(totals=False),
                "values":obj(fontColor="#eef4ff",backColor="#101826"),
                "columnWidth":[{"properties":{"value":literal(w-28)},"selector":{"metadata":"Metrics."+measure}}]})

    for n,t,s in zip(names,titles,subtitles):
        p=pages/n
        dump(p/"page.json",{"$schema":schema+"page/1.0.0/schema.json","name":n,"displayName":t,
             "displayOption":"FitToPage","height":900,"width":1600,
             "objects":{"background":[{"properties":{"color":{"solid":{"color":literal("#080e18")}},"transparency":literal(0)}}]}})
        text_card(p,"heading","Replay heading","",24,12,1060,64,32)
        text_card(p,"subtitle",s,"",24,80,1060,42,15)
        text_card(p,"source","Data health","Données / contrôle",1104,12,472,110,16)

    p=pages/"Replay"
    slicer(p,"driver","DimLap","Driver","PILOTE",24,136,250,80,default=drivers[0])
    slicer(p,"cursor","ReplayTime","Seconds","CHRONO · secondes",292,136,610,80,default=30,mode="Before")
    card(p,"elapsed","Current elapsed s","TEMPS ÉCOULÉ · s",920,136,310,80,font_size=28)
    card(p,"laptime","Lap time s","TEMPS DU TOUR · s",1248,136,328,80,font_size=28)
    visual(p,"track","scatterChart","MONZA · télémétrie sur la piste",24,232,610,390,
           {"Category":[projection("DimDistance","Bin")],"X":[projection("Metrics","Track X",True)],
            "Y":[projection("Metrics","Track Y",True)],"Size":[projection("Metrics","Track marker size",True)],
            "Series":[projection("FactTelemetry","SpeedBand")],
            "Tooltips":[projection("Metrics","Speed trace",True),projection("Metrics","Elapsed trace s",True)]},
           {"categoryAxis":obj(show=False,start=0,end=640),"valueAxis":obj(show=False,start=0,end=460),
            "legend":obj(show=True,position="Bottom",labelColor="#a5b4cc",fontSize=12),
            "bubbles":obj(bubbleSize=12),"fillPoint":obj(show=True)})
    text_card(p,"hint","Replay instruction","",24,638,610,64,13)
    svg(p,"pedalbars","Pedals SVG","COMMANDES / instant sélectionné",24,718,610,158)
    visual(p,"gauge","gauge","VITESSE · km/h",654,232,440,280,
           {"Y":[projection("Metrics","Current speed kmh",True)],"TargetValue":[projection("Metrics","Top speed kmh",True)]},
           {"axis":obj(min=0,max=360),"labels":obj(color="#eef4ff",fontSize=45),
            "dataPoint":obj(fill="#74f7ce"),"target":obj(show=True)})
    card(p,"gear","Current gear","RAPPORT",1112,232,222,128,font_size=42)
    card(p,"progress","Replay progress pct","PROGRESSION · %",1352,232,224,128,font_size=34)
    card(p,"throttle","Current throttle pct","ACCÉLÉRATEUR · %",1112,378,222,134,font_size=34)
    card(p,"brake","Current brake","FREIN · 0 / 1",1352,378,224,134,font_size=34)
    line(p,"speedtrace",("DimDistance","ProgressPct"),["Speed trace","Replay speed cursor"],
         "PROFIL DE VITESSE · position sélectionnée",654,528,922,164)
    line(p,"pedals",("DimDistance","ProgressPct"),["Throttle trace","Brake trace"],
         "ACCÉLÉRATEUR / FREIN · progression du circuit %",654,710,922,166)

    p=pages/"Comparison"
    slicer(p,"lapA","LapA","Driver","RÉFÉRENCE A",24,136,286,80,default=drivers[0])
    slicer(p,"lapB","LapB","Driver","COMPARAISON B",328,136,286,80,default=drivers[1])
    card(p,"timeA","Lap time A s","TOUR A · s",632,136,300,80,font_size=28)
    card(p,"timeB","Lap time B s","TOUR B · s",950,136,300,80,font_size=28)
    card(p,"delta","Lap delta s","DELTA B - A · s",1268,136,308,80,font_size=28)
    text_card(p,"insight","Comparison insight","LECTURE DU DUEL",24,232,1552,82,27)
    line(p,"compare",("DimDistance","ProgressPct"),["Speed A","Speed B"],
         "VITESSE · comparer au même endroit du circuit",24,330,1552,236)
    line(p,"deltatrace",("DimDistance","ProgressPct"),["Delta B minus A s"],
         "DELTA CUMULÉ · où se construit l'écart ?",24,584,990,228)
    for i in (1,2,3):
        card(p,"sector"+str(i),f"Sector {i} delta s",f"SECTEUR {i} · B - A · s",1032,584+(i-1)*80,544,68,font_size=26)
    text_card(p,"hint","Comparison instruction","",24,830,1552,46,14)

    p=pages/"Strategy"
    fields=[("FirstCompound","Compound","PNEU / RELAIS 1","MEDIUM"),
            ("SecondCompound","Compound","PNEU / RELAIS 2","HARD"),
            ("StopLap","Lap","ARRÊT APRÈS LE TOUR",24),("PitLoss","Seconds","PERTE AU STAND · s",22),
            ("Degradation","Multiplier","DÉGRADATION ×",1),("BasePace","Seconds","RYTHME DE BASE · s",84)]
    for i,(t,c,title,value) in enumerate(fields):
        slicer(p,t,t,c,title,24+i*260,136,252,80,default=value)
    text_card(p,"status","Strategy status","HYPOTHÈSES",24,232,1552,62,16)
    card(p,"total","Strategy time label","TEMPS SIMULÉ",24,310,500,94,font_size=30)
    card(p,"optimal","Best stop lap","MEILLEUR ARRÊT · tour",542,310,500,94,font_size=38)
    card(p,"penalty","Penalty vs best s","ÉCART AU MEILLEUR · s",1060,310,516,94,font_size=38)
    svg(p,"plan","Stint plan SVG","PLAN DES RELAIS",24,422,1552,140,108)
    line(p,"stints",("RaceLap","Lap"),["Simulated lap s","Optimal simulated lap s"],
         "RYTHME PAR TOUR · stratégie choisie / optimale",24,580,760,214)
    line(p,"candidates",("CandidateStop","Lap"),["Candidate penalty s","Chosen stop penalty s"],
         "COÛT DES ARRÊTS · écart au meilleur candidat (s)",802,580,774,214)
    text_card(p,"insight","Strategy insight","LECTURE DE LA STRATÉGIE",24,812,1552,64,19)

    # Charts cannot filter the controls or other visuals: only the controls drive the story.
    for n in names:
        p=pages/n
        definitions=[__import__("json").loads(f.read_text()) for f in sorted((p/"visuals").glob("*/visual.json"))]
        charts=[v["name"] for v in definitions if v["visual"]["visualType"] in ("lineChart","scatterChart","gauge","tableEx")]
        data=__import__("json").loads((p/"page.json").read_text())
        data["visualInteractions"]=[{"source":source,"target":v["name"],"type":"NoFilter"}
                                   for source in charts for v in definitions if source!=v["name"]]
        dump(p/"page.json",data)
