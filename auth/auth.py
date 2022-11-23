from database.db import Database
from helpers.constants import DB_RESYS, COLLECTION_USER
from uuid import uuid4
import json

class Auth:

    def __init__(self, db_name: str = DB_RESYS, secret: str = None):
        self.db = Database(db_name)
        self.secret = secret
        self.user = self._get_user()

    def login(self, secret):
        ''' Check if user exists '''
        pass


    def register(self, username, password):
        ''' Register a new user '''
        pass


    def _get_user(self):
        ''' Get user by secret '''
        return self.db.find_one(COLLECTION_USER, { 'secret': self.secret })


    def generate_uuid(self):
        ''' Generate a new uuid '''
        return str(uuid4())


    def get_bot(self, uuid: str):
        ''' Get bot by uuid '''
        user = self._get_user()
        bots = [b for b in user['bots'] if b['uuid'] == uuid] if user else None
        return bots[0] if bots else None
        

    def _user_exist(self):
        ''' Check if user exist '''
        return True if self._get_user() else False

    def _user_have_bots(self)-> bool:
        ''' Check if user has a bot created '''
        return True if (len(self.user['bots']) > 0) else False


    def update_bot_pid(self, uuid: str, pid: int):
        ''' Update bot pid '''
        return self.db.update_one(COLLECTION_USER, { 'secret': self.secret, 'bots.uuid': uuid }, { '$set': { 'bots.$.pid': pid } }) if self._user_exist() else None


    def _create_bot(self, bot):
        ''' Create a new bot '''
        _bot = bot.dict()
        _bot['uuid'] = self.generate_uuid()
        return self.db.update_one(COLLECTION_USER, { 'secret': self.secret }, { '$push': { 'bots': _bot } }) if self._user_exist() else None


    def _get_bots(self):
        ''' Get all bots from user '''
        return self.user['bots'] if self._user_exist() else None