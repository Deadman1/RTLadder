from games import createGame
from main import flatten, group

import ConfigParser
import logging
import random
import os.path
from datetime import datetime


#The template ID defines the settings used when the game is created.  You can create your own template on warlight.net and enter its ID here
templates = []
timeBetweenGamesInMinutes = None


def createGames(request, container):
    """This is called periodically to check for new games that need to be created.  
    You should replace this with your own logic for how games are to be created.
    Right now, this function just randomly pairs up players who aren't in a game."""
    
    # Read configuration settings for ladder
    readConfigForRTLadder()
    
    #Recent games. All players who have played each other recently, will not be paired together.
    recentGames = []
    for g in container.games:
        delta = (datetime.now() - g.dateCreated)
        timeElapsed = delta.total_seconds()        
        if int(timeElapsed) <  timeBetweenGamesInMinutes * 60:
            recentGames.append(g)
    
    #Retrieve all games that are ongoing
    activeGames = [g for g in container.games if g.winner is None]
    activeGameIDs = dict([[g.key.id(), g] for g in activeGames])
    logging.info("Active games: " + unicode(activeGameIDs))
    
    #Throw all of the player IDs that are in these ongoing games into a dictionary
    playerIDsInActiveGames = set(flatten([g.players for g in activeGames]))
    
    #Find all players who aren't any active games and also have not left the CLOT (isParticipating is true)
    playersNotInGames = [container.players[p] for p in container.lot.playersParticipating if p not in playerIDsInActiveGames]
    logging.info("Players not in games: " + ','.join([unicode(p) for p in playersNotInGames]))

    
    
    #Create a game for everyone not in a game.
    #From a list of templates, a random one is picked for each game
    gamesCreated = [createGame(request, container, pair, int(random.choice(templates))) for pair in createPlayerPairs(container.lot.playerRanks, playersNotInGames, recentGames)]
    logging.info("Created games " + unicode(','.join([unicode(g) for g in gamesCreated])))


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
If there are odd number of players, the top ranked player will not get paired.
There is also a restriction that players who have played each other recently cannot play each other.
"""
def createPlayerPairs(completePlayerListSortedByRank, EligibleForGamesplayerList, recentGames):
    eligiblePlayersSortedByRank = []
    for player in completePlayerListSortedByRank:
        for p in EligibleForGamesplayerList:
            if player == p.key.id():
                eligiblePlayersSortedByRank.append(p)
    
    # reverse the ranks. The pairing occurs from the bottom.
    eligiblePlayersSortedByRank.reverse()
    
    # Dict containing each player as key, and list of players they have played as value
    # {p1:[p2,p3]}
    recentMatchups = {}
    
    for game in recentGames:
        p1 = game.players[0]
        p2 = game.players[1]
        if p1 in recentMatchups.keys():
            recentMatchups[p1].append(p2)
        else:
            recentMatchups[p1] = [p2]
            
        if p2 in recentMatchups.keys():
            recentMatchups[p2].append(p1)
        else:
            recentMatchups[p2] = [p1]
    
    """ Groups the list of players into pairs.  For example, [1,2,3,4,5] would return [1,2],[3,4]
    However if the two players in a pair have played each other recently, then a different pair is formed"""
    numOfPlayers = len(eligiblePlayersSortedByRank)
    
    # Keeps track of players who have been allotted games
    playersAllotedGames = []
    
    # Pairs of players to be returned
    playerPairs = []
    
    for i in range(1, numOfPlayers):
        firstPlayer = eligiblePlayersSortedByRank[i-1]
        
        # if player has been allotted a game already, move onto the next one.
        if firstPlayer in playersAllotedGames:
            continue
        
        # Find the next player who firstPlayer has not played recently. Add both of them to playersAllotedGames
        # start from i+1(next player) till numberOfPlayers
        for j in range (i+1, numOfPlayers+1):
            secondPlayer = eligiblePlayersSortedByRank[j-1]
            if recentMatchups != None and firstPlayer in recentMatchups.keys() and secondPlayer in recentMatchups[firstPlayer]:
                continue
            else:
                playersAllotedGames.append(firstPlayer)
                playersAllotedGames.append(secondPlayer)
                playerPairs.append([firstPlayer, secondPlayer])
                break

    return playerPairs

"""Reads configuration for RT ladder"""
def readConfigForRTLadder():
    cfgFile = os.path.dirname(__file__) + '/config/Ladder.cfg'
    Config = ConfigParser.ConfigParser()
    Config.read(cfgFile)
    
    # declare as global variables
    global templates
    global timeBetweenGamesInMinutes
    
    try:
        allTemplates = Config.get("RTLadder", "templates")
        delimiter = Config.get("RTLadder","delimiter")
        templates = allTemplates.split(delimiter)
    except:
        #If no templates found in cfg file, use default template
        templates.append(251301)
    
    try:
        timeBetweenGamesInMinutes = int(Config.get("RTLadder", "timeBetweenGamesInMinutes"))
    except:
        timeBetweenGamesInMinutes = 120