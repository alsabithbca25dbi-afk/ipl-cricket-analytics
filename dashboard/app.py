from pathlib import Path
import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st
from ipl_theme import (
     inject_theme, header, hero_card, season_bars, ground_list, section, area_fig,
     heatmap_fig, style_fig, team_color, team_color_map
)

st.set_page_config(page_title="IPL Teams & Venues Analytics", page_icon="🏏", layout="wide")
inject_theme()

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "raw" / "ipl.db"

@st.cache_resource
def get_connection():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")
    return sqlite3.connect(str(DB_PATH), check_same_thread=False)

def q(sql, params=()):
    """Calculate dashboard values in SQL; pandas is only used to display results."""
    return pd.read_sql_query(sql, get_connection(), params=params)

def season_sql(season, alias="m"):
    return ("", []) if season == "All seasons" else (f" AND {alias}.season_year = ?", [int(season)])


def chart_filters(key, *, minimum_sample=False, team_filter=False):
    """Independent filters for one chart; values are passed into that chart's SQL only."""
    with st.expander("Customize this chart", expanded=False):
        cols = st.columns(3 if team_filter else (2 if minimum_sample else 1))
        with cols[0]:
            selected_season = st.selectbox(
                "Season", ["All seasons"] + seasons(), key=f"{key}_season"
            )
        selected_minimum = 10
        if minimum_sample:
            with cols[1]:
                selected_minimum = st.number_input(
                    "Minimum matches", min_value=1, max_value=1000, value=10,
                    step=1, key=f"{key}_minimum"
                )
        selected_team = "All teams"
        if team_filter:
            with cols[-1]:
                selected_team = st.selectbox(
                    "Team", ["All teams"] + teams(), key=f"{key}_team"
                )
    clause, params = season_sql(selected_season)
    return clause, params, int(selected_minimum), selected_team

def scalar(sql, params=(), default=0):
    df = q(sql, params)
    return default if df.empty or pd.isna(df.iloc[0, 0]) else df.iloc[0, 0]

def style(fig, height=380):
    return style_fig(fig, height)

def chart(fig, height=380):
    st.plotly_chart(style(fig, height), use_container_width=True)

@st.cache_data
def seasons():
    return q("SELECT DISTINCT season_year FROM matches_clean WHERE season_year IS NOT NULL ORDER BY season_year")["season_year"].astype(int).astype(str).tolist()

@st.cache_data
def teams():
    return q("""SELECT team FROM (
        SELECT team1 AS team FROM matches_clean UNION SELECT team2 AS team FROM matches_clean
    ) WHERE team IS NOT NULL AND TRIM(team)<>'' ORDER BY team""")["team"].tolist()

try:
    q("SELECT match_id FROM matches_clean LIMIT 1")
    q("SELECT match_id, innings, runs FROM v_innings LIMIT 1")
except Exception as exc:
    st.error(f"Database connection failed: {exc}")
    st.stop()

st.sidebar.title("Analysis Controls")
# New key resets the previously persisted 2008 selection and defaults to All seasons.
season = st.sidebar.selectbox("Season", ["All seasons"] + seasons(), index=0, key="season_domain_d_fixed")
sc, sp = season_sql(season)

match_count = int(scalar(f"SELECT COUNT(*) FROM matches_clean m WHERE 1=1{sc}", sp))
team_count = int(scalar(f"""SELECT COUNT(*) FROM (
 SELECT team1 AS team FROM matches_clean m WHERE team1 IS NOT NULL{sc}
 UNION SELECT team2 AS team FROM matches_clean m WHERE team2 IS NOT NULL{sc}
)""", sp + sp))

