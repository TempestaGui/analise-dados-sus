import pandas as pd

CID_CAT_PATH = "analise-dados-sus/lookup/data/raw/cid10/CID-10-CATEGORIAS.CSV"
CID_SUBCAT_PATH = "analise-dados-sus/lookup/data/raw/cid10/CID-10-SUBCATEGORIAS.CSV"
OUTPUT_PATH = "analise-dados-sus/lookup/data/transform"
CID_FINAL_FILENAME = "cid10_completo.parquet"
TRASH_FILENAME = "cid10_lixo.parquet"

cid_cat = pd.read_csv(CID_CAT_PATH, encoding='latin1', sep=';', usecols=["CAT","DESCRICAO"])
print(f"cid_cat:\n{cid_cat.count()}")
cid_subcat = pd.read_csv(CID_SUBCAT_PATH, encoding='latin1', sep=';', usecols=["SUBCAT","DESCRICAO"])
print(f"cid_subcat:\n{cid_subcat.count()}")
print()

cid_cat = cid_cat.rename(columns={"CAT":"Codigo"})
cid_subcat = cid_subcat.rename(columns={"SUBCAT":"Codigo"})
cid_final = pd.concat([cid_cat, cid_subcat], ignore_index=True)

print(f"> cid_final codigos distintos: {cid_final["Codigo"].nunique()}")
print(f"> cid_final:\n{cid_final.count()}")
print()

trash = cid_final[cid_final.duplicated(subset="Codigo",keep=False)]
cid_final = cid_final.drop_duplicates(subset="Codigo",keep="first")

# Códigos não presentes nessa tabela, mas presentes na tabela SIH:
# ['N184', 'N185', 'U099', 'U10', 'N182', 'N183', 'U109', 'N181']
aux_dataframe = pd.DataFrame({
    "Codigo": ['N184', 'N185', 'U099', 'U10', 'N182', 'N183', 'U109', 'N181'],
    "DESCRICAO": ['Doença renal crônica, estágio 4',
                  'Doença renal crônica, estágio 5',
                  'Condição pós-COVID-19 não especificada (long COVID / sequelas pós-infecção)',
                  'Síndrome inflamatória multissistêmica associada à COVID-19 (MIS-C/MIS-A)',
                  'Doença renal crônica, estágio 2',
                  'Doença renal crônica, estágio 3',
                  'Síndrome inflamatória multissistêmica associada à COVID-19, não especificada',
                  'Doença renal crônica, estágio 1']
})
cid_final = pd.concat([cid_final, aux_dataframe], ignore_index=True)

cid_final = cid_final.sort_values(by="Codigo")
trash = trash.sort_values(by="Codigo")

print(f"> cid_final codigos distintos: {cid_final["Codigo"].nunique()}")
print(f"> cid_final:\n{cid_final.count()}")
print()

cid_final.to_parquet(OUTPUT_PATH + "\\" + CID_FINAL_FILENAME,engine="pyarrow",index=False)
trash.to_parquet(OUTPUT_PATH + "\\" + TRASH_FILENAME,engine="pyarrow",index=False)