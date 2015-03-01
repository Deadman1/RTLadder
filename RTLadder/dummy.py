players = ['master of desaster', 'Jefferspin']


gameName = 'Deadman\'s ladder : ' +  ' vs '.join([p for p in players])

print gameName

gameName = gameName[:40] + "..."

print "--" + gameName