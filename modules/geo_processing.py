import pandas as pd


def extract_geojson_municipality_names(geojson_data: dict) -> set[str]:
    """Extrai os nomes dos municípios do GeoJSON usando a propriedade 'name'."""
    names = set()

    for feature in geojson_data.get("features", []):
        properties = feature.get("properties", {})
        name = properties.get("name")

        if name:
            names.add(name)

    return names


def find_unmatched_municipalities(
    municipal_df: pd.DataFrame,
    geojson_names: set[str],
) -> list[str]:
    """Retorna municípios presentes no DataFrame, mas ausentes no GeoJSON."""
    df_names = set(municipal_df["municipio_normalizado"].dropna().unique())
    unmatched = df_names - geojson_names

    return sorted(unmatched)


def build_geo_match_report(
    municipal_df: pd.DataFrame,
    geojson_data: dict,
) -> dict:
    """Gera relatório de correspondência entre dados municipais e GeoJSON."""
    geojson_names = extract_geojson_municipality_names(geojson_data)
    df_names = set(municipal_df["municipio_normalizado"].dropna().unique())

    unmatched = find_unmatched_municipalities(municipal_df, geojson_names)

    return {
        "total_agregados": len(df_names),
        "total_geojson": len(geojson_names),
        "encontrados": len(df_names) - len(unmatched),
        "nao_encontrados": len(unmatched),
        "lista_nao_encontrados": unmatched,
    }