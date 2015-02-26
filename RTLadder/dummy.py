class game:
    a=1
    b=2
    c=3
    
    
print "hi"    

gameList = []
for i in range(1,5):
    gameList.append(game())
    
print gameList    
for i in range(1,5):
    print i, gameList[i-1].a
    
    
for i in range(1,5):
    gameList[i-1].a = 4

print "--------------------------"
for i in range(1,5):
    print i, gameList[i-1].a

