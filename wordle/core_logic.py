import logging
import re


NUM_LETTERS = 26
WORD_LEN    = 5
LETTER_BASE = 65  #ASCII base for 'A'
NUM_SUGGESTIONS = 20

logger = logging.getLogger(__name__)

####
# DB format
#   - Master list: List of master nodes
#   - Letters DB: List for 5 letter-lists
#      - Letter list: List of words having the letter in corresponding
#                     position
def create_skeleton_db():
    db = {}
    db['letter_dbs'] = list()
    for i in range(NUM_LETTERS):
        letter_db = list()
        for j in range(WORD_LEN):
            letter_list = list()
            letter_db.append(letter_list)
        db['letter_dbs'].append(letter_db)
    
    db['master_list'] = list()
    return db

def add_word_to_master_list(db, word):
    master_obj = {}
    master_obj['name'] = word
    master_obj['letter_ptrs'] = list()
    db['master_list'].append(master_obj)
    return master_obj

def add_word_to_letter_list(db, word, position):
    letter_obj = {}

    word = word.upper()
    letter_index = ord(word[position:position+1]) - LETTER_BASE
    
    #logger.debug("Adding word %s to letter-list for pos %d, letter-index:%d" % 
    #             (word, position, letter_index))

    #logger.debug("Adding word %s, letter_index:%d to letter_dbs of len %d" %
    #              (word, letter_index, len(db['letter_dbs'])))
    letter_list = db['letter_dbs'][letter_index]
    pos_list = letter_list[position]
    pos_list.append(letter_obj)
    return letter_obj

def add_word_to_dictionary(db, word):

    #Perform validations
    if len(word) != WORD_LEN:
        logger.error("Incorrect word length for %s, skipping" % word)
        return -1  #skip
    
    word = word.upper()
    match = re.search("^[A-Z][A-Z][A-Z][A-Z][A-Z]$", word)
    if not match:
        logger.error("Wrongly formatted word %s, skipping" % word)
        return -1  #Skip
    
    #Validations complete, add to dictionary
    master_obj = add_word_to_master_list(db, word)
    for index in range(WORD_LEN):
        letter_obj = add_word_to_letter_list(db, word, index)
        master_obj['letter_ptrs'].append(letter_obj)
        letter_obj['master_ptr'] = master_obj
    
    return 0

def delete_word_by_mlist(db, master_obj):

    word = master_obj['name']
    logger.info("Deleting word %s by master list, letters-len:%d" % 
                (word, len(master_obj['letter_ptrs'])))
    for i in range(WORD_LEN):

        letter_obj = master_obj['letter_ptrs'][i]

        #sanity check
        letter_index = ord(word[i:i+1]) - LETTER_BASE 
        if letter_obj['master_ptr'] != master_obj:
            logger.error("Database corruption for letter %d at pos %d" %
                         (letter_index, i))
        letter_list = db['letter_dbs'][letter_index][i]

        letter_list.remove(letter_obj)
    
    db['master_list'].remove(master_obj)

def delete_word_by_letter_list(db, letter_node):
    master_obj = letter_node['master_ptr']
    delete_word_by_mlist(db, master_obj)

def build_word_database(db, dict_file):
    fd = open(dict_file, "r")

    count = 0
    for line in fd.readlines():
        word = line.strip()
        if len(word) != WORD_LEN:
            logger.error("Incorrect word len %d for %s" % (len(word), word))
            continue
        ret = add_word_to_dictionary(db, word)
        if not ret:
            count += 1
    logger.info("Added %d words to dictionary" % count)

def add_words_from_db(old_db, letter, position, new_db):
    letter_list = old_db['letter_dbs'][letter]
    pos_list = letter_list[position]
    count = 0
    for letter_obj in pos_list:
        master_obj = letter_obj['master_ptr']
        add_word_to_dictionary(new_db, master_obj['name'])
        count += 1
    logger.info("Added %d words with letter %s at position %d from old db" %
                (count, chr(letter+LETTER_BASE), position))

def letter_not_present(db, letter, pos):
    letter_list = db['letter_dbs'][letter]
    pos_list = letter_list[pos]

    count = 0
    while(len(pos_list) > 0):
        letter_obj = pos_list[0]
        delete_word_by_letter_list(db, letter_obj)
        count += 1

    logger.info("Removed %d words with %s at postion %d in list of length %d" %
                (count, chr(letter+LETTER_BASE), pos, len(pos_list)))

def process_word_in_db(db, word, outcomes):
    
    word = word.upper()
    for i in range(WORD_LEN):
        letter_idx = ord(word[i:i+1]) - LETTER_BASE
        outcome = outcomes[i:i+1]

        #The logic treats N as letter not present in any position
        #If an outcome is N while the same letter is present
        #somewhere else in the word, then treat the outcome as W
        if outcome == "N":
            for j in range(WORD_LEN):
                if j == i:
                    continue
                l_idx = ord(word[j:j+1]) - LETTER_BASE
                out = outcomes[j:j+1]
                if l_idx == letter_idx and out != "N":
                    #Same letter present somewhere else in the word
                    outcome = "W"

        logger.info("Processing outcome %s for %s[%d]" % (outcome, word, i))
        if outcome == "N":    #Letter not present
            for pos in range(WORD_LEN):
                letter_not_present(db, letter_idx, pos)
        elif outcome == "W":  #Letter in wrong position
            new_db = create_skeleton_db()
            for pos in range(WORD_LEN):
                if pos != i:
                    add_words_from_db(db, letter_idx, pos, new_db)
            letter_not_present(new_db, letter_idx, i)
            db = new_db
        elif outcome == "C":   #Letter in correct position
            #Create new db with letters from that position
            new_db = create_skeleton_db()
            add_words_from_db(db, letter_idx, i, new_db)
            db = new_db
        else:
            logger.error("Unknown outcome: %s" % outcome)
            return None
        logger.info("Left with db with vocab size: %d" % len(db['master_list']))
    return db
    
def process_next_word(db, word, outcomes):
    logger.info("Processing word %s with outcomes %s" % (word, outcomes))
    new_db = process_word_in_db(db, word, outcomes)
    if not new_db:
        logger.error("Could not create new db!!")
        return (None, None)
    
    suggested_words = list()
    master_list = new_db['master_list']
    for i in range(NUM_SUGGESTIONS):
        if len(master_list) > i:
            suggested_words.append(master_list[i]['name'])
        else:
            break
    
    #Duplicates are possible, remove them
    uniq_list = list()
    for word in suggested_words:
        if word not in uniq_list:
            uniq_list.append(word)

    return (new_db, uniq_list)

def initialize_db():
    logger.info("Initializing db")
    db = create_skeleton_db()
    build_word_database(db, "wordle/static/wordle/dictionary.txt")
    return db




