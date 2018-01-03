import cv2
import sys
import pyodbc
from PIL import Image
import urllib.request

cascPath = "haarcascade_frontalface_default.xml"

# Create the haar cascade
faceCascade = cv2.CascadeClassifier(cascPath)
cursor = pyodbc.connect(r'Driver={SQL Server};Server=.\SQLEXPRESS;Database=RateMe;Trusted_Connection=yes;').cursor()

cursor.execute("""
SELECT TOP (100) [ImagePath]

FROM [RateMe].[dbo].[Images]
""")

test = cursor.fetchall()
test = [x[0] for x in test]

for URL in test:
	URL = "https://s3-eu-west-1.amazonaws.com/ratemegirl/"+URL
	print(URL)
	with urllib.request.urlopen(URL) as url:
		with open('temp.jpg', 'wb') as f:
			f.write(url.read())

	image = cv2.imread('temp.jpg')
	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

	faces = faceCascade.detectMultiScale(gray,
		scaleFactor=1.2,
		minNeighbors=4,
		minSize=(30, 30)
		#flags = cv2.CV_HAAR_SCALE_IMAGE
	)

	print("Found {0} faces!".format(len(faces)))

	# Draw a rectangle around the faces
	for (x, y, w, h) in faces:
		cv2.rectangle(image, (x, y), (x+w, y+h), (0, 255, 0), 2)

	cv2.imshow("Facesfound.png", image)
	cv2.waitKey(0)
	cv2.destroyAllWindows()