import numpy as np
import pandas as pd
import math
import csv
import random

folder = './Project/data'
principal = 10000  # 本金
singleBet = 912  # 每場賭金


def StartBet(odds, result):
    win1 = BetAveraging(odds, result, False, False)
    win2 = BetAveraging(odds, result, True, False)
    win3 = EarnAveraging(odds, result, singleBet, False)
    win4 = DoubleDown(odds, result, 3, False)

    print("Principal: $", principal, "Single bet: $",  singleBet)
    print('Bet averaging: %.2f' % float(win1/principal*100), '%')
    print('Accumulated bet averaging: %.2f' % float(win2/principal*100), '%')
    print('Earn averaging: %.2f' % float(win3/principal*100), '%')
    print('Double down: %.2f' % float(win4/principal*100), '%')


"""
======均注======
玩法: 每次賭金相同
param:
bool all: if false, only bet probability above prob
float prob: probability threshold
bool accumulate: if true, bet accumulates
"""


def BetAveraging(df1, df2, accumulate=False, all=True, prob=0.6):
    win = 0
    bet = singleBet
    for i in range(len(df2.index)):
        if float(df2['probability'][i]) < prob and not all:
            continue
        if df2['Correct'][i] == 1:
            if df2['WLoc'][i] == 'V':
                win = win + bet*df1['odds_away'][i] - bet
                if accumulate:
                    bet = bet + (bet*df1['odds_away'][i] - bet)/2
            elif df2['WLoc'][i] == 'H':
                win = win + bet*df1['odds_home'][i] - bet
                if accumulate:
                    bet = bet + (bet*df1['odds_home'][i] - bet)/2
        elif df2['Incorrect'][i] == 1:
            win -= bet
            if accumulate:
                bet = singleBet
            if principal + win < bet:
                break
    return win


"""
======均利======
玩法: 每次的獲利都相同
param:
int profit: how much you earn everytime you win
"""


def EarnAveraging(df1, df2, profit=singleBet, all=True, prob=0.6):
    win = 0
    bet = singleBet
    for i in range(len(df2.index)):
        if float(df2['probability'][i]) < prob and not all:
            continue
        if df2['Correct'][i] == 1:
            win += profit
        elif df2['Incorrect'][i] == 1:
            if df2['WLoc'][i] == 'V':
                win -= profit/(df1['odds_away'][i]-1)
                if principal + win < 0:
                    break
            elif df2['WLoc'][i] == 'H':
                win -= profit/(df1['odds_home'][i]-1)
                if principal + win < 0:
                    break
    return win


"""
======倍注======
玩法: 如果輸，下一場就依照上一場的賭金往上多加一倍直到獲勝. 默認最多三倍
param:
int times: maximum times of doubling the bet (Careful!)
"""


def DoubleDown(df1, df2, times=3, all=True, prob=0.6):
    win = 0
    double = times
    bet = singleBet
    for i in range(len(df2.index)):
        if float(df2['probability'][i]) < prob and not all:
            continue
        if df2['Correct'][i] == 1:
            if df2['WLoc'][i] == 'V':
                win = win + bet*df1['odds_away'][i] - bet
            elif df2['WLoc'][i] == 'H':
                win = win + bet*df1['odds_home'][i] - bet
            bet = singleBet
        elif df2['Incorrect'][i] == 1:
            win -= bet
            if double == 0:
                bet = singleBet
                double = times
            else:
                bet = 2*bet
                double -= 1
            if principal + win < bet:
                if principal + win < singleBet:
                    break
                else:
                    bet = singleBet
    return win


if __name__ == '__main__':
    odds = pd.read_csv(folder + '/2021-2022_odds.csv')
    result = pd.read_csv(folder + '/Final_Result.csv')

    # data cleaning
    odds['team_home'][949]
    odds = odds.drop(odds.index[949])
    odds = odds.reset_index()
    odds = odds.drop('index', axis=1)
    result = result.drop('Unnamed: 0', 1)

    StartBet(odds, result)
