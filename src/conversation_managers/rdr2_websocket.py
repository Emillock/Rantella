print("Loading conversation_managers/rdr2_websocket.py...")
from src.logging import logging
from src.conversation_managers.base_conversation_manager import BaseConversationManager
import src.utils as utils
import json
import traceback
import uuid
import src.characters_manager as characters_manager  # Character Manager class
logging.info("Imported required libraries in conversation_managers/rdr2_websocket.py")

valid_games = ["rdr2"]
manager_slug = "rdr2_websocket"


class ConversationManager(BaseConversationManager):
    """Drives RDR2 conversations against the rdr2_websocket game interface:
    waits for the plugin's conversation_start, then loops player input →
    LLM response → TTS/actions until the conversation ends."""

    def __init__(self, config, initialize=True):
        super().__init__(config, initialize)
        self.current_location = None
        self.radiant_dialogue = False
        logging.info("RDR2 WebSocket Conversation Manager Initialized")

    def get_conversation_type(self):
        return 'single_player_with_npc'

    async def await_and_setup_conversation(self):
        """Wait for the player to start a conversation in game, then set it up."""
        self.conversation_id = str(uuid.uuid4())
        self.conversation_step += 1
        self.character_manager = characters_manager.Characters(self)  # Reset character manager
        logging.info('Waiting for the player to start a conversation in RDR2...')
        try:
            character_info, self.current_location, self.player_name, self.player_race, self.player_gender = self.game_interface.load_game_state()
        except characters_manager.CharacterDoesNotExist as e:
            logging.info('Restarting...')
            logging.error(f"Error Loading Character<await_and_setup_conversation>: {e}")
            return

        character = self.setup_character(character_info)

        self.messages = []  # clear messages

        self.tokens_available = self.config.maximum_local_tokens - self.tokenizer.num_tokens_from_messages(self.get_context())

        self.game_interface.update_game_events()  # update game events before first player input
        try:
            pp_name, _ = character.get_perspective_player_identity()
            self.new_message({'role': "system", 'content': "*" + pp_name + " approaches " + character.name + " with the intent to start a conversation with them.*"})
        except Exception as e:
            logging.error(f"Error Getting Response in await_and_setup_conversation(): {e}")
            tb = traceback.format_exc()
            logging.error(tb)
            input("Press Enter to exit.")
            raise e
        self.game_interface.update_game_events()  # update game events before player input

        self.in_conversation = True
        self.conversation_ended = False

    async def step(self):
        """Process player input and NPC response until the conversation ends."""
        self.conversation_step += 1
        if self.in_conversation == False:
            logging.info('Cannot step through conversation when not in conversation')
            self.conversation_ended = True
            return

        await self.update_game_state()
        logging.info('Stepping through RDR2 conversation...')
        logging.info(f"Messages: {json.dumps(self.get_context(), indent=2)}")

        transcript_cleaned = ''
        transcribed_text = None
        if not self.conversation_ended:  # get next player input
            logging.info('Getting player response...')

            possible_names = [character.name for character in self.character_manager.active_characters.values()]
            transcribed_text = self.game_interface.get_player_response(possible_names)
            self.behavior_manager.run_player_behaviors(transcribed_text)  # run player behaviors
            transcript_cleaned = utils.clean_text(transcribed_text)
            self.new_message({'role': "user", 'name': "[player]", 'content': transcribed_text})

            self.character_manager.before_step()  # Let the characters know before a step has been taken
            await self.update_game_state()

            active_character = self.character_manager.active_characters_list[0]
            # check if user is ending conversation
            end_convo = False
            for keyword in active_character.language["end_conversation_keywords"]:
                if utils.activation_name_exists(transcript_cleaned, keyword):
                    end_convo = True
                    break
            if end_convo or self.conversation_ended or self.game_interface.is_conversation_ended():
                # Detect who the player is saying goodbye to
                name_groups = []
                for character in self.character_manager.active_characters.values():
                    character_names = character.name.split(' ')
                    name_groups.append(character_names)
                all_words = transcript_cleaned.split(' ')
                goodbye_target_character = None
                for word in all_words:
                    for name_group in name_groups:
                        if word in name_group:
                            goodbye_target_character = self.character_manager.active_characters[' '.join(name_group)]
                            break
                await self.end_conversation(goodbye_target_character)

        if (transcribed_text is not None and transcribed_text != '') and not self.conversation_ended and self.in_conversation:
            await self.get_response()

        logging.info("Response Generated")

        # if the npc or the game plugin ended the conversation
        if (self.conversation_ended or self.game_interface.is_conversation_ended()) and self.in_conversation:
            await self.end_conversation(self.game_interface.active_character)

        self.character_manager.after_step()  # Let the characters know after a step has been taken
        # if the conversation is becoming too long, save the conversation to memory and reload
        if self.tokenizer.num_tokens_from_messages(self.messages[1:]) > (round(self.tokens_available * self.config.conversation_limit_pct, 0)):
            self.reload_conversation()