chase = q(f"""
WITH innings AS (
 SELECT m.match_id,m.match_winner,
 MAX(CASE WHEN i.innings=1 THEN i.batting_team END) AS first_team,
 MAX(CASE WHEN i.innings=2 THEN i.batting_team END) AS second_team
 FROM matches_clean m JOIN v_innings i ON i.match_id=m.match_id
 WHERE 1=1{sc} GROUP BY m.match_id,m.match_winner
)
SELECT COUNT(*) n,
 SUM(CASE WHEN match_winner=second_team THEN 1 ELSE 0 END) wins,
 100.0*SUM(CASE WHEN match_winner=second_team THEN 1 ELSE 0 END)/NULLIF(COUNT(*),0) pct
FROM innings WHERE match_winner IS NOT NULL AND first_team IS NOT NULL
 AND second_team IS NOT NULL AND first_team<>second_team
""", sp)
chase_n = int(chase.iloc[0]["n"] or 0)
chase_wins = int(chase.iloc[0]["wins"] or 0)
chase_pct = float(chase.iloc[0]["pct"] or 0)

header()

tab_overview, tab_venue, tab_team = st.tabs(["Overview", "Venue", "Team"])

with tab_overview:
    per_season = q("SELECT season_year season, COUNT(*) matches FROM matches_clean WHERE season_year IS NOT NULL GROUP BY season_year ORDER BY season_year")
    k1, k2 = st.columns([2, 3])
    with k1:
        hero_card(f"Matches won chasing · {'all seasons' if season == 'All seasons' else season}", chase_pct,
                  f"Chase sample: {chase_wins:,} wins / {chase_n:,} decisive matches with both innings",
                  f"{match_count:,} matches · {team_count} teams")
    with k2:
        season_bars(per_season["season"].astype(int).tolist(), per_season["matches"].tolist(), "Matches played per season")
    if season == "All seasons":
        if chase_n == 1187 and chase_wins == 647:
            st.caption("Validated result: 95% CI 51.66%–57.32%; p = 0.0021.")
        else:
            st.warning(f"Validation check: report expects 647/1,187; SQL currently returns {chase_wins}/{chase_n}. Do not attach the report's CI or p-value until reconciled.")

    chase_by_season = q("""WITH inn AS (
      SELECT m.match_id,m.season_year season,m.match_winner,
      MAX(CASE WHEN i.innings=1 THEN i.batting_team END) first_team,
      MAX(CASE WHEN i.innings=2 THEN i.batting_team END) second_team
      FROM matches_clean m JOIN v_innings i ON i.match_id=m.match_id WHERE m.season_year IS NOT NULL
      GROUP BY m.match_id,m.season_year,m.match_winner)
      SELECT season,COUNT(*) n,100.0*SUM(CASE WHEN match_winner=second_team THEN 1 ELSE 0 END)/COUNT(*) pct
      FROM inn WHERE match_winner IS NOT NULL AND first_team IS NOT NULL AND second_team IS NOT NULL
      AND first_team<>second_team GROUP BY season ORDER BY season""")
    g1, g2 = st.columns([3, 2])
    with g1:
        if not chase_by_season.empty:
            chart(area_fig(chase_by_season, "season", "pct", "Chasing win rate by season", ref=50, hover=("n",)), 400)
    with g2:
        top = q(f"""SELECT v.venue, COUNT(*) matches, AVG(i.runs) avg_score FROM matches_clean m JOIN venues v
          ON LOWER(TRIM(m.venue))=LOWER(TRIM(v.venue)) LEFT JOIN v_innings i ON i.match_id=m.match_id AND i.innings=1
          WHERE 1=1{sc} GROUP BY v.venue ORDER BY matches DESC LIMIT 6""", sp)
        ground_list("Busiest grounds · avg 1st-innings score",
                    [(r.venue, "n/a" if pd.isna(r.avg_score) else f"avg {r.avg_score:.0f}", f"{int(r.matches)}") for r in top.itertuples()])

    hm = q("""SELECT team, season_year season, 100.0*SUM(win)/COUNT(*) rate FROM (
      SELECT team1 team, season_year, CASE WHEN match_winner=team1 THEN 1 ELSE 0 END win FROM matches_clean
      WHERE team1 IS NOT NULL AND season_year IS NOT NULL
      UNION ALL SELECT team2, season_year, CASE WHEN match_winner=team2 THEN 1 ELSE 0 END FROM matches_clean
      WHERE team2 IS NOT NULL AND season_year IS NOT NULL) GROUP BY team, season_year""")
    if not hm.empty:
        pivot = hm.pivot(index="team", columns="season", values="rate")
        pivot.columns = pivot.columns.astype(int).astype(str)
        chart(heatmap_fig(pivot, "Win rate heatmap · team × season"), max(480, len(pivot) * 36 + 110))

    section("Deep dive", "· customise any chart with its own filters")
    wins_sc, wins_sp, _, wins_team = chart_filters("wins_chart", team_filter=True)
    wins = q(f"""SELECT m.match_winner team, COUNT(*) wins FROM matches_clean m
      WHERE m.match_winner IS NOT NULL AND TRIM(m.match_winner)<>''{wins_sc}
      AND (?='All teams' OR m.match_winner=?) GROUP BY m.match_winner ORDER BY wins""",
      wins_sp + [wins_team, wins_team])
    played = q(f"""SELECT team,SUM(n) matches_played FROM (
      SELECT m.team1 team,COUNT(*) n FROM matches_clean m WHERE m.team1 IS NOT NULL{wins_sc} GROUP BY m.team1
      UNION ALL SELECT m.team2 team,COUNT(*) n FROM matches_clean m WHERE m.team2 IS NOT NULL{wins_sc} GROUP BY m.team2
    ) GROUP BY team""", wins_sp+wins_sp)
    wins = wins.merge(played, on="team", how="left")
    if not wins.empty:
        f = px.bar(wins, x="wins", y="team", orientation="h", color="team",
          color_discrete_map=team_color_map(wins["team"]), hover_data=["matches_played"],
          title="Hero chart · Match wins by team",
          labels={"wins":"Wins","team":"Team","matches_played":"Matches played"})
        f.update_layout(showlegend=False)
        f.update_yaxes(categoryorder="total ascending")
        chart(f, max(430, len(wins)*28))

    l,r = st.columns(2)
    with l:
        grounds_sc, grounds_sp, grounds_min, _ = chart_filters("grounds_chart", minimum_sample=True)
        grounds = q(f"""SELECT v.venue,COUNT(*) matches FROM matches_clean m JOIN venues v
          ON LOWER(TRIM(m.venue))=LOWER(TRIM(v.venue)) WHERE 1=1{grounds_sc}
          GROUP BY v.venue HAVING COUNT(*)>=? ORDER BY matches""", grounds_sp+[grounds_min])
        if not grounds.empty:
            f=px.bar(grounds,x="matches",y="venue",orientation="h",title="Matches hosted by ground",
              color="matches",labels={"matches":"Matches","venue":"Ground"})
            f.add_vline(x=float(grounds["matches"].median()),line_dash="dash",line_color="#F4B860",annotation_text="Median")
            f.update_layout(coloraxis_showscale=False)
            chart(f,max(350,len(grounds)*20))
        else: st.info("No canonical venue matches for this selection.")
    with r:
        batting_sc, batting_sp, batting_min, _ = chart_filters("batting_first_chart", minimum_sample=True)
        batting_first = q(f"""WITH inn AS (
          SELECT m.match_id,m.venue,m.match_winner,
          MAX(CASE WHEN i.innings=1 THEN i.batting_team END) first_team,
          MAX(CASE WHEN i.innings=2 THEN i.batting_team END) second_team
          FROM matches_clean m JOIN v_innings i ON i.match_id=m.match_id WHERE 1=1{batting_sc}
          GROUP BY m.match_id,m.venue,m.match_winner)
          SELECT v.venue,COUNT(*) sample_matches,
          100.0*AVG(CASE WHEN x.match_winner=x.first_team THEN 1.0 ELSE 0.0 END) rate
          FROM inn x JOIN venues v ON LOWER(TRIM(x.venue))=LOWER(TRIM(v.venue))
          WHERE x.match_winner IS NOT NULL AND x.first_team IS NOT NULL AND x.second_team IS NOT NULL
          AND x.first_team<>x.second_team GROUP BY v.venue HAVING COUNT(*)>=? ORDER BY rate""",batting_sp+[batting_min])
        league_rate=scalar(f"""WITH inn AS (
          SELECT m.match_id,m.match_winner,MAX(CASE WHEN i.innings=1 THEN i.batting_team END) f,
          MAX(CASE WHEN i.innings=2 THEN i.batting_team END) s FROM matches_clean m
          JOIN v_innings i ON i.match_id=m.match_id WHERE 1=1{batting_sc} GROUP BY m.match_id,m.match_winner)
          SELECT 100.0*AVG(CASE WHEN match_winner=f THEN 1.0 ELSE 0.0 END) FROM inn
          WHERE match_winner IS NOT NULL AND f IS NOT NULL AND s IS NOT NULL AND f<>s""",batting_sp)
        if not batting_first.empty:
            f=px.bar(batting_first,x="rate",y="venue",orientation="h",title=f"Batting-first win rate by ground ({batting_min}+ matches)",
              hover_data=["sample_matches"],labels={"rate":"Win rate (%)","venue":"Ground","sample_matches":"Decisive matches"},
              color="rate")
            f.add_vline(x=league_rate,line_dash="dash",line_color="#F4B860",annotation_text=f"League {league_rate:.1f}%")
            f.update_layout(coloraxis_showscale=False)
            chart(f,max(350,len(batting_first)*20))
        else: st.info("No grounds meet the 10-match sample threshold.")

    l,r=st.columns(2)
    with l:
        sixes_sc, sixes_sp, _, sixes_team = chart_filters("sixes_chart", team_filter=True)
        sixes=q(f"""SELECT d.batting_team team,COUNT(*) sixes FROM v_deliveries_clean d
          JOIN matches_clean m ON m.match_id=d.match_id WHERE d.batter_runs=6 AND d.is_super_over=0
          AND d.batting_team IS NOT NULL{sixes_sc}
          AND (?='All teams' OR d.batting_team=?) GROUP BY d.batting_team ORDER BY sixes""",
          sixes_sp+[sixes_team,sixes_team])
        if not sixes.empty:
            f=px.bar(sixes,x="sixes",y="team",orientation="h",title="Sixes by team",
              color="team",color_discrete_map=team_color_map(sixes["team"]))
            f.update_layout(showlegend=False)
            f.update_yaxes(categoryorder="total ascending")
            chart(f,max(350,len(sixes)*20))
    with r:
        scores_sc, scores_sp, scores_min, _ = chart_filters("scores_chart", minimum_sample=True)
        scores=q(f"""SELECT v.venue,COUNT(*) sample,AVG(i.runs) avg_score FROM matches_clean m
          JOIN venues v ON LOWER(TRIM(m.venue))=LOWER(TRIM(v.venue))
          JOIN v_innings i ON i.match_id=m.match_id AND i.innings=1 WHERE 1=1{scores_sc}
          GROUP BY v.venue HAVING COUNT(*)>=? ORDER BY avg_score""",scores_sp+[scores_min])
        if not scores.empty:
            f=px.bar(scores,x="avg_score",y="venue",orientation="h",title=f"Average first-innings score by ground ({scores_min}+ innings)",
              hover_data=["sample"],color="avg_score")
            f.update_layout(coloraxis_showscale=False); chart(f,max(350,len(scores)*20))

