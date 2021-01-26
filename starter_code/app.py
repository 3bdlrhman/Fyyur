#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from datetime import datetime
# after seperating models
from Models import db, Show, Artist, Venue

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
migrate = Migrate(app, db)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#-------------------------------------------------------------#
#                       Controllers.                          #
#-------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')

##-----------------------------------------###
##                   Venues                ###
##-----------------------------------------###

@app.route('/venues')
def venues():
  # list of distinct cities
  query = db.session.query(Venue.city.distinct().label("city"))
  cities = [row.city for row in query.all()]
  
  # final returned objects
  objs=[]
  
  for city in cities:        
        venues_list = Venue.query.filter_by(city=city).all()
        ven_obj_list = []
        
        # get the number of upcomming shows
        list_of_all_shows = Show.query.all()
        up_com=[]
        for s in list_of_all_shows:
              if datetime.strptime(str(s.start_time),'%Y-%m-%d %H:%M:%S') > datetime.now():
                    up_com.append(str(s.start_time))
        
        # build the outer object
        for v in venues_list:
              ven_obj_list.append(
                {
                  'id' : v.id,
                  'name' : v.name,
                  'num_upcomming_shows' : len(up_com)
                }
              )
        
        ven = Venue.query.filter_by(city=city).first()
        
        obj = {
          'city' : city,
          'state' : ven.state,
          'venues' : ven_obj_list
        }
        
        objs.append(obj)
  
  return render_template('pages/venues.html', areas=objs);
  
#---------------------------------------------
@app.route('/venues/search', methods=['POST'])
def search_venues():
  # using form.get('term', '') instead of form['term']. Because it has a fallback option
  word = request.form.get('search_term', '')
  items = Venue.query.filter(Venue.name.ilike('%{}%'.format(word))).all()
  count = len(items)

  data=[]
  for item in items:
        shows = Show.query.filter(Show.venue_id==item.id)
        
        upcoming_shows=[]
        for show in shows:
             t = str(show.start_time)
             if datetime.strptime(t,'%Y-%m-%d %H:%M:%S') > datetime.now():
                   upcoming_shows.append(show)
        o = {
          'id': item.id,
          'name': item.name,
          'num_upcoming_shows': len(upcoming_shows)
        }
        data.append(o)
  
  response={
    "count": count,
    "data": data
  }

  response={
    "count": count,
    "data": data
  }
  return render_template('pages/search_venues.html', results=response, search_term=word)

#----------------------------------
@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  this_venue = Venue.query.get(venue_id)  
  shows = Show.query.filter(Show.venue_id== this_venue.id).all()
  
  upcoming_shows= db.session.query(Show).join(Venue).filter(Show.start_time > datetime.now()).filter(Show.venue_id==venue_id).all()
  past_shows= db.session.query(Show).join(Venue).filter(Show.start_time < datetime.now()).filter(Show.venue_id==venue_id).all()

  upcoming_shows_lst=[]
  past_shows_lst=[]  
  for i in upcoming_shows:
        ar_id = i.artist_id
        artist = Artist.query.get(ar_id)
        o = {
          'artist_id': artist.id,
          'artist_name': artist.name,
          'artist_image_link': artist.image_link,
          'start_time' : str(i.start_time)
        }        
        upcoming_shows_lst.append(o)
              
  for i in past_shows:
        ar_id = i.artist_id
        artist = Artist.query.get(ar_id)
        o = {
          'artist_id': artist.id,
          'artist_name': artist.name,
          'artist_image_link': artist.image_link,
          'start_time' : str(i.start_time)
        }        
        past_shows_lst.append(o)              
              
  obj = {
        'id':this_venue.id,
        'name':this_venue.name,
        'genres': [this_venue.genres],
        'address': this_venue.address,
        'city': this_venue.city,
        'state': this_venue.state,
        'phone': this_venue.phone,
        'website': this_venue.website,
        'facebook_link': this_venue.facebook_link,
        'seeking_talent': this_venue.seeking_talent,
        'seeking_description': this_venue.seeking_description,
        'image_link': this_venue.image_link,
        'past_shows': past_shows_lst,
        'upcoming_shows': upcoming_shows_lst,
        'past_shows_count': len(past_shows_lst),
        'upcoming_shows_count':len(upcoming_shows_lst)
      }
  
  return render_template('pages/show_venue.html', venue=obj)
  
  
#     Create Venue                     
#--------------------------------------------
@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

#---------------------------------------------#
@app.route('/venues/create', methods=['POST'])
def create_venue_submission():  
  newvenue = Venue(name=request.form['name'],city= request.form['city'],state=request.form['state'],
                   address=request.form['address'],phone=request.form['phone'],
                   genres=request.form['genres'],image_link=request.form['image_link'],
                   facebook_link=request.form['facebook_link'])
  
  try:
    db.session.add(newvenue)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
  finally:
    db.session.close()
    
  return render_template('pages/home.html')

#---------------------------------------------#

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    record = Venue.query.get(venue_id)
    db.session.delete(record)
    db.commit()
  except:
    flash('An error ocurred')
  finally:
    db.session.close()
  
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None


##------------------------------------------------------------------##
##                            Artists                               ##
##------------------------------------------------------------------##

