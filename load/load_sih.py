from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

FINAL_FILENAME = "sih_load.parquet"
TRASH_LOAD_FILENAME = "sih_lixo_load.parquet"


def find_project_root() -> Path:
    """
    Encontra a raiz do projeto 

    Esperado no projeto:
    - requirements.txt
    - data/
    - load/
    - transform/
    """
    current_path = Path(__file__).resolve()

    for parent in [current_path.parent, *current_path.parents]:
        if (parent / "requirements.txt").exists() and (parent / "data").exists():
            return parent

    # Fallback: considerando que este arquivo fica dentro da pasta load/
    return current_path.parent.parent


PROJECT_ROOT = find_project_root()

TRANSFORM_PATH = PROJECT_ROOT / "data" / "transform" / "sih_transformado.parquet"
TRASH_PATH = PROJECT_ROOT / "data" / "transform" / "sih_lixo.parquet"
LOAD_PATH = PROJECT_ROOT / "data" / "load"

EXPECTED_COLUMNS = [
    "idade_meses",
    "idade_anos",
    "faixa_etaria",
    "sexo",
    "raca_cor",
    "morte",
    "car_int",
    "espec",
    "qtd_comorb",
    "diag_princ_desc",
    "diagsec1_desc",
    "diagsec2_desc",
    "diagsec3_desc",
    "diagsec4_desc",
    "diagsec5_desc",
    "diagsec6_desc",
    "diagsec7_desc",
    "nome_hosp",
    "nome_municipio",
    "nome_uf",
    "diag_princ",
    "diagsec1",
    "diagsec2",
    "diagsec3",
    "diagsec4",
    "diagsec5",
    "diagsec6",
    "diagsec7",
    "cnes",
]

CATEGORY_COLUMNS = [
    "faixa_etaria",
    "sexo",
    "raca_cor",
    "car_int",
    "espec",
    "nome_municipio",
    "nome_uf",
]

INTEGER_COLUMNS = [
    "idade_meses",
    "idade_anos",
    "qtd_comorb",
]

STRING_COLUMNS = [
    "diag_princ",
    "diagsec1",
    "diagsec2",
    "diagsec3",
    "diagsec4",
    "diagsec5",
    "diagsec6",
    "diagsec7",
    "diagsec8",
    "diagsec9",
    "diag_princ_desc",
    "diagsec1_desc",
    "diagsec2_desc",
    "diagsec3_desc",
    "diagsec4_desc",
    "diagsec5_desc",
    "diagsec6_desc",
    "diagsec7_desc",
    "nome_hosp",
    "cnes",
]


def create_load_directory(directory: Path) -> None:
    """
    Cria o diretório da etapa de Load caso ele ainda não exista.
    """
    directory.mkdir(parents=True, exist_ok=True)


def read_transformed_data(path: Path) -> pd.DataFrame:
    """
    Lê o arquivo Parquet gerado na etapa de Transform.
    """
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    print("> Lendo dados transformados...")
    dataframe = pd.read_parquet(path, engine="pyarrow")

    print(f"> Arquivo lido: {path}")
    print(f"> Quantidade de linhas lidas: {len(dataframe)}")
    print(f"> Quantidade de colunas lidas: {len(dataframe.columns)}")

    return dataframe


def validate_expected_columns(dataframe: pd.DataFrame) -> None:
    """
    Verifica se as colunas esperadas do novo Transform estão presentes.
    Não interrompe a execução; apenas exibe avisos úteis.
    """
    current_columns = list(dataframe.columns)

    missing_columns = [column for column in EXPECTED_COLUMNS if column not in current_columns]
    extra_columns = [column for column in current_columns if column not in EXPECTED_COLUMNS]

    if missing_columns:
        print("> Atenção: colunas esperadas não encontradas no arquivo transformado:")
        for column in missing_columns:
            print(f"  - {column}")

    if extra_columns:
        print("> Atenção: colunas extras encontradas no arquivo transformado:")
        for column in extra_columns:
            print(f"  - {column}")


def model_storage_schema(dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica a modelagem final do armazenamento.

    Nesta etapa, os dados já foram limpos e tratados no Transform.
    O Load organiza o schema final, ajusta tipos e prepara o arquivo
    para armazenamento analítico em Parquet.
    """
    print("> Modelando schema final do armazenamento...")

    validate_expected_columns(dataframe)

    # Garante a ordem combinada das colunas, mantendo somente as que existem.
    ordered_columns = [column for column in EXPECTED_COLUMNS if column in dataframe.columns]
    dataframe = dataframe[ordered_columns].copy()

    for column in CATEGORY_COLUMNS:
        if column in dataframe.columns:
            dataframe[column] = dataframe[column].astype("category")

    for column in INTEGER_COLUMNS:
        if column in dataframe.columns:
            dataframe[column] = pd.to_numeric(dataframe[column], errors="raise")

    if "morte" in dataframe.columns:
        dataframe["morte"] = dataframe["morte"].astype(bool)

    for column in STRING_COLUMNS:
        if column in dataframe.columns:
            dataframe[column] = dataframe[column].astype("string")

    return dataframe

def save_parquet(dataframe: pd.DataFrame, output_path: Path) -> None:
    """
    Salva o dataframe final em formato Parquet com compressão Snappy.
    """
    print("> Salvando dados na camada Load...")

    table = pa.Table.from_pandas(dataframe, preserve_index=False)

    pq.write_table(
        table,
        output_path,
        compression="snappy",
    )

    print(f"> Arquivo salvo em: {output_path}")

def validate_load_file(path: Path) -> None:
    """
    Valida se o arquivo Parquet foi salvo corretamente.
    """
    print("> Validando arquivo salvo...")

    dataframe = pd.read_parquet(path, engine="pyarrow")

    print(f"> Linhas no arquivo final: {len(dataframe)}")
    print(f"> Colunas no arquivo final: {len(dataframe.columns)}")
    print(f"> Tamanho do arquivo: {path.stat().st_size / (1024 * 1024):.2f} MB")

    print("> Schema final:")
    print(dataframe.dtypes)

def load_sih() -> None:
    """
    Executa a etapa de Load do pipeline ETL.

    A função lê os dados tratados pela etapa de Transform,
    aplica a modelagem final do armazenamento e salva o dataset
    final em formato Parquet.
    """
    create_load_directory(LOAD_PATH)

    dataframe = read_transformed_data(TRANSFORM_PATH)
    dataframe = model_storage_schema(dataframe)

    final_output_path = LOAD_PATH / FINAL_FILENAME

    save_parquet(dataframe, final_output_path)
    validate_load_file(final_output_path)

if __name__ == "__main__":
    load_sih()