with tab_venue:
    st.subheader("Venue Analysis")
    vc=q(f"""SELECT v.venue,COUNT(*) matches FROM matches_clean m JOIN venues v
      ON LOWER(TRIM(m.venue))=LOWER(TRIM(v.venue)) WHERE 1=1{sc}
      GROUP BY v.venue ORDER BY matches DESC,v.venue""",sp)
    if vc.empty:
        st.warning("No venue matches found for this filter.")
    else:
        venue = st.selectbox(
            "Select ground (ranked by matches)",
            vc["venue"].tolist(),
            key="venue_fixed"
        )
        st.caption("Explore scoring and match outcomes for the selected ground.")
        venue_score_sc, venue_score_sp, _, _ = chart_filters("venue_score_chart")
        n=scalar(f"""SELECT COUNT(*) FROM matches_clean m JOIN venues v
          ON LOWER(TRIM(m.venue))=LOWER(TRIM(v.venue)) WHERE v.venue=?{sc}""",[venue]+sp)
        vs=q(f"""SELECT COUNT(*) sample,AVG(i.runs) avg_score FROM matches_clean m JOIN venues v
          ON LOWER(TRIM(m.venue))=LOWER(TRIM(v.venue)) JOIN v_innings i
          ON i.match_id=m.match_id AND i.innings=1 WHERE v.venue=?{venue_score_sc}""",[venue]+venue_score_sp).iloc[0]
        league_avg=scalar(f"""SELECT AVG(i.runs) FROM matches_clean m JOIN v_innings i
          ON i.match_id=m.match_id AND i.innings=1 WHERE 1=1{venue_score_sc}""",venue_score_sp)
        a,b,c=st.columns(3)
        a.metric("Matches at ground",f"{int(n):,}")
        b.metric("First-innings sample",f"{int(vs['sample'] or 0):,}")
        c.metric("Average first-innings score","N/A" if pd.isna(vs["avg_score"]) else f"{vs['avg_score']:.1f}")
        st.caption(f"League average first-innings score: {league_avg:.1f} runs.")
        f=px.bar(pd.DataFrame({"Category":["Selected ground","League average"],
          "Average score":[None if pd.isna(vs["avg_score"]) else float(vs["avg_score"]),float(league_avg)]}),
          x="Category",y="Average score",color="Category",color_discrete_sequence=["#F5B301","#3D7BFF"],
          title=f"Hero chart · First-innings score: {venue} vs league")
        chart(f,430)
        outcome_sc, outcome_sp, _, _ = chart_filters("venue_outcome_chart")
        outcome=q(f"""WITH inn AS (
          SELECT m.match_id,m.match_winner,MAX(CASE WHEN i.innings=1 THEN i.batting_team END) first_team,
          MAX(CASE WHEN i.innings=2 THEN i.batting_team END) second_team
          FROM matches_clean m JOIN venues v ON LOWER(TRIM(m.venue))=LOWER(TRIM(v.venue))
          JOIN v_innings i ON i.match_id=m.match_id WHERE v.venue=?{outcome_sc}
          GROUP BY m.match_id,m.match_winner)
          SELECT CASE WHEN match_winner=first_team THEN 'Batting first'
          WHEN match_winner=second_team THEN 'Chasing' ELSE 'Other / unresolved' END outcome,COUNT(*) matches
          FROM inn WHERE match_winner IS NOT NULL GROUP BY outcome ORDER BY matches DESC""",[venue]+outcome_sp)
        if not outcome.empty:
            f=px.bar(outcome,x="outcome",y="matches",color="outcome",title="Decisive outcomes at selected ground",
              labels={"outcome":"Outcome","matches":"Matches"},color_discrete_sequence=["#FF6B00","#3D7BFF","#F5B301"])
            chart(f)
        trend_sc, trend_sp, trend_min, _ = chart_filters("venue_season_chart", minimum_sample=True)
        byseason=q(f"""SELECT m.season_year season,COUNT(*) sample,AVG(i.runs) avg_score
          FROM matches_clean m JOIN venues v ON LOWER(TRIM(m.venue))=LOWER(TRIM(v.venue))
          JOIN v_innings i ON i.match_id=m.match_id AND i.innings=1 WHERE v.venue=?{trend_sc}
          GROUP BY m.season_year HAVING COUNT(*)>=? ORDER BY m.season_year""",[venue]+trend_sp+[trend_min])
        if not byseason.empty:
            f=px.line(byseason,x="season",y="avg_score",markers=True,hover_data=["sample"],
              title="First-innings average by season",labels={"season":"Season","avg_score":"Average runs"})
            f.add_hline(y=league_avg,line_dash="dash",line_color="#F4B860",annotation_text="League average")
            chart(f)

