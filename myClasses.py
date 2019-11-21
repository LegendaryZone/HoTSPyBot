import cv2
import mss
import numpy as np
from matplotlib import pyplot as plt
import queue

class LogObject():
    def __init__(self):
        self.messages = []
    def getMessages(self):
        return self.message
    def setMessages(self,m):
        self.message = m
    def log(self, m):
        if len(self.messages) > 0:
            if m != self.messages[-1]:
                print(f"{m}")
                self.messages.append(m)
        else:
            print(f"{m}")
            self.messages.append(m)            
    
    def lastMessage(self):
        print(f"{self.messages[-1]}")

class StateObject():
    def __init__(self):
        self.state = "undefined"
        self.side = "undefined"
        self.speed = 0
        self.maxSize = 15
        self.stateQ = queue.Queue(maxsize = self.maxSize)

        self.speedCount = 0

    def getState(self):
        return self.state
    def setState(self,state):
        if self.stateQ.qsize() >= self.maxSize:
            self.stateQ.get()
        self.stateQ.put(state)
        self.state = max(self.stateQ.queue)
    def getSide(self):
        return self.side
    def setSide(self,side):
        self.side = side
    def getSpeed(self):
        if self.speedCount > 0:
            return self.speed/self.speedCount
        return self.speed
        # return self.speed
    def setSpeed(self,speed):
        self.speed += speed
        self.speedCount += 1
        # self.speed = speed

class GameStateObject():
    def __init__(self):
        self.gameState = {}
        self.procRunning = False
    def getGameState(self):
        return self.gameState
    def getGameStateValue(self,k):
        if k in self.gameState.keys():
            return self.gameState[k]
        else:
            return ""
    def setGameStateKeyValue(self,k,v):
        self.gameState[k] = v
    def setProcStatus(self,p):
        self.procRunning = p
    def getProcRunning(self):
        return self.procRunning


class KeyboardObject():
    def __init__(self):
        self.action = "undefined"
    def getAction(self):
        return self.action
    def setAction(self,action):
        self.action = action

class TemplateFinder():
    def __init__(self, **kwargs):
        #self.val2 = kwargs.get('val2',"default value")
        pass

    def find(self, zone, template, threshold, vis = False):
        methods = ['cv2.TM_CCOEFF', 'cv2.TM_CCOEFF_NORMED', 'cv2.TM_CCORR', 'cv2.TM_CCORR_NORMED', 'cv2.TM_SQDIFF', 'cv2.TM_SQDIFF_NORMED']
        method = eval(methods[1])
        with mss.mss() as sct:
            img = np.array(sct.grab(zone))
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            w, h = template.shape[::-1]
            res = cv2.matchTemplate(img,template,method)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
            
            if vis:
                # Visualisation of best match
                bottom_right = (max_loc[0] + w, max_loc[1] + h)
                cv2.rectangle(img,max_loc, bottom_right, 255, 2)
                plt.subplot(121),plt.imshow(res,cmap = 'gray')
                plt.title('Matching Result'), plt.xticks([]), plt.yticks([])
                plt.subplot(122),plt.imshow(img,cmap = 'gray')
                plt.title('Detected Point'), plt.xticks([]), plt.yticks([])
                plt.suptitle(max_val)
                plt.show()

            # If the method is TM_SQDIFF or TM_SQDIFF_NORMED, take minimum
            if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
                top_left = min_loc
                if min_val < 1 - threshold:
                    return True
                else:
                    return False
            else:
                top_left = max_loc
                if max_val > threshold:
                    return True
                else:
                    return False

class ColorFinder():
    def __init__(self):
        pass
    def checkColor(self, zone, color, sens, retPoints = False,vis = False):
        s = int(sens / 2)
        lower = np.array([i - s for i in color])
        upper = np.array([i + s for i in color])
        color = np.array(color)
        minArea = 1
        maxArea = 1000
        circularity = False

        with mss.mss() as sct:
            img = cv2.cvtColor(np.array(sct.grab(zone)), cv2.COLOR_BGRA2BGR) #sct.grab(zone)
            #color filtering
            filtered_color = cv2.bitwise_and(img,img,mask = cv2.inRange(img, lower, upper))
            _,mask = cv2.threshold(filtered_color,1,255,cv2.THRESH_BINARY)
            masked = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((10,10),np.float32)/10) #espansione
            #blob detection
            params = cv2.SimpleBlobDetector_Params()
            params.minThreshold = 1
            params.maxThreshold = 255
            
            params.filterByArea = True
            params.minArea = minArea
            params.maxArea = maxArea            

            params.filterByCircularity = circularity
            params.filterByInertia = False
            params.filterByConvexity = False
            params.filterByColor = False
            params.blobColor = 255
            # Create a detector with the parameters
            ver = (cv2.__version__).split('.')
            if int(ver[0]) < 3:
                detector = cv2.SimpleBlobDetector(params)
            else: 
                detector = cv2.SimpleBlobDetector_create(params)
            points = []
            keypoints = []    
            for k in detector.detect(masked):
                keypoints.append(k)
                points.append([k.pt[0],k.pt[1]])
            #print(f"keypoints: {keypoints}, points: {points}")

            if vis:
                cv2.imshow("Ori", img)
                cv2.imshow("filtered_color", filtered_color)
                cv2.imshow("mask", mask)
                cv2.imshow("masked", masked)
                if cv2.waitKey(25) & 0xFF == ord("q"):
                    cv2.destroyAllWindows()
            
            if retPoints:
                return keypoints, points
            else:
                if len(keypoints) > 0:
                    return True
                else: 
                    return False