from cmu_graphics import *
import copy

app.background = rgb(24, 24, 24)
app.endGroup = Group()
app.end = False
app.inMenu = True
app.width = 1000
app.height = 700
#app.maxUndo = 20
#app.undoLst = []

# main : void -> void
# Why not.
def main():
  initDict()
  loadBoard('levels/menu.txt')

# debug : void -> void
# Why not?
def debug():
  for key in app.board.catalog:
    print(key + ' ' + str(len(app.board.catalog[key])))
  print(len(app.board.ruleSet))
  for rule in app.board.ruleSet:
    print(rule.sub + ' ' + rule.prop)

# onKeyPress
# I mean, you know what this does.
def onKeyPress(key):
  #if (key == 'z'):
  #  undo()
  #  return

  # If on the end screen, press space to return to menu.
  if (app.end):
    if (key == 'space'):
      app.end = False
      app.endGroup.clear()
      loadBoard('levels/menu.txt')
      app.inMenu = True
    return

  # If in menu, enable level select function.
  if (app.inMenu):
    if (key == 'space'):
      youSet = app.board.catGet('you')
      for obj in youSet:
        for obj2 in app.board.data[obj.row][obj.col]:
          if (isinstance(obj2, Level)):
            app.inMenu = False
            loadBoard(obj2.lvlPath)
            return

  #app.undoLst.append(app.board.copy())
  #if (len(app.undoLst) > app.maxUndo):
  #  app.undoLst = app.undoLst[1:]

  if (key == 'left'):
    app.board.doMove(0, -1)
  elif (key == 'right'):
    app.board.doMove(0, 1)
  elif (key == 'up'):
    app.board.doMove(-1, 0)
  elif (key == 'down'):
    app.board.doMove(1, 0)

# findFit : int * int -> int
# Returns the best grid size for the current board setting
# Not used : I can't rescale images
def findFit(row, col):
  dx = 600 / row
  dy = 1000 / col
  return min(dx, dy)

