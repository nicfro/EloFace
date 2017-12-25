import pyodbc
import datetime
from passlib.context import CryptContext
from random import randint
myctx = CryptContext(schemes=["sha256_crypt", "md5_crypt", "des_crypt"])

def connect():
    cnxn = pyodbc.connect("""
            Driver={ODBC Driver 13 for SQL Server};
            Server=tcp:rateme.database.windows.net,1433;
            Database=RateMe;
            Uid=Nicolai@rateme;
            Pwd={Hejmor1!};
            Encrypt=yes;
            TrustServerCertificate=no;
            Connection Timeout=30;
            """
        )
    return cnxn.cursor()

cursor = connect()
'''
Create user in database
'''
def CreateNewUser(username, password, country, email, gender, birthYear):
    cursor.execute("""
                    SELECT 1
                    FROM [dbo].[Users]
                    WHERE Username = ?
                   """, [username])
    userExists = cursor.rowcount != 0
    if userExists:
        return "User already exists"
    else:
        myctx = CryptContext(schemes=["sha256_crypt", "md5_crypt", "des_crypt"])
        salt = str(randint(10000,200000))
        hash1 = myctx.hash(password+salt)
        
        Username = username.lower()
        HashedPwd = hash1
        PwdSalt = salt
        Country = country
        Email = email
        Gender = gender
        BirthYear = birthYear
        cursor.execute("""
            INSERT INTO [dbo].[Users]
                   ([Username]
                   ,[HashedPwd]
                   ,[PwdSalt]
                   ,[Country]
                   ,[Email]
                   ,[Gender]
                   ,[BirthYear]
                   ,[TimeStamp])
             VALUES
                   (?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    (getdate()))
        """, [Username, HashedPwd, PwdSalt, Country, Email, Gender, BirthYear])
        cnxn.commit()

'''
Login Function
Logs in a user given a username and a password
returns true if password is correct, false if wrong
returns user dosent exist, if the user lookup returned nothing
'''
def login(username, password):
    cursor.execute("""
    SELECT [HashedPwd]
          ,[PwdSalt]
    FROM [dbo].[Users]
    WHERE Username = ?
    """, username)
    
    resp = cursor.fetchone()
    try:
        hash1 = resp[0]
        salt = resp[1]
        return myctx.verify(password+salt, hash1)
    except:
        return "User dosen't exist"

'''
Writes reports to the database given a username and an imagepath
'''
def reportImage(username, ImagePath):
    cursor.execute("""
        INSERT INTO [dbo].[Report]
                   ([Username]
                   ,[ImagePath]
                   ,[TimeStamp])
             VALUES
                   (?,
                    ?,
                    (getdate()))
    """, [Username, ImagePath])
    cnxn.commit()

'''
fetches an images elo score
'''

def getEloScore(image):
    cursor.execute("""
    SELECT [EloScore]
    FROM [dbo].[Elo]
    WHERE [ImagePath] = ?
    """, image)
    
    return cursor.fetchone()

'''
calculates new elo score.
Given a winner and loser image
A tie indicator (0 for no tie 1 for tie)
k is the k value for the elo calculation
'''
def updateScore(winner, loser, tie, k):
    winner = getEloScore(winner)[0]
    loser = getEloScore(loser)[0]
    EA = (1 / (1 + 10**((loser - winner)/400)))
    EB = (1 / (1 + 10**((winner - loser)/400)))
    
    if tie == 0:
        winner  = winner + k * (1 - EA)
        loser  = loser + k * (0 - EB)
    else: 
        winner = winner + k * (0.5 - EA)
        loser = loser + k * (0.5 - EB)
    
    return winner, loser

