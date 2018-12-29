import sqlite3, math, urllib.request, urllib.parse, urllib.error, ssl, traceback, logging
from bs4 import BeautifulSoup

#SSL certificates
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

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

class team:
    #Purpose of glick_round - To ensure rounds in the same tournament don't effect glicko
    #Purpose of glick_time - If you go multiple weeks without competing
    elo = 1500
    glicko = 350
    glick_time = 0
    glick_round = 350
    elo_round = 1500
    history = dict()

    def __init__(self):
        pass

    def __init__(self, el = 1500, glick = 350, glick_t = 0):
        self.elo = el
        self.elo_round = el
        self.glicko = glick
        self.glick_round = glick
        self.glick_time = glick_t


    # def round(self, opponent, res, rounds):
    #     #Updates the objects self-history
    #     try:
    #         self.history[opponent] += (res, rounds)
    #     except:
    #         self.history[opponent] = (res,rounds)

    def round(self, res, rounds, oppelo):
        #Updates the objects self-history
        #self.round(opponent, res, rounds)

        #Updates the glicko based off of how long the team has been inactive
        if self.glick_time != 0:
            self.glicko = min(math.sqrt(self.glicko*self.glicko + 34.6*34.6*self.glick_time), 350)
            self.glick_time = 0

        #Updates the elo
        q = math.log1p(10)/400
        g = 1/math.sqrt(1+(3*q*q*self.glicko*self.glicko)/(3.1415*3.1415))

        e = 1+math.pow(10, g*(self.elo_round-oppelo)/(-400))
        e = 1/(e)

        d2 = 1/(q*q*g*g*e*(1-e))
        a = (q/(1/(self.glicko*self.glicko)+1/(d2)))
        b = g*(res-rounds*e)
        val = a*b
        self.elo_round = self.elo_round + val

        #Updates the glicko based on the round
        self.glick_round = math.sqrt(1/(1/(self.glick_round*self.glick_round)+1/d2))
        print(self.elo_round, self.glick_round)

    def glicko(self):
        self.glick_time += 1

    def gr(self):
        self.glicko = self.glick_round
        self.elo = self.elo_round

class tournament:
    rounds = list()

    def round(self, team1, team2, res, round):
        #Initializes the match
        self.rounds.append((team1, team2, res, round))