# The board class. Keeps the board of this game in check.
class Board(object):
  # Init : int * int -> void
  def __init__(self, row, col):
    self.row = row
    self.col = col

    # Let it be 25 as I don't know how to rescale images without messing
    # up with transparency.
    #self.sqSize = findFit(row, col)
    self.sqSize = 25 # Size of a single square grid
    self.width = self.col * self.sqSize # Width of the board
    self.height = self.row * self.sqSize # Height of the board
    self.origin = (50, 50) # Subject to dynamic rescale (if I can rescale)

    # Rescaling the app window itself. For now. Not working either.
    # app.width = self.width + 100
    # app.height = self.height + 100

    # Initialize the data on the board.
    self.data = []
    for i in range(self.row):
      colData = []
      for i in range(self.col):
        colData.append([])
      self.data.append(colData)

    # Initialize the rule set.
    self.ruleSet = set()
    self.ruleSet.add(Rule('text', 'push'))

    # Initialize the set for deleted rules
    self.deletedRules = set()

    # Initialize the catalog of things
    self.catalog = dict()

  # copy : void -> Board
  # Make a copy of itself.
  # Unused. Too much trouble.
  #def copy(self):
  #  newBoard = Board(self.row, self.col)
  #  print('1')
  #  newBoard.data = copy.deepcopy(self.data)
  #  print('2')
  #  newBoard.ruleSet = copy.deepcopy(self.ruleSet)
  #  print('3')
  #  newBoard.deletedRules = copy.deepcopy(self.deletedRules)
  #  print('4')
  #  newBoard.catalog = copy.deepcopy(self.catalog)
  #  print('5')
  #  return newBoard


  # invalid : int * int -> bool
  # Checks if a given index is out of bound.
  def invalid(self, row, col):
    return row < 0 or col < 0 or row >= self.row or col >= self.col

  # getMid : int * int -> (float * float)
  # Returns the middle point of a grid given its index on the board.
  def getMid(self, row, col):
    if (self.invalid(row, col)): raise IndexError("GridIndexOutOfBound")
    return (self.origin[0] + self.sqSize / 2 + row * self.sqSize,
      self.origin[1] + self.sqSize / 2 + col * self.sqSize)

  # getCorner : int * int -> (float * float)
  # Returns the top-left corner point of a grid given its index on the board.
  def getCorner(self, row, col):
    if (self.invalid(row, col)): raise IndexError("GridIndexOutOfBound")
    return (self.origin[0] + col * self.sqSize,
      self.origin[1] + row * self.sqSize)

  # add : Obj -> void
  # Adds an object into a grid on the board, according to its properties.
  # Does not take in x and y coords as the object itself determines that, and
  # as we are not coding in C++.
  def add(self, obj):
    (row, col) = (obj.row, obj.col)
    self.data[row][col].append(obj)
    self.catAdd(obj.type, obj)
    if (isinstance(obj, Text) and obj.textValue == 'is'):
      self.catAdd('is', obj)

  # remove : Obj -> void
  # Removes an object complete from the game.
  def remove(self, obj):
    catSet = obj.category()
    for prop in catSet:
      self.catRemove(prop, obj)
    self.data[obj.row][obj.col].remove(obj)
    obj.remove()

  # catGet : str -> Obj set
  # Queries the catalog and return the set of objects with specified type.
  def catGet(self, typ):
    if (not typ in self.catalog):
      self.catalog[typ] = set()
    return self.catalog[typ]

  # catAdd : str * Obj -> void
  # Adds the object into the catalog under specified type.
  def catAdd(self, typ, obj):
    if (not typ in self.catalog):
      self.catalog[typ] = set()
    self.catalog[typ].add(obj)

  # catRemove : str * Obj -> void
  # Removes the object from the catalog under specified type.
  def catRemove(self, typ, obj):
    if (not typ in self.catalog):
      self.catalog[typ] = set()
    if (obj in self.catalog[typ]):
      self.catalog[typ].remove(obj)

  # moveQuery : Obj * int * int -> bool
  # Attempt to move an item in the direction. If there is a PUSH object 
  # recursively attempt to move it. Return true if success.
  def moveQuery(self, obj, drow, dcol):
    trow = obj.row + drow
    tcol = obj.col + dcol

    if (self.invalid(trow, tcol)):
      return False

    for obj2 in self.data[trow][tcol]:
      if (obj2.isStop):
        return False
      if (obj2.isPush):
        if (not self.moveQuery(obj2, drow, dcol)): 
          return False

    self.data[obj.row][obj.col].remove(obj)
    obj.row = trow
    obj.col = tcol
    self.data[obj.row][obj.col].append(obj)
    
    (x, y) = self.getCorner(obj.row, obj.col)
    obj.draw(x, y)
    return True

  # doMove : int * int -> void
  # Attempt to move every object with YOU in the direction.
  def doMove(self, drow, dcol):
    for obj in (app.board.catalog['you']):
      self.moveQuery(obj, drow, dcol)

    self.detectRule()
    self.updateRule()
    self.checkDefeat()
    self.checkSink()
    if (self.checkWin()):
      endScreen(True)
      return
    if (self.checkFail()):
      endScreen(False)
      return

  # searchRule : int * int * int * int -> Text set
  # Searches in one direction until an invalid grid appears.
  def searchRule(self, row, col, drow, dcol):
    txSet = set()
    valid = True
    lfAnd = False

    while (valid):
      valid = False
      row += drow
      col += dcol
      if (self.invalid(row, col)): break
      objLst = self.data[row][col]
      for obj in objLst:
        if (isinstance(obj, Text)):
          if (lfAnd):
            if (obj.textValue == 'and'):
              valid = True
              break
          else:
            if (obj.textType != 'conj'):
              valid = True
              txSet.add(obj)
              break
      lfAnd = not lfAnd

    return txSet

  # detectRule : void -> void
  # Primes an detection of all rules present on the board.
  def detectRule(self):
    newRuleSet = set()

    isSet = self.catGet('is')
    for obj in isSet:
      crow = obj.row
      ccol = obj.col
      
      subSet = self.searchRule(crow, ccol, 0, -1)
      propSet = self.searchRule(crow, ccol, 0, 1)
      for sub in subSet:
        if (sub.textType != 'obj'):
          continue
        for prop in propSet:
          newRuleSet.add(Rule(sub.textValue, prop.textValue))

      subSet = self.searchRule(crow, ccol, -1, 0)
      propSet = self.searchRule(crow, ccol, 1, 0)
      for sub in subSet:
        if (sub.textType != 'obj'):
          continue
        for prop in propSet:
          newRuleSet.add(Rule(sub.textValue, prop.textValue))

    newRuleSet.add(Rule('text', 'push'))
    self.deletedRules = self.ruleSet.difference(newRuleSet)
    self.ruleSet = newRuleSet

  # updateRule : void -> void
  # Primes an update of all properties on all objects.
  def updateRule(self):
    # Apply all OBJ-OBJ rules.
    for rule in self.ruleSet:
      if (rule.type == 'obj'):
        if (rule.sub == rule.prop):
          continue

        catSet = self.catGet(rule.sub)
        for obj in catSet:
          obj.changeType(rule.prop)
          (x, y) = self.getCorner(obj.row, obj.col)
          obj.draw(x, y)
          self.catAdd(rule.prop, obj)
        catSet.clear()

    for rule in self.deletedRules:
      if (rule.type == 'rule'):
        catSet = self.catGet(rule.sub)
        for obj in catSet:
          obj.setProp(rule.prop, False)
          self.catRemove(rule.prop, obj)

    self.deletedRules.clear()

    for rule in self.ruleSet:
      if (rule.type == 'rule'):
        catSet = self.catGet(rule.sub)
        for obj in catSet:
          obj.setProp(rule.prop, True)
          self.catAdd(rule.prop, obj)

  # checkDefeat : void -> void
  # Initiate a check of whether any YOU object is on DEFEAT, and eliminate.
  def checkDefeat(self):
    youSet = self.catGet('you')
    removeSet = set()

    for obj in youSet:
      for obj2 in self.data[obj.row][obj.col]:
        if (obj2.isDefeat):
          removeSet.add(obj)
          break

    for obj in removeSet:
      self.remove(obj)

  # checkSink : void -> void
  # Initiate a check of whether any SINK object is on any other object.
  # If so, destroy them all.
  def checkSink(self):
    sinkSet = self.catGet('sink')
    removeSet = set()

    for obj in sinkSet:
      sunk = False
      for obj2 in self.data[obj.row][obj.col]:
        if (obj2 != obj):
          removeSet.add(obj2)
          sunk = True

      if (sunk):
        removeSet.add(obj)

    for obj in removeSet:
      self.remove(obj)

  # checkWin : void -> bool
  # Initiate a check of whether you win or not.
  def checkWin(self):
    youSet = self.catGet('you')
    winSet = self.catGet('win')
    youCoord = set()
    winCoord = set()

    for obj in youSet:
      youCoord.add((obj.row, obj.col))

    for obj in winSet:
      winCoord.add((obj.row, obj.col))

    chkSet = youCoord.intersection(winCoord)
    if (len(chkSet) > 0):
      return True
    return False

  # checkFail : void -> bool
  # Initiate a check of whether there are any YOU object on the board.
  # If there is no YOU, well, you kind of lose.
  def checkFail(self):
    youSet = self.catGet('you')

    if (len(youSet) == 0):
      return True
    return False

  # drawGrid : void -> void
  # Draws a grid, duh.
  def drawGrid(self):
    for i in range(self.row + 1):
      Line(self.origin[0], self.origin[1] + i*self.sqSize, 
        self.origin[0] + self.width, self.origin[1] + i*self.sqSize,
        fill='cyan', opacity=20)
    for j in range(self.col + 1):
      Line(self.origin[0] + j*self.sqSize, self.origin[1], 
        self.origin[0] + j*self.sqSize, self.origin[1] + self.height,
        fill='cyan', opacity=20)

  # drawBoard : void -> void
  # Draws everything on the board, duh.
  def drawBoard(self):
    for i in range(self.row):
      for j in range(self.col):
        for obj in self.data[i][j]:
          (x, y) = self.getCorner(i, j)
          obj.draw(x, y)


