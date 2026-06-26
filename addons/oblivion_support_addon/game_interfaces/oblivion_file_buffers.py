print("Importing oblivion_file_buffers.py")
from src.logging import logging, time
from src.game_interfaces.fnv_file_buffers import GameInterface as FNVFileBuffersInterface
from src.ui import FolderSelectionDialog, root_context_manager
import src.utils as utils
import os
import shutil
from pydub import AudioSegment
logging.info("Imported required libraries in oblivion_file_buffers.py")

def convert_wav_to_mp3(input_file, output_file):
    """
    Converts a WAV audio file to MP3 format using pydub.
    
    Args:
        input_file (str): The path to the input .wav file.
        output_file (str): The path where the output .mp3 file will be saved.
    """
    try:
        # Load the WAV file
        audio: AudioSegment = AudioSegment.from_wav(input_file)
        
        # Export as MP3 format (pydub automatically uses ffmpeg for the conversion) with bitrate of 64k and samplerate of 44100 Hz
        audio.export(output_file, format="mp3", bitrate="64k", parameters=["-ar", "44100"])
        
        logging.info(f"Successfully converted '{input_file}' to '{output_file}'")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        logging.error("Please ensure FFmpeg is installed and accessible in your system's PATH.")

valid_games = ["oblivion"]
interface_slug = "oblivion_file_buffers"

