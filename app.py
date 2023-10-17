#!/usr/bin/python3 -u
#    headlessNSPythonRecruiter
#    A headless Python3 script to automate sending API request to NationStates API to recruit nations.
#    By Clarissa Au
#    Under GNU GPL v3.0 License
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Imports
import requests
import yaml
import os
import logging
import time
import xml.etree.ElementTree as ET
import re
import random

# Global Variables & Constants
VERSION = "0.0.2"
USERAGENT = "headlessNSPythonRecruiter/" + VERSION + " (by Clarissa Au)"
REQUESTS_HEADER = {"User-Agent": USERAGENT}
choice = None
logger = None
telegram = None
tg_target = 0
tg_amt = 0
tg_sent_history = [] # List of nations that have been sent telegram, will not be sent telegram until program restarts
PWD = os.getcwd()
RECRUITMENT_TELEGRAM_RATELIMIT = 180 # 3 minutes
NONRECRUITMENT_TELEGRAM_RATELIMIT = 30 # 30 seconds

# Color Codes
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"
BLACK = "\033[30m"
RESET = "\033[0m"

# Load config file if it exists
def load_config():
    global config
    try:
        with open("config.yml", 'r') as ymlfile:
            config = yaml.safe_load(ymlfile)
    except FileNotFoundError:
        default_config = {
            "clientkey": "YOUR_CLIENT_KEY_HERE",
            "clientname": "YOUR_CLIENT_NAME_HERE",
            "recruiting":{
                "flag_FoundingRefounding": False,
                "flag_Ejected": False,
                "individual_nations": [],
                "blocked_nations": [],
                "optimization": False,
                "ratio":{
                    "found": 0.8,
                    "refound": 0.2,
                    "ejected": 0.0,
                }
            }
        }
        with open("config.yml", 'w') as ymlfile:
            yaml.dump(default_config, ymlfile)
        print(RED + "Config file not found. A new config file has been created. Please edit the config file and restart the program." + RESET)
        exit()
    finally:
        logging.debug("Config file loaded.")

