
class Measure:
    pass

class Directive:
    def __init__(self,directiveText):
        text = directiveText[0][1:]        
        if text.startswith("Channel_"):
            pass
            raise Exception("Unknown directive '"+text+"' at line "+str(directiveText[2])+" in file '"+directiveText[1]+"'")
        elif text.startswith("Time_"):
            pass
            raise Exception("Unknown directive '"+text+"' at line "+str(directiveText[2])+" in file '"+directiveText[1]+"'")
        elif text.startswith("Speed_"):
            pass
            raise Exception("Unknown directive '"+text+"' at line "+str(directiveText[2])+" in file '"+directiveText[1]+"'")
        elif text.startswith("Voice_"):
            pass
            raise Exception("Unknown directive '"+text+"' at line "+str(directiveText[2])+" in file '"+directiveText[1]+"'")
        elif text.startswith("Octave_"):
            pass
            raise Exception("Unknown directive '"+text+"' at line "+str(directiveText[2])+" in file '"+directiveText[1]+"'")
        elif text.startswith("Sharp_"):
            pass
            raise Exception("Unknown directive '"+text+"' at line "+str(directiveText[2])+" in file '"+directiveText[1]+"'")
        elif text.startswith("Flat_"):
            pass
            raise Exception("Unknown directive '"+text+"' at line "+str(directiveText[2])+" in file '"+directiveText[1]+"'")
        elif text.startswith("Key_"):
            pass
            raise Exception("Unknown directive '"+text+"' at line "+str(directiveText[2])+" in file '"+directiveText[1]+"'")
        elif text.startswith("Volume_"):
            pass
            raise Exception("Unknown directive '"+text+"' at line "+str(directiveText[2])+" in file '"+directiveText[1]+"'")
        elif(text==":p" or text==":f" or text==":mp" or
               text==":mf" or text==":pp" or text==":ff" or
               text==":>" or text=="::" or text==":<"):
            self.dynamic = text
            raise Exception("Unknown directive '"+text+"' at line "+str(directiveText[2])+" in file '"+directiveText[1]+"'")     
        else:
            raise Exception("Unknown directive '"+text+"' at line "+str(directiveText[2])+" in file '"+directiveText[1]+"'")
        
class Note:      
    # style
    # octaveMod            
    # baseLength        
    # numDots
    # isTriplet
    # isDoublet
    # noteName
    # accidental
    # isHeld
    
    def __init__(self,originalText):
        
        text = originalText[0]
        
        # Ignore underscores
        text = text.translate(None,'_')
        
        # Must have SOMETHING besides underscores
        if(len(text)==0):
            
            raise Exception("Bad note syntax. Must have note name. '"+text+"' at line "+str(originalText[2])+" in file '"+originalText[1]+"'")
        
        # Peel off style        
        if(text[0]=='.' or text[0]=='t' or text[0]=='>'):
            self.style = text[0]
            text = text[1:]
            if(len(text)==0):
                raise Exception("Bad note syntax. Must have note name. '"+text+"' at line "+str(originalText[2])+" in file '"+originalText[1]+"'")
            
        # Peel off octave modifiers       
        self.octaveMod = 0
        while text[0]=="+" or text[0]=="-":
            if text[0]=="+":
                self.octaveMod = self.octaveMod + 1
            if text[0]=="-":
                self.octaveMod = self.octaveMod - 1
            text = text[1:]
            if(len(text)==0):
                raise Exception("Bad note syntax. Must have note name. '"+text+"' at line "+str(originalText[2])+" in file '"+originalText[1]+"'")
            
        # Get the base length, dots, and trip/dub if given
        if text[0]>='0' and text[0]<='9':
            self.baseLength = int(text[0])
            text = text[1:]
            while(text[0]>='0' and text[0]<='9'):
                self.baseLength = self.baseLength*10+int(text[0])
                text = text[1:] 
                if(len(text)==0):
                    raise Exception("Bad note syntax. Must have note name. '"+text+"' at line "+str(originalText[2])+" in file '"+originalText[1]+"'")           
            if text[0]=='t':
                self.isTriplet = True
                text = text[1:]
                if(len(text)==0):
                    raise Exception("Bad note syntax. Must have note name. '"+text+"' at line "+str(originalText[2])+" in file '"+originalText[1]+"'") 
            if text[0]=='d':
                self.isDoublet = True
                text = text[1:]
                if(len(text)==0):
                    raise Exception("Bad note syntax. Must have note name. '"+text+"' at line "+str(originalText[2])+" in file '"+originalText[1]+"'") 
            self.numDots = 0
            while(text[0]=='.'):
                self.numDots = self.numDots + 1
                text = text[1:]    
                if(len(text)==0):
                    raise Exception("Bad note syntax. Must have note name. '"+text+"' at line "+str(originalText[2])+" in file '"+originalText[1]+"'")
                
        # Now the note name. This is NOT optional, and it is a good place to sanity check.
        if(len(text)==0):
            raise Exception("Bad note syntax. Must have note name. '"+text+"' at line "+str(originalText[2])+" in file '"+originalText[1]+"'") 
        if(text[0]=='R' or (text[0]>='A' and text[0]<='G')):
            self.noteName = text[0]
            text = text[1:]
        else:
            raise Exception("Invalid note name '"+text[0]+"' in '"+text+"' at line "+str(originalText[2])+" in file '"+originalText[1]+"'")
                
        # Now any accidentals
        if len(text)==0:
            return
        if(text[0]=='#' or text[0]=='b' or text['n']):
            self.accidental = text[0]
            text = text[1:]
            
        # Finally any holds
        if len(text)==0:
            return
        if(text[0]=='~'):
            self.isHeld = True
            text = text[1:]
        
        # Make sure nothing is left    
        if(len(text)!=0):
            raise Exception("Bad note syntax '"+text+"' in '"+text+"' at line "+str(originalText[2])+" in file '"+originalText[1]+"'")            
        
def getTokens(textLines,filename):
    ret = [] # list of tuples (token,file,line)
    lineno = 0
    for line in textLines:
        lineno = lineno + 1
        if ";" in line:
            line = line[0:line.index(";")]
        words = line.split()
        if(len(words)==2 and words[0]=="include"):
            with open(words[1]) as f:
                text = f.readlines()
            incToks = getTokens(text,words[1])
            ret.extend(incToks)
            continue
        for word in words:
            ret.append((word,filename,lineno))
    return ret

if __name__ == "__main__":
    
    filename = "InstantConcert.txt"
    
    with open(filename) as f:
        text = f.readlines()
        
    tokens = getTokens(text,filename)
    
    music = []
    
    # Some directive defaults    
    music.append(Directive((":Channel_0",     'Default Values',-1)))
    music.append(Directive((":Time_4/4",      'Default Values',-1)))
    music.append(Directive((":Speed_4=60",    'Default Values',-1)))
    music.append(Directive((":Voice_0",       'Default Values',-1)))
    music.append(Directive((":Octave_4",      'Default Values',-1)))
    music.append(Directive((":Volume_75",     'Default Values',-1)))
    music.append(Directive((":f",             'Default Values',-1)))
    music.append(Directive((":NoteLength_4",  'Default Values',-1)))
    
    # Now parse the music file
    for tok in tokens:
        if tok[0][0]==':':
            music.append(Directive(tok))
        elif tok[0]=='|':
            music.append(Measure())
        else:
            music.append(Note(tok))
            
    #print music
    