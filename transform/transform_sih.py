import os
import pandas as pd
import numpy as np

# Para rodar esse codigo certifique-se que esse arquivos existem, caso 
# nao existem rode os codigos de lookup e concat

SIH_PATH = "analise-dados-sus/data/raw/datasus"
UF_ZI_PATH = "analise-dados-sus/lookup/data/transform/tabela_municipios.parquet"
CID_10_PATH = "analise-dados-sus/lookup/data/transform/tabela_cid10.parquet"
CNES_PATH = "analise-dados-sus/lookup/data/transform/tabela_cnes.parquet"
ESPEC_PATH = "analise-dados-sus/lookup/data/transform/tabela_espec.parquet"
OUTPUT_PATH = "analise-dados-sus/data/transform"

OUTPUT_FILENAME = "sih_transformado.parquet"

COLUMNS = ['UF_ZI', 'COD_IDADE', 'IDADE', 'SEXO', 'RACA_COR',
           'CAR_INT', 'MORTE', 'DIAG_PRINC', 'DIAGSEC1', 'DIAGSEC2',
           'DIAGSEC3', 'DIAGSEC4', 'DIAGSEC5', 'DIAGSEC6', 
           'DIAGSEC7', 'DIAGSEC8', 'DIAGSEC9', 'CNES', 'ESPEC']

def load_SIH(directory, columns=None):
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
                    dataframe = pd.read_parquet(path, engine="pyarrow", columns=columns)

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

def load_parquet(path, columns=None):
    print(f"> Tentando ler \"{path}\"...")
    if not os.path.isfile(path):
        print(f"> Arquivo \"{path}\" nao foi encontrado.")
        return None
    
    try:
        dataframe = pd.read_parquet(path, engine="pyarrow", columns=columns)
        print(f"> \"{path}\" lido com sucesso!")
        return dataframe
    except Exception as e:
        print(f">> Falha ao ler arquivo: {path}")
        print(f">> Exception: {e}")
        return None

# Ta feio, ainda preciso mudar essa verificacao
def is_dataframe_empty(name, dataframe):
    if dataframe is None or dataframe.empty:
        print(f"> Dataframe {name} vazio.")
        return True
    return False

def transform_sih_df(dataframe,uf_zi_df,cid_10_df,cnes_df,espec_df):
    # Ta feio, ainda preciso mudar essa verificacao
    if is_dataframe_empty("dataframe", dataframe):
        return None
    if is_dataframe_empty("uf_zi_df", uf_zi_df):
        return None
    if is_dataframe_empty("cid_10_df", cid_10_df):
        return None
    if is_dataframe_empty("cnes_df", cnes_df):
        return None
    if is_dataframe_empty("espec_df", espec_df):
        return None

    for col in dataframe.columns:
        dataframe = dataframe.rename(columns={col:col.lower()})

    print(f"> Quantidade de linhas: {len(dataframe)}")
    print("> Fazendo deduplicacao exata...")
    dataframe = dataframe.drop_duplicates()
    print(f"> Quantidade de linhas: {len(dataframe)}")

    print("> Transformando uf_zi para nome_uf e nome_municipio...")
    dataframe = dataframe.merge(uf_zi_df,how="left",on="uf_zi")
    dataframe = dataframe.drop(columns="uf_zi")

    print("> Transformando cod_idade e idade para idade_meses e idade_anos...")
    dataframe[["cod_idade","idade"]] = dataframe[["cod_idade","idade"]].apply(pd.to_numeric, errors="raise").astype("Int64")
    cod_idade_conditions = [
        dataframe["cod_idade"] == 2,
        dataframe["cod_idade"] == 3,
        dataframe["cod_idade"] == 4,
        dataframe["cod_idade"] == 5,
    ]
    idade_meses = [
        0,
        dataframe["idade"],
        dataframe["idade"] * 12,
        (dataframe["idade"] + 100) * 12,
    ]
    idade_anos = [
        0,
        0,
        dataframe["idade"],
        dataframe["idade"] + 100,
    ]
    dataframe["idade_meses"] = np.select(cod_idade_conditions,idade_meses,default=None)
    dataframe["idade_meses"] = pd.to_numeric(dataframe["idade_meses"], errors='coerce')
    dataframe["idade_anos"] = np.select(cod_idade_conditions,idade_anos,default=None)
    dataframe["idade_anos"] = pd.to_numeric(dataframe["idade_anos"], errors='coerce')
    dataframe = dataframe.drop(columns=["cod_idade","idade"])

    print("> Criando faixa etaria...")
    age_bins = [
            0,    
            1,    
            24,   
            108,  
            228,  
            468,  
            708,  
            888,  
            1068, 
            float("inf")
    ]
    age_labels = [
        "Recem-Nascido",
        "Lactente",
        "Criança",
        "Adolescente",
        "Adulto Jovem",
        "Meia-idade",
        "Idoso Jovem",
        "Idoso",
        "Muito Idoso / Longevo"
    ]
    dataframe["faixa_etaria"] = pd.cut(
        dataframe["idade_meses"],
        bins=age_bins,
        labels=age_labels,
        right=True,
        include_lowest=True
    )

    print("> Transformando sexo...")
    dataframe["sexo"] = dataframe["sexo"].map({
        "1":"Masculino",
        "2":"Feminino",
        "3":"Feminino"
    })
    dataframe["sexo"] = dataframe["sexo"].astype("category")

    print("> Transformando raca_cor...")
    dataframe["raca_cor"] = dataframe["raca_cor"].map({
        "01":"Branca",
        "02":"Preta",
        "03":"Parda",
        "04":"Amarela",
        "05":"Indígena"
    })
    dataframe = dataframe.dropna(subset=["raca_cor"])
    dataframe["raca_cor"] = dataframe["raca_cor"].astype("category")

    print("> Transformando car_int...")
    dataframe["car_int"] = dataframe["car_int"].map({
        "01": "Eletivo",
        "02": "Urgência",
        "03": "Acidente no local trabalho ou a serviço da empresa",
        "04": "Acidente no trajeto para o trabalho",
        "05": "Outros tipos de acidente de trânsito",
        "06": "Outros tipos de lesões, intoxicações ou envenenamentos causados por agentes químicos ou físicos."
    })
    dataframe["car_int"] = dataframe["car_int"].astype("category")

    print("> Transformando morte...")
    dataframe["morte"] = dataframe["morte"].map({
        "0": False,
        "1": True,
    })

    print("> Transformando diagnosticos...")
    diag_cols = ['diag_princ', 'diagsec1', 'diagsec2', 'diagsec3', 'diagsec4',
                 'diagsec5', 'diagsec6', 'diagsec7', 'diagsec8', 'diagsec9']

    for col in diag_cols:
        print(f"> Criando descrição de {col}...")
        dataframe[col] = dataframe[col].str.strip()
        dataframe[col] = dataframe[col].replace("", pd.NA)
        dataframe = dataframe.merge(
            cid_10_df.rename(columns={
                "codigo":col,
                "descricao":f"{col}_desc"
            }),
            how="left",
            on=col
        )
    dataframe["qtd_comorb"] = dataframe[diag_cols[1:]].notna().sum(axis=1)

    print("> Obtendo nomes de hospitais...")
    dataframe = dataframe.merge(cnes_df,how="left",on="cnes")

    print("> Traduzindo especialidades de leito...")
    dataframe = dataframe.merge(espec_df,how="left",on="espec")
    dataframe = dataframe.drop(columns="espec")
    dataframe = dataframe.rename(columns={"desc_espec":"espec"})
    dataframe["espec"] = dataframe["espec"].astype("category")

    print("> Reorganizando colunas...")
    new_order = ["idade_meses","idade_anos","faixa_etaria","sexo",
                 "raca_cor","morte","car_int","espec","qtd_comorb",
                 "diag_princ_desc","diagsec1_desc","diagsec2_desc",
                 "diagsec3_desc","diagsec4_desc","diagsec5_desc",
                 "diagsec6_desc","diagsec7_desc","diagsec8_desc",
                 "diagsec9_desc","nome_hosp","nome_municipio","nome_uf",
                 "diag_princ","diagsec1","diagsec2","diagsec3","diagsec4",
                 "diagsec5","diagsec6","diagsec7","diagsec8","diagsec9",
                 "cnes"]
    dataframe = dataframe[[col for col in new_order if col in dataframe.columns]]

    return dataframe
    
