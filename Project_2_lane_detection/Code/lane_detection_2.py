import cv2
import numpy as np
import matplotlib.pyplot as plt
import warnings


# This function analyzes the histogram of the warped road image and returns likely locations of 
# lane candidates in terms of lower and upper bounds of their x coordinates.
def getLanesFromHist(hist):
	l = list(hist[0].copy())
	max1 = max(l)
	l.remove(max1)
	max2 = max(l)
	lower1 = lower2 = upper1 = upper2 = 0
	for i in range(len(hist[0])):
		if hist[0][i] == max1:
			lower1 = hist[1][i]
			upper1 = hist[1][i+1]
		elif hist[0][i] == max2:
			lower2 = hist[1][i]
			upper2 = hist[1][i+1]

	return [[lower1, upper1], [lower2, upper2]]


# This function runs a sliding window search on the likely lane candidates to get all points in that lane.
def getLanePoints(warped, lower, upper):
	width = upper - lower
	height = 70
	yStart = warped.shape[0]-1
	points = []

	while yStart:

		pixelCount = 0
		xsum = 0
		for x in range(lower, upper):
			for y in range(yStart, yStart-height, -1):
				if warped[y][x] != 0:
					pixelCount += 1
					points.append((x,y))
					xsum += x

		yStart -= height
		if yStart < height:
			height = yStart

		if pixelCount:
			lower = int(max(0, np.floor((xsum/pixelCount) - width/2)))
			upper = min(lower + width, warped.shape[1]-1)

		# print(lower, upper)
	return points


# A function to draw the histogram to get lane candidates
def drawHistogram(thresh, nbins, height):
	count = []
	for x in range(thresh.shape[1]):
		for y in range(thresh.shape[0]-height, thresh.shape[0]):
			if thresh[y][x] != 0:
				count.append(x)

	#plt.plot(range(len(count)), count)
	ret = plt.hist(count, bins=nbins, range=(0, thresh.shape[1]-1))
	#plt.show()

	return ret	


# A function that takes a set of points belonging to a lane and returns evenly spaced points that lie on
# the curve fitted to that set of points.
def fitPolynomial(img, dataset):
	matrix_y = []
	matrix_x = []
	for point in dataset:
	 	matrix_y.append(point[1])
	 	#matrix_x.append((point[0]**2, point[0], 1))
	 	matrix_x.append(point[0])
	y = np.array(matrix_y)
	x = np.array(matrix_x)

	with warnings.catch_warnings():
		warnings.filterwarnings('error')
		try:												# Default fit is a line. If polyfit() throws a warning message due to a bad fit, we change to a second order polynomial.
			coeffs = np.polyfit(matrix_x, matrix_y, 1)		# The default is set to a line because a second order polynomial has a worse fit as comparison to the line
		except:
			coeffs = np.polyfit(matrix_x, matrix_y, 2)
	points = []

	x = range(0, img.shape[1]-1, 10)
	if len(coeffs) == 3:
		for xi in x:
			y = coeffs[0]*(xi**2) + coeffs[1]*xi + coeffs[2]
			if y > 470 and y < frame.shape[0]:
				points.append((int(xi), int(y)))
	else:
		for xi in x:
			y = coeffs[0]*xi + coeffs[1]
			if y > 470 and y < frame.shape[0]:
				points.append((int(xi), int(y)))

	diff = abs(points[0][0] - points[-1][0])

	return points, diff


#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------MAIN BODY--------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
firstFrame = True
K_matrix = np.array([[1.15422732e+03,0.00000000e+00,6.71627794e+02], [0.00000000e+00,1.14818221e+03,3.86046312e+02], [0.000000e+00, 0.000000e+00, 1.000000e+00]], np.float32)
distCoeffs = np.array([-2.42565104e-01,-4.77893070e-02,-1.31388084e-03,-8.79107779e-05,2.20573263e-02], np.float32)