'''
Votes and update elo
'''
def vote(username, imagepath1, imagepath2, result):
    cursor.execute("""
            INSERT INTO [dbo].[Vote]
                   ([Username]
                   ,[imagePath1]
                   ,[imagePath2]
                   ,[Result]
                   ,[TimeStamp])
             VALUES
                   (?,
                    ?,
                    ?,
                    ?,
                    (getdate()))
        """, [username, imagepath1, imagepath2, result])
    cnxn.commit()
    
    updateElo(imagepath1, imagepath2, result)

'''
Writes the vote to the elo table
Updates the Elo in the image table
Takes in two imagepaths as arguments
the result argument indicates the winner, eg
image1 for imagepath 1 as winner
image2 for imagepath 2 as winner
tie for tie
'''

def updateElo(imagepath1, imagepath2, result):   
    if result == "image1":
        winner = imagepath1
        loser = imagepath2
        tie = 0
        imagepath1Elo , imagepath2Elo = updateScore(winner, loser, tie, 30)
    elif result == "image2":
        winner = imagepath2
        loser = imagepath1
        tie = 0
        imagepath2Elo , imagepath1Elo  = updateScore(winner, loser, tie, 30)
    elif result == "tie":
        winner = imagepath1
        loser = imagepath2
        tie = 1
        imagepath1Elo , imagepath2Elo = updateScore(winner, loser, tie, 30)
    
    imagepath1Elo = int(imagepath1Elo)
    imagepath2Elo = int(imagepath2Elo)
    
    post1 = [[imagepath1, imagepath1Elo], [imagepath2, imagepath2Elo]]
    
    cursor.executemany("""
            INSERT INTO [dbo].[Elo]
                   ([ImagePath]
                   ,[EloScore]
                   ,[TimeStamp])
             VALUES
                   (?,
                    ?,
                    (getdate()))
        """, post1)
    cnxn.commit()
    
    post2 = [[imagepath1Elo, imagepath1], [imagepath2Elo, imagepath2]]
    cursor.executemany("""
            UPDATE [dbo].[Images]
               SET [EloScore] = ?
             WHERE [ImagePath] = ?
        """, post2)
    cnxn.commit()

'''
Uploads an image to the database 
Inserts an elo record of that image in the database
'''
def uploadImage(ImagePath, Username, GenderOfImage):
    cursor.execute("""
        INSERT INTO [dbo].[Images]
               ([ImagePath]
               ,[Username]
               ,[EloScore]
               ,[GenderOfImage]
               ,[TimeStamp])
         VALUES
               (?,
                ?,
                ?,
                ?,
                (getdate()))
    """, [ImagePath, Username, 1500, GenderOfImage])
    cnxn.commit()
    
    cursor.execute("""
        INSERT INTO [dbo].[Elo]
                   ([ImagePath]
                   ,[EloScore]
                   ,[TimeStamp])
             VALUES
                   (?,
                    ?,
                    (getdate()))
    """, [ImagePath, 1500]) 
    cnxn.commit()

'''
Fetches 2 random images from the database
'''
def getRandomImages(gender):
    cursor.execute("""
    SELECT TOP 2 * 
    FROM Images
    WHERE [GenderOfImage] = ?
    ORDER BY NEWID()
    """, gender)
    
    resp = cursor.fetchall()
    img1 = resp[0][0]
    img2 = resp[1][0]
    return [img1, img2]

'''
Grabs all images a user has voted on
'''
def getVotes(username):
    cursor.execute("""
    SELECT [ImagePath1]
          ,[ImagePath2]
    FROM [dbo].[Vote]
    WHERE [Username] = ?
    """, username)
    
    resp = cursor.fetchall()
    return resp

'''
Gets an image set the user has not previously voted for
'''
def getContesters(username, gender):
    votes = getVotes(username)
    random = getRandomImages(gender)
    
    catRandom = random[0]+random[1]
    catRandomSwitch = random[1]+random[0]
    catVotes = ["".join(x) for x in votes]
    
    if catRandom in catVotes:
        getContesters(username, gender)
    elif catRandomSwitch in catVotes:
        getContesters(username, gender)

    return random