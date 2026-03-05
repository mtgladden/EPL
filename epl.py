import streamlit as st
import pandas as pd
import altair as alt 

st.set_page_config(page_title="Premier League Data", layout="wide")

@st.cache_data
def load_and_transform_data():
    df = pd.concat([
        pd.read_csv('PL-season-2324.csv').assign(Season='2023-24'), 
        pd.read_csv('PL-season-2425.csv').assign(Season='2024-25')
    ])
    cols = ['Date', 'Season', 'Team', 'Opponent', 'GoalsFor', 'GoalsAgainst', 'Result']
    home = df[['Date', 'Season', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR']].set_axis(cols, axis=1).assign(Venue='Home', Points=df['FTR'].map({'H':3, 'D':1, 'A':0}))
    away = df[['Date', 'Season', 'AwayTeam', 'HomeTeam', 'FTAG', 'FTHG', 'FTR']].set_axis(cols, axis=1).assign(Venue='Away', Points=df['FTR'].map({'A':3, 'D':1, 'H':0}))
    res = pd.concat([home, away]).sort_values(['Season', 'Team', 'Date'])
    res['Week'] = res.groupby(['Season', 'Team']).cumcount() + 1
    return res

team_df = load_and_transform_data()

st.title("Premier League Trends")

teams_list = sorted(team_df['Team'].unique()) ##must if going to separate for st viz
col1, col2 = st.columns(2)
selected_team = col1.selectbox("Select a Team:", teams_list, index=teams_list.index("Arsenal"))
selected_season = col2.selectbox("Filter Season:", ["All Seasons", "2023-24", "2024-25"])
filtered_df = team_df if selected_season == "All Seasons" else team_df[team_df['Season'] == selected_season]

st.markdown("""
The most successful Premier League teams tend to preform somewhat consistently,
as their rolling goal averages remain relatively high throughout the season even
if they experience "slumps", while less sucessful teams tend to be much more volatile.
""")

table = alt.Chart(filtered_df).transform_aggregate(
    TotalPoints='sum(Points)',
    groupby=['Team']
).mark_bar().encode(
    y=alt.Y('Team:N', sort='-x', title='League Table'),
    x=alt.X('TotalPoints:Q', title='Points Accumulation'),
    color=alt.condition(alt.datum.Team == selected_team, alt.value('blue'), alt.value('gray')),
    tooltip=['Team:N', 'TotalPoints:Q']
).properties(width=300, height=400)

avg = alt.Chart(filtered_df).transform_filter(
    alt.datum.Team == selected_team
).transform_window(
    RollingGoals='mean(GoalsFor)', frame=[-3, 0], groupby=['Team'], sort=[{'field': 'Week'}] #3 games #
).mark_line(point=True).encode(
    x=alt.X('Week:O', title='Match Week'),
    y=alt.Y('RollingGoals:Q', title='4-Match Rolling Goal Average'),
    color='Season:N',
    tooltip=['Team', 'Week', 'GoalsFor']
).properties(width=500, height=400)

st.altair_chart((table | avg).configure_title(anchor='start', fontSize=18), use_container_width=True)

st.header("Home Field Advantage?")
st.markdown("""
Home field advantage varies wildly in the Premier League, as some teams see a huge home field advantage,
some see very little home field advantage, and some even see a home field disadvantage...
""")


match_brush = alt.selection_interval()

scat = alt.Chart(filtered_df).transform_filter(
    alt.datum.Team == selected_team
).mark_circle(size=70).encode(
    x=alt.X('GoalsFor:Q', title='Goals Scored'),
    y=alt.Y('GoalsAgainst:Q', title='Goals Conceded'),
    color=alt.condition(
        match_brush,
        alt.Color('Venue:N', legend=alt.Legend(title="Venue")),
        alt.value('lightgray')
    ),
    tooltip=['Team:N','Opponent:N','Week:O','GoalsFor:Q','GoalsAgainst:Q','Points:Q']
).add_params(match_brush).properties(width=400, height=400, title="Match Outcomes Scatter")

venue = alt.Chart(filtered_df).transform_filter(
    alt.datum.Team == selected_team
).mark_bar().encode(
    x=alt.X('Venue:N', title='Venue'),
    y=alt.Y('sum(Points):Q', title='Total Points'),
    color='Venue:N',
    tooltip=['Venue:N', 'sum(Points):Q']
).properties(width=250, height=400, title="Points by Venue")

bottom_row = alt.hconcat(scat, venue).resolve_scale(color='independent')
st.altair_chart(bottom_row.configure_title(anchor='start', fontSize=18), use_container_width=True)

st.markdown("""The English Premier League table only provides simple data on a teams success,
            by selecting a  specific team and focusing on their specific season, their advantages and disadvantages,
            great wins, devastating losses, overall consistency, and home field advantage, it is easier to understand 
            the full story of each team's respective success, or failure.
            """)
