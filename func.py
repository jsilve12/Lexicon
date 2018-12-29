import sqlite3
class team:
    elo = 1500
    glicko = 350
    glick_time = 0
    history = dict()

    def __init__(self):
        pass

    def __init__(self, el, glick, glick_t):
        self.elo = el
        self.glicko = glick
        self.glick_time = glick_t

    # def round(self, opponent, res, rounds):
    #     #Updates the objects self-history
    #     try:
    #         self.history[opponent] += (res, rounds)
    #     except:
    #         self.history[opponent] = (res,rounds)

    def round(self, oppelo):
        #Updates the objects self-history
        #self.round(opponent, res, rounds)

        #Updates the glicko based off of how long the team has been inactive
        if self.glick_time != 0:
            self.glicko = min(sqrt(self.glicko*self.glicko + 34.6*34.6*self.glick_time), 350)
            self.glick_time = 0

        #Updates the elo
        q = ln(10)/400
        g = 1/sqrt(1+(3*q*q*self.glicko*self.glicko)/(3.1415*3.1415))
        e = 1/(1+10^(g*(self.elo-oppelo)/(-400)))
        d2 = 1/(q*q*g*g*E*(1-E))
        self.elo = self.elo + (q/(1/(glicko*glicko)+1/(d2)))*g*(res-e)

        #Updates the glicko based on the round
        self.glicko = sqrt(1/(1/(self.glicko*self.glicko)+1/d))

    def glicko(self):
        self.glick_time += 1

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
            cur.execute('SELECT * FROM Teams')
        except:
            return
        for team in cur.fetchone():
            self.teams[team[1]] = team(team[2], team[3], team[4])

        #Imports Tournaments
        cur.execute('SELECT * FROM Tournaments')
        for tournament in cur.fetchone():
            self.tournaments[tournament[1]] = tournament()

            #Imports Rounds
            cur1.execute('SELECT * FROM Rounds WHERE tourney_id = ' + tournament[0])
            for round in cur1.fetchone():

                #Get the teams
                cur2.execute('SELECT name FROM Teams WHERE id = ?', (round[0]))
                team_1 = cur2.fetchone()[1]
                cur2.execute('SELECT name FROM Teams WHERE id = ?', (round[1]))
                team_2 = cur2.fetchone()[1]

                self.round(team_1, team_2, round[3], round[4] ,tournament[0])

    def elo(self, tournamen):
        for rund in self.tournaments[tournamen].rounds:
            if rund[0] not in self.teams:
                self.teams[rund[0]] = team()
            elif rund[1] not in self.teams:
                self.teams[rund[1]] = team()

            temp_el = self.teams[rund[0]].elo
            self.teams[rund[0]].round(self.teams[rund[1]].elo)
            self.teams[rund[1]].round(temp_el)

    def glicko(self):
        for team in self.teams:
            team.glicko()

    def newTourney(self, tournamen):
        self.tournaments[tournamen] = tournament()
        return tournamen

    def round(self, team1, team2, wins, num, tournNum):
        self.tournaments[tournNum].round(team1, team2, wins, num)

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
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
            name TEXT UNIQUE
            elo REAL
            glicko REAL
            glick_time REAL
        );

        CREATE TABLE Tournament(
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
            name TEXT UNIQUE
        );

        CREATE TABLE Round(
            Team1_id INTEGER,
            Team2_id INTEGER,
            Tournament_id INTEGER,
            Res REAL,
            Rounds INTEGER,
            PRIMARY KEY(Team1_id, Team2_id, Tournament_id)
        );
        ''')
        conn.commit()

        #Creates all the teams
        for key,team in self.teams.item():
            cur.execute('INSERT OR IGNORE INTO Team (name, elo, glicko) VALUES (?,?,?)',(key, team.elo, team.glicko, team.glick_time))

        conn.commit()

        #Enters the tournaments
        for key,tournament in self.tournament.item():
            cur.execute('INSERT OR IGNORE INTO Tournament (name) VALUES (?)', (key))
            cur.execute('SELECT id FROM Tournament WHERE name = ?', (key,))
            tourn_id = cur.fetchone()[0]

            #Enters the individual rounds
            for round in rounds:

                #Gets the team indexes
                cur.execute('SELECT id FROM Team WHERE name = ? ', (round[0],))
                team1 = cur.fetchone()[0]
                cur.execute('SELECT id FROM Team WHERE name = ? ', (round[1],))
                team2 = cur.fetchone()[0]

                #Inserts the Round
                cur.execute('INSERT INTO Round (Team1_id, Team2_id, Tournament_id, Res, Rounds) VALUES ( ?,?,?,?,?)', (team1, team2, tourn_id, round[2], round[3]))
        conn.commit()
