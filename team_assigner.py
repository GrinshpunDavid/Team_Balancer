import pandas as pd
import numpy as np


class TeamAssigner:
    def __init__(self, data_frame, num_teams=3, max_team_size=5):
        self.data_frame = data_frame
        self.num_teams = num_teams
        self.max_team_size = max_team_size
        self.calculation_df = None

    def calculate_player_statistics(self, raw_data):
        # Perform calculations for each player's statistics
        calculation_data = []
        for col in raw_data.columns:
            col_data = raw_data[col].dropna()
            if not col_data.empty:
                calculation_data.append({
                    "player": col,
                    "mean": np.mean(col_data),
                    "std": np.std(col_data),
                    "observations": len(col_data)
                })

        # Convert the list of dictionaries into a DataFrame
        self.calculation_df = pd.DataFrame(calculation_data)
        self.global_prior_mean = self.calculation_df['mean'].mean()

    def dynamic_c(self, num_observations, std, k=7, epsilon=1e-5):
        if std < 0.1:
            c_value = k / np.sqrt(num_observations)
        else:
            c_value = k / (np.sqrt(num_observations) * (std + epsilon))
        return min(c_value, 5)

    def calculate_player_scores(self):
        # Calculate player scores and apply score adjustments based on standard deviation
        for index, row in self.calculation_df.iterrows():
            num_obs = row['observations']
            C = self.dynamic_c(num_obs, row['std'])
            player_score = (0.3 * C * self.global_prior_mean + 0.7 * num_obs * row['mean']) / (0.3 * C + 0.7 * num_obs)
            std_adjustment = row['std'] / (2 * self.calculation_df['std'].max())
            self.calculation_df.at[index, 'player_score'] = player_score - std_adjustment

        # Normalize the player scores between 1 and 10
        min_score = self.calculation_df['player_score'].min()
        max_score = self.calculation_df['player_score'].max()

        for index in self.calculation_df.index:
            original_score = self.calculation_df.at[index, 'player_score']
            normalized_score = 1 + (original_score - min_score) * (10 - 1) / (max_score - min_score)
            self.calculation_df.at[index, 'normalized_score'] = round(normalized_score, 1)

        # Sort players by normalized score and number of observations
        self.calculation_df = self.calculation_df.sort_values(
            by=['normalized_score', 'observations'], ascending=[False, False]).reset_index(drop=True)

    def sum_scores_by_team(self, df):
        team_scores = df.groupby('team')['normalized_score'].sum()
        return team_scores.sort_values().index.tolist()

    def assign_teams(self):
        # Initialize the 'team' column if it doesn't exist
        if 'team' not in self.calculation_df.columns:
            self.calculation_df['team'] = None

        # Assign the first players to teams
        for i in range(min(self.num_teams, len(self.calculation_df))):
            self.calculation_df.loc[i, 'team'] = i + 1  # Assign team numbers starting from 1

        # Calculate the number of players per team
        team_size = min((len(self.calculation_df) // self.num_teams), self.max_team_size) - 1

        # Assign players to teams
        for _ in range(team_size):
            team_order = self.sum_scores_by_team(self.calculation_df)
            for team in team_order:
                if not self.calculation_df[self.calculation_df['team'].isnull()].empty:
                    max_score_player_idx = self.calculation_df[self.calculation_df['team'].isnull()][
                        'normalized_score'].idxmax()
                    self.calculation_df.loc[max_score_player_idx, 'team'] = team

    def create_team_dataframe(self):
        # Create a new DataFrame with team names as columns
        team_columns = {f'team_{i}': [] for i in range(1, self.calculation_df['team'].nunique() + 1)}
        for team in range(1, len(team_columns) + 1):
            players_in_team = self.calculation_df[self.calculation_df['team'] == team]['player'].tolist()
            team_columns[f'team_{team}'] = players_in_team

        teams_df = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in team_columns.items()]))
        return teams_df

    def assign_players_to_teams(self):
        self.calculate_player_statistics(self.data_frame)
        self.calculate_player_scores()
        self.assign_teams()
        return self.create_team_dataframe()

#
# # Test for the class
# if __name__ == "__main__":
#
#     raw_data = pd.read_excel('team_stat.xlsx')
#     team_assigner = TeamAssigner(raw_data, 2, 6)
#
#     # Call the function
#     result_teams_df = team_assigner.assign_players_to_teams()
#
#     # Print the resulting teams DataFrame
#     print(result_teams_df)