# The object class. 
# Anything other than the board and abstract rules is an object.
class Obj(object):
  # Init : str * int * int -> void
  def __init__(self, typ, row, col):
    self.type = typ.lower();
    self.path = 'sprites/' + self.type + '.png'
    self.image = None
    self.row = row
    self.col = col

    self.isYou = False
    self.isStop = False
    self.isPush = False
    self.isWin = False
    self.isDefeat = False
    self.isSink = False

  # category : void -> str set
  # Returns a set of all catalog categories this object belongs to.
  def category(self):
    res = set()
    res.add(self.type)
    if (self.isYou):
      res.add('you')
    if (self.isStop):
      res.add('stop')
    if (self.isPush):
      res.add('push')
    if (self.isWin):
      res.add('win')
    if (self.isDefeat):
      res.add('defeat')
    if (self.isSink):
      res.add('sink')
    return res

  # remove : void -> void
  # Remove this instance.
  def remove(self):
    if (self.image):
      self.image.visible = False

  # changeType : str -> void
  # Change the type of an object.
  def changeType(self, typ):
    self.type = typ.lower()
    self.path = 'sprites/' + self.type + '.png'

  # draw : float * float -> void
  # Draws or redraws this object on the given coords.
  def draw(self, x, y):
    if (self.image):
      self.image.visible = False
    self.image = Image(self.path, x, y)

  # setProp : str * bool -> void
  # Sets a property of an object according to the input.
  def setProp(self, prop, val):
    if (prop == 'you'):
      self.isYou = val
    elif (prop == 'stop'):
      self.isStop = val
    elif (prop == 'push'):
      self.isPush = val
    elif (prop == 'win'):
      self.isWin = val
    elif (prop == 'defeat'):
      self.isDefeat = val
    elif (prop == 'sink'):
      self.isSink = val