@app.route('/artists')
def artists():  
  newData = Artist.query.all()
  allArtists=[]
  for n in newData:
        allArtists.append(
          {
            'id' : n.id,
            'name' : n.name
          }
        )
        
  return render_template('pages/artists.html', artists=allArtists)

#---------------------------------------------#
@app.route('/artists/search', methods=['POST'])
def search_artists():
  word = request.form['search_term']
  items = Artist.query.filter(Artist.name.ilike('%{}%'.format(word))).all()
  count = len(items)
  data=[]
  for item in items:
        shows = Show.query.filter(Show.artist_id==item.id)
        
        upcoming_shows=[]
        for show in shows:
             t = str(show.start_time)
             if datetime.strptime(t,'%Y-%m-%d %H:%M:%S') > datetime.now():
                   upcoming_shows.append(show)
        o = {
          'id': item.id,
          'name': item.name,
          'num_upcoming_shows': len(upcoming_shows)
        }
        data.append(o)
  
  response={
    "count": count,
    "data": data
  }
  
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

#---------------------------------------------#
@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  this_artist = Artist.query.get(artist_id)
    
  shows = Show.query.filter(Show.artist_id== this_artist.id).all()

  upcoming_shows= db.session.query(Show).join(Artist).filter(Show.start_time > datetime.now()).filter(Artist.id==artist_id).all()
  past_shows= db.session.query(Show).join(Artist).filter(Show.start_time < datetime.now()).filter(Artist.id==artist_id).all()

  upcoming_shows_lst=[]
  past_shows_lst=[]

  for i in upcoming_shows:
        ven_id = i.venue_id
        venue = Venue.query.get(ven_id)
        o = {
          'venue_id': venue.id,
          'venue_name': venue.name,
          'venue_image_link': venue.image_link,
          'start_time' : str(i.start_time)
        }
        
        upcoming_shows_lst.append(o)
              
  for i in past_shows:
        ven_id = i.venue_id
        venue = Venue.query.get(ven_id)
        o = {
          'venue_id': venue.id,
          'venue_name': venue.name,
          'venue_image_link': venue.image_link,
          'start_time' : str(i.start_time)
        }        
        past_shows_lst.append(o)              
              
  obj = {
        'id':this_artist.id,
        'name':this_artist.name,
        'genres': [this_artist.genres],
        'city': this_artist.city,
        'state': this_artist.state,
        'phone': this_artist.phone,
        'website': this_artist.website,
        'facebook_link': this_artist.facebook_link,
        'seeking_venue': this_artist.seeking_venue,
        'seeking_description': this_artist.seeking_description,
        'image_link': this_artist.image_link,
        'past_shows': past_shows_lst,
        'upcoming_shows': upcoming_shows_lst,
        'past_shows_count': len(past_shows_lst),
        'upcoming_shows_count':len(upcoming_shows_lst)
      }
  
  return render_template('pages/show_artist.html', artist=obj)

#  Update             "NOT COMPLETED"
#  ----------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()

  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  --------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  
    newartist = Artist(name=request.form['name'],city= request.form['city'],state=request.form['state'],
                   phone=request.form['phone'],
                   genres=request.form['genres'],
                   facebook_link=request.form['facebook_link'])
  
    try:
      db.session.add(newartist)
      db.session.commit()
      flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except:
      db.session.rollback()
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
    finally:
      db.session.close()
  
    return render_template('pages/home.html')


##  ---------------------------------------------------------------##
##                        SHOWS                                    ##
##  ---------------------------------------------------------------##

@app.route('/shows')
def shows():
  info=db.session.query(
    Venue.id, Venue.name, Artist.id, Artist.name, Artist.image_link, 
    Show.start_time).select_from(Show).join(Venue, Venue.id==Show.venue_id).join(Artist, Artist.id==Show.artist_id).all()
    
  new_data = []
  for i in info:
        o = {
              "venue_id": i[0],
              "venue_name": i[1],
              "artist_id": i[2],
              "artist_name": i[3],
              "artist_image_link": i[4], 
              "start_time": str(i[5])
            }
        new_data.append(o)
  
  return render_template('pages/shows.html', shows=new_data)

  
@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():

  new_show = Show( 
                  artist_id=request.form['artist_id'] , 
                  venue_id=request.form['venue_id'] ,
                  start_time=request.form['start_time']
                  )
  try:
    db.session.add(new_show)
    db.session.commit()
    # on successful db insert, flash success
    flash('Show was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Show could not be listed.')
  finally:
    db.session.close()
  
  return render_template('pages/home.html')

          ##############################################################
          ##############################################################

                   #########      ####     ######  ##   ######## 
                   ##########    ##  ##    ##  ##  ##   ##          
                   ###    ####  ##    ##   ##  ##  ##   ##
                   ###    ####  ##    ##   ##  ##  ##   #######         
                   ##########    ##  ##    ##  ##  ##   ##   
                   #########      ####     ##  ######   ########      

          ###############################################################
          ###############################################################
  
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500

if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
#            ****************      Launch.    **********************         #
#----------------------------------------------------------------------------#
if __name__ == '__main__':
    app.run(debug=True)
