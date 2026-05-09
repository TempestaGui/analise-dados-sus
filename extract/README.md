# Documentação tecnica - Extractor de dados do DataSUS (SIH/SUS)

> Script python para coleta automatizada de Autorizações de Internação Hospitalar

---

## 1. Visão Geral do Projeto

**O que é este script??** Este arquivo Python tem como objetivo realizar o dowload automatizado de dados hospitalares públicos disponibilizados pelo Ministerio da saude do brasil, por meio do sistema DataSUS.

Mais especificamente, o script baixa registros do *SIH/SUS (Sistema de Informações Hospitalares do SUS)**, que é a base de dados que armazena as **Autorizações de Internação Hospitalar (AIH)** - ou seja, documentos gerados sempre que um paciente é internado em hospital vinculado ao SUS.

> **Por que isso é importante??**

> As AIH contêm informações riquissimas: diagnostico do paciente (CID-10), procedimento realizado, tempo de internação, valor pago pelo SUS, municipio, hospital, entrre outros. Pesquisadores, gestores de saude e analistas de politicas publicas usam esses dados para avaliar padrões de doenças, qualidade do entendimento e distribuição de recursos.

---

## 2. Contexto: DataSUS e SIH/SUS

### 2.1 O que é o DataSUS?

O DataSUS é o departamento de informatica do SUS responsavel por coletar, processar e disseminar informações de saude do Brasil. Ele disponibiliza gratuitamente diversas bases de dados via FTP, incluindo o SIH.

### 2.2 O que são as AIH (grupo RD)??

Dentro do SIH, os arquivos do grupo `RD` representam as **Autorizações de Internação Hospitalar ja pagas e consolidadas**. São registros mais completos e mais utilizados em pesquisas epidemiológicas e de gestão.

- **Cada linha** = um internação hospitalar
- Abrangência: todo o territorio nacional
- Autorização: mensal
- Formato dos arquivos: DBC (compactação proprietária do DataSUS, baseada em DBF)

### 2.3 Por que automatizar o download?
 
Fazer o download manual dos dados pelo portal DataSUS é inviável quando se precisa de múltiplos estados e vários anos. Por exemplo, baixar dados de todos os 27 estados de 2018 a 2023 geraria centenas de arquivos. Este script resolve esse problema com poucas linhas de comando.
 
---

## 3. Dependências e Tecnologias Utilizadas
 
### 3.1 Linguagem
 
**Python 3.x** — linguagem de programação de alto nível amplamente usada em ciência de dados e automação.
 
### 3.2 Bibliotecas
 
#### `os`
 
Módulo nativo do Python. É usado neste script para criar o diretório onde os arquivos serão salvos, por meio da função `os.makedirs()`.
 
#### `argparse`
 
Também nativo do Python. Permite criar uma interface de linha de comando (CLI) de forma simples. É ele que processa os argumentos `--anos` e `--ufs` que o usuário passa ao executar o script.
 
#### `pysus`
 
Biblioteca Python de código aberto desenvolvida especificamente para facilitar o acesso aos dados do DataSUS. A função `pysus.online_data.SIH.download()` abstrai toda a complexidade de conexão ao FTP do Ministério da Saúde, identificação e download dos arquivos corretos.
 
