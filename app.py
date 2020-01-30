import dash
import dash_auth
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input,Output,State
import plotly
#authentication library
from flask import request
#Grep imagenames list libraries
import os
import pathlib
#database
import sqlite3

#used with sqlite3
def removesymbolfromstring(symbol,s):
    delimiter = symbol
    x = s.split(delimiter)
    print(x)
    delimiter = ''
    s = delimiter.join(x)
    print(s)
    return s


#this fuction creates a list of images from the path.
def imagelist(path) :
    #define path
    path = pathlib.Path(path)
    #string path to be appended as part of image #relative path.
    pathstr = str(path)
    #create empty list
    imageslist = [] 

    #create list of images in path given
    with os.scandir(path) as listOfEntries:
        for entry in listOfEntries:
            #print all entries that are files.
            if entry.is_file():
                imageslist.append(pathstr + "/" + entry.name)
                print(entry.name)
    #sort list alphanumerically
    imageslist.sort()
    print(imageslist)
    return imageslist



VALID_USERNAME_PASSWORD_PAIRS = { # put these in a file.
    'hello': 'world',
    'Jason': 'mdot'
}

# external CSS stylesheets
external_stylesheets = ["https://cdnjs.cloudflare.com/ajax/libs/skeleton/2.0.4/skeleton.min.css",
                        "https://fonts.googleapis.com/css?family=Raleway:400,400i,700,700i",
                        "https://fonts.googleapis.com/css?family=Product+Sans:400,400i,700,700i"]

app = dash.Dash(__name__,external_stylesheets=external_stylesheets)

auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS
)

x = 0 #the default image, my code has been built around the default being 0.#esp in single click.
y = 0 #default1 when both clicked. #used when next_time_greater thanprev_timestamp
z = 0 #default2 when both clicked. #used when prev_time_greater than next_timestamp

imagenames = imagelist('./static/images')
num_images = len(imagenames)


app.layout = html.Div(style = {'textAlign' : 'center'},
                        children = [html.H1('Image Annotation tool'),
                                    html.Img(id = 'image-seen',src = imagenames[x],width = '500px',height = '250px',),
                                    html.Div(id='inference',children='Submit annotation for current image'),
                                    html.P(children = [ html.Div(id = 'prevend'),html.Button('Prev',id = 'prevbutton'),html.Button('Next', id = 'nextbutton'),html.Div(id = 'nextend')],),
                                    html.Div(style = {'marginLeft':'500px'},
                                        children = [html.P(children = [dcc.Dropdown(id = 'condition',
                                                                        options = [ {'label' : i , 'value' : i} for i in ['condition one','condition two','not sure']], #list of conditions
                                                                        placeholder = "Select the condition",
                                                                        style={'height': '30px', 'width': '400px', 'textAlign' : "middle"}),
                                                            html.P(),
                                                            dcc.Dropdown( id = 'view',
                                                                            options = [{'label' : j,'value': j } for j in ['view one','view two','null']],#list of views
                                                                            placeholder = "Select view",
                                                                            style={'height': '30px', 'width': '400px', 'textAlign' : 'center'})])]),
                                    html.P(),
                                    html.Button('Submit', id = 'submit'),
                                    html.Div(id = 'thesubmitted')
                                    ])

#Manage the image slider.
@app.callback(
    dash.dependencies.Output('image-seen','src'),
    [dash.dependencies.Input('prevbutton','n_clicks'),
    dash.dependencies.Input('nextbutton','n_clicks'),],
    [dash.dependencies.State('prevbutton','n_clicks_timestamp'),
    dash.dependencies.State('nextbutton','n_clicks_timestamp'),
    dash.dependencies.State('image-seen','src')]
    )
