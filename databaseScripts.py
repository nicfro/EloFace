import pyodbc
import datetime
from passlib.context import CryptContext
import random
import csv
import tinys3

myctx = CryptContext(schemes=["sha256_crypt", "md5_crypt", "des_crypt"])

def connect():
    cnxn = pyodbc.connect(r'Driver={SQL Server};Server=.\SQLEXPRESS;Database=RateMe;Trusted_Connection=yes;')
    return cnxn.cursor()

cursor = connect()

def getS3Credentials():
    with open('credentials.csv', 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            access_key = row[2]
            secret_key = row[3]
    return access_key, secret_key

access_key, secret_key = getS3Credentials()

'''
Upload image to S3 bucket
'''
def uploadS3Image(image, fileName):
    conn = tinys3.Connection(access_key,secret_key,default_bucket='ratemegirl')
    conn.upload(fileName,image)

'''
Delete file from S3 bucket
'''
def suspendS3Image(filename):
    conn = tinys3.Connection(access_key,secret_key,default_bucket='ratemegirl')
    conn.copy(filename,"ratemegirl",'suspended'+filename[3:])
    conn.delete(filename)
    cursor.execute("""
                UPDATE [dbo].[Report]
                   SET [Suspended] = 1
                 WHERE ImagePath = ?
                   """, filename)

'''
Check if user exists in database
'''
def userExists(username):
    cursor.execute("""
                    SELECT 1
                    FROM [dbo].[Users]
                    WHERE Username = ?
                   """, [username])
    userExists = cursor.rowcount != 0
    if userExists:
        return True
    else:
        return False


def CreateNewUser(username, password, country, email, gender, bday, race):
    myctx = CryptContext(schemes=["sha256_crypt", "md5_crypt", "des_crypt"])
    ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    salt=[]
    [salt.append(random.choice(ALPHABET)) for x in range(16)]
    salt = "".join(salt)
    hash1 = myctx.hash(password+salt)
    
    username = username.lower()
    HashedPwd = hash1
    PwdSalt = salt
    cursor.execute("""
        INSERT INTO [dbo].[Users]
               ([Username]
               ,[HashedPwd]
               ,[PwdSalt]
               ,[Country]
               ,[Email]
               ,[Gender]
               ,[BirthYear]
               ,[Race]
               ,[TimeStamp])
         VALUES
               (?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                (getdate()))
    """, [username, HashedPwd, PwdSalt, country, email, gender, bday, race])
    cursor.commit()

'''
Login Function
Logs in a user given a username and a password
returns true if password is correct, false if wrong
returns user dosent exist, if the user lookup returned nothing
'''
def userLogin(username, password):
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
        return False

'''
Writes reports to the database given a username and an imagepath
'''
def reportImage(username, imagePath):
    cursor.execute("""
        INSERT INTO [dbo].[Report]
                   ([Username]
                   ,[ImagePath]
                   ,[TimeStamp]
                   ,[Suspended])
             VALUES
                   (?,
                    ?,
                    (getdate()),
                    0)
    """, [username, imagePath])
    cursor.commit()

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
def ratePictures(username, imagepath1, imagepath2, result):
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
    cursor.commit()
    
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
    cursor.commit()
    
    post2 = [[imagepath1Elo, imagepath1], [imagepath2Elo, imagepath2]]
    cursor.executemany("""
            UPDATE [dbo].[Images]
               SET [EloScore] = ?
             WHERE [ImagePath] = ?
        """, post2)
    cursor.commit()

'''
Uploads an image to the database 
Inserts an elo record of that image in the database
'''
def uploadImage(ImagePath, Username, GenderOfImage, Race, Age):
    cursor.execute("""
        INSERT INTO [dbo].[Images]
               ([ImagePath]
               ,[Username]
               ,[EloScore]
               ,[GenderOfImage]
               ,[Race]
               ,[AgeGroup]
               ,[TimeStamp])
         VALUES
               (?,
                ?,
                ?,
                ?,
                ?,
                ?,
                (getdate()))
    """, [ImagePath, Username, 1500, GenderOfImage, Race, Age])
    cursor.commit()
    
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
    cursor.commit()

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
Get 2 images set the user has not previously voted for
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

def getNewFileName():
    cursor.execute("""
    SELECT MAX([ImagePath])
    FROM [RateMe].[dbo].[Images]
    """)
    
    resp = cursor.fetchone()[0]
    firstPart = resp[:-5]
    addOne = str(int(resp[-5])+1)
    lastPart = resp[-4:]
    return firstPart+addOne+lastPart

def suspendImages():
    cursor.execute("""
    SELECT Distinct
    [ImagePath]
    FROM [RateMe].[dbo].[Report]
    WHERE suspended = 0
    """)
    resp = cursor.fetchall()
    resp = [x[0] for x in resp]
    suspended = []
    for image in resp:
        suspendS3Image(image)
        suspended.append(image)
    print("Suspended following images:")
    print(suspended)

def getHighscores(gender):
    cursor.execute("""
        SELECT TOP(10) [ImagePath],
                       [EloScore]
        FROM [RateMe].[dbo].[Images]
        WHERE GenderOfImage = ?
        ORDER BY EloScore DESC
    """, gender)
    resp = cursor.fetchall()
    return resp

#Better the deletion of reported images -> Add admin site 

#handle quality of uploaded images

#handle duplicates of uploaded images

#add feedback site

#add solid face detection

#add voting on males