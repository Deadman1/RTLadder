from games import createGame
from main import flatten, group

import ConfigParser
import logging
import random
import os.path


def createGames(request, container):
    """This is called periodically to check for new games that need to be created.  
    You should replace this with your own logic for how games are to be created.
    Right now, this function just randomly pairs up players who aren't in a game."""
    
    #Retrieve all games that are ongoing
    activeGames = [g for g in container.games if g.winner is None]
    activeGameIDs = dict([[g.key.id(), g] for g in activeGames])
    logging.info("Active games: " + unicode(activeGameIDs))
    
    #Throw all of the player IDs that are in these ongoing games into a dictionary
    playerIDsInActiveGames = set(flatten([g.players for g in activeGames]))
    
    #Find all players who aren't any active games and also have not left the CLOT (isParticipating is true)
    playersNotInGames = [container.players[p] for p in container.lot.playersParticipating if p not in playerIDsInActiveGames]
    logging.info("Players not in games: " + ','.join([unicode(p) for p in playersNotInGames]))

    #The template ID defines the settings used when the game is created.  You can create your own template on warlight.net and enter its ID here
    templates = getTemplates()
    
    #Create a game for everyone not in a game.
    #From a list of templates, a random one is picked for each game
    gamesCreated = [createGame(request, container, pair, int(random.choice(templates))) for pair in createPlayerPairs(container.lot.playerRanks, playersNotInGames)]
    logging.info("Created games " + unicode(','.join([unicode(g) for g in gamesCreated])))


def pairs(lst):
    """Simple helper function that groups a list into pairs.  For example, [1,2,3,4,5] would return [1,2],[3,4]"""
    for i in range(1, len(lst), 2):
        yield lst[i-1], lst[i]


def setRanks(container):
    """This looks at what games everyone has won and sets their currentRank field.
    The current algorithm is very simple - just award ranks based on number of games won.
    You should replace this with your own ranking logic."""
    
    #Load all finished games
    finishedGames = [g for g in container.games if g.winner != None]
    
    #Group them by who won
    finishedGamesGroupedByWinner = group(finishedGames, lambda g: g.winner)
    
    #Get rid of the game data, and replace it with the number of games each player won
    container.lot.playerWins = dict(map(lambda (playerID,games): (playerID, len(games)), finishedGamesGroupedByWinner.items())) 
    
    #Map this from Player.query() to ensure we have an entry for every player, even those with no wins
    playersMappedToNumWins = [(p, container.lot.playerWins.get(p.key.id(), 0)) for p in container.players.values()]
    
    #sort by the number of wins each player has.
    playersMappedToNumWins.sort(key=lambda (player,numWins): numWins, reverse=True)
    
    #Store the player IDs back into the LOT object
    container.lot.playerRanks = [p[0].key.id() for p in playersMappedToNumWins]
    
    logging.info('setRanks finished')


def gameFailedToStart(elapsed):
    """This is called for games that are in the lobby.  We should determine if the game failed to
    start or not based on how long it's been in the lobby"""
    
    return elapsed.seconds >= 600

"""
This method creates pairs between players, so that games can be created for each pair.
The algorithm creates pairs of the 2 lowest ranked players from the pool till no further pairs can be created.
If there are odd number of players, the top ranked player will not get paired
"""
def createPlayerPairs(completePlayerListSortedByRank, EligibleForGamesplayerList):
    eligiblePlayersSortedByRank = []
    for player in completePlayerListSortedByRank:
        for p in EligibleForGamesplayerList:
            if player == p.key.id():
                eligiblePlayersSortedByRank.append(p)
    
    # reverse the ranks. The pairing occurs from the bottom.
    eligiblePlayersSortedByRank.reverse()
    
    return pairs(eligiblePlayersSortedByRank)
   

def getTemplates():
    templates = []    
    
    cfgFile = os.path.dirname(__file__) + '/config/Ladder.cfg'
    Config = ConfigParser.ConfigParser()
    Config.read(cfgFile)
    
    if Config.has_section('RTLadder'):
        allTemplates = Config.get("RTLadder", "templates")
        delimiter = Config.get("RTLadder","delimiter")
        templates = allTemplates.split(delimiter)
    else:
        #If no templates found in cfg file, use default template
        templates.append(251301)
        
    return templates