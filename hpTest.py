import mss
import numpy as np 
import cv2

hpBar={
        "box":{
            "top":1009,
            "left":206,
            "width":192,
            "height":1
        },
        "maskVerts":[
[            [0,19],
            [10,0],
            [208,0],
            [198,19]]
        ],
        "hpColor":[ 21 ,196 ,62 ],
        "shieldColor":[236,243,240]
    }
scan = True

def colorFilter(img,lower,upper):
    # s = int(sens / 2)
    # lower = np.array([i - s for i in color])
    # upper = np.array([i + s for i in color])
    # color = np.array(color)
    lower=np.array(lower)
    upper=np.array(upper)
    filtered_color = cv2.bitwise_and(img,img,mask = cv2.inRange(img, lower, upper))
    _,mask = cv2.threshold(filtered_color,1,255,cv2.THRESH_BINARY)
    return cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((10,10),np.float32)/10) #espansione

class Log:
    def __init__(self):
        self.messages = []
    def log(self,m):
        if len(self.messages) > 0:
            if m != self.messages[-1]:
                print(f"{m}")
                self.messages.append(m)
        else:
            print(f"{m}")
            self.messages.append(m) 

if __name__ == "__main__":
    with mss.mss() as sct:
        total = hpBar["box"]["width"] * hpBar["box"]["height"]
        Log = Log()
        while scan:
            img = cv2.cvtColor(np.array(sct.grab(hpBar["box"])),cv2.COLOR_BGRA2BGR)
            cv2.imshow("img",img)
            blurred = cv2.GaussianBlur(img, (5, 5), 0)
            green = cv2.cvtColor(colorFilter(blurred,[0,80,0],[128,255,128]),cv2.COLOR_BGR2GRAY)
            cv2.imshow("blurred",blurred)
            cv2.imshow("green",green)
            nonzero = cv2.countNonZero(green)
            
            Log.log(f"HP: {(nonzero/total)*100}%")
            if cv2.waitKey(25) & 0xFF == ord("q"):
                scan = False
                cv2.destroyAllWindows()