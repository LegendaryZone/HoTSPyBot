import time
import multiprocessing
import json
import cv2
import os
import pickle
from multiprocessing.managers import BaseManager
from processes import StateFinder, KeyboardListener,UIScanner
from myClasses import StateObject, KeyboardObject, LogObject, GameStateObject

version = 0.1
procList = {}
settings = 0

def firstRun():
    resString = input("Entre the inGame resolution ex 1920x1080: ")
    if "x" in resString:
        settings["resolution"] = [int(i) for i in resString.split("x")]
        print(f"Res: {settings['resolution']}")
        print(f"Updating settings file..")
        with open("settings.json","w") as f:
            json.dump(settings,f)
    else:
        print("resolution\'s dimensions should be separed by a \"x\"")
        exit(1)


if __name__ == '__main__':
    print(f"Welcome to HoTSPyBot ver: {version}")
    # Loading configuration, setting resolution and patterns
    print("Loading configuration file...")
    with open("settings.json") as f:
        settings = json.load(f)
    if settings["resolution"] == "undefined":
        firstRun()
    print("Loading templates...")
    with open("templates.pickle","rb") as f:
        t = pickle.load(f)
        for k,v in t.items():
            for k1,v1 in v.items():
                settings["stateFindingResources"][k][k1]["template"] = t[k][k1]["template"]
    # Registering all objects needed for processes
    BaseManager.register('KeyboardObject',KeyboardObject)
    BaseManager.register('StateObject',StateObject)
    BaseManager.register('LogObject',LogObject)
    BaseManager.register('GameStateObject',GameStateObject)
    manager = BaseManager()
    manager.start()
    state = manager.StateObject()
    keyboard = manager.KeyboardObject()
    Log = manager.LogObject()
    gameState = manager.GameStateObject()

    procList.update({"StateFinder": StateFinder(state, Log, settings["stateFindingResources"])})
    procList.update({"KeyboardListener": KeyboardListener(keyboard,Log)})
    procList.update({"UIScanner": UIScanner(gameState,Log,settings,state)})

    procList["KeyboardListener"].start()
    
    Log.log("Enter the lobby and press F5 to start the bot, F6 to kill it!")
    # Wait until user presses F10
    while not keyboard.getAction()=="Start":
        pass
    # Starts the bot!
    for k in procList:
        if k != "KeyboardListener" and k != "UIScanner":
            procList[k].start()
    lastTime = 0
    while not keyboard.getAction() == "Exit":
        lastTime = time.time()
        s = '{0:.2f}'.format(state.getSpeed())
        Log.log(f"{s} Hz STATE: {state.getState()} SIDE: {state.getSide()}")
        
        if gameState.getProcRunning():
            Log.log(f"HP: {gameState.getGameStateValue('hp')}")
            #Log.log(f"GameState: {json.dumps(gameState.getGameState(),indent = 4)}")
        if state.getState() == "inGame" and not gameState.getProcRunning():
            procList["UIScanner"].start()
            Log.log("sleeping...")
            time.sleep(5)
        # if state.getState() != "inGame" and gameState.getProcRunning():
        #     procList["UIScanner"].shutdown()
        #     Log.log("sleeping...")
        #     time.sleep(5)
        delta = (time.time() - lastTime)
        if delta > 0: state.setSpeed( ( 1/(time.time() - lastTime) ) )
    print("Stopping all processes")
    for k in procList:
        procList[k].shutdown()