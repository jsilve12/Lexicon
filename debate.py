import urllib.request, urllib.parse, urllib.error, ssl, traceback, logging
from func import team, tournament, season
from bs4 import BeautifulSoup

def teamName(url1):
    url1 = urllib.request.urlopen(url1, context=ctx)
    team = BeautifulSoup(url1, 'html.parser')

    #Fetches all the Teams
    name = team('h4')
    name = name[3].string.split()
    school = team('h2')
    school = school[0].string.strip()

    #Naming convention (School name, first name alphabetically, second name alphabetically)
    n1 = name[0] + " " + name[1]
    n2 = name[3] + " " + name[4]
    if n1 > n2:
        n1,n2 = n2,n1
    return school[:(len(school)-3)] + " " + name[0] + " " + name[1] + " " + name[3] + " " + name[4]

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
        url = urllib.request.urlopen(url, context=ctx)
        url = url.read()

        #Gets through each team
        teams = BeautifulSoup(url, 'html.parser')
        numTourney = sea.newTourney(Tournam3nt)
        teams = teams('tr')

        #Goes through each team
        for team in teams:
            try:
                url1 = "https://www.tabroom.com"+team.a.get('href')
            except:
                continue

            #Gets 'this' team
            team1 = teamName(url1)
            print('\n', team1, '\n')

            #Gets each opponents team
            url1 = urllib.request.urlopen(url1, context=ctx)
            url2 = BeautifulSoup(url1, 'html.parser')
            url2 = url2.findAll('h5')[1].next_sibling.next_sibling
            #print(teamName("https://tabroom.com/index/tourn/postings/"+url2.a.get('href')))
            while True:
                try:
                    #Gets the results of the round, and the Opponent Team
                    wins = 0
                    num = 0
                    val = url2.findAll(class_=("tenth centeralign semibold"))
                    for v in val:
                        num += 1
                        if v.string.strip() == "W":
                            wins += 1
                    team2 = teamName("https://tabroom.com/index/tourn/postings/"+url2.a.get('href'))
                    print(team2)

                    #Picks one team, and uses that as the model
                    if team1 < team2:
                        #Inserts the information
                        try:
                            sea.round(team1, team2, wins, num, numTourney)
                        except Exception:
                            traceback.print_exc()

                    #The next iteration of the loop
                    url2 = url2.next_sibling.next_sibling
                except:
                    break

        sea.elo(numTourney)

    elif op == "Print Results":
        fh = open("Results", w)
        for key, value in sea.teams.item():
            fh.write(key, value.elo)
        #Do other fancy things with results?
    elif op == "Glicko":
        sea.glicko()
