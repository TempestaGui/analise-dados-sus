import os
import pandas as pd

INPUT_FILE = "analise-dados-sus/lookup/data/raw/LEITOS.CNV"
OUTPUT_FILENAME = "tabela_espec.parquet"
OUTPUT_PATH = "analise-dados-sus/lookup/data/transform"

def load_espec(path):
    if not os.path.isfile(path):
        print(f"> Arquivo {path} nao foi encontrado.")
        return None
    
    try:
        dataframe = pd.read_csv(INPUT_FILE, header=None, encoding="latin1", sep='\t')
        return dataframe
    except Exception as e:
        print(f">> Falha ao ler arquivo: {path}")
        print(f">> Exception: {e}")
        return None

def transform_espec(raw_dataframe):
    if raw_dataframe is None or raw_dataframe.empty:
        print("> Dataframe vazio.")
        return
    
    print(raw_dataframe.head())
    raw_dataframe.info()

    columns = raw_dataframe.columns
    dataframe = raw_dataframe[columns[0]].str.extract(r"(\d{2}-.*?\S(?=\s+\d{2}$))")
    dataframe.columns = ["descricao"]
    dataframe[["espec", "desc_espec"]] = dataframe["descricao"].str.split('-', n=1, expand=True)
    dataframe = dataframe.drop(columns="descricao")
    dataframe = dataframe.dropna()

    print(dataframe["espec"].unique())
    print(dataframe["desc_espec"].unique())
    print(dataframe.head())
    dataframe.info()

    return dataframe

def write_dataframe(dataframe):
    if dataframe is None or dataframe.empty:
        print("> Dataframe vazio.")
        return
    
    os.makedirs(OUTPUT_PATH, exist_ok=True)
    dataframe.to_parquet(OUTPUT_PATH + "/" + OUTPUT_FILENAME,engine="pyarrow",index=False)

if __name__ == "__main__":
    espec = load_espec(INPUT_FILE)
    espec = transform_espec(espec)
    write_dataframe(espec)