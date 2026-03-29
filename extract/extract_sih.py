import os
import argparse
from pysus.online_data.SIH import download

BASE_DIR = "data/raw/datasus"

def extract_date(anos, ufs): 
    os.makedirs(BASE_DIR, exist_ok=True)

    meses = list(range(1, 13))

    for ano in anos:
        for uf in ufs:
            print(f"Baixando dados de {uf} - {anos}...")

            try:
                arquivos = download(
                    states=uf,
                    years=ano,
                    months=meses,
                    groups="RD",          
                    data_dir=BASE_DIR     
                )
                
                for arq in arquivos:
                    print(f"{arq}")
            
            except Exception as e:
                print(f"Erros em {uf} - {ano}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract DataSUS SIH")
    parser.add_argument("--anos", nargs="+", type=int, required=True)
    parser.add_argument("--ufs", nargs="+", required=True)

    args = parser.parse_args()

    extract_date(args.anos, args.ufs)