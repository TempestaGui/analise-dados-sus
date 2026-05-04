import pandas as pd

INPUT_PATH = "analise-dados-sus/lookup/data/raw/RELATORIO_DTB_BRASIL_2024_MUNICIPIOS.ods"
OUTPUT_PATH = "analise-dados-sus/lookup/data/transform"
PARQUET_FILENAME = "lista_municipios.parquet"

dataframe = pd.read_excel(
    INPUT_PATH,
    engine="odf",
    skiprows=6,
    header=0,
    usecols=["UF","Nome_UF","Código Município Completo","Nome_Município"])

# Renomeando coluna "Código Município Completo" para "UF_ZI" por questao
# de clareza.
dataframe = dataframe.rename(columns={"Código Município Completo": "UF_ZI"})

# Codigo UF_ZI da tabela do SIH nao tem o digito verificador.
# Removendo o digito verificador do codigo do municipio dessa tabela.
dataframe["UF_ZI"] = dataframe["UF_ZI"].astype("str")
dataframe["UF_ZI"] = dataframe["UF_ZI"].str[:-1]

# Codigo do DF nao esta igual nas duas tabelas, entao estou mudando o 
# valor do codigo do DF dessa tabela de "530010" para "530000".
dataframe["UF_ZI"] = dataframe["UF_ZI"].replace({"530010": "530000"})

# 1.3 milhões de codigos UF_ZI nao tem a parte dos municipios, criando
# linhas para lidar com esses casos.
ufs = dataframe["UF"].unique().tolist()
ufs.pop()
nome_ufs = dataframe["Nome_UF"].unique().tolist()
nome_ufs.pop()
aux_dataframe = pd.DataFrame({
    "Nome_UF": nome_ufs,
    "UF_ZI": [uf*10000 for uf in ufs],
    "Nome_Município": "Nao informado"
})
dataframe = dataframe.drop(columns="UF")
dataframe = pd.concat([dataframe, aux_dataframe], ignore_index=True)

# Verificando tamanho dos codigos.
print(f"Tamanho dos codigos:\n{dataframe["UF_ZI"].str.len().value_counts()}")
print()

# Convertendo de volta para int.
dataframe["UF_ZI"] = pd.to_numeric(dataframe["UF_ZI"], errors="raise").astype("Int32")

pd.set_option('display.max_columns', None)

print(dataframe.head())
print()
dataframe.info()
print()
print(f"> Número de linhas: {len(dataframe)}")
print(f"> Número de códigos únicos: {dataframe['UF_ZI'].nunique()}")

dataframe.to_parquet(OUTPUT_PATH + "/" +  PARQUET_FILENAME, engine="pyarrow", index=False)