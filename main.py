import time
import multiprocessing
import json
import cv2
import os
import pickle
import socketio
import asyncio
import sys
from aiohttp import web
import aiohttp_cors
from multiprocessing.managers import BaseManager
from processes import StateFinder, KeyboardListener,UIScanner
from myClasses import StateObject, KeyboardObject, LogObject, GameStateObject
from threads import Server
version = 0.1
procList = {}
settings = 0

sio = socketio.AsyncServer(cors_allowed_origins='*')
app = web.Application()
sio.attach(app)
client = None
# cors = aiohttp_cors.setup(app, defaults={
#     "*": aiohttp_cors.ResourceOptions(
#             allow_credentials=True,
#             expose_headers="*",
#             allow_headers="*",
#         )
# })
# resource = cors.add(app.router.add_resource("/socket.io"))


async def index(request):
    print("Serving index.html")
    with open('client/index.html') as f:
        return web.Response(text=f.read(), content_type='text/html')

@sio.event
async def connect(sid, environ):
    client = sid
    await sio.emit("stateUpdate",data="WELCOME",to=client)
    print("connected:", sid)

def testCB():
    print("testCB")

app.router.add_get('/', index)

async def stopServer(thread):
    await thread.stop()
    Log.log("Server thread is dead")

def firstRun():
    resString = input("Enter the inGame resolution ex 1920x1080: ")
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
    
    procList.update({"KeyboardListener": KeyboardListener(keyboard,Log)})
    procList.update({"StateFinder": StateFinder(state, Log, settings["stateFindingResources"])})
    procList.update({"UIScanner": UIScanner(gameState,Log,settings,state)})

    serverThread = Server(web,app,asyncio.get_event_loop(),Log)
    serverThread.start()
    procList["KeyboardListener"].start()
    

    Log.log("Enter the lobby and press F5 to start the bot, F6 to kill it!")
    # Wait until user presses F10
    while not keyboard.getAction()=="Start":
        pass
    # Starts the bot!
    for k in procList:
        if k != "KeyboardListener":
            procList[k].start()
    lastTime = 0

    
    

    while not keyboard.getAction() == "Exit":
        lastTime = time.time()
        s = '{0:.0f}'.format(state.getSpeed())
        #Log.log(f"{s} Hz STATE: {state.getState()} HP: {gameState.getGameStateValue('hp')} SIDE: {state.getSide()}")
        asyncio.run(sio.emit("stateUpdate",state.getState(),to=client))
        asyncio.run(sio.emit("gameStateUpdate",gameState.getGameState(),to=client))
        asyncio.run(sio.emit("loopSpeed",s,to=client))
        # if gameState.getProcRunning():
              #Log.log(f"HP: {gameState.getGameStateValue('hp')}")
        #     #Log.log(f"GameState: {json.dumps(gameState.getGameState(),indent = 4)}")

        delta = (time.time() - lastTime)
        if delta > 0: state.setSpeed( ( 1/(time.time() - lastTime) ) )

    for k in procList:
        if hasattr(procList[k],"threadList"):
            print(f"Process {k} has threads: {procList[k].threadList} stopping them")
            for t in procList[k].threadList:
                procList[k].threadList[t].stop()
            procList[k].shutdown()
    asyncio.run(stopServer(serverThread))
    print("Stopped all processes")
    exit()