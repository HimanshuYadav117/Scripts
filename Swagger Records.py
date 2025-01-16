import datetime
import shutil
import os
import json
import sys

DEFAULT_CONFIG = {
        "permanent_backup_location": r"C:\Backup\DataSwaggerRecords.txt",
        "permanent_log_location_dir": r"C:\Backup\log_SwaggerRecords.pkl"
    }

CONFIG_FILE = "config.json"
PWD_MainData = "./DataSwaggerRecords.txt"  # Temporary backup in the current directory
PWD_LOG = "./log_SwaggerRecords.pkl"  # Temporary log file in the current directory
#############################################################

def sync_backups():
    try:
        # Paths to current files
        pwd_main_data = PWD_MainData
        pwd_log = PWD_LOG
        
        # Paths to permanent backup files
        perm_main_data = DEFAULT_CONFIG["permanent_backup_location"]
        perm_log = DEFAULT_CONFIG["permanent_log_location_dir"]

        # Check if current and permanent main data files exist
        if not os.path.exists(pwd_main_data):
            print("Current main data file does not exist.")
            return

        if not os.path.exists(perm_main_data):
            inpt = input("Current main data file does not exist. do you wish to copy this current updated file to permenant backup?Y/N").strip().upper()
            if inpt == 'Y': 
                shutil.copy(pwd_main_data, perm_main_data)  
            else:
                return
        if not os.path.exists(perm_log):

            print("permenant log file does not exist. Log syncing up from current to permenant.")
            shutil.copy(pwd_log, perm_log)

        # Read both main data files
        with open(pwd_main_data, "r") as current_file, open(perm_main_data, "r") as backup_file:
            current_data = current_file.readlines()
            backup_data = backup_file.readlines()

        # Display the difference between the two files
        print("Differences between current main data and permanent backup:")
        diff = [line for line in current_data if line not in backup_data]
        for i, line in enumerate(diff, 1):
            print(f"{i}. {line.strip()}")

        if not diff:
            print("No differences found. Backups are already synced.")
            return

        # Ask the user for confirmation
        user_input = input("Do you want to make these changes permanent? [Y/N]: ").strip().upper()
        if user_input != "Y":
            print("Sync operation aborted.")
            return

        # Overwrite the permanent backup files
        shutil.copy(pwd_main_data, perm_main_data)
        print(f"Main data file synced to {perm_main_data}.")
        shutil.copy(pwd_log, perm_log)
        print(f"Log file synced to {perm_log}.")

 

    except PermissionError:
        print("Permission error occurred during the sync process.")
    except FileNotFoundError as e:
        print(f"File not found: {e}")
    except IOError as e:
        print(f"Error reading or writing files: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def change_backup_location(new_directory):
    try:
        # Ensure the new directory exists and is writable
        if not os.path.isdir(new_directory):
            print("The specified directory does not exist.")
            return

        if not os.access(new_directory, os.W_OK):
            print("You do not have write access to the specified directory.")
            return

        # Check if both files exist
        current_backup_location = DEFAULT_CONFIG["permanent_backup_location"]
        current_log_location = DEFAULT_CONFIG["permanent_log_location_dir"]

        if not os.path.exists(current_backup_location):
            print(f"Backup file not found at {current_backup_location}. Operation aborted.")
            return

        if not os.path.exists(current_log_location):
            print(f"Log file not found at {current_log_location}. Operation aborted.")
            return

        # Define new file locations
        new_backup_location = os.path.join(new_directory, os.path.basename(current_backup_location))
        new_log_location = os.path.join(new_directory, os.path.basename(current_log_location))

        # Move the files to the new directory
        shutil.move(current_backup_location, new_backup_location)
        shutil.move(current_log_location, new_log_location)

        print(f"Backup file moved to {new_backup_location}.")
        print(f"Log file moved to {new_log_location}.")

        # Update DEFAULT_CONFIG with the new locations
        DEFAULT_CONFIG["permanent_backup_location"] = new_backup_location
        DEFAULT_CONFIG["permanent_log_location_dir"] = new_log_location

        # Save the updated paths to the config file
        with open(CONFIG_FILE, "r") as file:
            config_data = json.load(file)

        config_data["permanent_backup_location"] = new_backup_location
        config_data["permanent_log_location_dir"] = new_log_location

        with open(CONFIG_FILE, "w") as file:
            json.dump(config_data, file, indent=4)

        print("Configuration updated successfully.")

    except PermissionError:
        print("Permission error occurred while moving the files.")
    except json.JSONDecodeError:
        print("Configuration file is corrupted or unreadable.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def load_data():
    data = {}
    try:
        # Check if the current main data file exists
        if os.path.exists(PWD_MainData):
            with open(PWD_MainData, 'r') as f:
                lines = f.readlines()
                for line in lines:
                    try:
                        if ":" in line:
                            api_name, entry_data = line.split(":", 1)
                            api_name = api_name.strip()
                            entry_data = entry_data.strip()

                            if api_name not in data:
                                data[api_name] = []
                            data[api_name].append(entry_data)
                    except ValueError:
                        print(f"Skipping malformed line: {line.strip()}")
            return data
        else:
            print(f"Warning: {PWD_MainData} not found.")

            # Check if the permanent main data file exists
            perm_main_data = DEFAULT_CONFIG["permanent_backup_location"]
            if os.path.exists(perm_main_data):
                user_input = input(f"Permanent main data file found at {perm_main_data}. Do you want to copy it to {PWD_MainData}? [Y/N]: ").strip().upper()
                if user_input == "Y":
                    shutil.copy(perm_main_data, PWD_MainData)
                    print(f"Copied permanent main data file to {PWD_MainData}.")
                    # Retry loading data after copying
                    return load_data()
                else:
                    print("Starting with an empty dataset. ")
            else:
                print("No permanent backup file found. Starting with an empty dataset. ")
            return data
    except IOError as e:
        print(f"Error loading data from {PWD_MainData}: {e}")
        return data
    except Exception as e:
        print(f"An unexpected error occurred while loading data: {e}")
        return data

def display_entries(service_name, data):
    try:
        if service_name in data:
            print(f"Entries for {service_name}:")
            for entry in data[service_name]:
                print(entry)
        else:
            print(f"No entries found for API: {service_name}")
    except KeyError as e:
        print(f"Error: Service {service_name} not found in data: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while displaying entries: {e}")

def delete_entry(data, api_name):
    try:
        if api_name in data and data[api_name]:
            recent_entry = data[api_name][0]
            timestamp, dev_name = recent_entry.split(", ", 1)
            confirmation = input(
                f"Do you really want to delete the most recent entry for {api_name} associated with {dev_name}? [Y/N] "
            ).strip().upper()

            if confirmation == "Y":
                data[api_name].pop(0)
                print(f"Successfully deleted the most recent entry for {api_name} associated with {dev_name}.")
                if not data[api_name]:
                    del data[api_name]
                save_data(data)
            else:
                print("Deletion cancelled by user.")
        else:
            print(f"No entries found for API: {api_name}")
    except Exception as e:
        print(f"An error occurred while deleting the entry: {e}")

def save_data(data):
    try:
        # Check if the main data file exists
        if os.path.exists(PWD_MainData):
            with open(PWD_MainData, 'w') as f:
                for api_name, entries in data.items():
                    for entry in entries:
                        f.write(f"{api_name}: {entry}\n")
            print(f"Data saved successfully to {PWD_MainData}")
        else:
            # Main data file doesn't exist, check the backup location from the config
            backup_location = DEFAULT_CONFIG.get("permanent_backup_location")
            if backup_location and os.path.exists(backup_location):
                print(f"Main file not found, loading backup from {backup_location}")
                shutil.copy(backup_location, PWD_MainData)
                print(f"Backup loaded and saved as {PWD_MainData}")
                save_data(data)  # Recursively save data after loading backup
            else:
                # If no backup, create a new file in the current directory
                print(f"{PWD_MainData} and backup location not found. Creating a new file.")
                with open(PWD_MainData, 'w') as f:
                    for api_name, entries in data.items():
                        for entry in entries:
                            f.write(f"{api_name}: {entry}\n")
                print(f"New file created and data saved to {PWD_MainData}")
    except IOError as e:
        print(f"Error saving data: {e}")
    except FileNotFoundError as e:
        print(f"File not found error: {e}")
    except PermissionError as e:
        print(f"Permission error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

def add_log_entry(entry1, entry2, log_file=PWD_LOG):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}]: {entry1} --> {entry2}\n"
    existing_logs = []
    if os.path.exists(log_file):
        with open(log_file, "r") as file:
            existing_logs = file.readlines()
    with open(log_file, "w") as file:
        file.write(log_entry)
        file.writelines(existing_logs)

def add_entry(data, api_name, developer_name):

    try:
        if not api_name or not developer_name:
            raise ValueError("API name and developer name cannot be empty")

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_entry = f"{timestamp}, {developer_name}"
        
        if api_name not in data:
            data[api_name] = []
        
        data[api_name].insert(0, new_entry)  # Insert at the beginning to keep recent entries first
        print(f"New entry added: {api_name} assigned to {developer_name}")
        
        save_data(data)
    except ValueError as e:
        print(f"Input Error: {e}")
    except Exception as e:
        print(f"Error adding entry: {e}")


def display_plain_logs(log_file=PWD_LOG):
    if not os.path.exists(log_file):
        print("No logs available.")
        print("trying to load the log file through permenant Logs")

        try:
            if "permanent_log_location_dir" not in DEFAULT_CONFIG:
                print(f"Error: Permenant Log file location Config key does not exist in CONFIG File.")
                return
            shutil.copy(DEFAULT_CONFIG.get('permanent_log_location_dir'), PWD_LOG)
            print(f"File copied successfully to {PWD_LOG}")
        except FileNotFoundError:
            print("Source file not found.") 
            return
        except PermissionError:
            print("Permission denied while copying the file.")
            return 
        except Exception as e:
            print(f"An error occurred: {e}")
            return
        

    with open(log_file, "r") as file:
        logs = file.readlines()
    print("=== Top Logs ===")
    for i, log in enumerate(logs[:10]):
        print(f"{i + 1}: {log.strip()}")


def load_config():

    if not os.path.exists(CONFIG_FILE):
        create_default_config()
        raise FileNotFoundError(f"Configuration file '{CONFIG_FILE}' not found. A default config has been created.")
    
    with open(CONFIG_FILE, "r") as file:
        try:
            return json.load(file)
        except json.JSONDecodeError:
            raise ValueError(f"Configuration file '{CONFIG_FILE}' is corrupted. Please fix or delete it.")
def create_default_config():

    with open(CONFIG_FILE, "w") as file:
        json.dump(DEFAULT_CONFIG, file, indent=4)


def main():
    load_config()
    MainData = load_data()
    
    print("\n+++ Welcome to Swagger Records V 1.0 +++ \n")
    MainFlag = True
    while MainFlag:
        print(" 1. Add Record \n 2. Fetch Records Menu \n 3. Delete Recent assigned Entry \n 4.Backup Menu\n 5. Save and Exit")
        choice = input("Enter choice: ")
        os.system('cls')
        
        if choice == "1":       #Adding a Record as API_NAME as Key : and its enteries/updation value with assigned dev name as Value
            os.system('cls')

            loopvalue = input("enter the number of records you want to add: ")
            dragger = int(loopvalue)
            if(dragger<=10 and dragger>=0):
                for i in range(0,dragger):
                    DevName=input("Add the developers Name:  ").strip()
                    SwaggerApiName = input("Add the API Name:  ").strip()

                    if not DevName or not SwaggerApiName:
                        print("One of the two entries is invalid or empty ")
                        temp = input("\nDo you wish to continue? [Y/N]: ").strip().upper()
                        if temp != 'Y':
                            MainFlag = False
                            continue
                        
                    #############################################################

                    add_entry(MainData, SwaggerApiName, DevName)           

                    #############################################################
                    add_log_entry(DevName,SwaggerApiName)
                    print("Record was Updated Successfully! ")
            else:
                print("more than 10 enteries are not allowed simultaniously")
            
            
            temp = input("\n do you wish to continue?[Y/N]: ").strip().upper()
            if temp == 'Y':
                os.system('cls')
            else:
                MainFlag = False
            #os.system('cls')
        elif choice == "2": #Fetching Records based on 1. Latest 10 enteries , 2. Particular API NAME Records
            os.system('cls')
            fetchflag = 'Y'
            while fetchflag == 'Y':
                print("Kindly select your choice")
                print(" 1. Fetch all log enteries  \n 2. Fetch Particular Record using Service Name \n 3. Exit ")
                fetchChoice = input()
                os.system('cls')
            
                if fetchChoice == "1":
                    os.system('cls')
                    print("entries are [Log enteries are permenant once assigned]: ")
                    #print latest 10 enteries stored in a different backup document
                    #############################################################
                    display_plain_logs()
                    #############################################################

                    fetchflag = input("\n do you wish to continue?[Y/N]: ").strip().upper()
                    os.system('cls') 
                    
                elif fetchChoice == "2":
                    os.system('cls')
                    ServiceName=input("Enter the Service Name:  ")
                    #print specific service list 
                    #############################################################
                
                    display_entries(ServiceName,MainData)
                    #############################################################
                    fetchflag = input("\n do you wish to continue?[Y/N]:  ").strip().upper()
                    os.system('cls')
                
                else:
                    break           

        elif choice == "3":
            os.system('cls')
            ServiceName=input("Enter the Service Name:  ")
                    #print specific service list 
                    #############################################################
            delete_entry(MainData,ServiceName)
                    #############################################################

           
            fetchflag = input("\n do you wish to continue?[Y/N]: ").strip().upper()


            
        elif choice == "4":
            os.system('cls')
            
            backupflag = 'Y'
            
            while backupflag == 'Y':
                os.system('cls')
                print("Kindly select your choice")
                BackupChoice = input("1. Display Permenant Backup file Location \n  2. Force Sync backup , Save & Exit \n")
 
            
                if BackupChoice == "1":
                    print("The Current permenant Backup Location is:  ")
                    #print backup file path 
                    print("MainData backup location: " + DEFAULT_CONFIG.get("permanent_backup_location"))
                    print("LogFile backup location: " + DEFAULT_CONFIG.get("permanent_log_location_dir"))

                    backupflag = input("\n do you wish to continue?[Y/N]:  ").strip().upper()
        

                elif BackupChoice == "2":

                    print("\n*****Saving and syncing backups*****")
                    sync_backups()
                    backupflag = input("\n do you wish to continue?[Y/N]:  ").strip().upper()
          
                else:

                    backupflag = input("\n Wrong Choice... Do you wish to retry? Y/N?:  ").strip().upper()
              
            
        
        
        elif choice == "5":
            os.system('cls')
            print("*****Saving*****!")
            print("*****Backing Up*****")
            #############################################################
            sync_backups()
            #############################################################SYNC BACKUPS
            print("*****Exiting*****!")

            break
        else:
            tempflag = input("Invalid choice! Try again.?[Y/N]:  ").strip().upper()
            if tempflag != 'Y':
                break

if __name__ == "__main__":
    main()
