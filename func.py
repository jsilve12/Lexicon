import sqlite3, math
class team:
    #Purpose of glick_round - To ensure rounds in the same tournament don't effect glicko
    #Purpose of glick_time - If you go multiple weeks without competing
    elo = 1500
    glicko = 350
    glick_time = 0
    glick_round = 350
    history = dict()

    def __init__(self):
        pass

    def __init__(self, el = 1500, glick = 350, glick_t = 0):
        self.elo = el
        self.glicko = glick
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

        e = 1+math.pow(10, g*(self.elo-oppelo)/(-400))
        e = 1/(e)

        d2 = 1/(q*q*g*g*e*(1-e))
        a = (q/(1/(self.glicko*self.glicko)+1/(d2)))
        b = g*(res-rounds*e)
        val = a*b
        self.elo = self.elo + val

        #Updates the glicko based on the round
        self.glick_round = math.sqrt(1/(1/(self.glick_round*self.glick_round)+1/d2))
        print(self.elo, self.glicko, self.glick_round)

    def glicko(self):
        self.glick_time += 1

    def gr(self):
        self.glicko = self.glick_round

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
