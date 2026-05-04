import os
import pandas as pd
import numpy as np

INPUT_PATH = "analise-dados-sus/data/raw/datasus"
OUTPUT_PATH = "analise-dados-sus/data/transform"
UF_ZI_LIST = "analise-dados-sus/lookup/data/transform/lista_municipios.parquet"
CID_10_LIST = "analise-dados-sus/lookup/data/transform/cid10_completo.parquet"
TRANSFORM_FILENAME = "sih_transformado.parquet"
TRASH_FILENAME = "sih_lixo.parquet"

def load_SIH(directory):
    if not os.path.isdir(directory):
        print("> Diretorio de entrada nao foi encontrado.")
        return None
    
    columns = ['UF_ZI', 'COD_IDADE', 'IDADE', 'SEXO', 'RACA_COR',
               'CAR_INT', 'MORTE', 'DIAG_PRINC', 'DIAGSEC1', 'DIAGSEC2', 
               'DIAGSEC3', 'DIAGSEC4', 'DIAGSEC5', 'DIAGSEC6', 
               'DIAGSEC7', 'DIAGSEC8', 'DIAGSEC9', 'CNES']

    dataframes = []

    print("> Lendo arquivos parquet...")
    for root, dirs, files in os.walk(directory):
        print("> Diretorio Atual:", root)

        for f in files:
            if f.endswith(".parquet"):
                path = os.path.join(root, f)
                try:
                    dataframe = pd.read_parquet(path, engine="pyarrow", columns=columns)

                    if not set(columns).issubset(dataframe.columns):
                        print(">> Colunas necessarias nao foram encontradas no arquivo.")
                        continue

                    dataframes.append(dataframe)
                except Exception as e:
                    print(f">> Falha ao ler arquivo: {path} | Exception: {e}")
                    continue
    if dataframes:
        print("> Concatenando arquivos parquet...")
        return pd.concat(dataframes, ignore_index=True)
    else:
        print("> Nenhum arquivo parquet encontrado.")
        return None

def transform_SIH(dataframe, uf_lookup, cid10_lookup):
    numeric_cols = ['UF_ZI', 'COD_IDADE', 'IDADE', 'SEXO', "RACA_COR", 'CAR_INT']
    dataframe[numeric_cols] = dataframe[numeric_cols].apply(pd.to_numeric, errors="raise").astype("int64")

    print("> Transformando UF_ZI...")
    print(dataframe["UF_ZI"].value_counts(dropna=False))
    dataframe = dataframe.merge(
        uf_lookup[['UF_ZI', 'Nome_UF', 'Nome_Município']],
        on='UF_ZI',
        how='left'
    )
    print(dataframe["Nome_UF"].value_counts(dropna=False))
    print(f"> Quantidade de NaN: {dataframe["Nome_UF"].isna().sum()}")
    print(dataframe["Nome_Município"].value_counts(dropna=False))
    print(f"> Quantidade de NaN: {dataframe["Nome_Município"].isna().sum()}")
    dataframe[["Nome_UF","Nome_Município"]] = dataframe[["Nome_UF","Nome_Município"]].astype("category")
    dataframe = dataframe.drop(columns="UF_ZI")
    print()

    print("> Transformando IDADE...")
    cod_idade_values = [
        sih["COD_IDADE"] == 2,
        sih["COD_IDADE"] == 3,
        sih["COD_IDADE"] == 4,
        sih["COD_IDADE"] == 5
    ]
    age_years = [
        0,
        0,
        sih["IDADE"],
        sih["IDADE"] + 100
    ]
    age_months = [
        0,
        sih["IDADE"],
        sih["IDADE"] * 12,
        (sih["IDADE"] + 100) * 12
    ]
    dataframe["Idade_Anos"] = np.select(cod_idade_values, age_years, default=None)
    dataframe["Idade_Meses"] = np.select(cod_idade_values, age_months, default=None)
    dataframe["Idade_Meses"] = dataframe["Idade_Meses"].apply(pd.to_numeric, errors="raise").astype("int16")
    dataframe["Idade_Anos"] = dataframe["Idade_Anos"].apply(pd.to_numeric, errors="raise").astype("int16")
    dataframe = dataframe.drop(columns=["COD_IDADE","IDADE"])
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
        "Meia-Idade",
        "Idoso Jovem",
        "Idoso",
        "Muito Idoso / Longevo"
    ]
    dataframe["Faixa_Etaria"] = pd.cut(
        dataframe["Idade_Meses"],
        bins=age_bins,
        labels=age_labels,
        right=True,
        include_lowest=True
    )
    print(dataframe["Faixa_Etaria"].value_counts(dropna=False))
    print(f"> Quantidade de NaN: {dataframe["Faixa_Etaria"].isna().sum()}")
    print(dataframe["Idade_Anos"].value_counts(dropna=False))
    print(f"> Quantidade de NaN: {dataframe["Idade_Anos"].isna().sum()}")
    print(dataframe["Idade_Meses"].value_counts(dropna=False))
    print(f"> Quantidade de NaN: {dataframe["Idade_Meses"].isna().sum()}")

    print("> Transformando SEXO...")
    print(dataframe["SEXO"].value_counts(dropna=False))
    dataframe["SEXO"] = dataframe["SEXO"].map({
        1:"Masculino",
        3:"Feminino"
    })
    print(dataframe["SEXO"].value_counts(dropna=False))
    print(f"> Quantidade de NaN: {dataframe["SEXO"].isna().sum()}")
    dataframe["SEXO"] = dataframe["SEXO"].astype("category")
    print()

    print("> Transformando RACA_COR...")
    print(dataframe["RACA_COR"].value_counts(dropna=False))
    dataframe["RACA_COR"] = dataframe["RACA_COR"].map({
        1:"Branca",
        2:"Preta",
        3:"Parda",
        4:"Amarela",
        5:"Indígena"
    })
    print(dataframe["RACA_COR"].value_counts(dropna=False))
    print(f"> Quantidade de NaN: {dataframe["RACA_COR"].isna().sum()}")
    dataframe["RACA_COR"] = dataframe["RACA_COR"].astype("category")
    print()

    print("> Transformando CAR_INT...")
    print(dataframe["CAR_INT"].value_counts(dropna=False))
    car_groups = {  
        "Eletiva": [1, 11],
        "Emergência": [2, 3, 5, 20, 21],
        "Internação de alta complexidade": [4, 41],
        "Acidente": [6, 7, 8, 9, 26, 27, 28, 29]
    }
    car_map = { 
        code: group
        for group, codes in car_groups.items()
        for code in codes
    }
    dataframe["CAR_INT"] = dataframe["CAR_INT"].map(car_map)
    print(dataframe["CAR_INT"].value_counts(dropna=False))
    print(f"> Quantidade de NaN: {dataframe["CAR_INT"].isna().sum()}")
    dataframe["CAR_INT"] = dataframe["CAR_INT"].astype("category")
    print()

    print("> Transformando MORTE...")
    print(dataframe["MORTE"].value_counts(dropna=False))
    dataframe['MORTE'] = dataframe["MORTE"].map({
        '0':False,
        '1':True
    })
    print(dataframe["MORTE"].value_counts(dropna=False))
    print(f"> Quantidade de NaN: {dataframe["MORTE"].isna().sum()}")
    print()

    print("> Transformando Diagnosticos...")
    diag_cols = ['DIAG_PRINC', 'DIAGSEC1', 'DIAGSEC2', 'DIAGSEC3', 'DIAGSEC4',
                    'DIAGSEC5', 'DIAGSEC6', 'DIAGSEC7', 'DIAGSEC8', 'DIAGSEC9']
    diag_cols_desc = []
    for col in diag_cols:
        dataframe[col] = dataframe[col].str.replace(r"\s+", "", regex=True)
        dataframe = dataframe.merge(
            cid10_lookup.rename(columns={
                "Codigo": col,
                "DESCRICAO": f"{col}_desc"
            }),
            on=col,
            how="left"
        )
        diag_cols_desc.append(f"{col}_desc")
    dataframe["Qtd_Comorb"] = dataframe[diag_cols_desc[1:]].notna().sum(axis=1)
    for col in diag_cols:
        print(dataframe[col].value_counts(dropna=False))
        print(f"> Quantidade de NaN: {dataframe[col].isna().sum()}")
    for col in diag_cols_desc:
        print(dataframe[col].value_counts(dropna=False))
        print(f"> Quantidade de NaN: {dataframe[col].isna().sum()}")

    dataframe = dataframe[
        ['Idade_Meses', 'Idade_Anos', 'Faixa_Etaria', 'SEXO', 'RACA_COR', 'CAR_INT', 'MORTE', 'Qtd_Comorb'] +
        diag_cols_desc +
        ['Nome_UF', 'Nome_Município', 'CNES'] +
        diag_cols
    ]
    return dataframe
    
