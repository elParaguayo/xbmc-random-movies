# Random movie selecter
# Massive thanks to the developers of the script.randommitems addon, without whom this would not have been possible
#
# Author - el_Paraguayo
# Website - https://github.com/elParaguayo/
# Version - 0.1

import xbmc
import xbmcgui
from urllib import quote_plus, unquote_plus
import re
import sys
import os
import random

# let's parse arguments before we start
try:
  # parse sys.argv for params
  params = dict( arg.split( "=" ) for arg in sys.argv[ 1 ].split( "&" ) )
except:
  # no params passed
  params = {}
# set our preferences
filterGenres = params.get( "filtergenre", "" ) == "True"

def getRandomMovie(filterWatched, filterGenre, genre):
  # set our unplayed query
  if filterWatched:
    unplayed = "where (playCount is null "
  else:
    unplayed = ""
  # filter by genre? (There must be a neater way of doing this)
  if filterGenre:
    # if we're already filtering unplayed films then we need to ADD an extra criteria
    if filterWatched:
      filter = "AND movieview.c14 like '%%" + genre + "%%') "
    # otherwise it's a new criteria
    else:
      filter = " where movieview.c14 like '%%" + genre + "%%' "
  else:
    if filterWatched:
      filter = ") "
    else:  
      filter = ""
    
  # sql statement
  sql_movies = "select movieview.c00, movieview.c08, movieview.c14, movieview.strPath, movieview.strFilename from movieview %s%sorder by RANDOM() limit 1" % ( unplayed, filter )
  # query the database
  movies_xml = xbmc.executehttpapi( "QueryVideoDatabase(%s)" % quote_plus( sql_movies ), )
  # separate the records
  movies = re.findall( "<record>(.+?)</record>", movies_xml, re.DOTALL )
  # enumerate thru our records and set our properties
  for count, movie in enumerate( movies ):
    # # separate individual fields
    fields = re.findall( "<field>(.*?)</field>", movie, re.DOTALL )
    thumb_cache, fanart_cache, play_path = get_media(fields[3], fields[4])
  # return the filepath for the film  
  return play_path
  
def selectGenre(filterWatched):
  success = False
  selectedGenre = ""
  # need to make sure we don't show genres from watched films if user only wants unwatched
  if filterWatched:
    unplayed = "where playCount is null "
  else:
    unplayed = ""
  # sql statement - get genres from the films in our library
  sql_genres = 'select c14 from movieview %s' % ( unplayed )
  # query the database
  genres_xml = xbmc.executehttpapi( "QueryVideoDatabase(%s)" % quote_plus( sql_genres ), )
  # separate the records
  genres = re.findall( "<record>(.+?)</record>", genres_xml, re.DOTALL )
  # set up empty array
  myGenres = []  
  # enumerate thru our records and set our properties
  for count, genre in enumerate( genres ):
    # # separate individual fields
    fields = re.findall( "<field>(.*?)</field>", genre, re.DOTALL )
    for field in fields:
      # split the genre field into single genres
      genres = field.split(" / ")
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
  
  
def get_media( path, file ):
  # set default values
  play_path = fanart_path = thumb_path = path + file
  # we handle stack:// media special
  if ( file.startswith( "stack://" ) ):
    play_path = fanart_path = file
    thumb_path = file[ 8 : ].split( " , " )[ 0 ]
  # we handle rar:// and zip:// media special
  if ( file.startswith( "rar://" ) or file.startswith( "zip://" ) ):
    play_path = fanart_path = thumb_path = file
  # return media info
  return xbmc.getCacheThumbName( thumb_path ), xbmc.getCacheThumbName( fanart_path ), play_path
  
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

# ask user if they want to only play unwatched movies  
unwatched = getUnwatched()  


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