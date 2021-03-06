﻿#! python3
# -*- coding: utf-8 -*-
#title           :web_interface.py
#description     :Ce programme lance le serveur web du projet
#author          :Synntix
#date            :12/05/2019
#python_version  :3.7
#=======================================================================
from flask import Flask, render_template, url_for, request, session
import time
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
import reportlab.lib.styles
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from copy import deepcopy
import sqlite3
import tournament
import tournoi_DB
app = Flask(__name__)   # Initialise l'application Flask
debug=True
debug_algo=True

app.secret_key = 'TournoiAJE'


@app.route('/')  #On donne la route ici "/"  l'adresse sera donc localhost:5000/
def accueil():
    #On utilise le template accueil.html
    return render_template("accueil.html.j2")




@app.route('/donnees')  #On donne la route ici "/"  l'adresse sera donc localhost:5000/
def donnees():
    #On utilise le template donnees.html
    return render_template("donnees.html")




@app.route('/player_entry/', methods=['POST'])
def player_entry():
    #On récupère les réponses des formulaires de la page d'accueil
    session['Nbr_player'] = int(request.form['nbr_player'])
    session['Type_tournoi']=request.form['type_tournoi']
    session['Mode_points']=request.form['mode_points']


    if debug==True:
        print("Nombre de joueurs : {}".format(session['Nbr_player']))
        print("Type de tournoi : {}".format(session['Type_tournoi']))
        print("Mode points : {}".format(session['Mode_points']))

    #On utilise le template page2.html
    return render_template('page2.html.j2' , nbr_player=session['Nbr_player'], type_tournoi=session['Type_tournoi'], mode_points=session['Mode_points'])




@app.route('/display/', methods=['POST'])
def display():

################################################################################
#RÉCUPÉRATION DES INPUTS HTML
################################################################################

    #On crée la liste 'Players' et on ajoute tous les pseudo des participants
    session['Players']=[]
    for i in range(1,session['Nbr_player']+1) :
        #On ajoute le pseudo des joueurs à la liste "Players"
        session['Players'].append(request.form['pseudo{}'.format(i)])
    if debug==True:
        print("Liste des joueurs :\n{}".format(session['Players']))

    session['Pts_draw']=int(request.form['pts_draw'])
    session['Pts_lose']=int(request.form['pts_lose'])
    session['Pts_win']=int(request.form['pts_win'])
    if debug==True:
        print("Nombre de points par match gagné : {}".format(session['Pts_win']))
        print("Nombre de points par égalité : {}".format(session['Pts_draw']))
        print("Nombre de points par match perdu : {}".format(session['Pts_lose']))

#Inputs dédiés à la ligue
################################################################################
    if session['Type_tournoi'] == "Ligue" :
        #On récupère le choix sur la longueur du tournoi et on en fait un booléen
        Extended=request.form['shortcheckbox']
        if Extended == "0":
            Extended=True
        elif Extended=="1":
            Extended=False
        if debug==True:
            print("Extended = {}".format(Extended))

        #On récupère le choix sur les matchs de barrage et on en fait un booléen
        Barrages=request.form['match_barrages']
        if Barrages == "0":
            Barrages=True
        elif Barrages=="1":
            Barrages=False
        if debug==True:
            print("Barrages = {}".format(Barrages))

        #On fait de le méthode de rencontre un booléen
        session['Methode_rencontre']=request.form['methode_rencontre']
        if session['Methode_rencontre'] == 'Force_berger':
            session['Methode_rencontre'] = True
        else:
            session['Methode_rencontre'] = False

################################################################################
#Instructions en cas de ligue
################################################################################

    if session['Type_tournoi'] == "Ligue" :
        #On récupère la liste des matchs
        #Matchlist est de la forme [(numéro_round,id_j1,id_j2),...]
        Matchlist=tournament.getMatchList(session['Nbr_player'],Extended,session['Methode_rencontre'],debug_algo)
        session['Matchlist']=Matchlist
        if debug==True:
            print("Liste des matchs par ID :\n{}".format(Matchlist))
        session['Nbr_matchs'] = len(Matchlist)

        #On crée les tables de la base de donnée
        tournoi_DB.openDB()
        tournoi_DB.createTables()
        #On donne la liste des joueurs à la base de donnée
        tournoi_DB.createPlayers(session['Players'])

        #On crée une liste des matchs avec le pseudo des joueurs au lieu de leur IDs
        #Matchlist_pseudo est de la forme [(numéro_round,pseudo_j1,pseudo_j2),...]
        session['Matchlist_pseudo']=deepcopy(session['Matchlist'])
        for i in range(len(session['Matchlist_pseudo'])):
            session['Matchlist_pseudo'][i]=list(session['Matchlist_pseudo'][i])
        for i in session['Matchlist_pseudo']:
            i[1]=tournoi_DB.getPseudo(i[1])
            i[2]=tournoi_DB.getPseudo(i[2])
        if debug==True:
            print("Liste des matchs par pseudo : \n{}".format(session['Matchlist_pseudo']))
        #On donne la liste des matchs à la DB
        tournoi_DB.creatematch(session['Matchlist_pseudo'])

        #On utilise le template display.html
        return render_template('display.html.j2' , players=session['Players'] ,nbr_player=session['Nbr_player'], type_tournoi=session['Type_tournoi'], matchlist=Matchlist, matchlist_pseudo=session['Matchlist_pseudo'], nbr_matchs=session['Nbr_matchs'], mode_points=session['Mode_points'])

