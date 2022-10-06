import numpy as np
import pandas as pd
import math
import csv
import random
from sklearn import linear_model
from sklearn.model_selection import cross_val_score

base_elo = 1600
team_elo = {}   # reset each yr
team_stat = {}
X = []
y = []
folder = './Project/data'
# predition_yr = 1516     #2015~2016


def initialize_data(Mstat, Ostat, Tstat):
    new_Mstat = Mstat.drop(['Rk', 'Arena'], axis=1)
    new_Ostat = Ostat.drop(['Rk', 'G', 'MP'], axis=1)
    new_Tstat = Tstat.drop(['Rk', 'G', 'MP'], axis=1)

    team_stats = pd.merge(new_Mstat, new_Ostat, how='left', on='Team')
    team_stats = pd.merge(team_stats, new_Tstat, how='left', on='Team')
    return team_stats.set_index('Team', inplace=False, drop=True)


def get_elo(team):
    try:
        return team_elo[team]
    except:
        team_elo[team] = base_elo
        return team_elo[team]


"""
def get_elo(season, team):
    try:
        return team_elo[season][team]
    except:
        try:
            # Get the previous season's ending value.
            team_elo[season][team] = team_elo[season-1][team]
            return team_elo[season][team]
        except:
            # Get the starter elo.
            team_elo[season][team] = base_elo
            return team_elo[season][team]
"""


def update_elo(win_team, lose_team):
    winner_rank = get_elo(win_team)
    loser_rank = get_elo(lose_team)

    rank_diff = winner_rank - loser_rank
    exp = (rank_diff * -1) / 400
    odds = 1 / (1 + math.pow(10, exp))
    
    # change K base on elo
    if winner_rank < 2100:
        k = 32
    elif winner_rank >= 2100 and winner_rank < 2400:
        k = 24
    else:
        k = 16

    # update rank
    new_winner_rank = round(winner_rank + (k * (1 - odds)))
    new_loser_rank = round(loser_rank + (k * (0 - odds)))
    return new_winner_rank, new_loser_rank


def build_data(all_data):
    print("Building data set..")
    X = []
    skip = 0
    for index, row in all_data.iterrows():
        Wteam = row['WTeam']
        Lteam = row['LTeam']

        team1_elo = get_elo(Wteam)
        team2_elo = get_elo(Lteam)

        # home team elo+100
        if row['WLoc'] == 'H':
            team1_elo += 100
        else:
            team2_elo += 100

        team1_features = [team1_elo]
        team2_features = [team2_elo]

        # 添加我们从basketball reference.com获得的每个队伍的统计信息
        for key, value in team_stat.loc[Wteam].iteritems():
            team1_features.append(value)
        for key, value in team_stat.loc[Lteam].iteritems():
            team2_features.append(value)

        # 将两支队伍的特征值随机的分配在每场比赛数据的左右两侧
        # 并将对应的0/1赋给y值
        if random.random() > 0.5:
            X.append(team1_features + team2_features)
            y.append(0)
        else:
            X.append(team2_features + team1_features)
            y.append(1)

        if skip == 0:
            print('X', X)
            skip = 1

        # 根据这场比赛的数据更新队伍的elo值
        new_winner_rank, new_loser_rank = update_elo(Wteam, Lteam)
        team_elo[Wteam] = new_winner_rank
        team_elo[Lteam] = new_loser_rank

    return np.nan_to_num(X), y


def predict_winner(team_1, team_2, model):
    features = []

    # team 1，away
    features.append(get_elo(team_1))
    for key, value in team_stat.loc[team_1].iteritems():
        features.append(value)

    # team 2，home
    features.append(get_elo(team_2) + 100)
    for key, value in team_stat.loc[team_2].iteritems():
        features.append(value)

    features = np.nan_to_num(features)
    return model.predict_proba([features])


if __name__ == '__main__':

    Mstat = pd.read_csv(folder + '/15-16Miscellaneous_Stat.csv')
    Ostat = pd.read_csv(folder + '/15-16Opponent_Per_Game_Stat.csv')
    Tstat = pd.read_csv(folder + '/15-16Team_Per_Game_Stat.csv')

    team_stat = initialize_data(Mstat, Ostat, Tstat)

    result_data = pd.read_csv(folder + '/2015-2016_result.csv')
    X, y = build_data(result_data)

    # 训练网络模型
    print("Fitting on %d game samples.." % len(X))

    model = linear_model.LogisticRegression()
    model.fit(X, y)

    # 利用10折交叉验证计算训练正确率
    print("Doing cross-validation..")
    print(cross_val_score(model, X, y, cv=10,
          scoring='accuracy', n_jobs=-1).mean())
    model.fit(X, y)

    print('Predicting on new schedule..')
    schedule = pd.read_csv(folder + '/16-17Schedule.csv')
    result = []
    for index, row in schedule.iterrows():
        team1 = row['Vteam']
        team2 = row['Hteam']
        pred = predict_winner(team1, team2, model)
        prob = pred[0][0]
        if prob > 0.5:
            winner = team1
            loser = team2
            result.append([winner, loser, prob])
        else:
            winner = team2
            loser = team1
            result.append([winner, loser, 1 - prob])

    with open(folder + '16-17Result.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['win', 'lose', 'probability'])
        writer.writerows(result)
        print('done.')
