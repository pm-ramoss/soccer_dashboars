import pandas as pd
import streamlit as st
from statsbombpy import sb


@st.cache_data(show_spinner=False, ttl=60 * 60 * 24)
def load_competitions() -> pd.DataFrame:
    """Retorna todas as competições/temporadas disponíveis nos dados abertos do StatsBomb."""
    comps = sb.competitions()
    return comps


@st.cache_data(show_spinner=False, ttl=60 * 60 * 24)
def load_matches(competition_id: int, season_id: int) -> pd.DataFrame:
    """Retorna todas as partidas de uma competição/temporada específica."""
    matches = sb.matches(competition_id=competition_id, season_id=season_id)
    matches = matches.copy()
    matches["label"] = (
        matches["home_team"]
        + " "
        + matches["home_score"].astype(str)
        + " x "
        + matches["away_score"].astype(str)
        + " "
        + matches["away_team"]
        + "  ("
        + matches["match_date"].astype(str)
        + ")"
    )
    return matches.sort_values("match_date", ascending=False)


@st.cache_data(show_spinner=False, ttl=60 * 60 * 24)
def load_events(match_id: int) -> pd.DataFrame:
    """Retorna todos os eventos (passes, chutes, desarmes, etc.) de uma partida."""
    events = sb.events(match_id=match_id)
    return events


@st.cache_data(show_spinner=False, ttl=60 * 60 * 24)
def load_lineups(match_id: int) -> dict:
    """Retorna as escalações (lineups) das duas equipes de uma partida."""
    return sb.lineups(match_id=match_id)


def get_match_row(matches: pd.DataFrame, match_id: int) -> pd.Series:
    """Retorna a linha (Series) da partida selecionada a partir do match_id."""
    return matches.loc[matches["match_id"] == match_id].iloc[0]


def basic_match_stats(events: pd.DataFrame) -> dict:
    """Calcula estatísticas básicas (gols, chutes, passes) a partir do dataframe de eventos."""
    shots = events[events["type"] == "Shot"]
    passes = events[events["type"] == "Pass"]
    goals = shots[shots["shot_outcome"] == "Goal"]

    successful_passes = passes[passes["pass_outcome"].isna()]

    stats = {
        "total_goals": len(goals),
        "total_shots": len(shots),
        "total_passes": len(passes),
        "successful_passes": len(successful_passes),
        "pass_accuracy": (len(successful_passes) / len(passes) * 100) if len(passes) else 0.0,
        "conversion_rate": (len(goals) / len(shots) * 100) if len(shots) else 0.0,
    }
    return stats


def player_pass_count(events: pd.DataFrame) -> pd.DataFrame:
    """Ranking de jogadores por número de passes (total e bem-sucedidos)."""
    passes = events[events["type"] == "Pass"].copy()
    passes["successful"] = passes["pass_outcome"].isna()

    grouped = (
        passes.groupby("player")
        .agg(total_passes=("id", "count"), passes_certos=("successful", "sum"))
        .reset_index()
    )
    grouped["taxa_acerto (%)"] = (grouped["passes_certos"] / grouped["total_passes"] * 100).round(1)
    return grouped.sort_values("total_passes", ascending=False)


def player_shot_stats(events: pd.DataFrame) -> pd.DataFrame:
    """Ranking de jogadores por chutes e gols."""
    shots = events[events["type"] == "Shot"].copy()
    grouped = (
        shots.groupby("player")
        .agg(
            total_chutes=("id", "count"),
            gols=("shot_outcome", lambda s: (s == "Goal").sum()),
        )
        .reset_index()
    )
    grouped["conversao (%)"] = (grouped["gols"] / grouped["total_chutes"] * 100).round(1)
    return grouped.sort_values("total_chutes", ascending=False)
