class SelectionFilters(object):
  _myfilters = {}
 
  def __init__(self):
    # New tests should be initialised here
    # Structure should be {"Filter Name": {"enabled": False, "testname": "name_of_function"}}
    # When enabled you should add parameters as follows:
    # {"Filter Name": {"enabled": False, "testname": "name_of_function", "params": {"param1": "value"}}}
    # The parameters can then be checked in the test
    # You need to create a "def name_of_function(self, movie): ..." and pass the JSON movie object
    # the test should return True is the test is passed
       
    # MPAA - filter by ratings
    mpadict = {}
    mpadict["enabled"] = False
    mpadict["testname"] = "TestMPAA"
    self._myfilters["mpaa"] = mpadict
    
    # Genre - filter by movie genre
    genredict = {}
    genredict["enabled"] = False
    genredict["testname"] = "TestGenre"
    self._myfilters["genre"] = genredict
    
    # Unwatched - filter by unwatched movies
    unwatcheddict = {}
    unwatcheddict["enabled"] = False
    unwatcheddict["testname"] = "TestUnwatched"
    self._myfilters["unwatched"] = unwatcheddict
    
    # _mpaa = False
    # _genre = False
    # _year = False
    # _watched = False

# Standard functions    
    
  def HasActiveFilter(self):
    a = 0
    for filter in self._myfilters:
      if self._myfilters[filter]["enabled"]:
        a += 1
    
    if a > 0:
      return True
    else:
      return False
      
  def MeetsCriteria(self, movie):
    meets = True
    
    for filter in self._myfilters:
      if self._myfilters[filter]["enabled"]:
        test = getattr(self, self._myfilters[filter]["testname"])
        if not test(movie):
          meets = False
          break
          
    return meets
        
  def SetFilter(self, filterName, enabled, **kwargs):
    success = False
    
    if filterName in self._myfilters:
      self._myfilters[filterName]["enabled"] = enabled
      if kwargs and enabled:
        self._myfilters[filterName]["params"] = kwargs
    success = True

    return success

  def GetFilter(self, filterName):
    if filterName in self._myfilters:
      return self._myfilters[filterName]    
    else:
      return False
      
  def FilterEnabled(self, filterName):
    if filterName in self._myfilters:
      return self._myfilters[filterName]["enabled"]
    else:
      return False
  
  def __str__(self):
    return str(self._myfilters)

# Specific filter tests - named as per _init_ (above).

  def TestMPAA(self, movie):
    success = False
    if movie["mpaa"] == self._myfilters["mpaa"]["params"]["rating"]:
      success = True
    return success
      
  def TestGenre(self, movie):
    success = False
    if self._myfilters["genre"]["params"]["genre"] in movie["genre"]:
      success = True
    return success

  def TestUnwatched(self, movie):
    success = False
    if movie["playcount"] == 0:
      success = True
    return success
  
