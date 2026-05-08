import os
import pandas as pd

INPUT_FILE = "analise-dados-sus/data/raw/datasus"
OUTPUT_FILENAME = "sih_raw_concat.parquet"
OUTPUT_PATH = "analise-dados-sus/data/intermediate"

def load_SIH(directory):
    if not os.path.isdir(directory):
        print("> Diretorio de entrada nao foi encontrado.")
        return None

    dataframes = []

    print("> Lendo arquivos parquet...")
    for root, dirs, files in os.walk(directory):

        for f in files:
            if f.endswith(".parquet"):
                path = os.path.join(root, f)
                try:
                    dataframe = pd.read_parquet(path, engine="pyarrow")

                    dataframes.append(dataframe)
                except Exception as e:
                    print(f">> Falha ao ler arquivo: {path}")
                    print(f">> Exception: {e}")
                    continue
    print(f"> {len(dataframes)} arquivos lidos.")

    if dataframes:
        print("> Concatenando arquivos parquet...")
        return pd.concat(dataframes, ignore_index=True)
    else:
        print("> Nenhum arquivo parquet encontrado.")
        return None
    
def write_SIH(dataframe):
    os.makedirs(OUTPUT_PATH, exist_ok=True)

    if dataframe is None or dataframe.empty:
        print("> Dataframe vazio.")
        return

    try:
        dataframe.to_parquet(OUTPUT_PATH + "/" +  OUTPUT_FILENAME, engine="pyarrow", index=False)
        print("> Arquivo gravado com sucesso.")
    except Exception as e:
        print(f">> Falha ao gravar arquivo: {OUTPUT_PATH} | Exception: {e}")

if __name__ == "__main__":
    sih = load_SIH(INPUT_FILE)
    write_SIH(sih)