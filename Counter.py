import obspython as obs
from threading import Thread
import time
import socket
from pprint import pprint

oauth       = ""
nick_name   = ""
channel     = ""
addr        = "irc.chat.twitch.tv"
port        = 6667
sock = None

class Hotkey:
    '''Handles the hotkey in OBS settigns. _id = id of the hotkey.'''

    def __init__(self, callback, obs_settings, _id):
        self.obs_data = obs_settings
        self.hotkey_id = obs.OBS_INVALID_HOTKEY_ID
        self.hotkey_saved_key = None
        self.callback = callback
        self._id = _id

        self.load_hotkey()
        self.register_hotkey()
        self.save_hotkey()

    def register_hotkey(self):
        '''Registers a Hotkey.'''
        description = self._id
        hotkey_id = obs.obs_hotkey_register_frontend(
            "htk_id" + str(self._id), description, self.callback
        )
        obs.obs_hotkey_load(hotkey_id, self.hotkey_saved_key)

    def load_hotkey(self):
        '''Loads the hotkey.'''
        hotkey_saved_key = obs.obs_data_get_array(
            self.obs_data, "htk_id" + str(self._id)
        )
        obs.obs_data_array_release(hotkey_saved_key)

    def save_hotkey(self):
        '''Saves the hotkey.'''
        hotkey_saved_key = obs.obs_hotkey_save(self.hotkey_id)
        obs.obs_data_set_array(
            self.obs_data, "htk_id" + str(self._id), hotkey_saved_key
        )
        obs.obs_data_array_release(hotkey_saved_key)

class HotkeyDataHolder:
    '''Holds an instance of a Hotkey.'''
    htk_copy = None  # this attribute will hold instance of Hotkey

counter = 0
text_source = ""
sound_source = ""
counter_name = "Counter"
current_counter_command = "!counter"
increase_counter_command = "!counter+"
decrease_counter_command = "!counter-"
sound_on = False
h01 = HotkeyDataHolder()
h02 = HotkeyDataHolder()

def script_description():
	return "<b>Counter</b>" + \
			"<hr>" + \
			"You can select a Hotkey to assign the increase and decrease counter to in the settings menu under Hotkeys." +\
            "<hr>" + \
            "Twitch chat can also increase the counter by simply typing the assigned commands." + \
            "<hr>" + \
            "To get an Oauth token go to: <b>https://twitchapps.com/tmi/</b>."

def script_update(settings):
    global counter
    global text_source
    global sound_source
    global sound_on
    global counter_name
    global current_counter_command
    global increase_counter_command
    global decrease_counter_command

    current_counter_command = obs.obs_data_get_string(settings, "current_counter")
    increase_counter_command = obs.obs_data_get_string(settings, "increase_counter")
    decrease_counter_command = obs.obs_data_get_string(settings, "decrease_counter")

    sound_source = obs.obs_data_get_string(settings, "sound_source")
    counter_name = obs.obs_data_get_string(settings, "counter_name")
    sound_on = obs.obs_data_get_bool(settings,"sound_bool")
    counter = obs.obs_data_get_int(settings,"counter")
    text_source = obs.obs_data_get_string(settings, "text_source")

    update_counter(True, 0, counter, text_source, sound_source, sound_on)

    setSetting(obs.obs_data_get_string(settings, "channel").lower(),obs.obs_data_get_string(settings, "user").lower(), obs.obs_data_get_string(settings, "oauth").lower())


