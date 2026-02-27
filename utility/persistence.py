import json
import re
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any


class PersistenceUtility:
    storage_dir: Path
    file_path: Path
    file_name: str
    extension: str
    admitted_extensions: set[str] = {"json"}     # {"json", "csv"}
    saved_data: dict | None = None


    def __init__(
        self,
        caller: Any,
        extension: str = "json",
    ):
        if extension not in self.admitted_extensions:
            raise ValueError(f"Extension '{extension}' non supportata. Estensioni ammesse: {self.admitted_extensions}")
        
        self.extension = extension
        try:
            project_root = Path(__file__).resolve().parents[1]
            self.storage_dir = project_root / "storage"
            self.storage_dir.mkdir(parents=True, exist_ok=True)

            caller_name = self._resolve_caller_name(caller)
            self.file_name = (f"{self._class_name_to_file_stem(caller_name)}.{extension}")
            self.file_path = self.storage_dir / self.file_name

        except Exception as exception_obj:
            print(f"Errore durante l'inizializzazione di PersistenceUtility: {exception_obj}")
            # self.storage_dir = Path(".")
            # self.file_name = f"extracted-data-{caller_name.lower()}.{extension}"
            # self.file_path = self.storage_dir / self.file_name
            return

    def _resolve_caller_name(self, caller: Any) -> str | None:
        if caller is None:
            return None

        if isinstance(caller, str):
            candidate = caller.strip()
            return candidate or None

        if isinstance(caller, type):
            return caller.__name__

        return caller.__class__.__name__

    def _class_name_to_file_stem(self, class_name: str) -> str:
        normalized = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", class_name)
        normalized = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", normalized)
        normalized = normalized.replace("-", "_")
        normalized = re.sub(r"-{2,}", "_", normalized).strip("_")

        return normalized.lower()

    def exists(self) -> bool:
        return self.file_path.is_file()

    def load_data(self):
        try:
            # TODO: implementare il supporto al csv => dic (per saved_data)
            with open(self.file_path, "r", encoding="utf-8") as file_obj:
                if self.extension == "json":
                    self.saved_data = json.load(file_obj)
                elif self.extension == "csv":
                    raise ValueError(f"Extension '{self.extension}' non supportata. Estensioni ammesse: {self.admitted_extensions}")
                
                return self.saved_data
        except Exception as exception_obj:
            print(f"Errore durante il caricamento del file '{self.file_path}': {exception_obj}")
            return None

    def save_data(
        self,
        payload: Any,
        indent: int = 4,
    ):
        try:
            with open(self.file_path, "w", encoding="utf-8") as file_obj:
                if self.extension == "json":
                    json.dump(payload, file_obj, indent=indent)
                elif self.extension == "csv":
                    raise ValueError(f"Extension '{self.extension}' non supportata. Estensioni ammesse: {self.admitted_extensions}")
                    
            return True
        except Exception as exception_obj:
            print(f"Errore durante il salvataggio del file '{self.file_path}': {exception_obj}")
            return None

    def to_serializable(self, payload: Any):
        if is_dataclass(payload):
            return asdict(payload)

        if isinstance(payload, dict):
            return {key: self.to_serializable(value) for key, value in payload.items()}

        if isinstance(payload, list):
            return [self.to_serializable(item) for item in payload]

        if hasattr(payload, "__dict__"):
            return {
                key: self.to_serializable(value)
                for key, value in payload.__dict__.items()
                if not key.startswith("_")
            }

        return payload

    def merge_with_defaults(
        self,
        defaults: Any,
        payload: Any,
        strict_keys: bool = True,
    ) -> dict:
        default_data = self.to_serializable(defaults)
        if not isinstance(default_data, dict):
            raise TypeError("defaults deve essere un dict o un oggetto serializzabile in dict")

        if payload is None:
            return default_data

        payload_data = self.to_serializable(payload)
        if not isinstance(payload_data, dict):
            raise TypeError("payload deve essere un dict o un oggetto serializzabile in dict")

        merged_data = dict(default_data)
        for key, value in payload_data.items():
            if strict_keys and key not in merged_data:
                continue
            merged_data[key] = value

        return merged_data

    def get_payload(self, payload: Any, key: str | None = None):
        if not isinstance(payload, dict):
            return None

        if key is None:
            return payload

        return payload.get(key, payload)

    @staticmethod
    def print_data(data):
        print("=" * 100)
        if isinstance(data, dict):
            items = data.items()
        elif hasattr(data, "__dict__"):
            items = data.__dict__.items()
        else:
            print(data)
            print("=" * 100 + "\n\r\n")
            return

        for key, value in items:
            key_length = len(str(key))
            if key_length < 6:
                tabs = "\t\t\t"
            elif key_length < 14:
                tabs = "\t\t"
            else:
                tabs = "\t"

            if isinstance(value, dict) or isinstance(value, list):
                if not value: continue

                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        print(f"\t{key}: {tabs}{sub_key}: {sub_value}")
                    continue

                if isinstance(value, list):
                    print(f"\t{key}: {' - '.join(value)}")
                    continue

            print(f"\t{key}: {tabs}{value}")
        print("=" * 100 + "\n\r\n")
