from main import BaseHandler, get_template
from games import Game
from players import Player
import lot


class PlayerPage(BaseHandler):
    def get(self, playerID, lotID):
        playerID = long(playerID)
        p = Player.get_by_id(playerID)
        games = Game.query(Game.players == playerID)
        container = lot.getLot(lotID)
        self.response.write(get_template('viewplayer.html').render({'player': p, 'games': games, 'container':container}))