def script_properties():
    props = obs.obs_properties_create()

    channel = obs.obs_properties_add_text(props, "channel", "Channel", obs.OBS_TEXT_DEFAULT)
    obs.obs_property_set_long_description(channel, "This is the channel to which you want to connect to.")
    user = obs.obs_properties_add_text(props, "user", "User", obs.OBS_TEXT_DEFAULT)
    obs.obs_property_set_long_description(user, "This is the channel you want to use to connect to the chat room to (channel and user can be the same)")
    obs.obs_properties_add_text(props, "oauth", "Oauth", obs.OBS_TEXT_PASSWORD)
    obs.obs_properties_add_text(props, "current_counter", "Current Counter Command", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "increase_counter", "Increase Counter Command", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "decrease_counter", "Decrease Counter Command", obs.OBS_TEXT_DEFAULT)

    obs.obs_properties_add_button(props, "start_bot", "Start Bot", start_bot)
    obs.obs_properties_add_button(props, "restart_bot", "Restart Bot", restart_bot)
    obs.obs_properties_add_button(props, "shutdown_bot", "Shutdown Bot", shutdown_bot)
    
    obs.obs_properties_add_text(props, "counter_name", "Counter Name", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_bool(props,"sound_bool","Sound On?")
    obs.obs_properties_add_int_slider(props,"counter","Counter",0,1000,1) 
    text_source = obs.obs_properties_add_list(props,"text_source","Text Source",obs.OBS_COMBO_TYPE_EDITABLE,obs.OBS_COMBO_FORMAT_STRING,)
    obs.obs_property_set_long_description(text_source, "Select the text source which is resposinble for keeping track of the counter.")
    sound_source = obs.obs_properties_add_list(props,"sound_source","Sound Source",obs.OBS_COMBO_TYPE_EDITABLE,obs.OBS_COMBO_FORMAT_STRING,)
    obs.obs_property_set_long_description(sound_source, "OPTIONAL: Select a media source which is played when the counter increases.")

    sources = obs.obs_enum_sources()
    if sources is not None:
        for source in sources:
            # exclude Desktop Audio and Mic/Aux by their capabilities
            capability_flags = obs.obs_source_get_output_flags(source)
            if (
                capability_flags & obs.OBS_SOURCE_DO_NOT_SELF_MONITOR
            ) == 0 and capability_flags != (
                obs.OBS_SOURCE_AUDIO | obs.OBS_SOURCE_DO_NOT_DUPLICATE
            ):
                source_id = obs.obs_source_get_unversioned_id(source)
                if source_id == "text_gdiplus" or source_id == "text_ft2_source":
                    name = obs.obs_source_get_name(source)
                    obs.obs_property_list_add_string(text_source, name, name)
                elif source_id == "image_source" or source_id == "ffmpeg_source":
                    name = obs.obs_source_get_name(source)
                    if source_id == "ffmpeg_source":
                        obs.obs_property_list_add_string(sound_source, name, name)
        obs.source_list_release(sources)

    return props

def start_bot(prop, props):
    thread = Thread(target=bot)
    thread.start()

def restart_bot(prop, props):
    try:
        sock.close()
    except:
        pass
    thread = Thread(target=bot)
    thread.start()

def shutdown_bot(prop, props):
    try:
        sock.close()
    except:
        pass

def setSetting(new_channel, new_nick, new_oauth):
    '''Sets the Twitch server settings.'''
    global channel
    global nick_name
    global oauth
    channel = new_channel
    nick_name = new_nick
    oauth = new_oauth

def script_load(settings):
    '''Loads data upon opening the script'''
    h01.htk_copy = Hotkey(callback_hk1, settings, "Counter Increase")
    h02.htk_copy = Hotkey(callback_hk2, settings, "Counter Decrease")

def script_save(settings):
    '''Saves script settings'''
    obs.obs_data_set_int(settings, "counter", counter)  #saves the death counter before exiting
    h01.htk_copy.save_hotkey()  #saves hotkey
    h02.htk_copy.save_hotkey()  
    
def callback_hk1(pressed):
    '''Performs action upon pressing Hotkey 1'''
    if pressed:
        global counter
        counter = counter + 1
        update_counter(True, 1, counter, text_source, sound_source, sound_on)

def callback_hk2(pressed):
    '''Performs action upon pressing Hotkey 2'''
    if pressed:
        global counter
        counter = counter - 1
        update_counter(True, 0, counter, text_source, sound_source, sound_on)

def update_counter(visible, status, counter, text_source, sound_source, sound_on):
        '''Updates the death counter.'''
        current_scene = obs.obs_frontend_get_current_scene()
        source_visibility(get_fitting_scene(text_source), text_source, visible)
        update_text(text_source, f"{counter_name} {counter}")
        obs.obs_source_release(current_scene)
        if status > 0 and sound_on:
            #start a seperate thread to play sounds, that way
            thread = Thread(target=play_sound, args=(get_fitting_scene(sound_source), sound_source)) #plays a sound effect
            thread.start()

def get_fitting_scene(source_name):
    '''Gets the scene where a source resides in.'''
    scenes = obs.obs_frontend_get_scenes()
    found_scene = "no scene"
    for scene in scenes:
        scene_name = obs.obs_source_get_name(scene)
        current_scene = obs.obs_scene_from_source(scene)
        item = obs.obs_scene_find_source(current_scene, source_name)
        if item is not None:
             found_scene = scene_name
             break
    obs.source_list_release(scenes)
    return found_scene

def source_visibility(scene_name, source_name, visibility):
        '''Turns a source on or off.'''
        scenes = obs.obs_frontend_get_scenes()
        for scene in scenes:
            name = obs.obs_source_get_name(scene)
            if name == scene_name:
                current_scene = obs.obs_scene_from_source(scene)
                item = obs.obs_scene_find_source(current_scene, source_name)
                obs.obs_sceneitem_set_visible(item, visibility)
                break
        obs.source_list_release(scenes)

def play_sound(scene, sound):
        '''Plays a media source and waits until it's finished playing.
        Preferably start this in a seperate thread.
        Otherwise other code will have to wait until the media has finished playing.'''
        source_visibility(scene, sound, False)
        source_visibility(scene, sound, True)
        time.sleep(0.2)
        source = obs.obs_get_source_by_name(sound)
        while obs.obs_source_media_get_state(source) == 1: #check is media is playing, 1 == playing
            time.sleep(0.2)
        source_visibility(scene, sound, False)
        obs.obs_source_release(source)
        
def update_text(text_source, new_text):
    '''Updates the text of a text source.'''
    source = obs.obs_get_source_by_name(text_source)
    settings = obs.obs_data_create()
    obs.obs_data_set_string(settings, "text", f"{new_text}")   #changes text of text source
    obs.obs_source_update(source, settings)            #updates the text
    obs.obs_data_release(settings)
    obs.obs_source_release(source)

def bot():  
    '''This function starts the bot and handles all twitch related functions. Run this in a thread.'''
    global sock
    sock = socket.socket()
    
    reconnect() #reconnect to server incase a prior connection has been lost

    global startTime

    message = ""
    #check for incoming messages
    while True:
        data = recv(sock, 1024) #extract msg from server
        pprint(data)
        message = parseMessageData(data)  #extracts the received message
        checkPing(sock, data)               #check if the twitch has requested a PONG message
        ####################################################################################################
        message = chatCommands(sock, message, data) #checks if the received message is a command
        time.sleep(1)   #time speed of received msg

def reconnect():
    '''reconnects/connects to the socket/twitch'''
    try:
        sock.connect((addr, port))  #connect to server
        #send login information
        send(sock, f"PASS {oauth}")
        send(sock, f"NICK {nick_name}")
        send(sock, f"CAP REQ :twitch.tv/tags twitch.tv/membership")
        send(sock, f"JOIN #{channel}")  #join specified channels chat
        print("Succesfully connected")
    except Exception as e:
        print("Connection failed or already connected")
        print(e)

def checkPing(sock, msg):
    '''Checks if a PING message has been received and responds with a PONG message.'''
    if 'PING' in msg:                   #if PING in msg then...
        data = msg.split(":")[1]        #extract message from PING msg
        send(sock, f"PONG :{data}") 
    else:
        pass

def send(sock, msg):
    '''Sends a message to the server.'''
    sock.send(bytes(msg + "\n", "ASCII"))

def recv(sock, buff_size):
    '''Receives and returns the msg from the server.'''
    return sock.recv(buff_size).decode("UTF-8")

def parseMessageData(msg):
        '''Extracts the chat message. TODO: links are not being extracted correctly.'''
        data    = msg.split(":")   #remove everything from the string until the second ":" has been reached
        for index, x in enumerate(data):
            if 'PRIVMSG' in x:
                msg    = data[index+1]
                msg    = msg.replace('\r\n','')
                return msg
            else:
                pass
        pass

def chatCommands(sock, msg, data): 
    '''Checks and executes commands from chat users.'''
    global nick_name
    global counter
    global current_counter_command
    global increase_counter_command
    global decrease_counter_command
    if nick_name != parse_name_data(data):
        if msg == None:
            return ""
        ###########################################commands###########################################
        elif msg.lower() == current_counter_command.lower():
            send(sock, f"@reply-parent-msg-id={get_message_id(data)} PRIVMSG #{channel} : Current count is: {counter}") #change reply message here
        elif msg.lower() == increase_counter_command.lower():
            counter = counter + 1
            update_counter(True, 1, counter, text_source, sound_source, sound_on)
            send(sock, f"@reply-parent-msg-id={get_message_id(data)} PRIVMSG #{channel} : Current count: {counter}") #change reply message here
        elif msg.lower() == decrease_counter_command.lower():
            counter = counter - 1
            update_counter(True, -1, counter, text_source, sound_source, sound_on)
            send(sock, f"@reply-parent-msg-id={get_message_id(data)} PRIVMSG #{channel} : Current count: {counter}") #change reply message here
            
def update_counter(visible, death_status, deaths, death_source, death_sound_source, sound_on):
        '''Updates the death counter.'''
        current_scene = obs.obs_frontend_get_current_scene()
        source_visibility(get_fitting_scene(death_source), death_source, visible)
        update_text(death_source, f"Deaths: {deaths}")
        obs.obs_source_release(current_scene)

        if death_status > 0 and sound_on:
            #start a seperate thread to play sounds, that way
            thread = Thread(target=play_sound, args=(get_fitting_scene(death_sound_source), death_sound_source)) #plays a sound effect
            thread.start()

def get_message_id(msg):
        '''Gets the id of the message (needed to reply to a message, see twitch client-server documentation for futher info).'''
        if 'PRIVMSG' in msg:                #if of PRIVMSG type...
            data    = msg.split(";")   #remove everything from the string until the second ":" has been reached
            for x in data:
                if 'id=' in x:
                    data    = x.replace('id=','')
                    return data
                else:
                    pass
        else:
            pass

def is_user_mod(msg):
    '''Checks if the user is a mod. Returns True if a mod.'''
    if 'PRIVMSG' in msg:                #if of PRIVMSG type...
        data    = msg.split(";")   #remove everything from the string until the second ":" has been reached
        for x in data:
            if 'mod=' in x:
                data    = x.replace('mod=','')
                return data is 1
            else:
                pass
    else:
        return False

def parseMessageData(msg):
    '''Extracts the chat message. TODO: links are not being extracted correctly.'''
    data    = msg.split(":")   #remove everything from the string until the second ":" has been reached
    for index, x in enumerate(data):
        if 'PRIVMSG' in x:
            msg    = data[index+1]
            msg    = msg.replace('\r\n','')
            return msg
        else:
            pass
    pass

def parse_name_data(msg):
    '''Extracts the user name of a chatter.'''
    if 'PRIVMSG' in msg: #if of PRIVMSG type...
        data    = msg.split(":")   #remove everything from the string until the second ":" has been reached
        for x in data:
            if 'PRIVMSG' in x:
                data    = x
                index   = x.index("!")
                return data[0:index]
            else:
                pass
    else:
        pass

def slicer(my_str,sub):
    '''Cuts the beginning portion of my_str until the sub string has been reached.'''
    index = my_str.find(sub)
    if index !=-1 :
            return my_str[index:] 
    else :
            print('Sub string not found!')