def clean_SIH(dataframe):
    # Algumas AIHs, estao em varias tabelas em diferentes meses mas no mesmo UF.
    # Por isso uma grande reducao nas linhas. Nao sei se deve manter, por 
    # enquanto eu nao vou.
    print(f"> Quantidade de linhas: {len(dataframe)}")
    print("> Deletando duplicacoes exatas...") 
    trash = dataframe[dataframe.duplicated(keep=False)]
    dataframe = dataframe.drop_duplicates()
    print(f"> Quantidade de linhas: {len(dataframe)}")

    print("> Removendo colunas nulas...")
    dataframe = dataframe.replace(r'^\s*$', pd.NA, regex=True)
    dataframe = dataframe.dropna(axis=1, how="all")

    print("> Removendo linhas não válidas...")
    print(f"> Quantidade de linhas: {len(dataframe)}")
    not_null_cols = [
        'Idade_Meses', 'Idade_Anos', 'Faixa_Etaria', 'SEXO', 'RACA_COR',
        'CAR_INT', 'MORTE', 'Qtd_Comorb', 'DIAG_PRINC_desc', 'Nome_UF', 
        'Nome_Município', 'CNES', 'DIAG_PRINC'
    ]
    trash = dataframe[dataframe[not_null_cols].isna().any(axis=1)]
    dataframe = dataframe.dropna(subset=not_null_cols)
    print(f"> Quantidade de linhas: {len(dataframe)}")

    dataframe["Idade_Anos"] = dataframe["Idade_Anos"].apply(pd.to_numeric, errors="raise").astype("uint8")
    return dataframe, trash

uf_zi_list = pd.read_parquet(UF_ZI_LIST, engine="pyarrow")
cid_10 = pd.read_parquet(CID_10_LIST, engine="pyarrow")

sih = load_SIH(INPUT_PATH)
sih.info()
sih = transform_SIH(sih,uf_zi_list,cid_10)
sih, trash = clean_SIH(sih)

print(sih.shape)
print(sih.isna().sum())
sih.info()

print(sih.isna().any())

sih = sih.sort_values(by="Qtd_Comorb", ascending=False)
sih.to_parquet(OUTPUT_PATH + "/" +  TRANSFORM_FILENAME, engine="pyarrow", index=False)
trash.to_parquet(OUTPUT_PATH + "/" +  TRASH_FILENAME, engine="pyarrow", index=False)