import csv
import io
import math
import os
import pickle
import sys

import numpy as np
from numpy.lib.function_base import append
import pandas as pd

import scipy.io as scio
import geopandas as gpd
import shapely
from cfEleP import cfEleP

from initData import initCellData

from uniqeFunction import (dirFlag,getWorkDir,SplitMultipleVreYear,GetHourSeed,getResDir)


dir_flag = dirFlag()
work_dir = getWorkDir()

hourSeed = []

for i in range(8760):
    hourSeed.append(i)

def initMultipleYearCell(vre,vreYear,equip,other,om,capScale,resTag,yearTag,save_in_data_pkl):
    res_dir = getResDir(yearTag,resTag)+dir_flag

    vreYears = SplitMultipleVreYear(vreYear)
    
    for year in vreYears:

        initCellData(vre,year,equip,other,om,capScale,1,hourSeed,resTag,yearTag,save_in_data_pkl)
    
    vreCells = {}

    for year in vreYears:
        vreCells[year] = {}
        with open(work_dir+'data_pkl'+dir_flag+vre+'_cell_'+year+'.pkl','rb+') as fin:
            cell = pickle.load(fin)
        fin.close()
        
        for pro in cell['provin_cf_sort']:
            vreCells[year][pro] = {'info':{},'CF':{}}
        
        for pro in vreCells[year]:
            for i in range(len(cell['provin_cf_sort'][pro])):
                key = (cell['provin_cf_sort'][pro][i][7],
                       cell['provin_cf_sort'][pro][i][8],
                       cell['provin_cf_sort'][pro][i][2])
                
                vreCells[year][pro]['info'][key] = cell['provin_cf_sort'][pro][i]
                vreCells[year][pro]['CF'][key] = cell['cf_prof'][pro][i]
    
    resCell = {'provin_cf_sort':{},'cf_prof':{}}
    
    for pro in vreCells[vreYears[0]]:
        resCell['provin_cf_sort'][pro] = []
        resCell['cf_prof'][pro] = []
        
        for key in vreCells[vreYears[0]][pro]['info']:
            info = vreCells[vreYears[0]][pro]['info'][key]
            info[5] = info[5] * info[4]
            cf = vreCells[vreYears[0]][pro]['CF'][key]
            count = 1
            
            for year in vreYears[1:]:
                
                if key in vreCells[year][pro]['info']:
                    count += 1
                    tmp_info = vreCells[year][pro]['info'][key]
                    tmp_cf = vreCells[year][pro]['CF'][key]

                    info[3] += tmp_info[3]
                    info[4] += tmp_info[4]
                    info[5] += tmp_info[5] * tmp_info[4]

                    cf = np.hstack((cf,tmp_cf))
            
            info[5] = info[5] / info[4]
            info[3] = info[3] / count
            
            if count == len(vreYears):
                resCell['provin_cf_sort'][pro].append(info)
                resCell['cf_prof'][pro].append(cf)
    
    provins = resCell['provin_cf_sort'].keys()
    provin_cf_sort = resCell['provin_cf_sort']
    cf_prof = resCell['cf_prof']
    
    sub_cell_info = {}

    for pro in provins:
        if pro not in sub_cell_info:
            sub_cell_info[pro] = {}
        
        for i in range(len(provin_cf_sort[pro])):
            sub_lat = provin_cf_sort[pro][i][16]
            sub_lon = provin_cf_sort[pro][i][17]

            if (sub_lat,sub_lon) not in sub_cell_info[pro]:
                sub_cell_info[pro][(sub_lat,sub_lon)] = {'cell':[]}
            
            if (vre == 'wind') or (vre == 'solar' and provin_cf_sort[pro][i][2] == 0):
                sub_cell_info[pro][(sub_lat,sub_lon)]['cell'].append(i)

            if 'dis' not in sub_cell_info[pro][(sub_lat,sub_lon)]:
                sub_cell_info[pro][(sub_lat,sub_lon)]['dis'] = provin_cf_sort[pro][i][12]

    for pro in provins:
        for s in sub_cell_info[pro]:
            sub_cfs = np.zeros(len(cf_prof[pro][0]))
            sub_cap = 0

            for c in sub_cell_info[pro][s]['cell']:
                sub_cfs += cf_prof[pro][c] * provin_cf_sort[pro][c][3]
                sub_cap += provin_cf_sort[pro][c][3]
            
            sub_cell_info[pro][s]['cf'] = sub_cfs/sub_cap
            sub_cell_info[pro][s]['cap'] = sub_cap
    
    resCell['sub_cell_info'] = sub_cell_info
    
    if save_in_data_pkl:
        with open(work_dir+'data_pkl'+dir_flag+vre+'_cell_'+vreYear+'.pkl','wb+') as fout:
            pickle.dump(resCell,fout)
        fout.close()
    
    with open(res_dir+vre+'_cell_'+vreYear+'.pkl','wb+') as fout:
        pickle.dump(resCell,fout)
    fout.close()

    

#initMultipleYearCell('wind','1516',[2000,3600],[1000,1500],[40,80],1,hourSeed)
