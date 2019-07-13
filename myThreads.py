import threading
import time
class myThread(threading.Thread):
    def __init__(self,name,count,keepGoing,mainObj):
        threading.Thread.__init__(self)
        self.count = count
        self.keepGoing = keepGoing
        self.name = name
        self.mainObj = mainObj
    
    def run(self):
        while self.keepGoing:
            self.count = self.count + 1
            self.mainObj[self.name] = self.count
            time.sleep(1)
        return 0