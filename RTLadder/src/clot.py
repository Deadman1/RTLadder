from games import createGame
from main import flatten, group

import logging
import random


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
    
    #Randomize the order
    random.shuffle(playersNotInGames)
    
    #The template ID defines the settings used when the game is created.  You can create your own template on warlight.net and enter its ID here
    templateID = 251301
    
    #Create a game for everyone not in a game.
    gamesCreated = [createGame(request, container, pair, templateID) for pair in pairs(playersNotInGames)]
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