import os
import pandas as pd
from simpledbf import Dbf5

INPUT_FILE = "analise-dados-sus/lookup/data/raw/TCNESBR.dbf"
OUTPUT_FILENAME = "tabela_cnes.parquet"
OUTPUT_PATH = "analise-dados-sus/lookup/data/transform"

def load_cnes(path):
    if not os.path.isfile(path):
        print(f"> Arquivo {path} nao foi encontrado.")
        return None
    
    try:
        dataframe = Dbf5(path).to_dataframe()
        return dataframe
    except Exception as e:
        print(f">> Falha ao ler arquivo: {path}")
        print(f">> Exception: {e}")
        return None
    
def transform_cnes(dataframe):
    if dataframe is None or dataframe.empty:
        print("> Dataframe vazio.")
        return
    
    dataframe.info()
    print(dataframe.head())
    
    dataframe = dataframe.rename(columns={
        "CNES":"cnes",
        "NOMEFANT":"nome_hosp"
    })
    
    for col in dataframe.columns:
        nulls = dataframe[col].isna().sum()
        empty = dataframe[col].astype(str).str.strip().eq("").sum()
        datatype = dataframe[col].dtype

        print(f"> Coluna {col}:")
        print(f"    > Tipo: {datatype}")
        print(f"    > Nulos (NaN): {nulls}")
        print(f"    > Vazios (''): {empty}")
        print(f"    > Total ausentes: {nulls + empty}")
        print()
    
    print("> Deletando linhas com valores nulos...")
    print(dataframe[dataframe["nome_hosp"].isna()])
    # Consultei no CNES os codigos com nome_hosp == NaN e nao recebi nada
    # codigos NaN: 2246821, 2817950, 5732158
    dataframe = dataframe.dropna(subset=["nome_hosp"])

    print(f"> Tamanho dos codigos do cnes:\n{dataframe["cnes"].str.len().value_counts()}")

    return dataframe

def write_dataframe(dataframe):
    if dataframe is None or dataframe.empty:
        print("> Dataframe vazio.")
        return
    
    os.makedirs(OUTPUT_PATH, exist_ok=True)
    dataframe.to_parquet(OUTPUT_PATH + "/" + OUTPUT_FILENAME,engine="pyarrow",index=False)

if __name__ == "__main__":
    cnes = load_cnes(INPUT_FILE)
    cnes = transform_cnes(cnes)
    write_dataframe(cnes)