def slide_images(ncp,ncn,ncpts,ncnts,current_image_path):
    #Initial variables had too many letters.(to simplify I created a key/legend) #a word legend
    #Keys : Value #ncp = n_clicks_of_prev #ncn = n_clicks_of_next #ncpts = n_clicks_timestamp_of_prev #ncnts = n_clicks_timestamp_of_next

    #Timestamps used to determine between prev and next, which was clicked first.
    #print('Timestamp prev button: ',ncpts, '\nType : ',type(ncpts)) 
    #print('Timestamp next button : ',ncnts, '\nType : ',type(ncnts))
    #print('ncn : ',ncn)
    #print('ncp : ',ncp)
    #print("Current image : ",current_image_path)
    #print("Current image length : ",len(current_image_path))
    #print("Image index : ",imagenames.index(current_image_path))
    
    #create table based on images.
    #database
    conn = sqlite3.connect('lebo.db')
    #cursor
    c = conn.cursor()
    #create table
    #Create table
    c.execute("""CREATE TABLE IF NOT EXISTS userlabels(
    	userid PRIMARY KEY
    	username

    	) WITHOUT ROWID"""
    	)
    for image in imagenames:
    	newimage = image
    	newimage = removesymbolfromstring('/',newimage)
    	newimage = removesymbolfromstring('.',newimage)
    	print(newimage)
    	try : 
        	addcolumnimage = "ALTER TABLE userlabels ADD COLUMN " +newimage+ " text"
        	c.execute(addcolumnimage)
    	except:
        	pass
    c.close()
    num_images = len(imagenames) 

    image_state = imagenames.index(current_image_path)
    #when only one has been pressed.

    if ncpts == None or ncnts == None:                                  #none clicked or one clicked
        if ncp == None and ncn == None :                                                            #none clicked
            return imagenames[x] #default image.
            #image state no change.           
        
        if ncp != None :                                                                            #only prev clicked
                return imagenames[x]

        if ncn != None :                                                                            #only next clicked. 
            if  ncn < num_images: #only next has been clicked till last image.
                image_state = ncn #not updating image_state #will try using pointers and addressing.
                return imagenames[x + ncn]

            if ncn >= num_images - 1:#clicked till last image 
                return imagenames[num_images - 1]
    
    elif image_state >= num_images or image_state < 0 : #guards against the upper and lower limits.
        if image_state >= num_images :#state never should go above len of list images.
            image_state = image_state -1
        if image_state < 0 :                #state never goes under index zero.
            image_state = image_state + 1
    else :                                              
        if ncpts > ncnts and image_state > 0 : 
            return imagenames[image_state - 1]
        if ncpts > ncnts and image_state == 0 :
            return imagenames[image_state]
        if ncnts > ncpts and image_state < (num_images - 1):
            return imagenames[image_state + 1]
        if ncnts > ncpts and image_state == (num_images -1 ):
            return imagenames[image_state]


#update and connect to database    
@app.callback(
    Output('thesubmitted','children'),
    [Input('submit','n_clicks')],
    [State('condition','value'),
    State('image-seen','src')]
)
def update_output_div(n_clicks,input_value,image_path):
    print(image_path,len(image_path))
    username = request.authorization['username']

    # connect sqlite3
    conn = sqlite3.connect('lebo.db')
    print("Database created")
    #cursor
    c = conn.cursor()
    print("Cursor connected")
    #create table if not exists
    '''c.execute("""CREATE TABLE IF NOT EXISTS userlabels(
    	userid PRIMARY KEY


    	) WITHOUT ROWID"""
    	)
    print("Table created")
    for image in imagenames:
    	print(image)
    	addcolumnimage = "ALTER TABLE userlabels ADD COLUMN " +image+ " text"
    	print(addcolumnimage)
    	#c.execute(addcolumnimage)
    	print("column {} added ".format(image))
    '''

    return 'You\'ve entered "{}" for image {} for user {}'.format(input_value,image_path[14:],username)

   
if __name__ == '__main__':
    app.run_server(debug = True,host = '0.0.0.0')
