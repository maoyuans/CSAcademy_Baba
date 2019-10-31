from cmu_graphics import *
import copy

app.background = rgb(24, 24, 24)

# main : void -> void
# Why not.
def main():
  initDict()
  app.board = Board(12, 20)
  app.board.drawGrid()
  app.board.add(Obj('baba', 1, 1))
  app.board.add(Text('baba', 2, 4))
  app.board.drawBoard()

  #test()

# test : void -> void
# Why not?
def test():
  app.board.ruleSet.add(Rule('baba', 'you'))
  app.board.updateRule()
  print(len(app.board.catGet('baba')))
  print(len(app.board.catGet('you')))
  app.board.ruleSet.add(Rule('rock', 'push'))
  app.board.updateRule()
  print(len(app.board.catGet('rock')))
  print(len(app.board.catGet('push')))

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

    # Rescaling the app window itself. For now.
    app.width = self.width + 100
    app.height = self.height + 100

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
    return (self.origin[0] + row * self.sqSize,
      self.origin[1] + col * self.sqSize)

  # add : Obj -> void
  # Adds an object into a grid on the board, according to its properties.
  # Does not take in x and y coords as the object itself determines that, and
  # as we are not coding in C++.
  def add(self, obj):
    (row, col) = (obj.row, obj.col)
    self.data[row][col].append(obj)
    self.catAdd(obj.type, obj)

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
          obj.updateType(rule.prop)
          obj.draw()
          self.catRemove(rule.sub, obj)
          self.catAdd(rule.prop, obj)

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
    self.isDeath = False
    self.isSink = False
    self.isOpen = False
    self.isShut = False

  # changeType : str -> void
  # Change the type of an object.
  def changeType(self, typ):
    self.type = typ.lower()
    self.path = 'sprites/' + self.type + '.png'

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
    elif (prop == 'death'):
      self.isDeath = val
    elif (prop == 'sink'):
      self.isSink = val
    elif (prop == 'open'):
      self.isOpen = val
    elif (prop == 'shut'):
      self.isShut = val

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

# initDict : void -> void
# The type dictionary. For convenience.
# Every key is a piece of text, corresponding value dictates what type it is.
def initDict():
  app.typeDict = dict()
  app.typeDict['baba'] = 'obj'
  app.typeDict['text'] = 'obj'
  app.typeDict['rock'] = 'obj'

  app.typeDict['is'] = 'conj'

  app.typeDict['you'] = 'rule'
  app.typeDict['push'] = 'rule'

main()

loop()
