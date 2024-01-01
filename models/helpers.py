import pickle
import os
import datetime

import pandas as pd
import hashlib

# Get the current working directory
cwd = os.getcwd()


def create_hash(df)->str:
    # create a sample dataframe
    df = pd.DataFrame({'A': [1, 2, 3], 'B': ['a', 'b', 'c']})

    # convert the dataframe to a string representation
    df_str = df.to_string(index=False)

    # create a SHA256 hash object
    hash_object = hashlib.sha256(df_str.encode())

    # get the hexdigest of the hash
    hash_value = hash_object.hexdigest()

    print("DataFrame hash value:", hash_value)
    return hash_value


class PickleObject:
    def __init__(self, pkl_loc= cwd+r'/data/raw/processed', pkl_name=__name__+datetime.date.today().strftime('%Y-%m-%d'), max_age_days=10, calcdate = datetime.date.today()):
        '''A class for saving and loading objects to and from a pickle file.
        
        Parameters
        ----------
        pkl_loc : str
            The location of the pickle file.
        pkl_name : str
            The name of the pickle file.
            max_age_days : int, optional
            The maximum age of the pickle file in days. If the pickle file is older than this, it will be deleted.
            If None, the pickle file will not be deleted. The default is None.
        max_age_days : int, optional
            The maximum age of the pickle file in days. If the pickle file is older than this, it will be deleted.
        calcdate : datetime.date, optional
            The date of the calculation. The default is datetime.date.today().

        Attributes
                ----------
        date : datetime.date
            The date of the calculation.
        max_age_days : int  
            The maximum age of the pickle file in days. If the pickle file is older than this, it will be deleted.
        data : object
            The object to be saved to the pickle file.
        status : str
            The status of the pickle file. This can be used to indicate if the data is up to date or at a specific point in the process.
            Stored as a string to allow for future expansion, in position 1 of the tuple returned by the save_to_pickle() function.
            ie (data, status)
        Returns
        -------
        None.

        Functions
        ---------
        save_to_pickle(data)
            Save an object to a pickle file.
        load_from_pickle()
            Load an object from a pickle file.
        remove_pickle()
            Remove the pickle file.
        '''
        self.date = calcdate
        self.max_age_days = max_age_days
        self.data = None
        self.status = None

        file_name = pkl_loc + "/" +  pkl_name
        self.pkl_loc = pkl_loc
        self.pkl_name = pkl_name
        self.file_name = file_name
        
        # If the file already exists and has a maximum age specified,
        # check if the file is older than the specified age. If it is, delete it.
        if max_age_days is not None and os.path.exists(file_name):
            file_age_days = (datetime.datetime.now() - datetime.datetime.fromtimestamp(os.path.getmtime(file_name))).days
            if file_age_days > max_age_days:
                os.remove(file_name)

        pick = self.get_pickle_status()
        if pick[0] > 0:
            self.data = pick[1][0] if isinstance(pick[1], tuple) else pick[1]
            self.status = pick[1][1] if isinstance(pick[1], tuple) else 'Loaded without status'
        elif pick[0] == 0:
            self.data = None
            self.status = "No data found"

        self.delete_old_pickles()

        
    def save_to_pickle(self, data):
        '''Save an object to a pickle file.
        
        Parameters
        ----------
        Save as tuple (data, status) to allow for future expansion
        data : object
            The object to save to the pickle file.
        status : str, optional
            The status of the pickle file. This can be used to indicate if the data is up to date or at a specific point in the process.
            
        Returns
        -------
        None.'''
        with open(self.file_name, 'wb') as f:
            pickle.dump(data, f)
        if isinstance(data, tuple):
            self.data = data[0]
            self.status = data[1]
        else:
            self.data = data
            self.status = "Saved without status"
    
    def save(self, data):
        self.save_to_pickle(data)

    def append_to_pickle(self, data):
        '''Append an object to a pickle file.
        
        Parameters
        ----------
        data : object
            The object to append to the pickle file.
            
        Returns
        -------
        None.'''
        with open(self.file_name, 'ab') as f:
            pickle.dump(data, f)
    
    def load_from_pickle(self):
        '''Load an object from a pickle file.
        
        Parameters
        ----------
        None.
        
        Returns
        -------
        object
            The object loaded from the pickle file.
        '''
        try:
            with open(self.file_name, 'rb') as f:
                return pickle.load(f)
        except EOFError:
            print(f'EOFError: {self.file_name} is empty. Removing File.')
            self.remove_pickle()
            return None
    
    def remove_pickle(self):
        '''Remove the pickle file.
        
        Parameters
        ----------
        None.
        
        Returns
        -------
        None.'''
        if os.path.exists(self.file_name):
            os.remove(self.file_name)
            self.status = "No data found"

    
    def get_pickle_status(self):
        if os.path.exists(self.file_name):
            data = self.load_from_pickle()
            if isinstance(data,pd.DataFrame) and not data.empty() or not isinstance(data,pd.DataFrame) and data is not None:
                return (len(data), data)
            else:
                return (0, None)
        else:
            return (0, None)

    def delete_old_pickles(self):
        """Delete old pickle files.
        
        Parameters
        ----------
        None.
        
        Returns
        -------
        None."""
        for file in os.listdir(path=self.pkl_loc):
            if file.endswith(".pickle") or file.endswith(".pkl"):
                file = self.pkl_loc+ "/" + file
                file_age_days = (datetime.datetime.now() - datetime.datetime.fromtimestamp(os.path.getmtime(file))).days
                if file_age_days > self.max_age_days:
                    os.remove(file)

