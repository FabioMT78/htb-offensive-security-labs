from dataclasses import dataclass, field
from typing import Dict, Literal, Optional, get_args


OptimizerType = Literal["anding", "bisection"]
SqlTypeType = Literal["mssql", "mysql", "postgresql", "oracle"]
optimizer: tuple[str, ...] = get_args(OptimizerType)
sql_types: tuple[str, ...] = get_args(SqlTypeType)


@dataclass
class Settings:
    delay: int = 10
    url: str = "http://10.129.204.202"
    sql_type: SqlTypeType = "mssql"
    post_parameters: Optional[str] = None
    get_parameters: Optional[str] = None
    header_parameters: Dict[str, str] = field(default_factory=dict)
    delimiter: str = ";"
    parameter_target: Optional[str] = None
    verbose: bool = False
    optimizer: OptimizerType = "anding"
    hurry_up: bool = True
    request_timeout: int = 20
    max_retries: int = 3
    retry_delay: float = 0.5

    def __post_init__(self):
        if isinstance(self.optimizer, str):
            self.optimizer = self.optimizer.strip().lower()
        if self.optimizer not in optimizer:
            raise ValueError(f"optimizer deve essere: {', '.join(optimizer)}")

        if isinstance(self.sql_type, str):
            self.sql_type = self.sql_type.strip().lower()
        if self.sql_type not in sql_types:
            raise ValueError(f"sql_type deve essere: {', '.join(sql_types)}")

        if self.request_timeout <= 0:
            raise ValueError("request_timeout deve essere > 0")

        if self.max_retries <= 0:
            raise ValueError("max_retries deve essere > 0")

        if self.retry_delay < 0:
            raise ValueError("retry_delay deve essere >= 0")

        if self.header_parameters is None:
            self.header_parameters = {}

        if not isinstance(self.header_parameters, dict):
            raise ValueError("header_parameters deve essere un dizionario")


@dataclass
class ExtractedDataTableNames:
    table_length: int = 0
    table_name: Optional[str] = None


@dataclass
class ExtractedDataTables:
    total_tables_num: int = 0
    table_names: list[ExtractedDataTableNames] = field(default_factory=list)

    def __post_init__(self):
        normalized_table_names: list[ExtractedDataTableNames] = []
        for table in self.table_names:
            if isinstance(table, ExtractedDataTableNames):
                normalized_table_names.append(table)
            elif isinstance(table, dict):
                normalized_table_names.append(ExtractedDataTableNames(**table))
            elif isinstance(table, str):
                normalized_table_names.append(ExtractedDataTableNames(table_name=table))
        self.table_names = normalized_table_names


@dataclass
class ExtractedDataColumnNames:
    column_length: int = 0
    column_name: Optional[str] = None


@dataclass
class ExtractedDataValues:
    column_name: Optional[str] = None
    row_number: Optional[int] = None
    value_length: int = 0
    value: Optional[str] = None


@dataclass
class ExtractedDataTarget:
    table_name: Optional[str] = None
    total_columns_num: int = 0
    column_names: list[ExtractedDataColumnNames] = field(default_factory=list)
    rows_num: int = 0
    target_column_name: Optional[str] = None
    target_row_number: Optional[int] = None
    extracted_values: list[ExtractedDataValues] = field(default_factory=list)

    def __post_init__(self):
        normalized_column_names: list[ExtractedDataColumnNames] = []
        for column in self.column_names:
            if isinstance(column, ExtractedDataColumnNames):
                normalized_column_names.append(column)
            elif isinstance(column, dict):
                normalized_column_names.append(ExtractedDataColumnNames(**column))
            elif isinstance(column, str):
                normalized_column_names.append(ExtractedDataColumnNames(column_name=column))
        self.column_names = normalized_column_names

        normalized_values: list[ExtractedDataValues] = []
        for value in self.extracted_values:
            if isinstance(value, ExtractedDataValues):
                normalized_values.append(value)
            elif isinstance(value, dict):
                normalized_values.append(ExtractedDataValues(**value))
        self.extracted_values = normalized_values

    @property
    def extraced_values(self) -> list[ExtractedDataValues]:
        return self.extracted_values

    @extraced_values.setter
    def extraced_values(self, values: list[ExtractedDataValues]):
        self.extracted_values = values


@dataclass
class ExtractedData:
    db_name: Optional[str] = None
    db_name_length: Optional[int] = 0
    tables: ExtractedDataTables = field(default_factory=ExtractedDataTables)
    target: ExtractedDataTarget = field(default_factory=ExtractedDataTarget)

    def __post_init__(self):
        if isinstance(self.tables, dict):
            self.tables = ExtractedDataTables(**self.tables)
        elif self.tables is None:
            self.tables = ExtractedDataTables()

        if isinstance(self.target, dict):
            target_data = dict(self.target)
            if "extraced_values" in target_data and "extracted_values" not in target_data:
                target_data["extracted_values"] = target_data.pop("extraced_values")
            self.target = ExtractedDataTarget(**target_data)
        elif self.target is None:
            self.target = ExtractedDataTarget()


