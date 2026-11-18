"""Generate synthetic fixture data mirroring the schema from audit.txt."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd

from pressure.config import SEED

RNG = np.random.default_rng(SEED)

def make_fixture(output_dir: Path) -> None:
    """Generate 6 synthetic CSV files matching the real schema in audit.txt."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Competitions
    comps_data = [
        {"comp_id": 1, "comp_name": "Indian Premier League 2023", "match_format": "T20", "season": "2023"},
        {"comp_id": 2, "comp_name": "Indian Premier League 2024", "match_format": "T20", "season": "2024"},
        {"comp_id": 3, "comp_name": "ICC Men's T20 World Cup", "match_format": "T20", "season": "2022/23"},
        {"comp_id": 4, "comp_name": "ICC Men's T20 World Cup", "match_format": "T20", "season": "2024"},
    ]
    df_comps = pd.DataFrame(comps_data)
    df_comps.to_csv(output_dir / "competitions.csv", index=False)

    # 2. Teams
    teams_data = []
    team_names = ["Mumbai Indians", "Chennai Super Kings", "Rajasthan Royals", "Kolkata Knight Riders",
                  "India", "Australia", "England", "South Africa"]
    for t_idx, t_name in enumerate(team_names, start=1):
        c_id = 1 if t_idx <= 4 else 3
        teams_data.append({"comp_id": c_id, "team_id": t_idx, "team_name": t_name})
    df_teams = pd.DataFrame(teams_data)
    df_teams.to_csv(output_dir / "teams.csv", index=False)

    # 3. Players (with 12 players per team and duplicate names with distinct ids)
    players_data = []
    p_id_counter = 100
    team_rosters = {}
    
    # Intentionally add a couple duplicate names
    dup_names = ["Rahul Sharma", "Amit Singh"]
    
    for t in df_teams["team_id"].unique():
        team_rosters[t] = []
        for p_idx in range(12):
            p_id = p_id_counter
            p_id_counter += 1
            if p_idx == 0 and t in [1, 2]:
                p_name = dup_names[0]
            elif p_idx == 1 and t in [3, 4]:
                p_name = dup_names[1]
            else:
                p_name = f"Player_{t}_{p_idx}"
            team_rosters[t].append((p_id, p_name))
            
            c_id = df_teams.loc[df_teams["team_id"] == t, "comp_id"].iloc[0]
            t_name = df_teams.loc[df_teams["team_id"] == t, "team_name"].iloc[0]
            players_data.append({
                "comp_id": c_id,
                "comp_name": df_comps.loc[df_comps["comp_id"] == c_id, "comp_name"].iloc[0],
                "team_id": t,
                "team_name": t_name,
                "player_id": p_id,
                "player_name": p_name
            })
    df_mapping = pd.DataFrame(players_data)
    df_mapping.to_csv(output_dir / "competition_team_player_mapping.csv", index=False)

    # 4. Matches (~60 matches, a few rain-revised)
    matches_data = []
    match_ids = list(range(1001, 1061))
    
    for m_id in match_ids:
        c_id = RNG.choice([1, 2, 3, 4])
        t_sub = df_teams[df_teams["comp_id"] == (1 if c_id in [1, 2] else 3)]["team_id"].tolist()
        home, away = RNG.choice(t_sub, size=2, replace=False)
        is_revised = (m_id in [1010, 1025])
        
        matches_data.append({
            "match_id": m_id,
            "comp_id": c_id,
            "match_number": m_id - 1000,
            "match_date": "2024-04-15",
            "stage": "Group",
            "venue_id": RNG.integers(1, 10),
            "venue_country": "India",
            "home_team_id": home,
            "home_team": df_teams.loc[df_teams["team_id"] == home, "team_name"].iloc[0],
            "away_team_id": away,
            "away_team": df_teams.loc[df_teams["team_id"] == away, "team_name"].iloc[0],
            "home_team_captain_id": float(team_rosters[home][0][0]),
            "away_team_captain_id": float(team_rosters[away][0][0]),
            "toss_win_team_id": float(home),
            "toss_opted": "bat",
            "man_of_the_match": team_rosters[home][1][0],
            "first_inn_revised_overs": 15.0 if is_revised else np.nan,
            "second_inn_revised_overs": 15.0 if is_revised else np.nan,
            "revised_target": 120.0 if is_revised else np.nan,
            "knock_out": 0,
            "win_team_id": float(home),
            "result": "Home team won by 10 runs"
        })
    df_matches = pd.DataFrame(matches_data)
    df_matches.to_csv(output_dir / "matches.csv", index=False)

    # 5. Playing Eleven
    eleven_data = []
    for m in matches_data:
        m_id = m["match_id"]
        for t_id in [m["home_team_id"], m["away_team_id"]]:
            roster = team_rosters[t_id]
            for order, (p_id, _) in enumerate(roster, start=1):
                eleven_data.append({
                    "match_id": m_id,
                    "team_id": t_id,
                    "player_id": p_id,
                    "batting_order": float(order),
                    "is_played": True,
                    "is_captain": (order == 1),
                    "is_wk": (order == 2),
                    "is_impact": 0,
                    "is_impact_off": 0
                })
    df_eleven = pd.DataFrame(eleven_data)
    df_eleven.to_csv(output_dir / "playing_eleven.csv", index=False)

    # 6. Ball by ball
    bbb_data = []
    
    for m in matches_data:
        m_id = m["match_id"]
        team1, team2 = m["home_team_id"], m["away_team_id"]
        
        # Innings 1 and 2, plus super over (innings 3) for match 1005
        innings_to_play = [1, 2]
        if m_id == 1005:
            innings_to_play.append(3)
            
        for inn in innings_to_play:
            bat_team = team1 if inn == 1 else team2
            bowl_team = team2 if inn == 1 else team1
            if inn == 3:
                bat_team, bowl_team = team2, team1
                
            bat_roster = team_rosters[bat_team]
            bowl_roster = team_rosters[bowl_team]
            
            striker_idx = 0
            non_striker_idx = 1
            wickets = 0
            
            max_overs = 1 if inn == 3 else (15 if not np.isnan(m["first_inn_revised_overs"]) else 20)
            inn_ball_num = 0
            
            for ov in range(max_overs):
                bowler = bowl_roster[4 + (ov % 5)] # bowler from roster
                legal_balls = 0
                ov_ball_num = 0
                
                while legal_balls < 6:
                    if wickets >= 10:
                        break
                    ov_ball_num += 1
                    inn_ball_num += 1
                    
                    # Random ball outcome
                    is_wide = (RNG.random() < 0.04)
                    is_nb = (not is_wide and RNG.random() < 0.01)
                    is_legal = not (is_wide or is_nb)
                    if is_legal:
                        legal_balls += 1
                        
                    is_wkt = False
                    d_type = None
                    d_player = np.nan
                    d_type_id = np.nan
                    
                    if is_legal and RNG.random() < 0.05:
                        is_wkt = True
                        wickets += 1
                        d_type = RNG.choice(["caught", "bowled", "lbw", "run out"])
                        d_type_id = 1.0 if d_type != "run out" else 2.0
                        d_player = float(bat_roster[striker_idx][0])
                    
                    runs = 0
                    if not is_wide:
                        runs = int(RNG.choice([0, 1, 2, 4, 6], p=[0.45, 0.30, 0.05, 0.12, 0.08])) if not is_wkt else 0
                    
                    e_type = "wides" if is_wide else ("noballs" if is_nb else None)
                    e1 = 1 if (is_wide or is_nb) else 0
                    e2 = 0
                    
                    bbb_data.append({
                        "match_id": m_id,
                        "innings": inn,
                        "overid": ov,
                        "over_ball_num": ov_ball_num,
                        "innings_ball_num": inn_ball_num,
                        "batting_team_id": bat_team,
                        "bowling_team_id": bowl_team,
                        "striker_id": bat_roster[striker_idx][0],
                        "striker_name": bat_roster[striker_idx][1],
                        "non_striker_id": bat_roster[non_striker_idx][0],
                        "non_striker_name": bat_roster[non_striker_idx][1],
                        "bowler_id": bowler[0],
                        "bowler_name": bowler[1],
                        "batting_type": "Right Hand",
                        "bowling_type": "Right-arm fast",
                        "batting_order": striker_idx + 1,
                        "runs": runs,
                        "is_four": (runs == 4),
                        "is_six": (runs == 6),
                        "is_wicket": is_wkt,
                        "dismissal_type_id": d_type_id,
                        "dismissal_type": d_type,
                        "dismissed_player_id": d_player,
                        "extras_type": e_type,
                        "extras1_runs": e1,
                        "extras_2_runs": e2,
                        "pace_or_spin": "Pace",
                        "bowl_speed": 135.0,
                        "stroke": "Defensive",
                        "delivery_style": "Good length",
                        "over_or_around": "Over",
                        "on_or_off": "Off",
                        "delivery_ist_time": "2024-04-15 19:30:00"
                    })
                    
                    if is_wkt and wickets < 10:
                        striker_idx = min(striker_idx + 2, 11)
                    elif runs % 2 == 1:
                        striker_idx, non_striker_idx = non_striker_idx, striker_idx
                
                # Strike change at end of over
                striker_idx, non_striker_idx = non_striker_idx, striker_idx

    df_bbb = pd.DataFrame(bbb_data)
    df_bbb.to_csv(output_dir / "ball_by_ball.csv", index=False)

if __name__ == "__main__":
    out_path = Path(__file__).resolve().parent / "fixture_data"
    make_fixture(out_path)
    print(f"Fixture created in {out_path}")