- **Instalação:** `pip install pysus`
- **Repositório:** [github.com/AlertaDengue/PySUS](https://github.com/AlertaDengue/PySUS)
---

## 4. Estrutura e Funcionamento do Código
 
### 4.1 Constante `BASE_DIR`
 
```python
BASE_DIR = "data/raw/datasus"
```
 
Define o diretório local onde todos os arquivos baixados serão armazenados. O caminho `data/raw/datasus` segue a convenção de projetos de dados que separam dados brutos (raw) de dados processados.

### 4.2 Função `extract_date(anos, ufs)`
 
```python
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
```
 
Esta é a função principal do script. Veja cada parte em detalhe:
 
- `os.makedirs(BASE_DIR, exist_ok=True)` — Cria o diretório de destino caso ele ainda não exista. O parâmetro `exist_ok=True` evita erro se a pasta já existir.
- `meses = list(range(1, 13))` — Gera a lista `[1, 2, 3, ..., 12]` para baixar todos os meses do ano automaticamente.
- `for ano in anos / for uf in ufs` — Duplo laço que garante o download de todas as combinações de ano e estado informados pelo usuário.
- `download(states, years, months, groups, data_dir)` — Chamada à função da biblioteca pysus. O parâmetro `groups="RD"` especifica o grupo de AIH consolidadas.
- `except Exception as e` — Tratamento de erros: se um estado/ano específico não estiver disponível ou ocorrer falha de rede, o script imprime o erro e continua para a próxima combinação, sem interromper toda a execução.

### 4.3 Bloco `__main__` e `ArgumentParser`
 
```python
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract DataSUS SIH")
    parser.add_argument("--anos", nargs="+", type=int, required=True)
    parser.add_argument("--ufs", nargs="+", required=True)
    args = parser.parse_args()
    extract_date(args.anos, args.ufs)
```
 
O bloco `if __name__ == "__main__"` garante que o script só execute quando chamado diretamente (não quando importado como módulo). O `ArgumentParser` cria a interface CLI:
 
- `--anos` aceita um ou mais inteiros (ex.: `2021 2022 2023`)
- `--ufs` aceita uma ou mais siglas de estados (ex.: `SP RJ MG`)
- `required=True` significa que ambos os parâmetros são obrigatórios
  
---

## 5. Fluxo de Execução
 
A tabela abaixo mostra, em ordem, o que acontece quando o script é executado:
 
| Etapa | Ação | Detalhe |
|:-----:|------|---------|
| **1** | **Início (main)** | Lê os argumentos `--anos` e `--ufs` passados pelo usuário na linha de comando. |
| **2** | **Criação de diretório** | Garante que a pasta `data/raw/datasus` existe antes de salvar qualquer arquivo. |
| **3** | **Loop por ano e UF** | Itera sobre cada combinação de ano × estado para cobrir todo o recorte solicitado. |
| **4** | **Chamada ao pysus** | Aciona a função `download()` da biblioteca pysus para buscar os dados no FTP do DataSUS. |
| **5** | **Impressão de status** | Exibe no terminal o caminho de cada arquivo baixado com sucesso. |
| **6** | **Tratamento de erro** | Caso uma combinação falhe (UF/ano indisponível), captura a exceção e continua sem interromper o script. |
 
---

## 6. Parâmetros da Interface de Linha de Comando
 
| Parâmetro | Flag CLI | Descrição |
|-----------|----------|-----------|
| `--anos` | `--anos 2022 2023` | Um ou mais anos para baixar os dados. Aceita múltiplos valores separados por espaço. |
| `--ufs` | `--ufs SP RJ MG` | Siglas dos estados brasileiros (UFs) de interesse. Aceita múltiplos valores. |
 
---
## 7. Exemplos de Uso
 
### Exemplo 1 — Baixar dados de São Paulo para 2023
 
```bash
python extrator_datasus.py --anos 2023 --ufs SP
```
 
### Exemplo 2 — Múltiplos estados e anos
 
```bash
python extrator_datasus.py --anos 2021 2022 2023 --ufs SP RJ MG BA
```
 
### Exemplo 3 — Todos os estados do Nordeste
 
```bash
python extrator_datasus.py --anos 2022 --ufs MA PI CE RN PB PE AL SE BA
```
 
Os arquivos serão salvos automaticamente em:
 
```
data/raw/datasus/<arquivo>.dbc
```
 
---
 
## 8. Saída Esperada no Terminal
 
Durante a execução, o script imprime mensagens informando o progresso:
 
```
Baixando dados de SP - [2023]...
data/raw/datasus/RDSP2301.dbc
data/raw/datasus/RDSP2302.dbc
...
data/raw/datasus/RDSP2312.dbc
Baixando dados de RJ - [2023]...
data/raw/datasus/RDRJ2301.dbc
...
```
 
Em caso de erro para um estado/ano específico, a mensagem será:
 
```
Erros em AC - 2005: [descrição do erro]
```
 
---
 
## 9. Justificativa — Por que este Script Existe?
 
Este script foi desenvolvido para resolver um problema prático e recorrente em pesquisas de saúde pública:
 
- **Volume de dados:** O DataSUS armazena décadas de dados hospitalares. Baixar manualmente arquivo por arquivo seria inviável.
- **Reprodutibilidade:** Ao parametrizar anos e estados via CLI, qualquer pessoa pode reproduzir exatamente a mesma coleta de dados.
- **Automação de pipeline:** O script pode ser integrado a pipelines de ETL (extração, transformação e carga), sendo executado periodicamente de forma automática.
- **Robustez:** O tratamento de exceções garante que falhas pontuais (ex.: estado sem dados naquele ano) não interrompam toda a coleta.
- **Padronização:** Todos os arquivos são salvos em um diretório padrão, facilitando etapas posteriores de processamento.
> **Contexto acadêmico / profissional**
>
> Este script é tipicamente a primeira etapa (extração) de um pipeline de análise de dados de saúde. Após o download, os arquivos `.dbc` são convertidos para formatos tabulares (CSV, Parquet) e analisados com ferramentas como pandas, R ou Power BI para estudos epidemiológicos, avaliações de políticas de saúde ou análises de custos hospitalares.


