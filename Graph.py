#!/usr/bin/env python3
#coding=utf8

from pygnuplot import gnuplot
import os
import pandas as pd
import sys
import datetime

if __name__ == "__main__":
    if (isinstance(int(sys.argv[1]), int) and len(sys.argv[1:]) == 1):
                names_files = []
                nb_client = int(sys.argv[1])
                debit_moyen = []
                f = open(".infos.txt",'r+')
                lines = f.readlines()
                f.seek(0)
                f.truncate()
                f.close()
                try:
                        os.remove(".infos.txt")
                except OSError as message:
                        print("ERROR : %s"%message)
                for line in lines:
                        line = line.strip('\n')
                        names_files.append(line)
                print(names_files)
                for client in range(1,nb_client+1):
                        # A demostration to generate pandas data frame data in python.
                        df = pd.read_csv(names_files[client-1], sep=';', index_col = False, parse_dates = False,
                        names = ['Temps (seconde)', 'Débit (bytes/sec)' ])

                        # print(df)

                        x_max = df["Temps (seconde)"].max()
                        y_max = df["Débit (bytes/sec)"].max()

                        df_display = pd.DataFrame(columns = ['Temps (seconde)', 'Débit (bytes/sec)'])

                        # df_display = df_display.append(df.loc[2], ignore_index=True)

                        # print(df.index[df['Temps (seconde)'] == 0][0])

                        value_list = []
                        for index in range(len(df.index)):
                                value_list.append(df['Temps (seconde)'][index])

                        # for index in range(x_max+1):
                        #         if index in df["Temps (seconde)"]:
                        #                 index_list = df.index[df['Temps (seconde)'] == index]
                        #                 if len(index_list) == 1:
                        #                         df_display = df_display.append(df.loc[index_list[0]], ignore_index=True)
                        #         else :
                        #                 df_display.loc[index] = [index, 0]

                        for index in range(int(x_max)+1):
                                if index in value_list:
                                        index_value = value_list.index(index)
                                        index_list = df.index[df['Temps (seconde)'] == index]
                                        if len(index_list) == 1:
                                                debit = df["Débit (bytes/sec)"][index_list[0]]
                                                df_display.loc[index] = [index, debit]
                                else :
                                        df_display.loc[index] = [index, 0]

                        # print(df_display)
                        df_display['Debit moyen'] = df_display["Débit (bytes/sec)"].mean()
                        debit_moyen.append(df_display["Débit (bytes/sec)"].mean())

                        # Create a Gnuplot instance and set the options at first;
                        g = gnuplot.Gnuplot(log = True,
                                output = '"Graphe_Thread-%i_%s.png"'%(client, datetime.datetime.now()),
                                term = 'pngcairo font "arial,10" fontscale 1.0 size 900, 600',
                                #multiplot = ""DwZ-DXh-zAn-B2E)
                                )

                        g.plot_data(df_display, 

                                'using "Temps (seconde)" : "Débit (bytes/sec)" notitle with linespoints lw 2 lc "web-blue" ',
                                'using "Temps (seconde)" : "Debit moyen" notitle with lines lw 2 lc"red" ',
                                # style = 'data linespoints',
                                title = '" Analyse de test TLP-RACK "',
                                #logscale = 'y',
                                xrange = '[0:%s]'%x_max,
                                yrange = '[0:%s]'%y_max,
                                #format = 'x ""',
                                #xtics = '(66, 87, 109, 130, 151, 174, 193, 215, 235)',
                                ytics = '0,50000,%s'%y_max,
                                xtics = '0, 1,%s'%x_max,
                                mytics = 10,
                                format = 'y"%.1tx10^%T"',
                                lmargin = '16',
                                rmargin = '8',
                                bmargin = '0',
                                origin = '0, 0.2',
                                size = ' 1, 0.8',
                                grid = 'xtics mytics',
                                xlabel = '"Temps (secondes)"',
                                ylabel = '"Débit en (bytes/sec)"',
                                #label = ['1 "Acme Widgets" at graph 0.5, graph 0.9 center front']
                                )
                somme = 0
                print("Les débits moyens sont :")
                for index in debit_moyen:
                        somme += index
                print(somme/nb_client)