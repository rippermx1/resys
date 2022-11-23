from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models.bot import NewBotRequest, UserSecret
from helpers.constants import COLLECTION_USER, DB_RESYS
from auth.auth import Auth

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
