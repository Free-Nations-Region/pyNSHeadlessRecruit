#!/usr/bin/python3 -u
#    headlessNSPythonRecruiter
#    A headless Python3 script to automate sending API request to NationStates API to recruit nations.
#    By Clarissa Au @ clarissayuenyee@gmail.com
#    Under GNU GPL v3.0 License
#    Copyright (C) 2023 Clarissa Au
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
import sys
import os
import logging
import time
import xml.etree.ElementTree as ET
import re
import random
import requests
import yaml

# Global Constants
VERSION = "0.0.2"
USERAGENT = "headlessNSPythonRecruiter/" + VERSION + " (by Clarissa Au)"
REQUESTS_HEADER = {"User-Agent": USERAGENT}
PWD = os.getcwd()
RECRUITMENT_TELEGRAM_RATELIMIT = 180 # 3 minutes
NONRECRUITMENT_TELEGRAM_RATELIMIT = 30 # 30 seconds
REQ_TIMEOUT = 5 # 5 seconds

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


# Global Variables
choice = None
logger = None
telegram = None
tg_target = 0
tg_amt = 0
tg_sent_history = [] # List of nations that have been sent telegram, will not be sent telegram until program restarts

# GNU GPL v3.0 Boilerplates
class GNU_GPL_v3_class():

    """GNU GPL v3.0 Boilerplates - combined because they are short"""

    def boilerplate(self):

        """Prints the GNU GPL v3.0 boilerplate"""

        print("Copyright (C) 2023 Clarissa Au")
        print("This program comes with ABSOLUTELY NO WARRANTY; for details type '[L]icense'.")
        print("This is free software, and you are welcome to redistribute it")
        print("under certain conditions; type '[W]arranty' for details.")

    def license(self):

        """Prints the GNU GPL v3.0 License"""

        with open("LICENSE", 'r', encoding="utf-8") as license_file:
            print(license_file.read())

    def warranty(self):

        """Prints the GNU GPL v3.0 Warranty"""

        print("BECAUSE THE PROGRAM IS LICENSED FREE OF CHARGE, THERE IS NO WARRANTY ")
        print("FOR THE PROGRAM, TO THE EXTENT PERMITTED BY APPLICABLE LAW.  EXCEPT WHEN ")
        print("OTHERWISE STATED IN WRITING THE COPYRIGHT HOLDERS AND/OR OTHER PARTIES ")
        print("PROVIDE THE PROGRAM \"AS IS\" WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESSED ")
        print("OR IMPLIED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF ")
        print("MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.  THE ENTIRE RISK AS ")
        print("TO THE QUALITY AND PERFORMANCE OF THE PROGRAM IS WITH YOU.  SHOULD THE ")
        print("PROGRAM PROVE DEFECTIVE, YOU ASSUME THE COST OF ALL NECESSARY SERVICING, ")
        print("REPAIR OR CORRECTION.")

# Quickstarting Recruitment
def quickstart():

    """Quickstart Recruitment from quickstart.yml"""

    global quickstart_config
    global telegram
    try:
        with open("quickstart.yml", 'r', encoding="utf-8") as ymlfile:
            quickstart_config = yaml.safe_load(ymlfile)
    except FileNotFoundError:
        default_quickstart_config = {
            "use_quickstart": False,
            "target_telegram_file": "recruitment.yml",
            "skip_confirmation" : False,
        }
        with open("quickstart.yml", 'w', encoding="utf-8") as ymlfile:
            yaml.dump(default_quickstart_config, ymlfile)
        quickstart_config = None
    if quickstart_config is not None:
        if quickstart_config["use_quickstart"]:
            print("---------------------------------------------------------")
            print("Python Process online.")
            print("Quickstart Enabled.")
            with open(
                os.path.join(PWD, "telegrams", quickstart_config["target_telegram_file"])
                , 'r'
                , encoding="utf-8"
                ) as telegram_file:
                telegram = yaml.safe_load(telegram_file)
            if quickstart_config["skip_confirmation"]:
                recruitment_loop()
            else:
                recruit()
            return True
    return False

# Load config file if it exists
def load_config():

    """Load config.yml"""

    global config
    try:
        with open("config.yml", 'r', encoding="utf-8") as ymlfile:
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
        with open("config.yml", 'w', encoding="utf-8") as ymlfile:
            yaml.dump(default_config, ymlfile)
        print(RED
              + "Config file not found. A new config file has been created."
              + "Please edit the config file and restart the program."
              + RESET)
        sys.exit()
    finally:
        logging.debug("Config file loaded.")

# Logger
class Logger():

    """Logger class to log messages to log file and display them to the user"""

    def __init__(self):

        """Initialize Logger"""

        self.storage = []
        logging.basicConfig(
            filename='headlessNSPythonRecruiter.log',
            level=logging.DEBUG,
            format='%(asctime)s %(levelname)s %(message)s')
        logging.debug("headlessNSPythonRecruiter v" + VERSION + " by Clarissa Au")
        logging.debug("Licensed under GNU GPL v3.0 License")
        logging.debug("Logging Initialized.")

    def display(self, level, amount):

        """Display logs to user"""

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

        """Log message to log file and display to user"""

        self.storage.append(Log(level, message))


class Log():

    """Log class to store log messages"""

    def __init__(self, level, message):

        """Initialize a Log"""

        self.message = message
        self.level = level
        logging.log(level, message)


