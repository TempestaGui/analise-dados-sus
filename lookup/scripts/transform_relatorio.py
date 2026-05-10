import pandas as pd

INPUT_PATH = "analise-dados-sus/lookup/data/raw/RELATORIO_DTB_BRASIL_2024_MUNICIPIOS.ods"
OUTPUT_PATH = "analise-dados-sus/lookup/data/transform"
PARQUET_FILENAME = "tabela_municipios.parquet"

dataframe = pd.read_excel(
    INPUT_PATH,
    engine="odf",
    skiprows=6,
    header=0,
    usecols=["UF","Nome_UF","Código Município Completo","Nome_Município"])

# Renomeando coluna "Código Município Completo" para "UF_ZI" por questao
# de clareza.
dataframe = dataframe.rename(columns={
    "UF": "uf",
    "Nome_UF": "nome_uf",
    "Código Município Completo": "uf_zi",
    "Nome_Município": "nome_municipio"
})

# Codigo UF_ZI da tabela do SIH nao tem o digito verificador.
# Removendo o digito verificador do codigo do municipio dessa tabela.
dataframe["uf_zi"] = dataframe["uf_zi"].astype("str")
dataframe["uf_zi"] = dataframe["uf_zi"].str[:-1]

# Codigo do DF nao esta igual nas duas tabelas, entao estou mudando o 
# valor do codigo do DF dessa tabela de "530010" para "530000".
dataframe["uf_zi"] = dataframe["uf_zi"].replace({"530010": "530000"})

# 1.3 milhões de codigos UF_ZI nao tem a parte dos municipios, criando
# linhas para lidar com esses casos.
ufs = dataframe["uf"].unique().tolist()
ufs.pop()
nome_ufs = dataframe["nome_uf"].unique().tolist()
nome_ufs.pop()
aux_dataframe = pd.DataFrame({
    "nome_uf": nome_ufs,
    "uf_zi": [uf*10000 for uf in ufs],
    "nome_municipio": "Nao informado"
})
dataframe = dataframe.drop(columns="uf")
dataframe = pd.concat([dataframe, aux_dataframe], ignore_index=True)

# Verificando tamanho dos codigos.
print(f"Tamanho dos codigos:\n{dataframe["uf_zi"].str.len().value_counts()}")
print()

dataframe["uf_zi"] = dataframe["uf_zi"].astype("string")

pd.set_option('display.max_columns', None)

print(dataframe.head())
print()
dataframe.info()
print()
print(f"> Numero de linhas: {len(dataframe)}")
print(f"> Numero de codigos unicos: {dataframe['uf_zi'].nunique()}")

dataframe.to_parquet(OUTPUT_PATH + "/" +  PARQUET_FILENAME, engine="pyarrow", index=False)