from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DADOS_DIR = BASE_DIR / "dados"

PATH_CSV = DADOS_DIR / "base_final_consolidada_etapa2.csv"
PATH_GEOJSON = DADOS_DIR / "municipios_rs.geojson"

CSV_SEP = ";"

COL_LOCALIDADE = "Localidade de aplicação do recurso"
COL_VALOR_PAGO = "Valor Pago"
COL_PARLAMENTAR = "Parlamentar_Limpo"
COL_VOTOS = "QT_VOTOS"
COL_CODIGO_IBGE_IPS = "codigo_ibge_ips"
COL_FAIXA_PRIORIDADE = "faixa_prioridade"
COL_MUNICIPIO_FAVORECIDO = "MUNICÍPIO DO FAVORECIDO"

COLUNAS_OBRIGATORIAS = [
    COL_LOCALIDADE,
    COL_VALOR_PAGO,
    COL_PARLAMENTAR,
    COL_VOTOS,
    COL_CODIGO_IBGE_IPS,
    COL_FAIXA_PRIORIDADE,
    COL_MUNICIPIO_FAVORECIDO,
]

UF_IDENTIFIER = "RIO GRANDE DO SUL (UF)"

MAPA_COR_GRADIENTE = "Reds"
COR_BOLHAS = "blue"

MAP_CENTER_LAT = -30.0
MAP_CENTER_LON = -53.0
MAP_ZOOM = 6