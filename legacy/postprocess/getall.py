import os
import subprocess
prefix = 'letour.fr'

id = 1
with open("domainendings.txt", "r") as ins:
    for line in ins:
        id += 1
        if id%2==0:
            url = prefix+line
            output = 'raw/id_'+str(int(id/2))+'.txt'
            mycommand = 'w3m -dump -cols 1000 ' + url
            result = subprocess.check_output(mycommand, shell=True)
            
            file = open(output,"w")
            file.write(result)
            file.close
