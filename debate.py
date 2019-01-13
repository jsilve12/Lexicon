import urllib.request, urllib.parse, urllib.error, ssl, traceback, logging,time
from func import team, tournament, season
from bs4 import BeautifulSoup

#SSL certificates
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

sea = season()
while True :
    op = input("What do you want to do? ")
    if op == "Break":
        break

    elif op == "Insert Tournament":
        #Opens the URL
        url = input("Enter Tournament Results page: ")
        Tournam3nt = input("Enter Tournament Name: ")
        sea.insertTournament(url, Tournam3nt)

    elif op == "Insert Season":
        for tea in sea.teams.keys():
            sea.teams[tea] = team()
        Tourn = open("tournaments.txt", 'r')
        for lines in Tourn:
            if(lines.strip() == "Break"):
                sea.glicko()
            else:
                lines = lines.split()
                if lines[1] not in sea.tournaments:
                    sea.insertTournament(lines[0], lines[1])
                    time.sleep(50)
                else:
                    sea.elo(lines[1])

    elif op == "Elo Tournament":
        tourn = input("Which Tournament: ")
        sea.elo(tourn)

    elif op == "Print Results":
        sea.teams.elo.sort()
        fh = open("Results.html", "w")
        fh.write("<table><tr><th>Team</th><th>Elo</th><th>Ratings Distributions</th></tr>")
        for key, value in sea.teams.items():
            if value.glicko < 120 and value.glick_time < 10:
                fh.write("<tr><td>" + key + "</td><td>" + str(value.elo)[:7] + "</td><td>" + str(value.glicko)[:5] + "</td></tr>\n")
        fh.write("</table>")
        #Do other fancy things with results?
    elif op == "Glicko":
        sea.glicko()