# Logger
class Logger(object):

    def __init__(self):
        self.storage = []
        logging.basicConfig(filename='headlessNSPythonRecruiter.log', level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
        logging.debug("headlessNSPythonRecruiter v" + VERSION + " by Clarissa Au")
        logging.debug("Licensed under GNU GPL v3.0 License")
        logging.debug("Logging Initialized.")

    def display(self, level, amount):
        for log in reversed(self.storage):
            if log.level >= level:
                print(log.message)
                amount -= 1
            if amount <= 0:
                break
        while amount >= 0:
            print("")
            amount -= 1

    def log(self, level, message):
        self.storage.append(Log(level, message))
    

class Log(object):
    def __init__(self, level, message):
        self.message = message
        self.level = level
        logging.log(level, message)
        

# Display main menu
def display():
    global choice
    print("---------------------------------------------------------")
    print("headlessNSPythonRecruiter v" + VERSION + " by Clarissa Au")
    print("This program is licensed under GNU GPL v3.0 License")
    print("---------------------------------------------------------")
    logger.display(logging.INFO, 5)
    print("---------------------------------------------------------")
    print(f"Hello, {config['clientname']}!")
    print("")
    print("Configure [T]elegram")
    print("[S]elect Recepients")
    print("[R]ecruit")
    print("[Q]uit")
    print("")
    choice = input("> ")

# Configure Telegram - Menu
def configure_telegram_menu():
    while True:
        print("---------------------------------------------------------")
        print("Configure Telegram - Menu")
        print("[S]elect Existing Telegram")
        print("[C]reate New Telegram")
        print("[D]elete Current Telegram")
        print("[B]ack")
        print("")
        choice = input("> ")
        match choice:
            case "S":
                select_telegram()
                break
            case "C":
                create_telegram()
                break
            case "D":
                delete_telegram()
                break
            case "B":
                main()
                break
            case _:
                print("Invalid choice. Please try again.")

# Configure Telegram - Select
def select_telegram():
    global telegram
    print("---------------------------------------------------------")
    print("Configure Telegram - Select")
    print("Select a Telegram to use.")
    print("")
    telegram_folder = os.path.join(PWD, "telegrams")
    if not os.path.exists(telegram_folder):
        os.makedirs(telegram_folder)
    for i in range(0,len(os.listdir(telegram_folder))):
        print(f"{i}. {os.listdir(telegram_folder)[i]}")
    choice = input("> ")
    try:
        with open(os.path.join(telegram_folder, os.listdir(telegram_folder)[int(choice)]), 'r') as telegram_file:
            telegram = yaml.safe_load(telegram_file)
            print(f"Telegram {os.listdir(telegram_folder)[int(choice)]} selected.")
            logger.log(logging.INFO, f"Telegram {os.listdir(telegram_folder)[int(choice)]} selected.")
    except FileNotFoundError:
        print("File not found. Please try again.")
        logger.log(logging.DEBUG, "File not found.")
    except ValueError:
        print("Invalid choice. Please try again.")
        logger.log(logging.DEBUG, "Invalid choice.")
    except IndexError:
        print("No such Telegram exists. Please try again.")
        logger.log(logging.DEBUG, "Invalid choice.")
    except Exception as e:
        print(f"Somehow an error has occured({e}). Please try again.")
        logger.log(logging.DEBUG, e)
    finally:
        configure_telegram_menu()

# Configure Telegram - Create
def create_telegram():
    global telegram
    print("---------------------------------------------------------")
    print("Configure Telegram - Create")
    print("Create a new Telegram.")
    print("")
    telegram_folder = os.path.join(PWD, "telegrams")
    if not os.path.exists(telegram_folder):
        os.makedirs(telegram_folder)
    print("Enter the Telegram's name.")
    name = input("> ")
    print("Enter the Telegram's TGID.")
    tgid = input("> ")
    print("Enter the Telegram's secret key.")
    tgsecretkey = input("> ")
    print("Enter the Type of the Telegram. [R]ecruitment/[N]on-Recruitment")
    print(RED + "Warning: If you're recruiting, you must enter R." + RESET)
    print("Failure to do so will result in Site API Ban.")
    isrecruitment = input("> ")
    print("Confirmation:")
    print(f"Name: {name}")
    print(f"TGID: {tgid}")
    print(f"Secret Key: {tgsecretkey}")
    if isrecruitment == "R":
        isrecruitment = "Recruitment"
        print("Type: Recruitment")
    else:
        isrecruitment = "Non-Recruitment"
        print("Type: Non-Recruitment")
    print("")
    print("Is this correct? [Y/N]")
    choice = input("> ")
    if choice == "Y":
        telegram = {
            "name": name,
            "tgid": tgid,
            "tgsecretkey": tgsecretkey,
            "type": isrecruitment
        }
        with open(os.path.join(telegram_folder, name + ".yml"), 'w') as telegram_file:
            yaml.dump(telegram, telegram_file)
        print(f"Telegram {name} created.")
        logger.log(logging.INFO, f"Telegram {name} created.")
        configure_telegram_menu()
        return
    else:
        print("Telegram discarded.")
        logger.log(logging.INFO, "Telegram discarded.")
        configure_telegram_menu()
        return

# Configure Telegram - Delete
def delete_telegram():
    print("---------------------------------------------------------")
    print("Configure Telegram - Delete")
    print("Delete a Telegram.")
    print("")
    telegram_folder = os.path.join(PWD, "telegrams")
    if not os.path.exists(telegram_folder):
        os.makedirs(telegram_folder)
    for i in range(0,len(os.listdir(telegram_folder))):
        print(f"{i}. {os.listdir(telegram_folder)[i]}")
    choice = input("> ")
    try:
        name = os.listdir(telegram_folder)[int(choice)]
        os.remove(os.path.join(telegram_folder, name))
        print(f"Telegram {name} deleted.")
        logger.log(logging.INFO, f"Telegram {name} deleted.")
    except FileNotFoundError:
        print("File not found. Please try again.")
        logger.log(logging.DEBUG, "File not found.")
    except ValueError:
        print("Invalid choice. Please try again.")
        logger.log(logging.DEBUG, "Invalid choice.")
    except IndexError:
        print("No such Telegram exists. Please try again.")
        logger.log(logging.DEBUG, "Invalid choice.")
    except Exception as e:
        print(f"Somehow an error has occured({e}). Please try again.")
        logger.log(logging.DEBUG, e)
    finally:
        configure_telegram_menu()
        return

# Select Recepients - Menu
def select_recepients_menu():
    while True:
        print("---------------------------------------------------------")
        print("Select Recepients - Menu")
        print("[A]dd Recepients")
        print("[R]emove Recepients")
        print("[B]ack")
        print("")
        choice = input("> ")
        match choice:
            case "A":
                add_recepients()
                break
            case "R":
                remove_recepients()
                break
            case "B":
                main()
                return
            case _:
                print("Invalid choice. Please try again.")

# Select Recepients - Add
def add_recepients():
    print("---------------------------------------------------------")
    print("Select Recepients - Add")
    print("Toggle a group of recepient.")
    print("If the group runs out, the program will automatically add more of the same group.")
    print("")
    print("[F]ounding/Refounding")
    print("[E]jected")
    print("[I]ndividual Nation - Note: They will be messaged one time only.")
    print("[B]ack")
    print("")
    choice = input("> ")
    with open("config.yml", 'r') as ymlfile:
        config = yaml.safe_load(ymlfile)
    match choice:
        case "F":
            if not config["recruiting"]["flag_FoundingRefounding"]:
                config["recruiting"]["flag_FoundingRefounding"] = True
                logger.log(logging.INFO, "Founding/Refounding nations will be messaged.")
                print(GREEN + "Founding/Refounding nations will be messaged." + RESET)
            else:
                config["recruiting"]["flag_FoundingRefounding"] = False
                logger.log(logging.INFO, "Founding/Refounding nations will not be messaged.")
                print(YELLOW + "Founding/Refounding nations will not be messaged." + RESET)
        case "E":
            if not config["recruiting"]["flag_Ejected"]:
                config["recruiting"]["flag_Ejected"] = True
                logger.log(logging.INFO, "Ejected nations will be messaged.")
                print(GREEN + "Ejected nations will be messaged." + RESET)
            else:
                config["recruiting"]["flag_Ejected"] = False
                logger.log(logging.INFO, "Ejected nations will not be messaged.")
                print(YELLOW + "Ejected nations will not be messaged." + RESET)
        case "I":
            print("Enter the nation name.")
            nation = input("> ")
            try:
                config["recruiting"]["blocked_nations"].remove(nation)
            except ValueError:
                pass
            config["recruiting"]["individual_nations"].append(nation)
            logger.log(logging.INFO, f"{nation} will be messaged.")
            print(CYAN + f"{nation} will be messaged." + RESET)
        case "B":
            select_recepients_menu()
            return
        case _:
            print("Invalid choice. Please try again.")
    with open("config.yml", 'w') as ymlfile:
        yaml.dump(config, ymlfile)
    select_recepients_menu()
    return

# Select Recepients - Remove
def remove_recepients():
    print("---------------------------------------------------------")
    print("Select Recepients - Remove")
    print("Set a receipient to not be messaged.")
    print("")
    print("[I]ndividual Nation")
    print("[B]ack")
    print("")
    choice = input("> ")
    match choice:
        case "I":
            print("Enter the nation name.")
            nation = input("> ")
            try:
                config["recruiting"]["individual_nations"].remove(nation)
            except ValueError:
                pass
            config["recruiting"]["blocked_nations"].append(nation)
            logger.log(logging.INFO, f"{nation} will not be messaged.")
            print(YELLOW + f"{nation} will not be messaged." + RESET)
            with open("config.yml", 'w') as ymlfile:
                yaml.dump(config, ymlfile)
            select_recepients_menu()
            return
        case "B":
            select_recepients_menu()
            return
        case _:
            print("Invalid choice. Please try again.")
            select_recepients_menu()
            return

# Recruit
def recruit():
    print("---------------------------------------------------------")
    print("Recruit")
    print("Confirmation:")
    print(f"User: {config['clientname']}")
    print(f"Telegram: {telegram['name']}")
    print(f"Type: {telegram['type']}")
    print("")
    if config["recruiting"]["ratio"]["found"] > 0:
        print(GREEN + f"Founding nations will be messaged with {config['recruiting']['ratio']['found']*100}% probability." + RESET)
    else:
        print(RED + "Founding nations will not be messaged." + RESET)
    if config["recruiting"]["ratio"]["refound"] > 0:
        print(GREEN + f"Refounding nations will be messaged with {config['recruiting']['ratio']['refound']*100}% probability." + RESET)
    else:
        print(RED + "Refounding nations will not be messaged." + RESET)
    if config["recruiting"]["ratio"]["ejected"] > 0:
        print(GREEN + f"Ejected nations will be messaged with {config['recruiting']['ratio']['ejected']*100}% probability." + RESET)
    else:
        print(RED + "Ejected nations will not be messaged." + RESET)
    for nation in config["recruiting"]["individual_nations"]:
        print(CYAN + f"{nation} will be messaged." + RESET)
    for nation in config["recruiting"]["blocked_nations"]:
        print(YELLOW + f"{nation} will not be messaged." + RESET)
    if config["recruiting"]["optimization"]:
        print(GREEN + "Optimizations are enabled." + RESET)
    else:
        print(RED + "Optimizations are disabled." + RESET)
    print("")
    print("Is this correct? [Y/N]")
    choice = input("> ")
    if choice != "Y":
        print("Recruitment cancelled.")
        logger.log(logging.INFO, "Recruitment cancelled.")
        main()
        return
    else:
        print("Recruitment started.")
        logger.log(logging.INFO, "Recruitment started.")
    print("---------------------------------------------------------")
    # Get people to telegram -> send them telegram -> rinse and repeat
    print("Use Ctrl+C to stop recruitment.")
    try:
        while True:

            next_target = find_next_target()
            print(f"Next target: {next_target}")
            send_telegram(next_target)


    except KeyboardInterrupt:
        print(f"Recruitment stopped, found {tg_target} and sent {tg_amt} telegrams.")
        logger.log(logging.INFO, f"Recruitment stopped, found {tg_target} sent {tg_amt} telegrams..")
        return
    


# Find the next target which is not telegrammed to telegram
def find_next_target():
    global tg_target
    for nation in config["recruiting"]["individual_nations"]:
        if nation not in tg_sent_history:
            if nation not in config["recruiting"]["blocked_nations"]:
                if recruitment_optimizer(nation):
                    tg_target += 1
                    return nation
    options = ['founding', 'refounding', 'ejected']
    weight = [config["recruiting"]["ratio"]["found"], config["recruiting"]["ratio"]["refound"], config["recruiting"]["ratio"]["ejected"]]
    selected = random.choices(options, weights=weight, k=1)[0]
    if selected == "founding":
        time.sleep(0.1) # To prevent API spamming
        request = requests.get(f"https://www.nationstates.net/cgi-bin/api.cgi?q=happenings;filter=founding;limit=50", headers=REQUESTS_HEADER)
        if request.status_code == 200:
            world = ET.fromstring(request.text)
            happenings = world.find("HAPPENINGS")
            for event in happenings:
                text = event.find("TEXT").text
                nation = re.search(r"@@(.*)@@", text).group(1)
                action = re.search(r"@@ was (founded|refounded) in %%", text).group(1)
                if nation not in tg_sent_history and action == "founded":
                    if nation not in config["recruiting"]["blocked_nations"]:
                        if recruitment_optimizer(nation):
                            tg_target += 1
                            return nation
        elif request.status_code == 524:
            time.sleep(30)
            print("Unable to locate any new founding nations. You may try turning off Optimization. Waiting 30 seconds before trying again.")
            return find_next_target()
    elif selected == "refounding":
        time.sleep(0.1)
        request = requests.get(f"https://www.nationstates.net/cgi-bin/api.cgi?q=happenings;filter=founding;limit=50", headers=REQUESTS_HEADER)
        if request.status_code == 200:
            world = ET.fromstring(request.text)
            happenings = world.find("HAPPENINGS")
            for event in happenings:
                text = event.find("TEXT").text
                nation = re.search(r"@@(.*)@@", text).group(1)
                action = re.search(r"@@ was (founded|refounded) in %%", text).group(1)
                if nation not in tg_sent_history and action == "refounded":
                    if nation not in config["recruiting"]["blocked_nations"]:
                        if recruitment_optimizer(nation):
                            tg_target += 1
                            return nation
        elif request.status_code == 524:
            time.sleep(30)
            print("Unable to locate any new refounding nations. You may try turning off Optimization. Waiting 30 seconds before trying again.")
            return find_next_target()
    elif selected == "ejected":
        time.sleep(0.1) # To prevent API spamming
        request = requests.get(f"https://www.nationstates.net/cgi-bin/api.cgi?q=happenings;filter=eject;limit=50", headers=REQUESTS_HEADER)
        if request.status_code == 200:
            world = ET.fromstring(request.text)
            happenings = world.find("HAPPENINGS")
            for event in happenings:
                text = event.find("TEXT").text
                nation = re.search(r"@@(.+?)@@", text).group(1)
                if nation not in tg_sent_history:
                    if nation not in config["recruiting"]["blocked_nations"]:
                        if recruitment_optimizer(nation):
                            tg_target += 1
                            return nation
        elif request.status_code == 524:
            time.sleep(30)
            print("Unable to locate any new ejected nations. You may try turning off Optimization. Waiting 30 seconds before trying again.")
            return find_next_target()

# Send Telegram
def send_telegram(telegram_target):
    global tg_amt
    current_target = telegram_target
    try:
        request = requests.get(f"https://www.nationstates.net/cgi-bin/api.cgi?a=sendTG&client={config['clientkey']}&tgid={telegram['tgid']}&key={telegram['tgsecretkey']}&to={current_target}", headers=REQUESTS_HEADER)
        print(f"Sent telegram to {current_target}, got {request.status_code}.")
        if request.status_code == 429:
            wait_time = int(request.headers["Retry-After"])
            print(f"We are being rate limited, waiting {wait_time} seconds before trying again.")
            time.sleep(wait_time)
            return send_telegram(current_target)
        logger.log(logging.INFO, f"Sent telegram to {current_target}, got {request.status_code}.")
    except Exception as e:
        print(f"Tried to send telegram to {current_target}, but got error: {e}")
        logger.log(logging.ERROR, f"Tried to send telegram to {current_target}, but got error: {e}")
    finally:
        tg_amt += 1
        tg_sent_history.append(current_target)
        if telegram["type"] == "Recruitment":
            time.sleep(RECRUITMENT_TELEGRAM_RATELIMIT)
        else:
            time.sleep(NONRECRUITMENT_TELEGRAM_RATELIMIT)

# Cleanse the nation given filters - if they fail the filters they will not be recruited
# True means go on to recruit, False means do not recruit and try another
def recruitment_optimizer(nation):
    if not config['recruiting']['optimization']:
        return True
    else:
        if isBadName(nation):
            print(f"{nation} is a bad name, skipping.")
            logger.log(logging.DEBUG, f"{nation} is a bad name, skipping.")
            return False
        if isPuppet(nation):
            print(f"{nation} is probably a puppet, skipping.")
            logger.log(logging.DEBUG, f"{nation} is probably a puppet, skipping.")
            return False
        if cannotRecruit(nation):
            print(f"{nation} cannot be recruited, skipping.")
            logger.log(logging.DEBUG, f"{nation} cannot be recruited, skipping.")
            return False
        return True

# Return true if a nation name contains bad words - likely to get No Such Nation errors and waste 180 seconds
def isBadName(nation):
    if re.search(r"(moderator|reichs|nuts|pedo)", nation, flags=re.IGNORECASE):
        return True
    else:
        return False

# Return True if a nation name likely means it is a puppet - likely to get ignored
def isPuppet(nation):
    if re.search(r"(puppet|bot|farm|card|founder)", nation, flags=re.IGNORECASE):
        return True
    if re.search(r"[0-9]+", nation):
        return True
    match = re.finditer(r"\bM{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})\b", nation, flags=re.IGNORECASE)
    for m in match:
        if m.group() != "":
            return True #bodging roman numeral checker, as it likes to match empty strings
    return False

# Return True if a nation cannot be recruited
def cannotRecruit(nation):
    try:
        request = requests.get(f"https://www.nationstates.net/cgi-bin/api.cgi?nation={nation}&q=tgcanrecruit", headers=REQUESTS_HEADER)
        if request.status_code == 200:
            nation = ET.fromstring(request.text)
            canrecruit = nation.find("TGCANRECRUIT").text
            if canrecruit == "1":
                return False
            else:
                return True
        else:
            return True
    except:
        return True

def main():
    global logger
    logger = Logger()
    load_config()
    logger.log(logging.INFO, "Python Process online.")
    display()

    match choice:
        case "T":
            configure_telegram_menu()
        case "S":
            select_recepients_menu()
        case "R":
            recruit()
        case "Q":
            print("Quitting...")
            Logger.log(logging.DEBUG, "Program terminated by user.")
            exit()
        case _:
            print("Invalid choice. Please try again.")
            main()

if __name__ == "__main__": 
    main()