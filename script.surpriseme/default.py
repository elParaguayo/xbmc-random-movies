# Surprise Me!
# 
# A script for when you just don't know what you want to watch.
#
# Author - el_Paraguayo
# Website - https://github.com/elParaguayo/
# Version - 0.1
# Compatibility - pre-Eden
#
# TO ADD:
#
# Video playlist selection
# Play x random trailers then select movie
# AUDIO: ??
#

import xbmc
import xbmcgui
import xbmcaddon
from urllib import quote_plus, unquote_plus
import re
import sys
import os
import random
import simplejson as json
from telnetlib import Telnet
import socket
import time
import SelectionFilters as sf

_A_ = xbmcaddon.Addon( "script.surpriseme" )
_S_ = _A_.getSetting


# Let's check for any arguments passed by the skin and parse if they exist

try:
  # parse sys.argv for params
  params = dict( arg.split( "=" ) for arg in sys.argv[ 1 ].split( "&" ) )
  argMode = True
except:
  # no params passed
  params = {}
  argMode = False

#####################
# set our preferences
#####################

# Defaults
numTrailers = 3
promptGenres = promptMPAA = promptUnwatched = fanartMode = playlistMode = False


if argMode:
  # Hard-coded arguments in script override user settings
  promptUser = params.get( "prompt" , "" ) == "True"
  filterGenres = params.get( "filtergenre", "" ) == "True"
  filterMPAA = params.get( "filtermpaa", "" ) == "True"
  filterUnwatched = params.get( "filterunwatched", "" ) == "True"
  trailerMode = params.get( "trailermode", "") == "True"
  playlistMode = params.get( "playlistmode", "" ) == "True"
  if trailerMode:
    numTrailers = params.get( "numtrailers", 3 )
  
  # Fanart mode is currently only callable by scripting
  fanartMode = params.get ( "fanartmode" , "") == "True"

elif int(_S_("runmode")) == 1:
  # User has set defined mode in settings
  promptUser = False
  
  if int(_S_("filtergenres")) == 0:
    promptGenres = True
  elif int(_S_("filtergenres")) == 1:
    promptGenres = False
    filterGenres = True
  else:
    promptGenres = False
    filterGenres = False
     
  if int(_S_("filtermpaa")) == 0:
    promptMPAA = True
  elif int(_S_("filtermpaa")) == 1:
    promptMPAA = False
    filterMPAA = True
  else:
    promptMPAA = False
    filterMPAA = False
    
  if int(_S_("filterunwatched")) == 0:
    promptUnwatched = True
  elif int(_S_("filterunwatched")) == 1:
    promptUnwatched = False
    filterUnwatched = True
  else:
    promptUnwatched = False
    filterUnwatched = False
  
  trailerMode = _S_( "trailermode" ) == "true"
  
  if trailerMode:
    numTrailers = int(float(_S_( "numtrailers" ) ) )
    
  playlistMode = _S_("playlistmode") == "true"
  
else: 
  # if not, we're in prompt mode
  promptUser = True
  filterUnwatched = filterMPAA = filterGenres = trailerMode = False
  playlistMode = _S_("playlistmode") == "true"