with tab_team:
    st.subheader("Team Analysis")
    team=st.selectbox("Select team",teams(),key="team_fixed")
    team_stats_sc, team_stats_sp, _, _ = chart_filters("team_metrics_chart")
    stats=q(f"""SELECT COUNT(*) played,
      SUM(CASE WHEN m.match_winner=? THEN 1 ELSE 0 END) wins,
      100.0*SUM(CASE WHEN m.match_winner=? THEN 1 ELSE 0 END)/NULLIF(COUNT(*),0) rate
      FROM matches_clean m WHERE (m.team1=? OR m.team2=?){team_stats_sc}""",
      [team,team,team,team]+team_stats_sp).iloc[0]
    a,b,c=st.columns(3)
    a.metric("Matches played",f"{int(stats['played'] or 0):,}")
    b.metric("Matches won",f"{int(stats['wins'] or 0):,}")
    c.metric("Win rate",f"{float(stats['rate'] or 0):.1f}%")
    team_season_sc, team_season_sp, _, _ = chart_filters("team_season_chart")
    seas=q(f"""SELECT m.season_year season,COUNT(*) played,
      SUM(CASE WHEN m.match_winner=? THEN 1 ELSE 0 END) wins,
      100.0*SUM(CASE WHEN m.match_winner=? THEN 1 ELSE 0 END)/NULLIF(COUNT(*),0) rate
      FROM matches_clean m WHERE (m.team1=? OR m.team2=?) AND m.season_year IS NOT NULL{team_season_sc}
      GROUP BY m.season_year ORDER BY m.season_year""",[team,team,team,team]+team_season_sp)
    if not seas.empty:
        chart(area_fig(seas, "season", "rate", f"Hero chart · {team} win rate by season",
                       color=team_color(team), ref=50, hover=("played", "wins")), 430)
    l,r=st.columns(2)
    with l:
        opp_sc, opp_sp, opp_min, _ = chart_filters("team_opponent_chart", minimum_sample=True)
        opp=q(f"""SELECT CASE WHEN m.team1=? THEN m.team2 ELSE m.team1 END opponent,
          COUNT(*) played,SUM(CASE WHEN m.match_winner=? THEN 1 ELSE 0 END) wins,
          SUM(CASE WHEN m.match_winner IS NOT NULL AND m.match_winner<>?
            AND m.match_winner=CASE WHEN m.team1=? THEN m.team2 ELSE m.team1 END THEN 1 ELSE 0 END) losses
          FROM matches_clean m WHERE (m.team1=? OR m.team2=?) AND m.team1 IS NOT NULL AND m.team2 IS NOT NULL{opp_sc}
          GROUP BY opponent HAVING COUNT(*)>=? ORDER BY played DESC,opponent""",
          [team,team,team,team,team,team]+opp_sp+[opp_min])
        if not opp.empty:
            f=px.bar(opp.sort_values("played"),x="played",y="opponent",orientation="h",color="wins",
              hover_data=["wins","losses"],title="Opponent record · sample and wins",
              labels={"played":"Matches played","opponent":"Opponent","wins":"Wins","losses":"Losses"})
            f.update_layout(coloraxis_showscale=False); chart(f,max(350,len(opp)*25))
    with r:
        ground_sc, ground_sp, ground_min, _ = chart_filters("team_ground_chart", minimum_sample=True)
        gr=q(f"""SELECT v.venue,COUNT(*) played,
          SUM(CASE WHEN m.match_winner=? THEN 1 ELSE 0 END) wins,
          100.0*SUM(CASE WHEN m.match_winner=? THEN 1 ELSE 0 END)/NULLIF(COUNT(*),0) rate
          FROM matches_clean m JOIN venues v ON LOWER(TRIM(m.venue))=LOWER(TRIM(v.venue))
          WHERE (m.team1=? OR m.team2=?){ground_sc} GROUP BY v.venue HAVING COUNT(*)>=? ORDER BY rate""",
          [team,team,team,team]+ground_sp+[ground_min])
        if not gr.empty:
            f=px.bar(gr,x="rate",y="venue",orientation="h",color="rate",hover_data=["played","wins"],
              title=f"Team win rate by ground ({ground_min}+ matches)",labels={"rate":"Win rate (%)","venue":"Ground"})
            f.update_layout(coloraxis_showscale=False); chart(f,max(350,len(gr)*22))

st.sidebar.divider()
st.sidebar.caption("IPL Cricket Analytics · Domain D")
st.sidebar.caption("Displayed metrics are calculated in SQL.")