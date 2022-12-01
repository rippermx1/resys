from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models.bot import NewBotRequest, UserSecret, BotStatus, BotActive, UserSecretUuid
from helpers.constants import COLLECTION_USER, DB_RESYS
from auth.auth import Auth
import subprocess
import os
import signal
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/new/bot")
async def new_bot(request: NewBotRequest):
    auth = Auth(DB_RESYS, request.secret)
    if not auth._user_exist():
        return { 'status': 'error', 'message': 'User not found' }
    if auth._create_bot(request.bot) is not None:        
        return { 'status': 'success', 'message': 'Bot created' }
    return { 'status': 'error', 'message': 'Bot not created' }


@app.post("/user/bots")
async def user_bots(request: UserSecret):
    auth = Auth(DB_RESYS, request.secret)
    if not auth._user_exist():
        return { 'status': 'error', 'message': 'User not found' }
    return { 'status': 'success', 'message': 'Bots fetched', 'data': auth._get_bots() }


@app.post("/user/bot/status")
async def bot_status(request: BotStatus):
    auth = Auth(DB_RESYS, request.secret)
    if not auth._user_exist():
        return { 'status': 'error', 'message': 'User not found' }
    return { 'status': 'success', 'message': 'Bots Updated', 'data': auth._update_bot_status(request.uuid, request.status) }


@app.post("/user/bot/active")
async def bot_active(request: BotActive):
    auth = Auth(DB_RESYS, request.secret)
    if not auth._user_exist():
        return { 'status': 'error', 'message': 'User not found' }
    
    if request.active:
        p = subprocess.Popen('start cmd /k python {}main.py -secret {} -bot_id {} '.format(os.getenv('PATH_BOT_FOLDER'), request.secret, request.uuid), shell=True)
        print(p.pid)
        auth.update_bot_pid(request.uuid, p.pid)
    else:
        bot = auth.get_bot(request.uuid)
        if bot['pid'] is not None:
            os.kill(bot['pid'], signal.SIGTERM)
            auth.update_bot_pid(request.uuid, None)
    return { 'status': 'success', 'message': 'Bots Updated', 'data': auth._update_bot_active(request.uuid, request.active) }


@app.post("/user/bot/delete")
async def bot_delete(request: BotStatus):
    auth = Auth(DB_RESYS, request.secret)
    if not auth._user_exist():
        return { 'status': 'error', 'message': 'User not found' }
    return { 'status': 'success', 'message': 'Bot deleted', 'data': auth._delete_bot(request.uuid) }


@app.post("/client/menu")
async def client_menu(request: UserSecretUuid):
    auth = Auth(DB_RESYS, request.secret)
    if not auth._user_exist():
        return { 'status': 'error', 'message': 'User not found' }
    print(auth._get_client_menu(request.uuid))
    return { 'status': 'success', 'message': 'Menu fetched', 'data': auth._get_client_menu(request.uuid) }