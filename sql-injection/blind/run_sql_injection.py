from blind_sqli_time_extractor import BlindSqlITimeExtractor
import os
from data_classes import ExtractedData


extractor = BlindSqlITimeExtractor()

def intestazione():
    os.system("cls" if os.name == "nt" else "clear")
    print("\r\n" + "=" * 100)
    print("CONSOLE INTERATTIVA - Blind SQL Injection - Time-Based\r\n")
    print("Questo micro-tool è da utilizzare solo dopo aver trovato la vulnerabilità per l'injection e aver verificato che sia di tipo time-based.\r\n")
    print("Permette di estrarre informazioni dal database sfruttando la vulnerabilità di SQL Injection in modalità blind, utilizzando il delay come canale " \
    "di comunicazione per dedurre i dati.\r\n")
    print("Ho provato a sostenere l'esame più volte con SQLMap ma non sono mai riuscito ad estrarre alcuna informazione, per questo ho realizzato questo tool.\r\n")
    print("Quindi ricordati di:")
    print(" - Aver ottenuto l'IP da HTB e di aver attivato la VPN")
    print(" - Aver individuato una vulnerabilità di SQL Injection di tipo time-based - Burp repeater aitua molto (non dimenticare di codificare le query che inserisci)")
    print("=" * 100 + "\r\n\r\n\r\n\r\n")
def check_stored_data():
    use_saved_settings = False
    extracted_data_exist = False
    if extractor.persistence.exists():
        saved_data = extractor.persistence.load_data()

        if saved_data is not None and "settings"  in saved_data:
            print("=> Sono state trovate delle impostazioni salvate in precedenza:")
            extractor.persistence.print_data(saved_data.get("settings", {}))
            use_saved_settings_input = input("Vuoi utilizzare queste impostazioni (y/n) ?").strip().lower()
        
            if use_saved_settings_input == "y":
                extractor.use_saved_settings()
                use_saved_settings = True
                print("Impostazioni caricate con successo !")
        
        if saved_data is not None and "extracted_data" in saved_data:
            print("\r\n\r\n=> Sono stati trovati dei dati estratti in precedenza:")
            # TODO: la visualizzazione fa schifo va decisamente migliorata !
            extractor.persistence.print_data(saved_data.get("extracted_data", {}))
            extractor.use_extracted_data()
            extracted_data_exist = True

    return {"settings": use_saved_settings, "extracted_data": extracted_data_exist}

def define_url():
    url_input = input(f"Inserisci l'url da utilizzare (default: {extractor.settings.url}): ").strip()
    if url_input:
        extractor.set_url(url_input)
    print(f"URL selezionato: {extractor.settings.url}\n")
def define_delay():
    delay_input = input(f"=> Inserisci il delay da utilizzare (default: {extractor.settings.delay}): ").strip()
    if delay_input:
        try:
            extractor.set_delay(int(delay_input))
        except ValueError:
            print("Errore: il delay deve essere un numero intero.")
    print(f"Delay selezionato: {extractor.settings.delay}\n")
def define_vector():
    print("=> Definisci il vettore per l'injection:")
    print("1. via POST")
    print("2. via GET")
    print("3. via HEADER")
    vector_input = input("Seleziona il vettore (1/2/3) oppure 'q' per uscire (default 3): ").strip()
    if not vector_input:
        vector_input = '3'
    if vector_input != '1' and vector_input != '2' and vector_input != '3' and vector_input.lower() != 'q':
        print("Vettore non valido. Inserisci 1, 2 oppure 3.")
        return
    print("\r\n")
    return vector_input

def set_parameters(vector_input, for_the_target=True):
    params_input = input("=> Inserisci i parametri da utilizzare per l'attacco - 1 SOLA RIGA - (es. 'Cookie: PHPSESSID=nqgure9mkvdgttujk25g2mehgu; TrackingId=5ada769c29c97c7b24be712c4c5702f6' per l'HEADER): ").strip()
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
            delimiter_input = input(f"=> Inserisci il delimitatore utilizzato per separare i parametri nell'header (default: {extractor.settings.delimiter}): ").strip()
            if delimiter_input and for_the_target:
                extractor.set_delimiter(delimiter_input)
            print(f"Delimitatore selezionato: '{extractor.settings.delimiter}'\n")

    elif vector_input.lower() == "q":
        print("Uscita dal programma.")
        return
