import multiprocessing
import random
from pynput import keyboard
from myClasses import TemplateFinder, ColorFinder
from threads import HPScanner, MapScanner

class KeyboardListener(multiprocessing.Process):

    def __init__(self, keyboardObject, Log, **kwargs):
        multiprocessing.Process.__init__(self)
        self.name = "KeyboardListener"
        self.keyboardObject = keyboardObject
        self.exit = multiprocessing.Event()
        self.Log = Log

    def run(self):
        self.Log.log(f"Starting {self.name}")
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()
        while not self.exit.is_set():
            pass
        self.Log.log(f"Shutdown complete for {self.name}")

    def shutdown(self):
        self.Log.log(f"Shutdown initiated for {self.name}")
        self.exit.set()

    def on_press(self,key):
        try:
            if key==keyboard.Key.f10:
                self.keyboardObject.setAction("Start")
                #self.Log.log(f"{self.name}: {self.keyboardObject.getAction()}")
            if key==keyboard.Key.f11:
                self.keyboardObject.setAction("Exit")  
        except AttributeError:
            self.Log.log('key {0} pressed'.format(key))



class StateFinder(multiprocessing.Process):

    def __init__(self, stateObject, Log, settings, **kwargs):
        multiprocessing.Process.__init__(self)
        self.name = "StateFinder"
        self.stateObject = stateObject
        self.exit = multiprocessing.Event()
        self.Log = Log
        self.templateFinder = TemplateFinder()
        self.colorFinder = ColorFinder()
        self.settings = settings

    def run(self):
        self.Log.log(f"Starting {self.name}")
        while not self.exit.is_set():
            if self.checkClientCommon():
                if self.checkLobby():
                    self.stateObject.setState("lobby")
                elif self.checkLeave():
                    self.stateObject.setState("leave")
                elif self.checkSearching():
                    self.stateObject.setState("searching")
                elif self.checkHome():
                    self.stateObject.setState("home")
                # else:
                #     self.stateObject.setState("undefined")                                
            elif self.checkRejoin():
                self.stateObject.setState("rejoin")
            elif self.checkThanks():
                self.stateObject.setState("thanks")
            elif self.checkLobby():
                self.stateObject.setState("roster")
            elif self.checkMVP():
                self.stateObject.setState("mvp")
            elif self.checkLoading():
                self.stateObject.setState("loading")
            elif self.checkInGame():
                self.stateObject.setState("inGame")
            # else:
            #     self.stateObject.setState("undefined")
        self.Log.log(f"Shutdown complete for {self.name}")

    def shutdown(self):
        self.Log.log(f"Shutdown initiated for {self.name}")
        self.exit.set()

    def checkClientCommon(self):
        l= ["coin","logo","gem"]
        th = 0.9
        return self.findTemplateInBox("clientCommon",l,th)

    def checkLobby(self):
        l = ["hero", "readyBL","readyBR","readyTR","readyTL"]
        th = 0.9
        return self.findTemplateInBox("lobby",l,th)

    def checkLeave(self):
        l= ["btnOne","btnTwo"]
        th = 0.9
        retval = self.findTemplateInBox("leave",l,th)
        if retval: self.stateObject.setSide("undefined")
        return  retval

    def checkSearching(self):
        l= ["TL","BR"]
        th = 0.9
        return self.findTemplateInBox("searching",l,th)

    def checkRejoin(self):
        l= ["btnOneTL","btnOneBR","btnTwoTL","btnTwoBR"]
        th = 0.9
        return self.findTemplateInBox("rejoin",l,th)

    def checkThanks(self):
        l= ["question","btnTL","btnBR"]
        th = 0.9
        return self.findTemplateInBox("thanks",l,th)
    
    def checkHome(self):
        l= ["ico"]
        th = 0.9
        return self.findTemplateInBox("home",l,th)

    def checkMVP(self):
        l1= ["arrowB"]
        l2= ["arrowR"]
        th = 0.9
        return self.findTemplateInBox("mvp",l1,th) or self.findTemplateInBox("mvp",l2,th)

    def checkInGame(self):
        #l=["exa","exa1","exa2","exa3"]
        l=["exa1","exa2","exa3"]
        th = 0.9
        return self.findTemplateInBox("inGame",l,th)

    def findTemplateInBox(self, category, tempList, th, vis = False):
        for l in tempList:
            if not self.templateFinder.find(self.settings[category][l]["box"],self.settings[category][l]["template"],th,vis):
                return False
        return True

    def checkLoading(self):
        sens = 50

        left = self.colorFinder.checkColor(self.settings["loading"]["left"],self.settings["loading"]["color"],sens) 
        right = self.colorFinder.checkColor(self.settings["loading"]["right"],self.settings["loading"]["color"],sens)

        if self.stateObject.getSide() == "undefined":
            if left: self.stateObject.setSide("left")
            elif right: self.stateObject.setSide("right")
        return left or right


class UIScanner(multiprocessing.Process):
    def __init__(self, gameStateObject, Log, settings, **kwargs):
        multiprocessing.Process.__init__(self)
        self.name = "UIScanner"
        self.gameStateObject = gameStateObject
        self.exit = multiprocessing.Event()
        self.Log = Log
        self.settings = settings
        self.running = False
        self.threadList = {}


    def run(self):
        self.gameStateObject.setProcStatus(True)
        self.Log.log(f"Starting {self.name}")
        self.threadList.update({"HPScanner":HPScanner("HPScanner",self.gameStateObject,self.Log,self.settings["inGameResources"]["hpBar"])})
        self.threadList.update({"MapScanner":MapScanner("MapScanner",self.gameStateObject,self.Log,self.settings["inGameResources"]["map"])})
        for k in self.threadList:
            self.threadList[k].start()
        while not self.exit.is_set():
            pass
        self.Log.log(f"Shutdown complete for {self.name}")
        self.gameStateObject.setProcStatus(False)

    def shutdown(self):
        self.Log.log(f"Shutdown initiated for {self.name}")
        for t in self.threadList:
            self.threadList[t].stop()
        self.exit.set()
    # def isRunning(self):
    #     self.Log.log(f"Process: {self.name} isRunning(): {self.running}")
    #     return self.running
