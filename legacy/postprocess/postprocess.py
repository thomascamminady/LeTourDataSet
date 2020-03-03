import os
import subprocess
prefix = 'raw/'

for id in range(1,105):   
    filetoread = prefix + 'id_'+str(id)+'.txt'
    with open(filetoread, "r") as ins:
        linecounter = 0
        for line in ins:
            linecounter += 1

            if linecounter == 1:
                year = int(line[-5:])
                print(year,end=''),
                print(',',end=''),
            if linecounter == 3:
                nstages = int(line[-3:])
                print(nstages,end=''),
                print(',',end=''),
            if linecounter == 4:
                nkm = line[-6:]
                nkm = nkm.replace(" ","")
                nkm = int(nkm)
                print(nkm,end=''),
                print(',',end=''),

            if linecounter == 5:
                nkm = line[-7:]
                nkm = float(nkm)
                print(nkm)


            if linecounter >  15: # drivers
                continue
                if not(len(line)==1 or  len(line)==14): # skip last line
                    wasname = False
                    wasriderno = False
                    wasteam = False
                    wastime = False
                    wasgap = False
                    wasfirst = False
                    lastisachar = False
                    lastchar = ''
                    last2char = ''
                    isnumberlast3 = False
                    isnumberlast2 = False
                    isnumberlast1 = False
                    isnumber = False
                    print(str(year)+", ",end=''),
                    flag = False        
                    col = 0
                    skipnext = 0
                    haveskipped = False
                    for char in line:
                        if skipnext>0:
                            skipnext -= 1
                            continue
                        if haveskipped and char.isalpha():
                            haveskipped = False
                            print(char,end= "")
                            continue
                
                        col += 1
                        if char=="\'" and col< 50:
                            continue
                        if char=="," and col< 50:
                            continue
                        if char.isspace():
                            print(" ",end=''),
                            continue
                        if char=="*":
                            lastisanumber = False
                            lastisachar = True
                            print(',',end='')
                            skipnext = 5
                            haveskipped = True
                            continue

                        isachar = char.isalpha() or char=="*" or char==")" or char=="."
                        isanumber = char.isdigit()

                        isnumberlast3 = isnumberlast2
                        isnumberlast2 = isnumberlast1
                        isnumberlast1 = isanumber

                        
                        if lastchar=='\'' and last2char =='\'':
                                break
                        if isachar and lastisanumber:
                            if not(char=="h"):
                                print(",",end=''),
                            if char=="\'":
                                if lastchar=="\'":
                                    print('s',end=''),
                                else:
                                    print('m',end=''),
                        if lastisachar and isanumber:
                            if not(lastchar=="h"):
                                if not(lastchar=="F" and char=="1" and last2char=="D"):
                                    print(",",end=''),
                        lastisachar = isachar
                        lastisanumber = isanumber
                        last2char = lastchar
                        lastchar = char;
                        if not(char=="*"):
                            print(char,end=''),
                        if lastchar=='\'' and last2char =='\'':
                            if id==16:
                                if not(flag):
                                    flag = True
                                else:
                                    print(",",end=''),
                            print(",",end=''),
                        #if char=="+":
                        #    print(",",end=''),
                   # if linecounter==16:
                    #    print(" ,+ 00h 00\' 00\'\'",end=''), 
                    print("")