class season:
    teams = dict()
    tournaments = dict()

    def __init__(self):
        #Import from the sqlite db
        conn = sqlite3.connect('seasondb.sqlite')
        cur = conn.cursor()
        conn1 = sqlite3.connect('seasondb.sqlite')
        cur1 = conn1.cursor()
        conn2 = sqlite3.connect('seasondb.sqlite')
        cur2 = conn2.cursor()

        #Imports Teams
        try:
            cur.execute('SELECT * FROM Team')
        except:
            return
        teams = cur.fetchall()
        if len(teams) == 0:
            return
        for tea in teams:
            self.teams[tea[1]] = team(tea[2], tea[3], tea[4])

        #Imports Tournaments
        cur.execute('SELECT * FROM Tournament')
        tournaments = cur.fetchall()
        if len(tournaments) == 0:
            return
        for tournamen in tournaments:
            self.tournaments[tournamen[1]] = tournament()

            #Imports Rounds
            cur1.execute('SELECT * FROM Round WHERE Tournament_id = ' + str(tournamen[0]))
            rounds = cur1.fetchall()
            if len(rounds) == 0:
                return
            for round in rounds:

                #Get the teams
                cur2.execute('SELECT name FROM Team WHERE id = ?', (round[0],))
                try:
                    team_1 = cur2.fetchone()[0]
                except:
                    team_1 = 100000

                cur2.execute('SELECT name FROM Team WHERE id = ?', (round[1],))
                try:
                    team_2 = cur2.fetchone()[0]
                except:
                    team_2 = 100000

                self.round(team_1, team_2, round[3], round[4] ,tournamen[1])

    def elo(self, tournamen):
        for rund in self.tournaments[tournamen].rounds:
            if rund[0] not in self.teams:
                self.teams[rund[0]] = team()
            elif rund[1] not in self.teams:
                self.teams[rund[1]] = team()

            temp_el = self.teams[rund[0]].elo
            print(rund[0])
            self.teams[rund[0]].round(rund[2], rund[3], self.teams[rund[1]].elo)
            print(rund[1])
            self.teams[rund[1]].round(math.fabs(rund[3] - rund[2]), rund[3], temp_el)

        for tea in self.teams.values():
            tea.gr()

    def glicko(self):
        for tea in self.teams.values():
            tea.glicko()

    def newTourney(self, tournamen):
        self.tournaments[tournamen] = tournament()
        return tournamen

    def round(self, team1, team2, wins, num, tournNum):
        self.tournaments[tournNum].round(team1, team2, wins, num)

    def insertTournament(self, url, Tournam3nt):
        url = urllib.request.urlopen(url, context=ctx)
        url = url.read()

        #Gets through each team
        teams = BeautifulSoup(url, 'html.parser')
        numTourney = self.newTourney(Tournam3nt)
        teams = teams('tr')

        #Goes through each team
        for tea in teams:
            try:
                url1 = "https://www.tabroom.com"+tea.a.get('href')
            except:
                continue

            #Gets 'this' team
            team1 = teamName(url1)
            print('\n', team1, '\n')
            if team1 not in self.teams:
                self.teams[team1] = team()

            #Gets each opponents team
            url1 = urllib.request.urlopen(url1, context=ctx)
            url2 = BeautifulSoup(url1, 'html.parser')

            #Gets results
            num = len(url2.findAll('h5'))
            for ta in range(0,num):
                if url2.findAll('h5')[ta].string.strip() == "Results":
                    url2 = url2.findAll('h5')[ta].next_sibling.next_sibling
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
                            self.round(team1, team2, wins, num, numTourney)
                        except Exception:
                            traceback.print_exc()
                    #The next iteration of the loop
                    url2 = url2.next_sibling.next_sibling
                except:
                    break

        self.elo(numTourney)

    def __del__(self):
        #Move back into the database
        conn = sqlite3.connect('seasondb.sqlite')
        cur = conn.cursor()

        #Creates the Database
        cur.executescript('''
        DROP TABLE IF EXISTS Team;
        DROP TABLE IF EXISTS Round;
        DROP TABLE IF EXISTS Tournament;

        CREATE TABLE Team(
            id  INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
            name    TEXT UNIQUE,
            elo REAL,
            glicko  REAL,
            glick_time  REAL
        );

        CREATE TABLE Tournament(
            id  INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
            name    TEXT UNIQUE
        );

        CREATE TABLE Round(
            Team1_id    INTEGER,
            Team2_id    INTEGER,
            Tournament_id   INTEGER,
            Res REAL,
            Rounds  INTEGER
        )
        ''')
        conn.commit()

        #Creates all the teams
        for team in self.teams.items():
            cur.execute('INSERT OR IGNORE INTO Team (name, elo, glicko, glick_time) VALUES (?,?,?,?)',(team[0], team[1].elo, team[1].glicko, team[1].glick_time))

        conn.commit()

        #Enters the tournaments
        for tournament in self.tournaments.items():
            cur.execute('INSERT OR IGNORE INTO Tournament (name) VALUES (?)', (tournament[0],))
            cur.execute('SELECT id FROM Tournament WHERE name = ?', (tournament[0],))
            tourn_id = cur.fetchone()[0]

            #Enters the individual rounds
            for round in tournament[1].rounds:

                #Gets the team indexes
                cur.execute('SELECT id FROM Team WHERE name = ? ', (round[0],))
                try:
                    team1 = cur.fetchone()[0]
                except:
                    team1 = 100000

                cur.execute('SELECT id FROM Team WHERE name = ? ', (round[1],))
                try:
                    team2 = cur.fetchone()[0]
                except:
                    team2 = 100000

                #Inserts the Round
                cur.execute('INSERT INTO Round (Team1_id, Team2_id, Tournament_id, Res, Rounds) VALUES ( ?,?,?,?,?)', (team1, team2, tourn_id, round[2], round[3]))
        conn.commit()
        print("Done")