################################################################################
#Instructions en cas de simple élimination
################################################################################

    if session['Type_tournoi'] == "Simple élimination" :
        session['InitialPlayers'] = session['Players']

        return 0




@app.route('/results/', methods=['POST'])
def results():
    Score_per_match=[]
    if session['Mode_points'] == "score":
        #Score_per_match est de la forme [(score j1 match1,score j2 match1),(score j1 match2,score j2 match2),...]
        for i in range(1,session['Nbr_matchs']+1) :
            #On récupère le score du match pour le mettre dans la liste Score_per_match
            tuple_score=(int(request.form['score_j1_match{}'.format(i)])),(int(request.form['score_j2_match{}'.format(i)]))
            Score_per_match.append(tuple_score)
        #On donne les scores à la DB
        tournoi_DB.insertScore(Score_per_match)
        if debug==True:
            print("Liste des scores : \n{}".format(Score_per_match))

        Results=[]
        for i in range(session['Nbr_matchs']) :
            #On compare les scores des joueurs pour déduire qui a gagné pour le mettre dans la liste Results
            if Score_per_match[i][0]>Score_per_match[i][1]:
                Results.append(session['Matchlist'][i][1])
            elif Score_per_match[i][0]<Score_per_match[i][1]:
                Results.append(session['Matchlist'][i][2])
            elif Score_per_match[i][0]==Score_per_match[i][1]:
                Results.append(0)
        if debug==True:
                    print("Liste des IDs des gagnants (0 = égalité) : \n{}".format(Results))
        Results_pseudo=[]
        for i in Results:
            if i == 0:
                Results_pseudo.append("Égalité")
            else:
                Results_pseudo.append(tournoi_DB.getPseudo(i))
        #On donne les gagnants à la DB
        tournoi_DB.insertWinner(Results_pseudo)

    elif session['Mode_points'] == "TOR":
        Results=[]
        for i in range(1,session['Nbr_matchs']+1) :
            #On récupère l'id des joueurs qui ont gagné pour les mettre dans la liste Results
            Results.append(int(request.form['match{}'.format(i)]))
        if debug==True:
            print("Liste des IDs des gagnants (0 = égalité) : \n{}".format(Results))
        Results_pseudo=[]
        for i in Results:
            if i == 0:
                Results_pseudo.append("Égalité")
            else:
                Results_pseudo.append(tournoi_DB.getPseudo(i))
        #On donne les gagnants à la DB
        tournoi_DB.insertWinner(Results_pseudo)

    #On récupère le classement et le convertit en classement_pseudo qui contient les pseudos
    if session['Mode_points'] == "score":
        Classement=tournament.getClassement(session['Nbr_player'],session['Matchlist'],Score_per_match,True,session['Pts_win'],session['Pts_draw'],session['Pts_lose'],debug_algo)
    elif session['Mode_points'] == "TOR":
        Classement=tournament.getClassement(session['Nbr_player'],session['Matchlist'],Results,False,session['Pts_win'],session['Pts_draw'],session['Pts_lose'],debug_algo)

    session['Classement']=Classement
    session['Classement_pseudo']=deepcopy(Classement)
    for i in range(len(session['Classement_pseudo'])):
        session['Classement_pseudo'][i]=list(session['Classement_pseudo'][i])
    for i in range(len(session['Classement_pseudo'])):
        session['Classement_pseudo'][i][0]=(tournoi_DB.getPseudo(session['Classement_pseudo'][i][0]))
    if debug==True:
        print("Classement_pseudo : {}".format(session['Classement_pseudo']))

    #Création du compte rendu en pdf avec le module reportlab
    doc = SimpleDocTemplate("Résultats-tournoi.pdf",pagesize=letter,rightMargin=10,leftMargin=10,topMargin=60,bottomMargin=18)

    #Les éléments ajoutés à Story (Paragraphe, tableau ...) seront écrits sur la page PDF du haut vers le bas
    Story=[]

    #Mise en place du style des paragraphes
    styles=reportlab.lib.styles.getSampleStyleSheet()
    styles.add(reportlab.lib.styles.ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
    styles.add(reportlab.lib.styles.ParagraphStyle(name='Center', alignment=TA_CENTER))
    styles.add(reportlab.lib.styles.ParagraphStyle(name='Left', alignment=TA_LEFT))

    #Mise en place des variables temporelles
    localtime = time.localtime(time.time())
    date=time.strftime('%d-%m-%Y', localtime)
    heure=time.strftime('%H:%M', localtime)

    #Paragraphe titre
    titre_pdf="{0} de {1} joueurs le {2} à {3}".format(session['Type_tournoi'],session['Nbr_player'],date,heure)
    ptext = '<font size=12>{}</font>'.format(titre_pdf)
    Story.append(Paragraph(ptext, styles["Center"]))

    Story.append(Spacer(1, 50))

    #Création du tableau
    table_data= [['Place', 'Pseudo', 'Points', 'Score de départage'],]
    for i in range (session['Nbr_player']):
        table_data.append([i+1,session['Classement_pseudo'][i][0],session['Classement_pseudo'][i][1],session['Classement_pseudo'][i][2]])
    table=Table(table_data, colWidths=[50*mm])
    #Édition du style du tableau
    table.setStyle(TableStyle([('ALIGN',(0,0),(-1,-1),'CENTER'),
                        ('BACKGROUND',(0,0),(-1,0),colors.orange),
                        ('BACKGROUND',(0,1),(-1,-1),HexColor("#1A1A1A")),
                        ('TEXTCOLOR',(0,1),(-1,1),colors.gold),
                        ('TEXTCOLOR',(0,2),(-1,2),colors.silver),
                        ('TEXTCOLOR',(0,3),(-1,3),colors.brown),
                        ('TEXTCOLOR',(0,4),(-1,-1),colors.white),
                        ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
                        ('BOX', (0,0), (-1,-1), 0.25, colors.black)])),

    Story.append(table)

    Story.append(Spacer(1, 50))

    #Paragraphe qui annonce le tableau récapitulatif
    Story.append(Paragraph('<font size=12><u>Récapitulatif des matchs :</u></font>', styles["Left"]))
    Story.append(Spacer(1, 10))

    #On récupère les information des matchs
    connexion = sqlite3.connect("tournoi.sqlite3", check_same_thread=False)
    curseur = connexion.cursor()
    recap_matchs = curseur.execute('SELECT * FROM match').fetchall()

    #On crée un tableau récapitulatif
    if session['Mode_points'] == "score":
        table_recap=[['Numéro match', 'Numéro round', 'Joueur 1', 'Score joueur 1', 'Score joueur 2', 'Joueur 2'],]
        for i in range (len(session['Matchlist'])):
            table_recap.append([i+1,recap_matchs[i][1],recap_matchs[i][2],recap_matchs[i][3],recap_matchs[i][4],recap_matchs[i][5]])

    elif session['Mode_points'] == "TOR":
        table_recap=[['Numéro match', 'Numéro round', 'Joueurs', 'Vainqueur'],]
        for i in range (len(session['Matchlist'])):
            table_recap.append([i+1,recap_matchs[i][1],recap_matchs[i][2] + " vs " + recap_matchs[i][5],recap_matchs[i][6]])

    table2=Table(table_recap, colWidths=[33.5*mm])
    #Édition du style du tableau
    table2.setStyle(TableStyle([('ALIGN',(0,0),(-1,-1),'CENTER'),
                        ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
                        ('BOX', (0,0), (-1,-1), 0.25, colors.black)])),

    Story.append(table2)


    #On se déplace dans /static pour enregistrer le pdf puis on revient au répertoir initial
    curr_dir=os.getcwd()
    os.chdir(curr_dir+'/static')
    doc.build(Story)
    os.chdir(curr_dir)

    #On utilise le template Results.html
    return render_template('results.html.j2', nbr_player=session['Nbr_player'], type_tournoi=session['Type_tournoi'], classement=session['Classement'], classement_pseudo=session['Classement_pseudo'], matchlist_pseudo=session['Matchlist_pseudo'], matchlist=session['Matchlist'], nbr_matchs=session['Nbr_matchs'], score_per_match=Score_per_match, mode_points=session['Mode_points'], results=Results)




if __name__ == '__main__' :
    app.run(debug=True)