def divide_cusip(cusip: str) -> dict:
    """
    Divides a CUSIP into its different subcategories.
    
    Parameters:
    cusip (str): The CUSIP to be divided.
    
    Returns:
    dict: A dictionary containing the different subcategories of the CUSIP.
    """
    # Get the base and issuer code.
    base = cusip[:6]
    issuer_code = cusip[6:9] 
    
    # Determine if the issuer code is reserved for internal use.
    if issuer_code.isdigit():
        if 990 <= int(issuer_code) <= 999:
            issuer_type = "Internal Use (990-999)"
        else:
            issuer_type = "Other Internal Use"
    elif issuer_code.isalpha():
        if "99A" <= issuer_code <= "99Z":
            issuer_type = "Internal Use (99A-99Z)"
        else:
            issuer_type = "Other Internal Use"
    else:
        issuer_type = "Unknown"
    
    # Determine the issue type.
    issue_type = cusip[7]
    if issue_type.isdigit():
        issue_type = "Equity"
    elif issue_type.isalpha():
        issue_type = "Fixed Income"
    else:
        issue_type = "Unknown"
    
    # Determine the issue number.
    issue_number = cusip[8]
    if issue_type == "Equity":
        if issue_number == "0":
            issue_number = "Initial Issue (10)"
        elif "1" <= issue_number <= "8":
            issue_number = f"New Issue ({int(issue_number)*10})"
        elif issue_number == "9":
            issue_number = "New Issue (88)"
        else:
            issue_number = "Unknown"
    elif issue_type == "Fixed Income":
        if issue_number == "A":
            issue_number = "Initial Issue (AA)"
        elif "2" <= issue_number <= "9":
            issue_number = f"New Issue ({int(issue_number)}A)"
        elif issue_number == "A":
            issue_number = "New Issue (A2)"
        elif issue_number == "B":
            issue_number = "New Issue (2A)"
        elif "C" <= issue_number <= "Y":
            issue_number = f"New Issue (A{chr(ord(issue_number)-2)})"
        elif issue_number == "Z":
            issue_number = "New Issue (A3)"
        else:
            issue_number = "Unknown"
    
    # Get the check digit.
    check_digit = cusip[8]
    
    # Create and return the dictionary.
    return {"Base": base,
            "Issuer Code": issuer_code,
            "Issuer Type": issuer_type,
            "Issue Type": issue_type,
            "Issue Number": issue_number,
            "Check Digit": check_digit}