def getMovieLibrary():
  # get the raw JSON output
  try:
    moviestring = unicode(xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": { "fields": ["fanart", "genre", "playcount", "file", "trailer", "mpaa"]}, "id": 1}'), errors='ignore')
    movies = json.loads(moviestring)
    # older "pre-Eden" versions accepted "fields" parameter but this was changed to "properties" in later versions.
    # the next line will throw an error if we're running newer version
    testError = movies["result"]
  except:
    moviestring = unicode(xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": { "properties": ["genre", "playcount", "file", "trailer", "mpaa"]}, "id": 1}'), errors='ignore')
    movies = json.loads(moviestring)
  # and return it
  return movies
  
def BuildFilter(movies):
  filter = sf.SelectionFilters()
  
  askGenres = askMPAA = askUnwatched = askTrailer = 0
  
  print "MPAA: " + _S_("filtermpaa")
  print "Genre: " + _S_("filtergenres")
  print "Unwatched: " + _S_("filterunwatched")
  
  # Do we need no filter by unwatched movies?
  # This needs to be done first as the other filters depend on it
  if promptUser or promptUnwatched:  
    askUnwatched = xbmcgui.Dialog().yesno("Show unwatched", "Only include unwatched movies?")

  if askUnwatched or filterUnwatched:
    filter.SetFilter("unwatched", True)
    unwatched = True
  else:
    unwatched = False
  
  # Do we want to show trailers?  
  if promptUser:  
    askTrailer = xbmcgui.Dialog().yesno("Show 3 trailers", "Do you want to watch trailers of 3 random movies? (This may restrict the results)")

  if askTrailer:
    global trailerMode
    trailerMode = True
      
  # Do we filter by genre?
  if promptUser or promptGenres:
    askGenres = xbmcgui.Dialog().yesno("Filter genres", "Restrict movies by genre?")

  if askGenres or filterGenres:
    success, genre = selectGenre(unwatched, trailerMode)
    if success:
      filter.SetFilter("genre", True, genre=genre)
  
  # Do we filter by MPAA rating
  if promptUser or promptMPAA:    
    askMPAA = xbmcgui.Dialog().yesno("Filter rating", "Restrict movies by rating?")
    
  if askMPAA or filterMPAA:
    success, rating = selectMPAA(unwatched, trailerMode)
    if success:
      filter.SetFilter("mpaa", True, rating=rating)
    
  return filter


def selectGenre(filterWatched, trailer):
  success = False
  selectedGenre = ""
  myGenres = []
  print "Trailer: " + str(trailer)
  
  for movie in moviesJSON["result"]["movies"]:
    # Let's get the movie genres
    # If we're only looking at unwatched movies then restrict list to those movies
    if (( filterWatched and movie["playcount"] == 0 ) or not filterWatched) and ((trailer and not movie["trailer"] == "") or not trailer):
      print movie["trailer"]
      genres = movie["genre"].split(" / ")
      for genre in genres:
        # check if the genre is a duplicate
        if not genre in myGenres:
          # if not, add it to our list
          myGenres.append(genre)
  # sort the list alphabeticallt        
  mySortedGenres = sorted(myGenres)
  # prompt user to select genre
  selectGenre = xbmcgui.Dialog().select("Select genre:", mySortedGenres)
  # check whether user cancelled selection
  if not selectGenre == -1:
    # get the user's chosen genre
    selectedGenre = mySortedGenres[selectGenre]
    success = True
  else:
    success = False
  # return the genre and whether the choice was successfult
  return success, selectedGenre


def selectMPAA(filterWatched, trailer):
  success = False
  selectedRating = ""
  myRatings = []
  print "Trailer: " + str(trailer)
  
  for movie in moviesJSON["result"]["movies"]:
    # Let's get the movie genres
    # If we're only looking at unwatched movies then restrict list to those movies
    if (( filterWatched and movie["playcount"] == 0 ) or not filterWatched)  and ((trailer and not movie["trailer"] == "") or not trailer):
      rating = movie["mpaa"]

      if not rating in myRatings:
        # if not, add it to our list
        myRatings.append(rating)
  # sort the list alphabeticallt        
  mySortedRatings = sorted(myRatings)
  # prompt user to select genre
  selectRating = xbmcgui.Dialog().select("Select rating:", mySortedRatings)
  # check whether user cancelled selection
  if not selectRating == -1:
    # get the user's chosen genre
    selectedRating = mySortedRatings[selectRating]
    success = True
  else:
    success = False
  # return the genre and whether the choice was successfult
  return success, selectedRating  
  
 
def getMovieFromFanart(fanart):
  fanartFound = False
  fanartMovie = ""
  
  for movie in moviesJSON["result"]["movies"]:
    
    if os.path.basename(movie["fanart"]) == os.path.basename(fanart):
      fanartFound = True
      fanartMovie = movie["file"]
      break
  
  return fanartFound, fanartMovie
  
def getVideoPlaylists():
  videostring = unicode(xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Files.GetDirectory", "params": {"directory": "special://videoplaylists"}, "id": 1}'), errors='ignore')
  myVideoPlaylists = json.loads(videostring)  
  return myVideoPlaylists

def chooseVideoPlaylist(videoPlaylists):
  myPlaylists = {}
  selectPlaylist = []
  for playlist in videoPlaylists["result"]["files"]:
    myPlaylists[playlist["label"]] = playlist["file"]
    selectPlaylist.append(playlist["label"])
  #selectPlaylist.append("Cancel")

  a = xbmcgui.Dialog().select("Select playlist",selectPlaylist)  
  if not a == -1:
    playliststring = unicode(xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Files.GetDirectory", "params": {"directory": "' + myPlaylists[selectPlaylist[a]] + '", "media": "video"}, "id": 1}'), errors='ignore')
    myVideoPlaylists = json.loads(playliststring)
    showfiles = []
    for movie in myVideoPlaylists["result"]["files"]:
      showfiles.append(movie["file"])
    
    return True, showfiles
  else:
    return False, ""

def getTrailers(movieList, numTrailers):
  trailerList = []
  #progress = xbmcgui.DialogProgress()
  #b = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Playlist.Clear", "params": {"playlistid": 1}, "id": 1}')
  #progress.create("Getting random playlist")
  # for movie in filteredMovies:      
    # movieDetail = {}
    # movieDetail["label"] = movie["label"]
    # movieDetail["file"] = movie["file"]
    # movieDetail["trailer"] = movie["trailer"]
    # movieList.append(movieDetail)
    # #progress.update(0,movie["label"])
     
  # We need to check that we have enough trailers to meet our user's requirements  
  if len(movieList) <= numTrailers:
    # if we don't then we need to limit the number of trailers to show
    listLimit = len(movieList)
  else:
    listLimit = numTrailers
  
  # Build list of trailers  
  i = 1
  myRandomMovies = []
  # s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  # s.settimeout(240)  
  # s.connect(("localhost",9090))
  xplaylist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
  xplaylist.clear()
  while len(trailerList) < listLimit:
    movieN = random.choice(movieList)

    
    if not movieN["trailer"] in trailerList:
      #percent = int(len(trailerList)*100/listLimit)
      trailerList.append(movieN["trailer"])
      #progress.update(percent, "", "Adding trailer " + str(i))
      #request = '{"jsonrpc": "2.0", "method": "Playlist.Add", "params": {"playlistid": 1, "item": {"file": "' + movieN["trailer"] + '"}}, "id": 1}'
      listitem = xbmcgui.ListItem('Random Movie ' + str(i))
      listitem.setInfo('video', {'Title': 'Random Movie ' + str(i)})
      xplaylist.add(movieN["trailer"], listitem=listitem)
      print str(movieN)
      #s.send(request)
      #time.sleep(0.5)
      #b = xbmc.executeJSONRPC(request)
      myRandomMovies.append(movieN)
      i += 1
      
  #time.sleep(0.5)    
  #progress.update(100,"Playing")
  #s.close()
  #xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Player.Open", "params": {"item": {"playlistid": 1}}, "id": 1}')    
  #progress.close()
  
  # s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  # s.settimeout(240)  
  # s.connect(("localhost",9090))
  # buffer = s.recv(2)
  # done = False
  # while not done:
    # if "Stop" in buffer:
      # done = True
    # else:
      # more = s.recv(2)
      # if not more:
        # done = True
      # else:
        # buffer = buffer+more
  

  xbmc.Player().play ( xbmc.PlayList( xbmc.PLAYLIST_VIDEO ) )

  while xbmc.Player().isPlaying():
    while xbmc.Player().isPlaying():
      time.sleep(1)
    time.sleep(0.5)
  

  randomList = []
  for movie in myRandomMovies:
    randomList.append(movie["label"])
  
  a = xbmcgui.Dialog().select("Select movie to watch:", randomList)
  if not a == -1:
    success = True
    myMovie = myRandomMovies[a]["file"]
  else:
    success = False
    myMovie = ""
    
  return success, myMovie

def FilterMovies(movies, filter, trailer):
  filteredlist = []
  for movie in movies["result"]["movies"]:
    if ((trailer and not movie["trailer"] == "") or not trailer):
      if filter.MeetsCriteria(movie):
        filteredlist.append(movie)

  return filteredlist

def playFanart():
  myFanart = params.get ( "fanart", "")
  fanartFound, fanartMovie = getMovieFromFanart(myFanart)
  if fanartFound:
    xbmc.executebuiltin('PlayMedia(' + fanartMovie + ',0,noresume)')
  else:
    xbmc.executebuiltin('Notification(Fanart error, Movie not found)')
  
if fanartMode:
  playFanart()
elif playlistMode:
  success, myMovies = chooseVideoPlaylist(getVideoPlaylists())
  print str(success)
  print str(myMovies)
  if success:
    myMovie = random.choice(myMovies)
    xbmc.executebuiltin('Playmedia(' + myMovie + ')')
else:
  # # get the full list of movies from the user's library
  moviesJSON = getMovieLibrary()
  # Create filter
  filter = BuildFilter(moviesJSON)
  # apply filter to our library
  filteredMovies = FilterMovies(moviesJSON, filter, trailerMode)
  if trailerMode:
    success, myMovie = getTrailers(filteredMovies, numTrailers)
    if success:
      xbmc.executebuiltin('Playmedia(' + myMovie + ')')
  else:
    randomMovie = random.choice(filteredMovies)
    xbmc.executebuiltin('Playmedia(' + randomMovie["file"] + ')')


#####################
# Surplus code      #
#                   #
# May need to reuse #
#####################

# class XBMCPlayer( xbmc.Player ):
    # """ Subclass of XBMC Player class.
        # Overrides onplayback events, for custom actions.
    # """
    # def __init__( self, *args ):
        # # self._playbackended = False
        # pass

    # def onPlayBackStarted( self ):
        # # Will be called when xbmc starts playing a file
        # xbmc.log( "Playlist started" )

    # def onPlayBackEnded( self ):
        # # Will be called when xbmc stops playing a file
        # xbmc.log( "End of Playlist" )
        # #self._playbackended = True
        # xbmc.executebuiltin('Notifcation(Ended, Ended)')
        
    # def onPlayBackStopped( self ):
        # # Will be called when user stops xbmc playing a file
        # xbmc.log( "playlist Stopped" )
        # xbmc.executebuiltin('Notifcation(Stopped, Stop)')

# player = XBMCPlayer()
    # def getplaybackended( self ):
        # return self._playbackended
        
    # PlayBackEnded = property(getplaybackended, None, None, None)
    
# def getUnwatched():
  # # default is to select from all movies
  # unwatched = False
  # # ask user whether they want to restrict selection to unwatched movies
  # a = xbmcgui.Dialog().yesno("Watched movies", "Restrict selection to unwatched movies only?")
  # # deal with the output
  # if a == 1: 
    # # set restriction
    # unwatched = True
  # return unwatched
  
# def askGenres():
  # # default is to select from all movies
  # selectGenre = False
  # # ask user whether they want to select a genre
  # a = xbmcgui.Dialog().yesno("Select genre", "Do you want to select a genre to watch?")
  # # deal with the output
  # if a == 1: 
    # # set filter
    # selectGenre = True
  # return selectGenre 
  
# def getRandomMovie(filterWatched, filterGenre, genre):
  # # set up empty list for movies that meet our criteria
  # movieList = []
  # # loop through all movies
  # for movie in moviesJSON["result"]["movies"]:
    # # reset the criteria flag
    # meetsCriteria = False
    # # If we're filtering by genre let's put the genres in a list
    # if filterGenre:
      # moviegenre = []
      # moviegenre = movie["genre"].split(" / ")
    # # check if the film meets the criteria
    # # Test #1: Does the genre match our selection (also check whether the playcount criteria are satisfied)
    # if ( filterGenre and genre in moviegenre ) and (( filterWatched and movie["playcount"] == 0 ) or not filterWatched):
      # meetsCriteria = True
    # # Test #2: Is the playcount 0 for unwatched movies (when not filtering by genre)
    # if ( filterWatched and movie["playcount"] == 0 and not filterGenre ):
      # meetsCriteria = True
    # # Test #3: If we're not filtering genre or unwatched movies, then it's added to the list!!
    # if ( not filterWatched and not filterGenre ):
      # meetsCriteria = True

    # # if it does, let's add the file path to our list
    # if meetsCriteria:
      # movieList.append(movie["file"])
  # # Make a random selection      
  # randomMovie = random.choice(movieList)
  # # return the filepath
  # return randomMovie
  
# if fanartMode:



# else:
    # # ask user if they want to only play unwatched movies  
    # unwatched = getUnwatched()  

    # # is skin configured to use one entry?
    # if promptUser and not filterGenres:
      # # if so, we need to ask whether they want to select genre
      # filterGenres = askGenres()

    # # did user ask to select genre?
    # if filterGenres:
      # # bring up genre dialog
      # success, selectedGenre = selectGenre(unwatched)
      # # if not aborted
      # if success:
        # # get the random movie...
        # randomMovie = getRandomMovie(unwatched, True, selectedGenre)
        # # ...and play it!
        # xbmc.executebuiltin('PlayMedia(' + randomMovie + ',0,noresume)')
    # else:
      # # no genre filter
      # # get the random movie...
      # randomMovie = getRandomMovie(unwatched, False, "")
      # # ...and play it
      # xbmc.executebuiltin('PlayMedia(' + randomMovie + ',0,noresume)')
      
#mylists = getVideoPlaylists()
#chooseVideoPlaylist(mylists)
