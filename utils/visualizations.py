import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from mplsoccer import Pitch, VerticalPitch

sns.set_theme(style="whitegrid")


def plot_pass_map(events: pd.DataFrame, player: str | None = None):
    """Desenha o mapa de passes de um jogador (ou da partida inteira se player=None)."""
    passes = events[events["type"] == "Pass"].copy()
    if player:
        passes = passes[passes["player"] == player]

    passes = passes.dropna(subset=["location", "pass_end_location"])

    pitch = Pitch(pitch_type="statsbomb", pitch_color="#0e1117", line_color="#c7c7c7")
    fig, ax = pitch.draw(figsize=(10, 7))
    fig.set_facecolor("#0e1117")

    completed = passes[passes["pass_outcome"].isna()]
    incomplete = passes[passes["pass_outcome"].notna()]

    for df_subset, color, label in [
        (completed, "#00c853", "Passe certo"),
        (incomplete, "#ff5252", "Passe errado"),
    ]:
        if df_subset.empty:
            continue
        x_start = df_subset["location"].apply(lambda p: p[0])
        y_start = df_subset["location"].apply(lambda p: p[1])
        x_end = df_subset["pass_end_location"].apply(lambda p: p[0])
        y_end = df_subset["pass_end_location"].apply(lambda p: p[1])
        pitch.arrows(
            x_start, y_start, x_end, y_end,
            ax=ax, color=color, width=1.5, headwidth=4, headlength=4,
            label=label, alpha=0.75,
        )

    ax.legend(facecolor="#0e1117", edgecolor="none", labelcolor="white", loc="upper left")
    title = f"Mapa de passes — {player}" if player else "Mapa de passes — partida completa"
    ax.set_title(title, color="white", fontsize=14, pad=10)
    return fig


def plot_shot_map(events: pd.DataFrame, team: str | None = None):
    """Desenha o mapa de chutes (shot map) de uma equipe ou da partida inteira."""
    shots = events[events["type"] == "Shot"].copy()
    if team:
        shots = shots[shots["team"] == team]
    shots = shots.dropna(subset=["location"])

    pitch = VerticalPitch(
        pitch_type="statsbomb", half=True, pitch_color="#0e1117", line_color="#c7c7c7"
    )
    fig, ax = pitch.draw(figsize=(8, 8))
    fig.set_facecolor("#0e1117")

    for outcome, color, marker in [
        ("Goal", "#00c853", "*"),
        ("Saved", "#ffd600", "o"),
        ("Blocked", "#ff9100", "o"),
        ("Off T", "#ff5252", "x"),
    ]:
        subset = shots[shots["shot_outcome"] == outcome]
        if subset.empty:
            continue
        x = subset["location"].apply(lambda p: p[0])
        y = subset["location"].apply(lambda p: p[1])
        size = subset["shot_statsbomb_xg"].fillna(0.05) * 900 + 50
        pitch.scatter(
            x, y, ax=ax, s=size, color=color, edgecolors="white",
            marker=marker, alpha=0.85, label=outcome,
        )

    ax.legend(facecolor="#0e1117", edgecolor="none", labelcolor="white", loc="lower center")
    title = f"Mapa de chutes — {team}" if team else "Mapa de chutes — partida completa"
    ax.set_title(title, color="white", fontsize=14, pad=10)
    return fig


def plot_passes_vs_goals(matches_events: dict[str, pd.DataFrame]):
    """
    Gráfico de dispersão (matplotlib/seaborn) relacionando total de passes de uma
    equipe com o número de gols marcados, a partir de um dicionário
    {nome_da_equipe: dataframe_de_eventos_da_equipe}.
    """
    rows = []
    for team, ev in matches_events.items():
        passes = len(ev[ev["type"] == "Pass"])
        goals = len(ev[(ev["type"] == "Shot") & (ev["shot_outcome"] == "Goal")])
        rows.append({"equipe": team, "passes": passes, "gols": goals})

    df = pd.DataFrame(rows)
    fig, ax = plt.subplots(figsize=(7, 5))
    sns.scatterplot(data=df, x="passes", y="gols", hue="equipe", s=150, ax=ax, legend=False)
    for _, r in df.iterrows():
        ax.annotate(r["equipe"], (r["passes"], r["gols"]), fontsize=8, xytext=(4, 4),
                    textcoords="offset points")
    ax.set_title("Relação entre volume de passes e gols marcados")
    ax.set_xlabel("Total de passes")
    ax.set_ylabel("Gols marcados")
    fig.tight_layout()
    return fig


def plot_player_bar(df: pd.DataFrame, x: str, y: str, title: str, top_n: int = 10):
    """Gráfico de barras genérico (top N jogadores) usando seaborn."""
    data = df.head(top_n)
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.barplot(data=data, x=x, y=y, ax=ax, palette="viridis")
    ax.set_title(title)
    fig.tight_layout()
    return fig
