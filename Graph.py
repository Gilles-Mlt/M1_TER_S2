#!/usr/bin/env python3
#coding=utf8

from pygnuplot import gnuplot
import pandas as pd

# A demostration to generate pandas data frame data in python.
df = pd.read_csv('h1Res.txt', sep=';', index_col = False, parse_dates = False,
        names = ['Tps_Trsfrt', 'NbrOct_Env','NbrOct_Rec']
        )

print(df)

# Create a Gnuplot instance and set the options at first;
g = gnuplot.Gnuplot(log = True,
        output = '"GrapheTest.png"',
        term = 'pngcairo font "arial,10" fontscale 1.0 size 900, 600',
        #multiplot = "" 
        )

g.plot_data(df,

        'using "NbrOct_Env":"Tps_Trsfrt" notitle lw 2 lc "web-blue" ',

        title = '" Analyse de test TLP "',
        #logscale = 'y',
        xrange = '[14016.5:14018.5]',
        yrange = '[0:7]',
        #format = 'x ""',
        #xtics = '(66, 87, 109, 130, 151, 174, 193, 215, 235)',
        # ytics = '0,0.05,7',
        mytics = 10,
        lmargin = '8',
        rmargin = '8',
        bmargin = '0',
        origin = '0, 0.2',
        size = ' 1, 0.8',
        grid = 'xtics mytics',
        xlabel = '"Taille du paquet envoyé"',
        ylabel = '"temps de transfert par paquet" offset 1',
        #label = ['1 "Acme Widgets" at graph 0.5, graph 0.9 center front']
        )