def clean_sih_df(dataframe):
    if dataframe is None or dataframe.empty:
        print("> Dataframe vazio.")
        return
    
    # Algumas AIHs, estao em varias tabelas em diferentes meses mas no mesmo UF.
    # Por isso uma grande reducao nas linhas. Nao sei se deve manter, por 
    # enquanto eu nao vou.
    print(f"> Quantidade de linhas: {len(dataframe)}")
    print("> Deletando duplicacoes exatas...")
    dataframe = dataframe.drop_duplicates()
    print(f"> Quantidade de linhas: {len(dataframe)}")

    print("> Removendo colunas nulas...")
    dataframe = dataframe.replace(r'^\s*$', pd.NA, regex=True)
    dataframe = dataframe.dropna(axis=1, how="all")

    print("> Removendo linhas com valores criticos vazios...")
    print(f"> Quantidade de linhas: {len(dataframe)}")
    critical_cols = ["idade_meses","idade_anos","faixa_etaria","sexo",
             "raca_cor","morte","car_int","espec","qtd_comorb",
             "diag_princ_desc","nome_hosp","nome_municipio","nome_uf",
             "diag_princ","cnes"]
    dataframe = dataframe.dropna(subset=critical_cols)
    print(f"> Quantidade de linhas: {len(dataframe)}")

    print("> Removendo idades muito grandes...")
    dataframe = dataframe[dataframe["idade_anos"] <= 122]
    print(f"> Quantidade de linhas: {len(dataframe)}")

    return dataframe

def write_dataframe(dataframe):
    if dataframe is None or dataframe.empty:
        print("> Dataframe vazio.")
        return
    
    os.makedirs(OUTPUT_PATH, exist_ok=True)
    dataframe.to_parquet(OUTPUT_PATH + "/" + OUTPUT_FILENAME,engine="pyarrow",index=False)

if __name__ == "__main__":
    uf_zi_df = load_parquet(UF_ZI_PATH)
    cid_10_df = load_parquet(CID_10_PATH)
    cnes_df = load_parquet(CNES_PATH)
    espec_df = load_parquet(ESPEC_PATH)
    sih_df = load_SIH(SIH_PATH,COLUMNS)

    sih_df = transform_sih_df(sih_df,uf_zi_df,cid_10_df,cnes_df,espec_df)
    sih_df = clean_sih_df(sih_df)

    try:
        sih_df = sih_df.sort_values(by="qtd_comorb", ascending=False)

        pd.set_option('display.max_columns', None)
        print(sih_df.head())
        sih_df.info()
        print(sih_df.shape)
        print(sih_df.isna().sum())
        print(sih_df.isna().any())
    except Exception as e:
        print("> Erro na exploracao do dataframe.")
        print(f"> Exception: {e}")

    write_dataframe(sih_df)

    # discrepancias entre diags e diags_descs, resolver isso mais tarde