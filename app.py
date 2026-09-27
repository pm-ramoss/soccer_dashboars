import time

import pandas as pd
import streamlit as st

from utils.data_loader import (
    basic_match_stats,
    get_match_row,
    load_competitions,
    load_events,
    load_matches,
    player_pass_count,
    player_shot_stats,
)
from utils.visualizations import (
    plot_pass_map,
    plot_passes_vs_goals,
    plot_player_bar,
    plot_shot_map,
)

st.set_page_config(
    page_title="Soccer Analytics",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

for key, default in {
    "competition_id": None,
    "season_id": None,
    "match_id": None,
    "events": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

st.sidebar.title("Filtros")
st.sidebar.caption("Dados públicos StatsBomb Open Data")

with st.spinner("Carregando competições disponíveis..."):
    competitions = load_competitions()

comp_options = (
    competitions[["competition_id", "season_id", "competition_name", "season_name", "country_name"]]
    .drop_duplicates()
    .assign(label=lambda d: d["country_name"] + " - " + d["competition_name"] + " (" + d["season_name"] + ")")
    .sort_values("label")
)

selected_label = st.sidebar.selectbox(
    "Competição / Temporada", comp_options["label"].tolist()
)
selected_row = comp_options.loc[comp_options["label"] == selected_label].iloc[0]
st.session_state["competition_id"] = int(selected_row["competition_id"])
st.session_state["season_id"] = int(selected_row["season_id"])

progress = st.sidebar.progress(0, text="Buscando partidas...")
matches = load_matches(st.session_state["competition_id"], st.session_state["season_id"])
for pct in (30, 70, 100):
    time.sleep(0.05)
    progress.progress(pct, text="Buscando partidas..." if pct < 100 else "Partidas carregadas!")
progress.empty()

match_label = st.sidebar.selectbox("Partida", matches["label"].tolist())
match_row = matches.loc[matches["label"] == match_label].iloc[0]
st.session_state["match_id"] = int(match_row["match_id"])

with st.spinner("Carregando eventos da partida..."):
    events = load_events(st.session_state["match_id"])
    st.session_state["events"] = events

home_team = match_row["home_team"]
away_team = match_row["away_team"]

st.sidebar.divider()
st.sidebar.markdown(
    f"**Partida selecionada:**\n\n{home_team} {match_row['home_score']} x "
    f"{match_row['away_score']} {away_team}\n\n📅 {match_row['match_date']}"
)

st.title("Soccer Analytics")
st.caption(
    "Explorando dados abertos do StatsBomb com Streamlit, StatsBombPy e mplsoccer."
)

tabs = st.tabs(
    ["Visão Geral", "Eventos", "Mapa de Passes", "Mapa de Chutes",
     "Análises", "Comparar Jogadores"]
)

with tabs[0]:
    st.subheader(f"{selected_row['competition_name']} — {selected_row['season_name']}")
    st.markdown(f"### {home_team} {match_row['home_score']} x {match_row['away_score']} {away_team}")

    stats = basic_match_stats(events)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Gols", stats["total_goals"])
    c2.metric("Chutes", stats["total_shots"])
    c3.metric("Passes", stats["total_passes"])
    c4.metric(
        "Precisão de passe",
        f"{stats['pass_accuracy']:.1f}%",
        delta=f"{stats['pass_accuracy'] - 80:.1f} pp vs média",
    )
    c5.metric("Conversão de chute", f"{stats['conversion_rate']:.1f}%")

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Top 5 — Passes por jogador**")
        st.dataframe(player_pass_count(events).head(5), use_container_width=True, hide_index=True)
    with col2:
        st.markdown("**Top 5 — Chutes/Gols por jogador**")
        st.dataframe(player_shot_stats(events).head(5), use_container_width=True, hide_index=True)

# --------------------------------------------------------------------------- #
# TAB 2 — Eventos (tabela filtrável + download)
# --------------------------------------------------------------------------- #
with tabs[1]:
    st.subheader("Eventos da partida")

    colf1, colf2, colf3 = st.columns(3)
    with colf1:
        tipo_evento = st.multiselect(
            "Tipo de evento",
            sorted(events["type"].dropna().unique().tolist()),
            default=["Pass", "Shot"],
        )
    with colf2:
        jogadores = st.multiselect(
            "Jogador(es)",
            sorted(events["player"].dropna().unique().tolist()),
        )
    with colf3:
        equipe_filtro = st.radio("Equipe", ["Ambas", home_team, away_team], horizontal=True)

    filtrado = events.copy()
    if tipo_evento:
        filtrado = filtrado[filtrado["type"].isin(tipo_evento)]
    if jogadores:
        filtrado = filtrado[filtrado["player"].isin(jogadores)]
    if equipe_filtro != "Ambas":
        filtrado = filtrado[filtrado["team"] == equipe_filtro]

    colunas_exibir = [
        c for c in ["minute", "second", "team", "player", "type", "location", "pass_outcome", "shot_outcome"]
        if c in filtrado.columns
    ]
    st.dataframe(filtrado[colunas_exibir], use_container_width=True, height=420)
    st.caption(f"{len(filtrado)} eventos encontrados.")

    csv = filtrado[colunas_exibir].to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇Baixar eventos filtrados (CSV)",
        data=csv,
        file_name=f"eventos_partida_{st.session_state['match_id']}.csv",
        mime="text/csv",
    )

with tabs[2]:
    st.subheader("Mapa de passes")
    jogadores_passe = sorted(events[events["type"] == "Pass"]["player"].dropna().unique().tolist())
    escolha = st.selectbox("Escolha um jogador (ou veja a partida completa)", ["Partida completa"] + jogadores_passe)
    player_arg = None if escolha == "Partida completa" else escolha

    with st.spinner("Desenhando mapa de passes..."):
        fig = plot_pass_map(events, player_arg)
    st.pyplot(fig, use_container_width=True)
    st.caption("Setas verdes = passe certo · Setas vermelhas = passe errado")

with tabs[3]:
    st.subheader("Mapa de chutes (shot map)")
    equipe_chute = st.radio("Equipe", ["Ambas", home_team, away_team], horizontal=True, key="shot_team")
    team_arg = None if equipe_chute == "Ambas" else equipe_chute

    with st.spinner("Desenhando mapa de chutes..."):
        fig2 = plot_shot_map(events, team_arg)
    st.pyplot(fig2, use_container_width=True)
    st.caption("Tamanho do marcador ∝ xG (probabilidade de gol) = gol")

with tabs[4]:
    st.subheader("Relação entre passes e gols")
    matches_events = {
        home_team: events[events["team"] == home_team],
        away_team: events[events["team"] == away_team],
    }
    fig3 = plot_passes_vs_goals(matches_events)
    st.pyplot(fig3, use_container_width=True)

    st.divider()
    st.subheader("Ranking de passes na partida")
    fig4 = plot_player_bar(
        player_pass_count(events), x="total_passes", y="player",
        title="Top 10 jogadores por número de passes",
    )
    st.pyplot(fig4, use_container_width=True)

with tabs[5]:
    st.subheader("Comparar dois jogadores")

    all_players = sorted(events["player"].dropna().unique().tolist())
    with st.form("form_comparacao"):
        col1, col2 = st.columns(2)
        with col1:
            jogador_a = st.selectbox("Jogador A", all_players, index=0)
        with col2:
            jogador_b = st.selectbox(
                "Jogador B", all_players, index=min(1, len(all_players) - 1)
            )
        n_eventos = st.slider("Número máximo de eventos a exibir por jogador", 5, 100, 20)
        enviado = st.form_submit_button("Comparar")

    if enviado:
        passes_df = player_pass_count(events).set_index("player")
        shots_df = player_shot_stats(events).set_index("player")

        colA, colB = st.columns(2)
        for col, jog in [(colA, jogador_a), (colB, jogador_b)]:
            with col:
                st.markdown(f"#### {jog}")
                p_total = int(passes_df.loc[jog, "total_passes"]) if jog in passes_df.index else 0
                p_certos = int(passes_df.loc[jog, "passes_certos"]) if jog in passes_df.index else 0
                s_total = int(shots_df.loc[jog, "total_chutes"]) if jog in shots_df.index else 0
                s_gols = int(shots_df.loc[jog, "gols"]) if jog in shots_df.index else 0

                st.metric("Passes totais", p_total)
                st.metric("Passes certos", p_certos)
                st.metric("Chutes", s_total)
                st.metric("Gols", s_gols)

                eventos_jog = events[events["player"] == jog].head(n_eventos)
                st.dataframe(
                    eventos_jog[[c for c in ["minute", "type", "team"] if c in eventos_jog.columns]],
                    use_container_width=True, hide_index=True,
                )

st.divider()
st.caption(
    "Fonte dos dados: StatsBomb Open Data · Projeto acadêmico desenvolvido com "
    "Streamlit, statsbombpy e mplsoccer."
)