# Display main menu
def display():

    """Display main menu"""

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

    """Configure Telegram Menu"""

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

    """Select Telegram Menu"""

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
        with open(
            os.path.join(
                telegram_folder, os.listdir(telegram_folder)[int(choice)]), 'r', encoding="utf-8"
            ) as telegram_file:
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

    """Create Telegram Menu"""

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
        with open(os.path.join(telegram_folder, name + ".yml"), 'w', encoding="utf-8") as telegram_file:
            yaml.dump(telegram, telegram_file)
        print(f"Telegram {name} created.")
        logger.log(logging.INFO, f"Telegram {name} created.")
        configure_telegram_menu()
        return
    print("Telegram discarded.")
    logger.log(logging.INFO, "Telegram discarded.")
    configure_telegram_menu()
    return

# Configure Telegram - Delete
def delete_telegram():

    """Delete Telegram Menu"""

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

    """Select Recepients Menu"""

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

    """Add Recepients Menu"""

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
    with open("config.yml", 'r', encoding="utf-8") as ymlfile:
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
    with open("config.yml", 'w', encoding="utf-8") as ymlfile:
        yaml.dump(config, ymlfile)
    select_recepients_menu()
    return

# Select Recepients - Remove
def remove_recepients():

    """Remove Recepients Menu"""

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
            with open("config.yml", 'w', encoding="utf-8") as ymlfile:
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

    """Recruiting"""

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
    recruitment_loop()

def recruitment_loop():

    """Recruitment Loop"""

    while True:
        next_target = find_next_target()
        print(f"Next target: {next_target}")
        send_telegram(next_target)

# Find the next target which is not telegrammed to telegram
def find_next_target():

    """Probablistically find the next target which is not telegrammed to telegram"""

    global tg_target
    for nation in config["recruiting"]["individual_nations"]:
        if nation not in tg_sent_history:
            if nation not in config["recruiting"]["blocked_nations"]:
                tg_target += 1
                return nation
    options = ['founding', 'refounding', 'ejected']
    weight = [config["recruiting"]["ratio"]["found"], config["recruiting"]["ratio"]["refound"], config["recruiting"]["ratio"]["ejected"]]
    selected = random.choices(options, weights=weight, k=1)[0]
    if selected == "founding":
        time.sleep(0.1) # To prevent API spamming
        request = requests.get("https://www.nationstates.net/cgi-bin/api.cgi?q=happenings;filter=founding;limit=50", headers=REQUESTS_HEADER, timeout=REQ_TIMEOUT)
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
                        else:
                            tg_sent_history.append(nation) #no need to check this nation again
        elif request.status_code == 524:
            time.sleep(30)
            print("Unable to locate any new founding nations. You may try turning off Optimization. Waiting 30 seconds before trying again.")
            return find_next_target()
    elif selected == "refounding":
        time.sleep(0.1)
        request = requests.get("https://www.nationstates.net/cgi-bin/api.cgi?q=happenings;filter=founding;limit=50", headers=REQUESTS_HEADER, timeout=REQ_TIMEOUT)
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
                        else:
                            tg_sent_history.append(nation) #no need to check this nation again
        elif request.status_code == 524:
            time.sleep(30)
            print("Unable to locate any new refounding nations. You may try turning off Optimization. Waiting 30 seconds before trying again.")
            return find_next_target()
    elif selected == "ejected":
        time.sleep(0.1) # To prevent API spamming
        request = requests.get("https://www.nationstates.net/cgi-bin/api.cgi?q=happenings;filter=eject;limit=50", headers=REQUESTS_HEADER, timeout=REQ_TIMEOUT)
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
                        else:
                            tg_sent_history.append(nation) #no need to check this nation again
        elif request.status_code == 524:
            time.sleep(30)
            print("Unable to locate any new ejected nations. You may try turning off Optimization. Waiting 30 seconds before trying again.")
            return find_next_target()

# Send Telegram
def send_telegram(telegram_target):

    """Send Telegram to a nation"""

    global tg_amt
    current_target = telegram_target
    try:
        request = requests.get(
            f"https://www.nationstates.net/cgi-bin/api.cgi?a=sendTG&client={config['clientkey']}&tgid={telegram['tgid']}&key={telegram['tgsecretkey']}&to={current_target}", 
            headers=REQUESTS_HEADER,
            timeout=REQ_TIMEOUT)
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

    """Optimize Recruitment"""

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
        if nation is None:
            print(f"One does not simply recruit from None, skipping.")
            logger.log(logging.DEBUG, f"One does not simply recruit from None, skipping.")
            time.sleep(30)
            return False
        return True

# Return true if a nation name contains bad words - likely to get No Such Nation errors and waste 180 seconds
def isBadName(nation):

    """Check if a nation name contains bad words"""

    if re.search(r"(moderator|reichs|pedo|\btos\b)", nation, flags=re.IGNORECASE):
        return True
    else:
        return False

# Return True if a nation name likely means it is a puppet - likely to get ignored
def isPuppet(nation):

    """Check if a nation name likely means it is a puppet"""

    if re.search(r"(puppet|bot|farm|card|founder|throwaway)", nation, flags=re.IGNORECASE):
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

    """Check if a nation cannot be recruited"""

    try:
        request = requests.get(f"https://www.nationstates.net/cgi-bin/api.cgi?nation={nation}&q=tgcanrecruit", headers=REQUESTS_HEADER, timeout=REQ_TIMEOUT)
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

    """Main Logic Loop"""

    global logger
    global GNU_GPL_v3
    GNU_GPL_v3 = GNU_GPL_v3_class()
    logger = Logger()
    load_config()
    quickstarts = quickstart()
    if not quickstarts:
        logger.log(logging.INFO, "Python Process online.")
        GNU_GPL_v3.boilerplate()
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
                logger.log(logging.DEBUG, "Program terminated by user.")
                exit()
            case "L":
                GNU_GPL_v3.license()
                main()
            case "W":
                GNU_GPL_v3.warranty()
                main()
            case _:
                print("Invalid choice. Please try again.")
                main()

if __name__ == "__main__":
    main()
