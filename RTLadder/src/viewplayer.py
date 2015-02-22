from main import BaseHandler, get_template
from games import Game
from players import Player


class PlayerPage(BaseHandler):
    def get(self, playerID):
        playerID = long(playerID)
        p = Player.get_by_id(playerID)
        games = Game.query(Game.players == playerID)
        self.response.write(get_template('viewplayer.html').render({'player': p, 'games': games}))