class GameInterface(FNVFileBuffersInterface):
    def __init__(self, conversation_manager, _valid_games, _interface_slug):
        if _valid_games is not None:
            valid_games = _valid_games
        if _interface_slug is not None:
            interface_slug = _interface_slug
        super().__init__(conversation_manager, valid_games, interface_slug)
        logging.info("Loading Oblivion file buffers game interface")
        self.mp3_file = f'PantellaQuest_PantellaDialogueLine_00002355_1.mp3'
        self.lip_file = f'PantellaQuest_PantellaDialogueLine_00002355_1.lip'
        

    def confirm_paths(self, _valid_games = None):
        logging.info(f"Confirming game and mod paths for {self.game_id}...")
        if _valid_games is not None:
            if not os.path.exists(f"{self.pluggy_path}"):
                self.ready = False
                logging.error(f"Game path does not exist: {self.pluggy_path}")
            else:
                pantella_folder_file_path = self.pluggy_path+f'\\_pantella_{self.config.game_id}_folder.txt'
                if self.config.linux_mode:
                    pantella_folder_file_path = self.pluggy_path+f'/_pantella_{self.config.game_id}_folder.txt'
                if not os.path.exists(pantella_folder_file_path):
                    logging.warn(f'''Warning: Could not find _pantella_{self.config.game_id}_folder.txt in {self.pluggy_path}.\nIf you have not yet activated Pantella in-game you can safely ignore this message.\nIf you have activated Pantella in-game please check that your {self.config.game_id} folder has been set correctly in the associated game interface config.\nIf you are still having issues, a list of solutions can be found here: \nhttps://github.com/Pathos14489/Pantella\n''')

        save_config = False
        if self.config.pluggy_path == "":
            logging.error(f"Pluggy User Files path not set for game id {self.game_id} in interface config file. Please set the Pluggy User Files path for {self.game_id} to the directory where your game is installed.")
            def select_pluggy_directory():
                with root_context_manager as root:
                    dlg = FolderSelectionDialog(root, f"Select Pluggy User Files Directory for {self.game_id}", f"Please select the Pluggy User Files directory for {self.game_id} (e.g. {self.pluggy_directory_path_example}): ")
                return dlg.result
            self.config.pluggy_path = select_pluggy_directory()
            save_config = True

        if self.config.mod_path == "":
            logging.error(f"Mod path not set for game id {self.game_id} in interface config file. Please set the mod path for {self.game_id} to the directory where your game mods are located.")
            def select_mod_directory():
                with root_context_manager as root:
                    dlg = FolderSelectionDialog(root, f"Select Mod Directory for {self.game_id}", f"Please select the mod directory for {self.game_id} (e.g. {self.mod_directory_path_example}): ")
                return dlg.result
            self.config.mod_path = select_mod_directory()
            save_config = True

        # TODO: Check if pluggy path is valid by checking for the existence of the directory and some expected files, and if not, prompt the user to select a new one. Same for mod path by checking for existence of mod voice file.
        # while not os.path.exists(self.game_executable_path):
        #     logging.error(f"Could not find game executable at {self.game_executable_path}. Please select the correct game directory.")
        #     def error_reselect_game_directory():
        #         with root_context_manager as root:
        #             dlg = FolderSelectionDialog(root, f"Error: Could not find game executable at {self.game_executable_path}. Please select the correct game directory.", f"Please select the game directory for {self.game_id} (e.g. {self.game_directory_path_example}): ")
        #         return dlg.result
        #     self.config.pluggy_path = error_reselect_game_directory()
        #     save_config = True
        
        while not os.path.exists(self.mod_voice_dir):
            def error_reselect_mod_directory():
                with root_context_manager as root:
                    dlg = FolderSelectionDialog(root, f"Error: Could not find mod voice directory at {self.mod_voice_dir}. Your selected Mod Directory was invalid. Please select a new one!\nSelect Mod Directory for {self.game_id}", f"Please select the mod directory for {self.game_id} (e.g. {self.mod_directory_path_example}): ")
                return dlg.result
            self.config.mod_path = error_reselect_mod_directory()
            save_config = True
            
        if save_config:            
            self.config.save()
            
    @utils.time_it
    def save_files_to_voice_folders(self, queue_output):
        """Save voicelines and subtitles to the correct game folders"""
        audio_file, subtitle = queue_output
        if audio_file is None or subtitle is None or audio_file == '' or subtitle == '':
            logging.error(f"Error saving voiceline to voice folders. Audio file: {audio_file}, subtitle: {subtitle}")
            return
        # logging.debug(f"Saving files to voice folders for character:", self.active_character.info)
        if self.config.linux_mode:
            mp3_file_path = f"{self.mod_voice_dir}/{self.active_character.info['voice_folder']}/{self.mp3_file}"
            lip_file_path = f"{self.mod_voice_dir}/{self.active_character.info['voice_folder']}/{self.lip_file}"
        else:
            mp3_file_path = f"{self.mod_voice_dir}\\{self.active_character.info['voice_folder']}\\{self.mp3_file}"
            lip_file_path = f"{self.mod_voice_dir}\\{self.active_character.info['voice_folder']}\\{self.lip_file}"
        if self.add_voicelines_to_all_voice_folders:
            logging.info(f"Adding voicelines to all voice folders")
            for sub_folder in os.scandir(self.mod_voice_dir):
                if sub_folder.is_dir():
                    #copy both the wav file and lip file if the game isn't Fallout4
                    out_path = f"{sub_folder.path}\\{self.mp3_file}"
                    if self.config.linux_mode:
                        out_path = f"{sub_folder.path}/{self.mp3_file}"
                    logging.info(f"Copying voiceline to {out_path}")
                    # shutil.copyfile(audio_file, out_path)
                    convert_wav_to_mp3(audio_file, out_path)
                    if self.config.linux_mode:
                        shutil.copyfile(audio_file.replace(".wav", ".lip"), f"{sub_folder.path}/{self.lip_file}")
                    else:
                        shutil.copyfile(audio_file.replace(".wav", ".lip"), f"{sub_folder.path}\\{self.lip_file}")
        else:
            logging.info(f"Converting and sending voiceline to {mp3_file_path}")
            # shutil.copyfile(audio_file, mp3_file_path)
            convert_wav_to_mp3(audio_file, mp3_file_path)
            logging.info(f"Copying lip file to {lip_file_path}")
            try:
                shutil.copyfile(audio_file.replace(".wav", ".lip"), f"{lip_file_path}")
            except:
                logging.error("Error copying lip file -- falling back to default lip file")
                default_lip_file = utils.resolve_path()+'/data/default.lip'
                shutil.copyfile(default_lip_file, f"{lip_file_path}")

        logging.info(f"{self.active_character.name} should speak")
        actor_number = self.active_character.info['actor_number']
        say_line_file = '_pantella_say_line_'+str(actor_number)
        logging.info(f"Voiceline File Buffer: _pantella_say_line_{actor_number}")
        self.write_game_info(say_line_file, subtitle.strip())

            
    def write_game_info(self, text_file_name, text, append = False):
        """Write text to a text file in the game directory"""
        logging.info(f'Writing {text} to {text_file_name}.txt')
        max_attempts = 2
        delay_between_attempts = 5

        for attempt in range(max_attempts):
            try:
                write_type = "w"
                if append:
                    write_type = "a"
                write_path = f'{self.pluggy_path}\\{text_file_name}.txt'
                if self.config.linux_mode:
                    write_path = f'{self.pluggy_path}/{text_file_name}.txt'
                logging.info(f'Writing to {write_path} with write type {write_type}')
                with open(write_path, write_type, encoding='utf-8') as f:
                    logging.info(f'Writing text to {text_file_name}.txt: {text}')
                    f.write(text)
                    logging.info(f'Wrote text to {text_file_name}.txt: {text}')
                    break
            except PermissionError:
                logging.info(f'Permission denied to write to {text_file_name}.txt. Retrying...')
                if attempt + 1 == max_attempts:
                    raise
                else:
                    time.sleep(delay_between_attempts)
        return None


    def load_data_when_available(self, text_file_name, text = '', callback = None):
        while text == '':
            if not os.path.exists(f'{self.pluggy_path}\\{text_file_name}.txt') and not os.path.exists(f'{self.pluggy_path}/{text_file_name}.txt'):
                logging.info(f"Waiting for {text_file_name}.txt to be created in {self.pluggy_path}/...")
                time.sleep(0.5)
                continue
            if self.config.linux_mode:
                try:
                    # print(f"Checking for '{text_file_name}.txt' in {self.pluggy_path}/")
                    with open(f'{self.pluggy_path}/{text_file_name}.txt', 'r', encoding='utf-8') as f:
                        # print(f"Found '{text_file_name}.txt' in {self.pluggy_path}/")
                        text = f.readline().strip()
                except:
                    try:
                        # print(f"Checking for '\\{text_file_name}.txt' in {self.pluggy_path}/")
                        with open(f'{self.pluggy_path}/\\{text_file_name}.txt', 'r', encoding='utf-8') as f:
                            # print(f"Found '\\{text_file_name}.txt' in {self.pluggy_path}/")
                            text = f.readline().strip()
                    except:
                        # print(f"Checking for '{text_file_name}.txt' in {self.pluggy_path}/")
                        with open(f'{self.pluggy_path}/{text_file_name}.txt', 'r', encoding='ansi') as f:
                            # print(f"Found '{text_file_name}.txt' in {self.pluggy_path}/")
                            text = f.readline().strip()
            else:
                try:
                    with open(f'{self.pluggy_path}\\{text_file_name}.txt', 'r', encoding='utf-8') as f:
                        text = f.readline().strip()
                except:
                    with open(f'{self.pluggy_path}\\{text_file_name}.txt', 'r', encoding='ansi') as f:
                        text = f.readline().strip()
            # decrease stress on CPU while waiting for file to populate
            if callback != None:
                callback()
            time.sleep(0.01)
        return text
    
    
    def queue_actor_method(self, actor_character, method_name, *args):
        """Queue an arbitrary method to be run on the actor in game via the game interface."""
        logging.info(f'Calling {method_name} on {actor_character.name}...')
        # string_id = actor_character.ref_id
        # if len(string_id) < 8:
        #     string_id = '0'*(8-len(string_id)) + string_id # pad string_id with leading zeros if it's less than 8 characters long
        # string_int = int(string_id, 16) # convert string_id from string hex to int hex
        function_call = f"{str(actor_character.refid_int)}|{method_name}"
        if len(args) > 0:
            function_call += '|'
            for arg in args:
                function_call += f'{arg}<>'
            if function_call.endswith('<>'):
                function_call = function_call[:-2]
        max_attempts = 2
        delay_between_attempts = 1
        for attempt in range(max_attempts):
            try:
                with open(f'{self.pluggy_path}\\_pantella_actor_methods.txt', 'a', encoding='utf-8') as f:
                    f.write(f'{function_call}\n')
                break
            except PermissionError:
                logging.info(f'Permission denied to write to _pantella_actor_methods.txt. Retrying...')
                if attempt + 1 == max_attempts:
                    raise
                else:
                    time.sleep(delay_between_attempts)
                    
    def is_conversation_ended(self):
        if self.config.linux_mode:
            with open(f'{self.pluggy_path}/_pantella_end_conversation.txt', 'r', encoding='utf-8') as f:
                conversation_ended = f.readline().strip().lower()
        else:
            with open(f'{self.pluggy_path}\\_pantella_end_conversation.txt', 'r', encoding='utf-8') as f: # check if conversation has ended
                conversation_ended = f.readline().strip().lower()
        return conversation_ended == 'true'
    
    def load_ingame_actor_count(self):
        actor_count_path = f'{self.pluggy_path}\\_pantella_actor_count.txt'
        if self.config.linux_mode:
            actor_count_path = f'{self.pluggy_path}/_pantella_actor_count.txt'
        with open(actor_count_path, 'r', encoding='utf-8') as f: # check how many characters are in the conversation
            try:
                num_characters_selected = int(f.readline().strip())
            except:
                logging.info('Failed to read _pantella_actor_count.txt')
                num_characters_selected = 0
        return num_characters_selected
    
    def check_mic_status(self):
        """Check if the microphone is enabled in the MCM"""
        microphone_path = f'{self.pluggy_path}\\_pantella_microphone_enabled.txt'
        if self.config.linux_mode:
            microphone_path = f'{self.pluggy_path}/_pantella_microphone_enabled.txt'
        if os.path.exists(microphone_path):
            with open(microphone_path, 'r', encoding='utf-8') as f:
                mcm_mic_enabled = f.readline().strip()
            logging.info(f'MCM Microphone Enabled: {mcm_mic_enabled}')
            return mcm_mic_enabled.lower() == 'true'
        else:
            logging.info(f'MCM Microphone Enabled file not found at {microphone_path} - defaulting to False')
            return False
    
    @utils.time_it
    def update_game_events(self, run=True):
        """Add in-game events to player's response"""

        if run:
            # append in-game events to player's response
            game_events_path = f'{self.pluggy_path}\\_pantella_in_game_events.txt'
            if self.config.linux_mode:
                game_events_path = game_events_path.replace("\\", "/")
            with open(game_events_path, 'r', encoding='utf-8') as f:
                if self.config.game_update_pruning:
                    in_game_events_lines = f.readlines()[-self.config.game_update_prune_count:] # read latest 5 events
                else:
                    in_game_events_lines = f.readlines()
            
            in_game_events_lines = [line.strip() for line in in_game_events_lines]
            new_in_game_events = []
            for in_game_events_line in in_game_events_lines:
                new_line = in_game_events_line.replace("*","")
                while "*" in new_line:
                    new_line = new_line.replace("*","")
                new_in_game_events.append(new_line)
            in_game_events_lines = [line for line in new_in_game_events if line.strip() != '']
            
            # Is Player in combat with NPC
            # in_combat = self.load_data_when_available('_pantella_actor_is_enemy', '').lower() == 'true' 
            # if in_combat:
            #     in_game_events_lines.append(self.conversation_manager.character_manager.language["game_events"]["player_started_combat"].format(name=self.active_character.name))
            self.new_game_events.extend(in_game_events_lines)
        
        super().update_game_events()
        
        # once the events are shared with the NPC, clear the file
        self.write_game_info('_pantella_in_game_events', '')
        
    @property
    def root_mod_folder(self):
        return self.pluggy_path
    
    @property
    def pluggy_directory_path_example(self):
        if self.config.linux_mode:
            return "/home/user/.steam/steam/steamapps/compatdata/22330/pfx/drive_c/users/steamuser/My Documents/My Games/Oblivion/Pluggy/User Files/"
        else:
            return "C:\\Users\\User\\My Documents\\My Games\\Oblivion\\Pluggy\\User Files\\"

    @property
    def game_events_path(self):
        game_events_path = f'{self.pluggy_path}\\_pantella_in_game_events.txt'
        if self.config.linux_mode:
            game_events_path = game_events_path.replace("\\", "/")
        return game_events_path
        
    # @property
    # def game_executable_path(self):
    #     return os.path.join(self.game_path, "Oblivion.exe")
    
    @property
    def pluggy_path(self):
        if self.config.linux_mode:
            return self.config.pluggy_path.replace("\\", "/")
        else:
            return self.config.pluggy_path.replace("/", "\\")

    @property
    def mod_voice_dir(self):
        if self.config.linux_mode:
            return f"{self.mod_path}/Sound/Voice/PantellaOB.esp"
        else:
            return f"{self.mod_path}\\Sound\\Voice\\PantellaOB.esp"
    
    def get_current_location(self, presume = ''):
        """Return the current location"""
        logging.info(f"Waiting for location to populate...")
        location = self.load_data_when_available('_pantella_current_location', presume)
        self.write_game_info('_pantella_backend_state', 'loading')
        if location.lower() == 'none' or location == "": # location returns none when out in the wild
            location = 'Cyrodiil'
        return location
    
    # Needs work  
    @utils.time_it
    def reset_game_info(self):
        # PantellaAddActorToConversation
        self.write_game_info('_pantella_text_input', '')
        self.write_game_info('_pantella_in_game_events', '')
        self.write_game_info('_pantella_actor_voice', '')
        self.write_game_info('_pantella_current_actor', '')
        self.write_game_info('_pantella_current_actor_ref_id', '')
        self.write_game_info('_pantella_current_actor_base_id', '')
        self.write_game_info('_pantella_current_actor_race', '')
        self.write_game_info('_pantella_current_actor_gender', '')
        self.write_game_info('_pantella_current_actors', '')

        # PantellaRepository
        self.write_game_info('_pantella_text_input_enabled', 'False')
        self.write_game_info('_pantella_player_name', '')
        self.write_game_info('_pantella_player_race', '')
        self.write_game_info('_pantella_player_sex', '')
        self.write_game_info('_pantella_actor_count', '0')
        self.write_game_info('_pantella_character_selection', 'True')
        self.write_game_info('_pantella_end_conversation', 'False')
        self.write_game_info('_pantella_status', 'False')
        self.write_game_info('_pantella_say_line_0', 'False')
        self.write_game_info('_pantella_say_line_1', 'False')

        # PantellaUpdate
        self.write_game_info('_pantella_player_is_starter', '')

        self.write_game_info('_pantella_current_location', '')
        self.write_game_info('_pantella_starter_light_level', '')
        self.write_game_info('_pantella_starter_in_combat', '')
        self.write_game_info('_pantella_starter_trespassing', '')
        self.write_game_info('_pantella_starter_alerted', '')
        self.write_game_info('_pantella_starter_detected', '')
        self.write_game_info('_pantella_starter_was_attacked', '')
        self.write_game_info('_pantella_starter_alarmed', '')
        self.write_game_info('_pantella_starter_sitting', '')
        self.write_game_info('_pantella_starter_sleeping', '')

        self.write_game_info('_pantella_target_light_level', '')
        self.write_game_info('_pantella_target_trespassing', '')
        self.write_game_info('_pantella_target_in_combat', '')
        self.write_game_info('_pantella_target_unconscious', '')
        self.write_game_info('_pantella_target_alerted', '')
        self.write_game_info('_pantella_target_detected', '')
        self.write_game_info('_pantella_target_was_attacked', '')
        self.write_game_info('_pantella_target_alarmed', '')
        self.write_game_info('_pantella_target_sitting', '')
        self.write_game_info('_pantella_target_sleeping', '')

        self.write_game_info('_pantella_current_time', '')
        self.write_game_info('_pantella_day_of_week', '')

        microphone_path = f'{self.pluggy_path}\\_pantella_microphone_enabled.txt'
        if self.config.linux_mode:
            microphone_path = f'{self.pluggy_path}/_pantella_microphone_enabled.txt'
        if not os.path.exists(microphone_path):
            self.write_game_info('_pantella_microphone_enabled', 'False')
        self.write_game_info('_pantella_context_string', '')
        self.write_game_info('_pantella_removed_from_conversation', '')
        self.write_game_info('_pantella_backend_state', 'idle')
        # self.write_game_info('xxx', '')

    def get_voice_for_racial_gender(self, race, gender):
        """Get the voice model for a given race and gender"""
        race_map = {
            "Argonian": "Argonian",
            "Breton": "Breton",
            "Dark Elf": "Dunmer",
            "Dark Seducer": "DarkSeducer",
            "Dremora": "Dremora",
            "Golden Saint": "GoldenSaint",
            "High Elf": "Altmer",
            "Imperial": "Imperial",
            "Khajiit": "Khajiit",
            "Nord": "Nord",
            "Orc": "Orsimer",
            "Redguard": "Redguard",
            "Sheogorath": "Sheogorath",
            "VampireRace": "VampireRace",
            "Wood Elf": "Bosmer",
        }
        voice_model_race_name = race_map.get(race, race)  # Default to actor_race if not found
        voice_model = voice_model_race_name+"_"+gender
        return voice_model

    def load_unnamed_npc(self, character_name):
        """Load generic NPC if character cannot be found in character database"""
        
        actor_race = self.load_data_when_available('_pantella_actor_race', '')
        actor_race = actor_race.strip()
        actor_sex = self.load_data_when_available('_pantella_actor_gender', '')
        
        voice_model = self.get_voice_for_racial_gender(actor_race, actor_sex)

        voice_folder = self.conversation_manager.character_database.get_voice_folder_by_voice_model(voice_model)
        
        character_info = {
            'name': character_name, # TODO: Generate random names for generic NPCs and figure out how to apply them in-game
            'bio': f'{character_name} is a {actor_race} {"Woman" if actor_sex=="1" else "Man"}.', # TODO: Generate more detailed background for generic NPCs
            "gender":{"Female" if actor_sex=="1" else "Male"},
            "race":actor_race,
            'voice_model': voice_model,
            'voice_folder': voice_folder[0], # Default to the first for now, maybe change later?
        }

        # TODO: Enable this after adding random name generation to generic NPCs, otherwise all generic NPCs will share the same info I think
        # (Example: All Bandits would see themselves as Male Nord Bandits if the first Bandit you talked to was a Male Nord Bandit)
        # character_database.patch_character_info(character_info) # Add character info to skyrim_characters json directory if using json mode

        return character_info
    
    @utils.time_it
    def load_game_state(self):
        """Load game variables from _pantella_ files in Skyrim folder (data passed by the Pantella spell)"""

        location = self.get_current_location()
        logging.info(f"Current location: {location}")
        in_game_time = self.get_current_game_time()
        logging.info(f"Current in-game time: {in_game_time['time12']}")
        character_name, character_ref_id, character_base_id, character_in_game_race, character_in_game_gender, character_is_guard, character_is_ghost, _pantella_actor_count = self.load_character() # get the character's name and id from _pantella_current_actor.txt and _pantella_current_actor_id.txt
        player_name = self.load_player_name() # get the player's name from _pantella_player_name.txt
        player_race = self.load_player_race() # get the player's race from _pantella_player_race.txt
        player_gender = self.load_player_gender() # get player's gender from _pantella_player_gender.txt
        radiant_dialogue = self.is_radiant_dialogue() # get the radiant dialogue setting from _pantella_radiant_dialogue.txt    
        # tell Skyrim papyrus script to start waiting for voiceline input
        self.write_game_info('_pantella_end_conversation', 'False')

        
        # actor_voice_model_id, actor_voice_model_name = self.load_actor_voice_model()
            # actor_voice_model = self.load_data_when_available('_pantella_actor_voice', '')
            # actor_voice_model_name = actor_voice_model.split('<')[1].split(' ')[0]
        # logging.info(f"Actor voice model: {actor_voice_model_name}, Actor voice model ID: {actor_voice_model_id}")
        voice_model = self.get_voice_for_racial_gender(character_in_game_race, character_in_game_gender)

        location = self.get_current_location(location) # Check if location has changed since last check

        character_info, _ = self.conversation_manager.character_database.get_character(character_name, character_ref_id, character_base_id, character_in_game_race, character_in_game_gender, character_is_guard, character_is_ghost, in_game_voice_model=voice_model, location=location) # get character info from character database
        
        if character_info == None:
            logging.error(f"Character {character_name} not found in character database.")
            if self.config.continue_on_missing_character:
                logging.warn(f"Character {character_name} not found in character database. Create a new character for them, use a character generation enabled LLM, or set continue_on_missing_character to False in the config.")
                character_info = self.load_unnamed_npc(character_name)
            else:
                raise ValueError(f"Character {character_name} not found in character database.")


        in_game_time = self.get_current_game_time() # Check if in-game time has changed since last check

        # character_info['in_game_voice_model'] = voice_model
        if "voice_model" not in character_info or character_info["voice_model"].strip() == "":
            character_info['voice_model'] = voice_model
        if "voice_folder" not in character_info or character_info["voice_folder"] is None or character_info["voice_folder"].strip() == "":
            character_info["voice_folder"] = voice_model
        # character_info['in_game_voice_model_id'] = actor_voice_model_id
        character_info['refid_int'] = character_ref_id
        if (character_ref_id is not None and character_ref_id != "0" and character_ref_id != "") and ("ref_id" not in character_info or character_info["ref_id"].strip() == ""):
            character_info["ref_id"] = str(hex(int(character_ref_id)))[2:]
        character_info['baseid_int'] = character_base_id
        if (character_base_id is not None and character_base_id != "0" and character_base_id != "") and ("base_id" not in character_info or character_info["base_id"].strip() == ""):
            character_info["base_id"] = str(hex(int(character_base_id)))[2:]
        character_info["in_game_race"] = character_in_game_race
        character_info["in_game_gender"] = character_in_game_gender
        character_info["is_guard"] = character_is_guard
        character_info["is_ghost"] = character_is_ghost
        character_info["actor_number"] = _pantella_actor_count
        character_info['character_name'] = character_name
        if "name" not in character_info or character_info["name"].strip() == "":
            character_info["name"] = character_name
        if "race" not in character_info or character_info["race"].strip() == "":
            character_info["race"] = character_in_game_race
        if "gender" not in character_info or character_info["gender"].strip() == "":
            character_info["gender"] = character_in_game_gender


        # actor_relationship_rank = self.load_data_when_available('_pantella_actor_relationship', '')
        # try:
        #     actor_relationship_rank = int(actor_relationship_rank)
        # except:
        #     logging.warn(f'Failed to read actor relationship rank from _pantella_actor_relationship.txt')
        #     actor_relationship_rank = 0
        # logging.info(f'Actor relationship rank set to {actor_relationship_rank}')
        character_info['in_game_relationship_level'] = 0

        return character_info, location, in_game_time, player_name, player_race, player_gender, radiant_dialogue