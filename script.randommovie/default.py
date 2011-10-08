# Random movie selecter
# Massive thanks to the developers of the script.randommitems addon, without whom this would not have been possible
#
# Author - el_Paraguayo
# Website - https://github.com/elParaguayo/
# Version - 0.1
# Compatibility - pre-Eden
#

import xbmc
import xbmcgui
from urllib import quote_plus, unquote_plus
import re
import sys
import os
import random
import simplejson as json

# let's parse arguments before we start
try:
  # parse sys.argv for params
  params = dict( arg.split( "=" ) for arg in sys.argv[ 1 ].split( "&" ) )
except:
  # no params passed
  params = {}
# set our preferences
filterGenres = params.get( "filtergenre", "" ) == "True"
promptUser = params.get( "prompt" , "" ) == "True"


def getMovieLibrary():
  # get the raw JSON output
  try:
    moviestring = unicode(xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": { "fields": ["genre", "playcount", "file"]}, "id": 1}'), errors='ignore')
    movies = json.loads(moviestring)
    # older "pre-Eden" versions accepted "fields" parameter but this was changed to "properties" in later versions.
    # the next line will throw an error if we're running newer version
    testError = movies["result"]
  except:
    moviestring = unicode(xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": { "properties": ["genre", "playcount", "file"]}, "id": 1}'), errors='ignore')
    movies = json.loads(moviestring)
  # and return it
  return movies

def getRandomMovie(filterWatched, filterGenre, genre):
  # set up empty list for movies that meet our criteria
  movieList = []
  # loop through all movies
  for movie in moviesJSON["result"]["movies"]:
    # reset the criteria flag
    meetsCriteria = False
    # If we're filtering by genre let's put the genres in a list
    if filterGenre:
      moviegenre = []
      moviegenre = movie["genre"].split(" / ")
    # check if the film meets the criteria
    # Test #1: Does the genre match our selection (also check whether the playcount criteria are satisfied)
    if ( filterGenre and genre in moviegenre ) and (( filterWatched and movie["playcount"] == 0 ) or not filterWatched):
      meetsCriteria = True
    # Test #2: Is the playcount 0 for unwatched movies (when not filtering by genre)
    if ( filterWatched and movie["playcount"] == 0 and not filterGenre ):
      meetsCriteria = True
    # Test #3: If we're not filtering genre or unwatched movies, then it's added to the list!!
    if ( not filterWatched and not filterGenre ):
      meetsCriteria = True

    # if it does, let's add the file path to our list
    if meetsCriteria:
      movieList.append(movie["file"])
  # Make a random selection      
  randomMovie = random.choice(movieList)
  # return the filepath
  return randomMovie
  
def selectGenre(filterWatched):
  success = False
  selectedGenre = ""
  myGenres = []
  
  for movie in moviesJSON["result"]["movies"]:
    # Let's get the movie genres
    # If we're only looking at unwatched movies then restrict list to those movies
    if ( filterWatched and movie["playcount"] == 0 ) or not filterWatched:
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
  
  
def getUnwatched():
  # default is to select from all movies
  unwatched = False
  # ask user whether they want to restrict selection to unwatched movies
  a = xbmcgui.Dialog().yesno("Watched movies", "Restrict selection to unwatched movies only?")
  # deal with the output
  if a == 1: 
    # set restriction
    unwatched = True
  return unwatched
  
def askGenres():
  # default is to select from all movies
  selectGenre = False
  # ask user whether they want to select a genre
  a = xbmcgui.Dialog().yesno("Select genre", "Do you want to select a genre to watch?")
  # deal with the output
  if a == 1: 
    # set filter
    selectGenre = True
  return selectGenre  

  
# get the full list of movies from the user's library
moviesJSON = getMovieLibrary()
  
# ask user if they want to only play unwatched movies  
unwatched = getUnwatched()  

# is skin configured to use one entry?
if promptUser and not filterGenres:
  # if so, we need to ask whether they want to select genre
  filterGenres = askGenres()

# did user ask to select genre?
if filterGenres:
  # bring up genre dialog
  success, selectedGenre = selectGenre(unwatched)
  # if not aborted
  if success:
    # get the random movie...
    randomMovie = getRandomMovie(unwatched, True, selectedGenre)
    # ...and play it!
    xbmc.executebuiltin('PlayMedia(' + randomMovie + ',0,noresume)')
else:
  # no genre filter
  # get the random movie...
  randomMovie = getRandomMovie(unwatched, False, "")
  # ...and play it
  xbmc.executebuiltin('PlayMedia(' + randomMovie + ',0,noresume)')