def set_parameter_target():
    param_target_input = input("=> Inserisci il nome del parametro da utilizzare per l'injection (es. 'TrackingId' per HEADER): ").strip()
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
    db_name_input = input("=> Inserisci il nome del database (OPZIONALE): ").strip()
    if db_name_input:
        if extractor.extracted_data.db_name != db_name_input:
            print(f"Il DB inserito ({db_name_input}) è diverso da quello precedentemente salvato ({extractor.extracted_data.db_name})! Cambiando il nome del DB verranno persi tutti i dati di {extractor.extracted_data.db_name}")
            confirmation = input("Procedere ugualmente (y/n) ?")
            if confirmation.strip() == 'y':
                extractor.extracted_data = ExtractedData()
        extractor.set_db_name(db_name_input)
        print(f"Nome del database selezionato: {extractor.extracted_data.db_name}\n")

def have_headers():
    print("=> Vuoi aggiungere degli HEADER (es. 'User-Agent: Mozilla/5.0, Referer: http://example.com') ?")
    headers_input = input("Inserisci tutti gli header in un'unica stringa oppure premi INVIO per saltare: ").strip()
    if headers_input:
        extractor.set_header_parameters(headers_input)
    print("\r\n")

def question_2():
    extracted_data = extractor.extracted_data
    total_tables = extracted_data.tables.total_tables_num or 0
    table_names = extracted_data.tables.table_names or []

    if total_tables <= 0:
        return "Estrai le tabelle presenti nel DB"

    all_names_found = len(table_names) >= total_tables and all(
        table_entry is not None
        and table_entry.table_name
        and table_entry.table_length
        and table_entry.table_length == len(table_entry.table_name)
        for table_entry in table_names[:total_tables]
    )

    if all_names_found:
        return "Sono stati trovati i nomi di tutte le tabelle, vuoi riprovare ?"

    return f"Si è già scoperto che ci sono {total_tables} tabelle, vuoi estrarne i nomi ?"



def run_cli():
    intestazione()
    use_stored_data = check_stored_data()

    if not use_stored_data or not use_stored_data.get("settings"):
        define_url()
        define_delay()
        vector_input = define_vector()
        set_parameters(vector_input)
        set_parameter_target()

        have_headers()
        set_optional_db_name()

    extracted_data = extractor.extracted_data
    db_name = extracted_data.db_name
    table_name = extracted_data.target.table_name
    q_0 = "/6" if table_name else ""
    q_1 = f'E\' già stato trovato il DB "{db_name}", vuoi riprovare ?' if db_name else "Estrai il nome del DB"
    q_2 = question_2()
    q_3 = f'Estrai i nomi delle colonne di "{table_name}"' if table_name else "Estrai i nomi delle colonne di una tabella"
    q_4 = f'Estrai i nomi delle colonne di "{table_name}"' if table_name else "Estrai i nomi delle colonne di una tabella"

    print("\r\n" + "=" * 50)
    print("Funzioni disponibili:")
    print(f"1. {q_1}")
    print(f"2. {q_2}")
    print(f"3. {q_3}")
    print(f"4. Estrai il numero di righe presenti nella tabella {table_name}")
    print("5. Estrai il contenuto di uno specifico record")
    if table_name:
        print("6. Cambia tabella")
    print("\r\n" + "=" * 50)

    while True:
        scelta = input(f"\n=> Seleziona una funzione (1/2/3/4/5{q_0}) oppure 'q' per uscire: ").strip().lower()

        if scelta == "q":
            print("Uscita dal programma.")
            break
        elif scelta == "1":
            extractor.extract_db_name()
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
            q_4_b = f'E\' stata selezionata la tabella "{table_name}", vuoi cambiarla (premi INVIO per lasciare quella selezionata) ?' if table_name else "Inserisci il nome della tabella: "
            table_name = input(q_4_b).strip()
            if table_name:
                extractor.set_table_target(table_name)
            extractor.extract_rows_length()
        
        elif scelta == "5":
            q_5_a = ''
            print("Scegli la colonna tra:")
            for i, c_n in enumerate(extracted_data.target.column_names):
                print(f"{i} - {extracted_data.target.column_names[i].column_name}")
                q_5_a += str(i) + ','

            column_number = input(f"\r\nScegli la colonna ({q_5_a}): ").strip()
            column_name = extracted_data.target.column_names[(int(column_number))].column_name
            row_number = input("Inserisci il numero della riga (partendo da 1): ").strip()
            if column_name and row_number:
                extractor.extract_record_content(column_name, int(row_number))
            else:
                print("Errore: tutti i parametri sono obbligatori!")
        
        elif scelta == "6":
            table_name = input("Inserisci il nome della tabella: ").strip()
            if table_name:
                extractor.set_table_target(table_name)
            else:
                print("Errore: tutti i parametri sono obbligatori!")
        else:
            print("Scelta non valida.")

    print("\n" + "=" * 50)
    print("Programma terminato")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    run_cli()
