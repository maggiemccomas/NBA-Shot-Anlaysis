
# import libraries

import ssl
import json 
import datetime
import pandas as pd
import urllib.request
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.offsetbox import  OffsetImage
from matplotlib.patches import Circle, Rectangle, Arc
from nba_api.stats.endpoints import shotchartdetail

# JSON requests

json_Steph = shotchartdetail.ShotChartDetail(team_id = 0, player_id = 201939, context_measure_simple = 'FGA', 
                                                  season_nullable = '2021-22', season_type_all_star = 'Regular Season')

json_Dell = shotchartdetail.ShotChartDetail(team_id = 0,player_id = 209, context_measure_simple = 'FGA', 
                                                  season_nullable = '1997-98', season_type_all_star = 'Regular Season')

# Get nba data

def process_nba_data(json_data):
    data = json.loads(json_data.get_json())
    data = data['resultSets'][0]
    headers = data['headers']
    rows = data['rowSet']
    return pd.DataFrame(rows, columns = headers)

shot_data_Steph = process_nba_data(json_Steph)
shot_data_Dell = process_nba_data(json_Dell)

def process_shot_data(data):
    data['GAME_DATE'] = data['GAME_DATE'].apply(lambda x: datetime.datetime.strptime(x, '%Y%m%d').strftime('%m-%d-%Y'))
    data['SHOT_TYPE'] = data['SHOT_TYPE'].replace({'2PT Field Goal': '2PT FG', '3PT Field Goal': '3PT FG'})

process_shot_data(shot_data_Steph)
process_shot_data(shot_data_Dell)

def map_period_to_qtr(period):
    quarter_map = {1: 'Q1', 2: 'Q2', 3: 'Q3', 4: 'Q4', 5: 'OT1', 6: 'OT2', 7: 'OT3', 8: 'OT4'}
    return quarter_map.get(period)

shot_data_Steph['QUARTER'] = shot_data_Steph['PERIOD'].apply(map_period_to_qtr)
shot_data_Dell['QUARTER'] = shot_data_Dell['PERIOD'].apply(map_period_to_qtr)

shot_data_Steph.to_csv('steph.csv')
shot_data_Dell.to_csv('dell.csv')

# Draw Court

def draw_court(ax=None, color='black', lw=1, outer_lines=False):
    if ax is None:
        ax = plt.gca()

    hoop = Circle((0, 0), radius=7.5, linewidth=lw, color=color, fill=False)
    backboard = Rectangle((-30, -7.5), 60, -1, linewidth=lw, color=color)

    paint_outer = Rectangle((-80, -47.5), 160, 190, linewidth=lw, color=color, fill=False)
    paint_inner = Rectangle((-60, -47.5), 120, 190, linewidth=lw, color=color, fill=False)
    
    top_free_throw = Arc((0, 142.5), 120, 120, theta1=0, theta2=180,linewidth=lw, color=color, fill=False)
    bottom_free_throw = Arc((0, 142.5), 120, 120, theta1=180, theta2=0,linewidth=lw, color=color, linestyle='dashed')
    restricted = Arc((0, 0), 80, 80, theta1=0, theta2=180, linewidth=lw,color=color)

    corner_three_a = Rectangle((-220, -47.5), 0, 137, linewidth=lw, color=color)
    corner_three_b = Rectangle((220, -47.5), 0, 137, linewidth=lw, color=color)
    three_arc = Arc((0, 0), 475, 475, theta1=22, theta2=158, linewidth=lw,color=color)

    court_elements = [hoop, backboard, paint_outer, paint_inner, top_free_throw, bottom_free_throw, restricted, corner_three_a, corner_three_b, three_arc]

    if outer_lines:
        outer_lines = Rectangle((-250, -47.5), 500, 470, linewidth=lw, color=color, fill=False)
        court_elements.append(outer_lines)

    for element in court_elements:
        ax.add_patch(element)
    
    ax.set_xlim(-250, 250)
    ax.set_ylim(-47.5, 422.5)

    return ax

# Jointplot 

def create_joint_plot(data, player_name, player_number, year, color):
    joint_plot = sns.jointplot(x = data['LOC_X'], y = data['LOC_Y'], kind = 'scatter', space = 0, alpha = 0.5, color = color, s = 50)
    joint_plot.fig.set_size_inches(12, 11)
    ax = joint_plot.ax_joint

    draw_court(ax, outer_lines = True)
    ax.set_xlabel('')
    ax.set_ylabel('')
    plt.tick_params(axis = 'both', which = 'both', length = 0, labelbottom = False, labelleft = False)
    
    ssl._create_default_https_context = ssl._create_unverified_context
    picture = urllib.request.urlretrieve(f"https://cdn.nba.com/headshots/nba/latest/1040x760/{player_number}.png", f'{player_number}.png')
    player_picture = plt.imread(picture[0])
    image = OffsetImage(player_picture, zoom = 0.175)
    image.set_offset((-30, 20)) 
    ax.add_artist(image)

    plt.figtext(0.5, 0.05, f'{player_name} FGA ' f'{year} Regular Season', ha= 'center', fontsize = 20)
    
    plt.savefig(f'{player_number}_joint_plot.png')

create_joint_plot(shot_data_Steph, 'Steph Curry', '201939', '2021-22', '#1D428A')
create_joint_plot(shot_data_Dell, 'Dell Curry', '209', '1997-98', '#00778B')

# misses vs. makes shot plot

def create_player_plot(data, player_name, player_number, year, color):
    fig, ax = plt.subplots(figsize = (12, 11))
    draw_court(ax, outer_lines = True)
    
    missed_shots = data[data['SHOT_MADE_FLAG'] == 0]
    plt.scatter(missed_shots['LOC_X'], missed_shots['LOC_Y'], color = color[0], label = 'Missed Shot', alpha = 0.75, marker = 'x', s = 55)
    
    made_shots = data[data['SHOT_MADE_FLAG'] == 1]
    plt.scatter(made_shots['LOC_X'], made_shots['LOC_Y'], color = color[1], label = 'Made Shot', edgecolor = color[2], alpha = 0.75, s = 50)
    
    plt.tick_params(axis = 'both', which = 'both', length = 0, labelbottom = False, labelleft = False)
    plt.title(f'{player_name} FGA ' f'{year} Regular Season', loc = 'center', fontsize = 20)
    
    plt.legend(loc = 'upper left', fontsize = 16)
    plt.savefig(f'{player_number}_plot.png')

colorSteph = ['#1D428A', '#FFC72C', '#E4A700']
colorDell = ['#F9423A', '#00778B', "#00475A"]
create_player_plot(shot_data_Steph, 'Steph Curry', '201939', '2021-22', colorSteph)
create_player_plot(shot_data_Dell, 'Dell Curry', '209', '1997-98', colorDell)