# The text class. A subclass of Obj.
# Texts that constitutes rules.
class Text(Obj):
  # Init : str * int * int -> void
  def __init__(self, typ, row, col):
    super(Text, self).__init__(typ, row, col)
    self.type = 'text'
    self.textValue = typ
    self.path = 'sprites/text_' + self.textValue + '.png'
    self.textType = app.typeDict[self.textValue]
    self.isActive = False
    self.isIs = (self.textValue == 'is')

  # category : void -> str set
  # Returns a set of all catalog categories this object belongs to.
  def category(self):
    res = super(Text, self).category()
    if (self.isIs):
      res.add('is')
    return res

# The level class. A subclass of Obj.
# Levels disguised as objects. Well.
class Level(Obj):
  # Init : str * int * int * str -> void
  def __init__(self, typ, row, col, path):
    super(Level, self).__init__(typ, row, col)
    self.lvlPath = 'levels/' + path +'.txt'
    self.isLevel = True

# The rule class.
# Each instance is a rule with a subject and a property.
# Property can be rules or objects.
class Rule(object):
  # Init : str * str * str -> void
  def __init__(self, sub, prop):
    self.sub = sub
    self.prop = prop
    self.type = app.typeDict[self.prop] # OBJ-OBJ rule or OBJ-RUL rule.
    self.id = self.sub + ' is ' + self.prop # For easy search and removal

# loadBoard : str -> void
# Parse the input file to load a board.
# The first line should be a pair of integers, separated by spaces, that
# records the dimension of the board
# The following lines should each specify an object type and the location of
# all instances of the object type.
# Text objects have 'text_' before their type.
def loadBoard(path):
  app.group.clear()
  #app.undoLst = []
  file = open(path)
  lines = file.readlines()
  dim = lines[0].split(' ')
  row = int(dim[0])
  col = int(dim[1])
  board = Board(row, col)

  for line in lines[1:]:
    line = line.rstrip()
    lst = line.split(' ')
    typ = lst[0]
    i = 1

    while (i < len(lst)):
      row = int(lst[i])
      col = int(lst[i+1])
      i += 2

      if ('-' in typ): # If it is a level
        path = lst[i]
        i += 1
        board.add(Level(typ[4:], row, col, path))
      elif ('_' in typ): # If it is a text
        board.add(Text(typ[5:], row, col))
      else: # Just a normal object
        board.add(Obj(typ, row, col))

  app.board = board
  app.board.drawGrid()
  app.board.drawBoard()
  app.board.detectRule()
  app.board.updateRule()

  debug()

# undo : void -> void
# Undoes the last step.
# Unused.
#def undo():
#  print('OK')
#  if (len(app.undoLst) == 0):
#    return
#
#  app.board = app.undoLst[-1]
#  app.undoLst = app.undoLst[:-1]
#
#  app.board.drawGrid()
#  app.board.drawBoard()
#  app.board.detectRule()
#  app.board.updateRule()

# endScreen : bool -> void
# Creates an end screen to tell if you win or lose.
def endScreen(win):
  app.endGroup = Group()
  app.endGroup.add(Rect(0, 0, app.width, app.height, fill=rgb(24, 24, 24),
    opacity=80))

  if (win):
    text = 'CONGRATULATIONS!'
  else:
    text = 'Uh... what now?'

  app.endGroup.add(Label(text, app.width / 2, app.height / 2,
    size=36, fill='cornSilk', font='monospace'))
  app.endGroup.toFront()

  app.end = True

# initDict : void -> void
# The type dictionary. For convenience.
# Every key is a piece of text, corresponding value dictates what type it is.
def initDict():
  app.typeDict = dict()
  app.typeDict['baba'] = 'obj'
  app.typeDict['text'] = 'obj'
  app.typeDict['rock'] = 'obj'
  app.typeDict['flag'] = 'obj'
  app.typeDict['wall'] = 'obj'
  app.typeDict['water'] = 'obj'
  app.typeDict['skull'] = 'obj'
  app.typeDict['pillar'] = 'obj'
  app.typeDict['crab'] = 'obj'

  app.typeDict['is'] = 'conj'
  app.typeDict['and'] = 'conj'

  app.typeDict['you'] = 'rule'
  app.typeDict['win'] = 'rule'
  app.typeDict['push'] = 'rule'
  app.typeDict['stop'] = 'rule'
  app.typeDict['sink'] = 'rule'
  app.typeDict['defeat'] = 'rule'

main()

loop()