imgArray = []
cap = cv2.VideoCapture("../../Media/data_2/challenge_video.mp4")
while cap.isOpened():
	ret, frame = cap.read()
	if not ret:
		cv2.destroyAllWindows()
		break
		
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# PART 1: GET REQUIRED POINTS AND HOMOGRAPHY MATRIX FROM THE FIRST FRAME OF THE VIDEO


	frame = cv2.undistort(frame, K_matrix, distCoeffs)
	if firstFrame:

		corners = np.array([[590,470],[754,470],[1120,690],[280,690]],np.float32)
		# for c in corners:
		# 	frame = cv2.circle(frame, tuple(c), 1, (0,0,255), 2)
		dims = (frame.shape[1], frame.shape[0])
		width = corners[1][0] - corners[0][0]
		height = np.sqrt((corners[3][1]-corners[0][1])**2 + (corners[3][0]-corners[0][0])**2)
		destCorners = np.array([[0,0],[width,0],[width,height],[0,height]],np.float32) #np.array([corners[0], [corners[0][0]+width,corners[0][1]], [corners[0][0]+width,corners[0][1]+height], [corners[0][0],corners[0][1]+height]], np.float32)
		H = cv2.getPerspectiveTransform(corners, destCorners)
		Hinv = cv2.getPerspectiveTransform(destCorners, corners)
		warped = np.zeros((int(height), int(width)), dtype=np.uint8)
		firstFrame = False

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# PART 2: FILTER AND TRANSFORM THE FRAME


	filtered = cv2.GaussianBlur(frame,(9,9),0)
	hsvFrame = cv2.cvtColor(filtered, cv2.COLOR_BGR2HLS)
	bwFrame = cv2.cvtColor(filtered, cv2.COLOR_BGR2GRAY)
	y_lower = np.array([15,0,60])
	y_upper = np.array([35,255,255])
	w_lower = np.array([170])
	w_upper = np.array([220])
	y_mask = cv2.inRange(hsvFrame, y_lower, y_upper)
	w_mask = cv2.inRange(bwFrame, w_lower, w_upper)
	mask = cv2.bitwise_or(y_mask, w_mask)
	output = cv2.bitwise_and(filtered,filtered, mask= mask)
	#ret, output = cv2.threshold(cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY), 180, 255, 0)
	#output = cv2.cvtColor(cv2.cvtColor(output,cv2.COLOR_HLS2BGR), cv2.COLOR_BGR2GRAY)
	#edges = cv2.Sobel(output, cv2.CV_64F, 1, 0, ksize=7)
	edges = cv2.Canny(output, 30, 100)
	warped = cv2.warpPerspective(edges, H, (warped.shape[1], warped.shape[0]))
	#warped = cv2.cvtColor(cv2.cvtColor(warped,cv2.COLOR_HLS2BGR), cv2.COLOR_BGR2GRAY)
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# PART 3: DRAW HISTOGRAM, EXTRACT LIKELY LANE CANDIDATES AND FIT A CURVE THROUGH THE LANE AND SHOW THE LANE ON THE FRAME


	hist = drawHistogram(warped, 7, warped.shape[0]-1)
	ind = 0
	allPoints = [[]]
	for element in getLanesFromHist(hist):
		newPointsX = newPointsY = []
		lowerBound = int(np.floor(element[0]))
		upperBound = int(min(np.ceil(element[1]), warped.shape[1]-1))
		lanePoints = np.array(getLanePoints(warped, lowerBound, upperBound),np.float32)
		for p in lanePoints:
			p = np.array([[p]],np.float32)
			tfPoint = cv2.perspectiveTransform(p, Hinv)[0][0]
			newPointsX.append(tfPoint[0])
			newPointsY.append(tfPoint[1])
			allPoints[ind].append([int(tfPoint[0]),int(tfPoint[1])])

		ind = 1
		allPoints.append([])
		
	newPointsX = np.array(newPointsX)
	newPointsY = np.array(newPointsY)
	points = []
	diff = [None, None]
	for i in range(2):
		polyPoints, diff[i] = fitPolynomial(frame, allPoints[i])
		for p in polyPoints:
			points.append(p)

	if abs(diff[0]-diff[1]) < 100:
		turn = ''
	elif diff[0] < diff[1]:
		turn = 'Right Turn'
	else:
		turn = 'Left Turn'
	overlayFrame = frame.copy()
	cv2.putText(frame, turn, (500,40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2, cv2.LINE_AA)
	cv2.fillPoly(overlayFrame, np.array([points],np.int32), (0,255,0))
	frame = cv2.addWeighted(overlayFrame, 0.4, frame, 0.6, 0)
	imgArray.append(frame)

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# PART 4: WRITE THE VIDEO FILE

	cv2.imshow('Data 2', frame)
	if cv2.waitKey(10) & 0xff == 27:	
	 	break
	 	cv2.destroyAllWindows()

output = cv2.VideoWriter('video_2.mp4', cv2.VideoWriter_fourcc('m','p','4','v'), 15, dims)
for i in range(len(imgArray)):
	output.write(imgArray[i])
output.release()