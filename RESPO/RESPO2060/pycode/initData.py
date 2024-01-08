import csv
import io
import math
import os
import pickle
import sys
from matplotlib.pyplot import winter

import numpy as np

import pandas as pd

import scipy.io as scio
import geopandas as gpd
import shapely
from cfEleP import cfEleP
import json

from uniqeFunction import (dirFlag,geo_distance,getResDir,getWorkDir,
                           makeDir,str2int,getCRF,extractProvinceName)

M = 600

dir_flag = dirFlag()
work_dir = getWorkDir()


def winterHour():
    dir_flag = dirFlag()
    work_dir = getWorkDir()

    winter_hour = []

    for i in range(24*74):
        winter_hour.append(i)

    for i in range(24*(365-46),24*365):
        winter_hour.append(i)

    f_wh = open(work_dir+'data_csv'+dir_flag+'winter_hour.csv','w+')

    for i in winter_hour:
        f_wh.write('%s\n' % i)
    f_wh.close()

    return winter_hour

def seedHour(vre_year,years,step,days,res_tag):
    res_dir = makeDir(getResDir(vre_year,res_tag))
    start_point = []
    hour_profile = []
    hour_pre = {}
    f_hour_seed = open(res_dir+dir_flag+'hour_seed.csv','w+')
    for i in range(days):
        start_point.append(i*step*24)

    if years == 0:
        for i in start_point:
            for k in range(24):
                if i+k < 8759:
                    hour_profile.append(i+k)
    else:
        for i in range(8760 * years):
            hour_profile.append(i)

    for i in range(1,len(hour_profile)):
        hour_pre[hour_profile[i]] = hour_profile[i-1]

    #print(hour_pre)
    for i in hour_profile:
        f_hour_seed.write('%s\n' % i)
    f_hour_seed.close()

    f_hour_pre = open(res_dir+dir_flag+'hour_pre.csv','w+')
    for h in hour_pre:
        f_hour_pre.write('%s,%s\n'%(h,hour_pre[h]))
    f_hour_pre.close()

    with open(res_dir+dir_flag+'hour_pre.pkl','wb') as fout:
        pickle.dump(hour_pre,fout)
    fout.close()


def seedHbh(is8760,step,hours):
    dir_flag = dirFlag()
    work_dir = getWorkDir()

    hour_profile = []
    hour_pre = {}
    f_hour_seed = open(work_dir+'data_csv'+dir_flag+'hour_seed.csv','w+')

    if is8760==0:
        for i in range(24):
            hour_profile.append(i)
        for i in  range(7,hours):
            hour_profile.append(step*i-1)
    else:
        for i in range(8760):
            hour_profile.append(i)

    for i in range(1,len(hour_profile)):
        hour_pre[hour_profile[i]] = hour_profile[i-1]

    #print(hour_pre)
    for i in hour_profile:
        f_hour_seed.write('%s\n' % i)
    f_hour_seed.close()

    with open(work_dir+'data_pkl'+dir_flag+'hour_pre.pkl','wb') as fout:
        pickle.dump(hour_pre,fout)
    fout.close()


def SpurTrunkDis(vre,year,isSubLcInterProvince):
    if vre == 'wind':
        vre_dir = work_dir
    elif vre == 'solar':
        vre_dir = work_dir.replace('LinearOpt2060'+dir_flag,'')

    county_lc_dis = {}

    load_center = {}
    county = {}

    wind_cell_file = {
                      '2016':['China_windpower_offshore_provin_2016.csv',
                            'China_windpower_onshore_provin_2016.csv'],
                      '2015':[
                          'China_windpower_offshore_provin_2015.csv',
                          'China_windpower_onshore_provin_2015.csv'
                      ]}

    solar_cell_file = {'2015':['China_solarpower_coordinate_2015.csv'],
                       '2016':['China_solarpower_coordinate_2016.csv']}

    cell_file = {'wind':wind_cell_file,'solar':solar_cell_file}

    f_lc = open(work_dir + 'data_csv' + dir_flag + 'city_pos.csv','r+')
    next(f_lc)

    for line in f_lc:
        line =  line.replace('\n','')
        line = line.split(',')
        if line[2] not in load_center:
            load_center[line[2]] = []
        load_center[line[2]].append( ( eval(line[0]), eval(line[1]) ) )

    f_lc.close()

    f_county = open(work_dir + 'data_csv' + dir_flag + 'county_geo.csv','r+')
    next(f_county)

    for line in f_county:
        line = line.replace('\n','')
        line = line.split(',')

        if line[2] not in county:
            county[line[2]] = []
        if line[2] == '':
            print(line)
        county[line[2]].append( (eval(line[1]), eval(line[0])) )

    f_county.close()

    county_lc_pair = {}

    for p in county:
        for c in county[p]:
            min_county_lc_dis = sys.maxsize
            if isSubLcInterProvince == 0:
                for lc in load_center[p]:
                    dis = geo_distance(c[1],c[0],lc[1],lc[0])
                    if dis < min_county_lc_dis:
                        min_county_lc_dis = dis
                        county_lc_dis[(c[1],c[0])] = dis
                        county_lc_pair[(c[1],c[0])] = (lc[1],lc[0])
            elif isSubLcInterProvince == 1:
                for p1 in load_center:
                    for lc in load_center[p1]:
                        dis = geo_distance(c[1],c[0],lc[1],lc[0])
                        if dis < min_county_lc_dis:
                            min_county_lc_dis = dis
                            county_lc_dis[(c[1]),c[0]] = dis
                            county_lc_pair[(c[1],c[0])] = (lc[1],lc[0])

    with open(work_dir+'data_pkl'+dir_flag+'county_lc_pair_'+vre+'_'+year+'.pkl','wb+') as fout:
        pickle.dump(county_lc_pair,fout)
    fout.close()

    for file in cell_file[vre][year]:
        fr_cell = open(vre_dir + 'data_csv' + dir_flag + file, 'r+')
        next(fr_cell)
        fw_cell = open(work_dir + 'data_csv' + dir_flag + 'inter_connect_' + file,'w+')
        for cell in fr_cell:
            cell = cell.replace('\n','')
            tmp_cell = cell
            tmp_cell = tmp_cell.split(',')
            if vre == 'wind':
                cell_lat = eval(tmp_cell[3])
                cell_lon = eval(tmp_cell[4])
                province = tmp_cell[8]
            if vre == 'solar':
                cell_lat = eval(tmp_cell[1])
                cell_lon = eval(tmp_cell[2])
                province = tmp_cell[3]

            min_cell_sub_dis = sys.maxsize
            for i in range(len(county[province])):
                cell_sub_dis = geo_distance(cell_lat,cell_lon,county[province][i][1],county[province][i][0])
                if cell_sub_dis < min_cell_sub_dis:
                    min_cell_sub_dis = cell_sub_dis
                    s_lc_dis = county_lc_dis[(county[province][i][1],county[province][i][0])]
                    sub_station_lat = county[province][i][1]
                    sub_station_lon = county[province][i][0]
            fw_cell.write('%s,%s,%s,%s,%s\n' % (cell,sub_station_lat,sub_station_lon,min_cell_sub_dis,s_lc_dis))
        fr_cell.close()
        fw_cell.close()


def initCellData(vre,vre_year,equip,other,om,cap_scale,cap_scale_east,hour_seed,res_tag,year_tag,save_in_data_pkl):

    res_dir = getResDir(year_tag,res_tag) + dir_flag

    with open(res_dir+dir_flag+'scen_params.pkl','rb+') as fin:
        scen_params = pickle.load(fin)
    fin.close()

    provin_abbrev = open(work_dir+'data_csv'+dir_flag+'China_provinces_hz.csv')

    provins = []
    next(provin_abbrev)
    for pro in provin_abbrev:
        pro = pro.replace('\n','')
        pro = pro.split(',')
        provins.append(pro[1])
    provin_abbrev.close()


    cell_file = {
        'wind':{
            '2016':{
                'off':'inter_connect_China_windpower_offshore_provin_2016.csv',
                'on':'inter_connect_China_windpower_onshore_provin_2016.csv'
            },
            '2015':{
                'on':'inter_connect_China_windpower_onshore_provin_2015.csv',
                'off':'inter_connect_China_windpower_offshore_provin_2015.csv'
            }
        }
    }

    mat_file = {
        'wind':{
            '2016':{
                'off':'offshore2016',
                'on':'onshore2016'
            },
            '2015':{
                'off':'offshore2015',
                'on':'onshore2015'
            }
        }
    }

    #read integrated wind or solar
    integrated_file = {
        'wind':'integrated_wind.csv',
        'solar':'integrated_solar.csv'
    }

    integrated = {}
    f_inted = open(work_dir+'data_csv'+dir_flag+integrated_file[vre],'r+',encoding='utf-8')
    next(f_inted)
    for line in f_inted:
        line = line.replace('\n','')
        line = eval(line)
        integrated[(line[0],line[1])] = line[2]
    f_inted.close()

    Hour = len(hour_seed)

    loss_rate = 0.000032 #%/km

    spur_capex = 1.76*getCRF(7.4,25) #yuan/kw-km
    spur_capex_fixed = 159*getCRF(7.4,25) #yuan/kw

    trunk_capex = 1.76*getCRF(7.4,25)
    trunk_capex_fixed = 159*getCRF(7.4,25)

    with open(work_dir+'data_pkl'+dir_flag+'province_loc_by_eco.pkl','rb+') as fin:
        province_loc_by_eco = pickle.load(fin)
    fin.close()


    provin_cell = {}
    provin_cell_lon = {}
    provin_cell_lat = {}
    provin_cf_sort = {}
    cf_prof = {}
    provin_cell_genC = {}
    c_s_dis = {}
    s_lc_dis = {}
    sub_lat = {}
    sub_lon = {}
    cf_elep = {'on':{},'off':{}}

    solar_p = {}

    loc_wind = 0

    if vre == 'solar':
        for i in np.arange(0.0020, 0.8000, 0.0001):
            i = round(i, 4)
            cf_elep['on'][i] = np.round(cfEleP(i,equip[0],other[0],om[0],0.062,25,15,15),3)

        for i in np.arange(0.0020, 0.8000, 0.0001):
            i = round(i, 4)
            cf_elep['off'][i] = np.round(cfEleP(i,equip[1],other[1],om[1],0.062,25,15,15),3)

    else:
        for i in np.arange(0.0020, 1.0000, 0.0001):
            i = round(i, 4)
            cf_elep['on'][i] = np.round(cfEleP(i,equip[0],other[0],om[0],0.062,25,15,15),3)

        for i in np.arange(0.0020, 0.8000, 0.0001):
            i = round(i, 4)
            cf_elep['off'][i] = np.round(cfEleP(i,equip[1],other[1],om[1],0.062,25,15,15),3)

    vre_dir = work_dir.replace('LinearOpt2060'+dir_flag,'')

    zj_count = 0

    for pro in provins:
        provin_cf_sort[pro] = []
        cf_prof[pro] = []
        provin_cell_genC[pro] = []

    if vre == 'wind':
        with open(work_dir+'data_pkl'+dir_flag+'wind_cap_poten_cof.pkl','rb+') as fin:
            wind_cap_poten_cof = pickle.load(fin)
        fin.close()

        wind_landuse_flag = scen_params['vre']['wind_land_use']

        for file in cell_file[vre][vre_year]:
            for pro in provins:
                provin_cell[pro] = {}
                provin_cell_lon[pro] = {}
                provin_cell_lat[pro] = {}
                c_s_dis[pro] = {}
                s_lc_dis[pro] = {}
                sub_lat[pro] = {}
                sub_lon[pro] = {}

            cell_file_r = open(work_dir+'data_csv'+dir_flag+cell_file[vre][vre_year][file])
            for cell in cell_file_r:
                cell = cell.replace('\n','')
                cell = cell.split(',')

                cell[1] = eval(cell[1])
                cell[2] = eval(cell[2])
                cell[1] = int(cell[1])
                cell[2] = int(cell[2])
                cell[1] = str(cell[1])
                cell[2] = str(cell[2])

                if cell[8] == 'Zhejiang':
                    zj_count += 1

                provin_cell[cell[8]][(cell[1],cell[2])] = eval(cell[7])

                provin_cell_lon[cell[8]][(cell[1],cell[2])] = eval(cell[4])

                provin_cell_lat[cell[8]][(cell[1],cell[2])] = eval(cell[3])

                c_s_dis[cell[8]][(cell[1],cell[2])] = eval(cell[11])
                s_lc_dis[cell[8]][(cell[1],cell[2])] = eval(cell[12])

                sub_lat[cell[8]][(cell[1],cell[2])] = eval(cell[9])
                sub_lon[cell[8]][(cell[1],cell[2])] = eval(cell[10])
            cell_file_r.close()

            for root,dirs,files in os.walk(work_dir+'data_mat'+dir_flag+mat_file[vre][vre_year][file]):
                for mat in files:
                    cell_flag = mat.replace('.mat','')
                    cell_flag = cell_flag.split('_')
                    for pro in provins:
                        if (cell_flag[1],cell_flag[2]) in provin_cell[pro]:
                            pro_flag = pro

                            cell_cf_prof = scio.loadmat(work_dir+'data_mat'+dir_flag+mat_file[vre][vre_year][file]+dir_flag+mat)['X_cf']
                            cell_cf_prof = np.round(cell_cf_prof[:8760],3)
                            
                            year_cf = np.sum(cell_cf_prof[:8760])/8760
                            year_cf = round(year_cf,4)
                            CF = sum(cell_cf_prof[i] for i in hour_seed)/Hour
                            CF = round(CF[0],4)
                            
                            cell_gen_poten = cap_scale*provin_cell[pro_flag][(cell_flag[1],cell_flag[2])]

                            cell_gen_poten = wind_cap_poten_cof[file][(cell_flag[1],cell_flag[2])][wind_landuse_flag] * cell_gen_poten

                            

                            if pro in province_loc_by_eco['east']:
                                cell_gen_poten = cap_scale_east * cell_gen_poten

                            if CF >= 0.0020 and year_cf >= 0.0020:
                                gen_cost = cf_elep[file][CF]*year_cf/CF
                                GEN_COST = cf_elep[file][year_cf]
                            if CF >= 0.0020 and gen_cost >= 0 and cell_gen_poten != 0:
                                cell_sub_dis = c_s_dis[pro_flag][(cell_flag[1],cell_flag[2])]
                                sub_lc_dis = s_lc_dis[pro_flag][(cell_flag[1],cell_flag[2])]
                                cell_sub_lat = sub_lat[pro_flag][(cell_flag[1],cell_flag[2])]
                                cell_sub_lon = sub_lon[pro_flag][(cell_flag[1],cell_flag[2])]

                                spur_cost = ((spur_capex*cell_sub_dis+spur_capex_fixed)/
                                                (Hour*CF*math.pow(1-loss_rate,cell_sub_dis)))
                                trunk_cost = ((trunk_capex*sub_lc_dis+trunk_capex_fixed)/
                                                (Hour*CF*math.pow(1-loss_rate,cell_sub_dis+sub_lc_dis)))

                                #spur_cost = ((spur_capex*cell_sub_dis+spur_capex_fixed))
                                #trunk_cost = ((trunk_capex*sub_lc_dis+trunk_capex_fixed))

                                cell_cf_prof = cell_cf_prof.T

                                inted_count = 0

                                lon = provin_cell_lon[pro_flag][(cell_flag[1],cell_flag[2])]
                                lat = provin_cell_lat[pro_flag][(cell_flag[1],cell_flag[2])]

                                cap_poten = cell_gen_poten/(8760*year_cf)

                                for pos in integrated.keys():
                                    if (lon-0.15625) <= pos[0] and pos[0] <= (lon+0.15625):
                                        if (lat-0.125) <= pos[1] and pos[1] <= (lat+0.125):
                                            inted_count += integrated[pos]

                                if cap_poten != 0:
                                    inted_cof = (inted_count * 0.001) / cap_poten
                                else:
                                    inted_cof = 0
                                if inted_cof >= 1:
                                    inted_cof = 1
                                
                                inted_cof = np.round(inted_cof,3)

                                loc_wind += inted_cof * cap_poten

                                #inted_cof = 0
                                if file == 'off':
                                    off_on = 0
                                elif file == 'on':
                                    off_on = 1

                                #if pro_flag == 'Zhejiang':
                                #    zj_count += 1

                                provin_cf_sort[pro_flag].append(
                                    [
                                        str2int(cell_flag[0]+cell_flag[1]),#0
                                        CF,#1
                                        off_on,#2
                                        cap_poten,#3
                                        np.round(sum(cap_poten*cell_cf_prof[0][h] for h in hour_seed),4),#4
                                        gen_cost,#5
                                        0,#6
                                        lon,#7
                                        lat,#8
                                        spur_cost,#9
                                        trunk_cost,#10
                                        cell_sub_dis,#11
                                        sub_lc_dis,#12
                                        inted_cof,#13
                                        GEN_COST,#14
                                        year_cf,#15
                                        cell_sub_lat,#16
                                        cell_sub_lon #17
                                    ]
                                )
                                cf_prof[pro_flag].append(cell_cf_prof[0])
                                provin_cell_genC[pro_flag].append(GEN_COST)
                            break #很关键，不要动它
    elif vre == 'solar':
        for pro in provins:
                provin_cell[pro] = {}
                provin_cell_lon[pro] = {}
                provin_cell_lat[pro] = {}
                c_s_dis[pro] = {}
                s_lc_dis[pro] = {}
                sub_lat[pro] = {}
                sub_lon[pro] = {}

        with open(vre_dir+'data_pkl'+dir_flag+'China_solarpower_province_'+vre_year+'.pkl','rb+') as fin:
            vre_cell = pickle.load(fin)
        fin.close()

        with open(work_dir+'data_pkl'+dir_flag+'solar_poten_info_'+vre_year+'.pkl','rb+') as fin:
            solar_poten_info = pickle.load(fin)
        fin.close()
        
        solar_landuse_flag = scen_params['vre']['solar_land_use']

        vre_coordinate = {}

        f_coor = open(work_dir+'data_csv'+dir_flag+'inter_connect_China_solarpower_coordinate_2015.csv','r+')

        for line in f_coor:
            line = line.replace('\n','')
            line = line.split(',')

            key = (eval(line[1]),eval(line[2]))

            vre_coordinate[key] = [
                eval(line[4]),
                eval(line[5]),
                eval(line[6]),
                eval(line[7])
            ]
        f_coor.close()

        for i in vre_cell['index']:
            key = (vre_cell['lat'][i],vre_cell['lon'][i])
            
            if vre_cell['province'][i] not in solar_p:
                solar_p[vre_cell['province'][i]] = 0

            if scen_params['vre']['is_solar_landuse_sw']:
                tmp_key = (vre_cell['lon'][i],vre_cell['lat'][i])
                vre_cell['cf'][i] = solar_poten_info[tmp_key][solar_landuse_flag]['cf']
                
                if vre_cell['isDPV'][i] == 0:
                    vre_cell['cap'][i] = solar_poten_info[tmp_key][solar_landuse_flag]['cap']
                
                    vre_cell['ele'][i] = (solar_poten_info[tmp_key][solar_landuse_flag]['cap']
                                          *solar_poten_info[tmp_key][solar_landuse_flag]['cf'])
                    
                elif vre_cell['isDPV'][i] == 1:
                    vre_cell['ele'][i] = vre_cell['cap'][i] * vre_cell['cf'][i]

            vre_cell['cf'][i] = np.round(vre_cell['cf'][i],3)

            year_cf = round(sum(vre_cell['cf'][i][:8760])/8760,4)

            CF = round(sum(vre_cell['cf'][i][h] for h in hour_seed)/Hour,4)

            cap_poten = cap_scale * vre_cell['cap'][i]

            #if vre_cell['province'][i] in province_loc_by_eco['east']:
            #    cap_poten = cap_scale_east * cap_poten

            ele_gen = cap_scale * round(sum(vre_cell['ele'][i][h] for h in hour_seed),4)

            if CF >= 0.0020 and year_cf >= 0.0020:
                if vre_cell['isDPV'][i] == 0:
                    gen_cost = cf_elep['on'][CF] * year_cf / CF

                    GEN_COST = cf_elep['on'][year_cf]
                else:
                    gen_cost = cf_elep['off'][CF] * year_cf / CF

                    GEN_COST = cf_elep['off'][year_cf]

            if CF >= 0.0020 and gen_cost >= 0 and cap_poten > 0:
                cell_sub_lat = vre_coordinate[key][0]
                cell_sub_lon = vre_coordinate[key][1]

                cell_sub_dis = vre_coordinate[key][2]
                sub_lc_dis = vre_coordinate[key][3]

                spur_cost = (
                    (spur_capex*cell_sub_dis+spur_capex_fixed)
                    / (Hour*CF*math.pow(1-loss_rate,cell_sub_dis))
                )

                trunk_cost = (
                    (trunk_capex*sub_lc_dis+trunk_capex_fixed)
                    / (Hour*CF*math.pow(1-loss_rate,cell_sub_dis+sub_lc_dis))
                )

                #spur_cost = ((spur_capex*cell_sub_dis+spur_capex_fixed))
                #trunk_cost = ((trunk_capex*sub_lc_dis+trunk_capex_fixed))

                inted_count = 0

                for pos in integrated:
                    if (key[1]-0.15625) <= pos[0] and pos[0] <= (key[1]+0.15625):
                        if (key[0]-0.125) <= pos[1] and pos[1] <= (key[0]+0.125):
                            inted_count += integrated[pos]

                if cap_poten > 0:
                    inted_cof = (0.001 * inted_count) / cap_poten
                else:
                    inted_cof = 0

                if inted_cof > 1:
                    inted_cof = 1

                solar_p[vre_cell['province'][i]] += inted_cof * cap_poten

                if vre_cell['isDPV'][i] == 1:
                    inted_cof = 0

                provin_cf_sort[vre_cell['province'][i]].append([
                    i, #0
                    CF, #1
                    vre_cell['isDPV'][i], #2 是否为分布式光伏,0:不是分布式, 1:是分布式
                    cap_poten, #3
                    ele_gen, #4
                    gen_cost, #5
                    0, #6
                    vre_cell['lon'][i], #7
                    vre_cell['lat'][i], #8
                    spur_cost, #9
                    trunk_cost, #10
                    cell_sub_dis, #11
                    sub_lc_dis, #12
                    inted_cof, #13
                    GEN_COST, #14
                    year_cf, #15
                    cell_sub_lat, #16
                    cell_sub_lon #17
                ])

                cf_prof[vre_cell['province'][i]].append(vre_cell['cf'][i])

                provin_cell_genC[vre_cell['province'][i]].append(GEN_COST)


   # print(provin_cell_genC['Anhui'][0])
    #print(cf_prof['Anhui'][0])
    #if vre == 'wind':
    #    print(len(provin_cf_sort['Zhejiang']))
    #print(zj_count)

    #print(loc_wind)
    #print(solar_p)
    #print(sum(solar_p.values()))

    for pro in provins:
        provin_cell_genC[pro] = np.array([provin_cell_genC[pro]]).T
        cf_prof[pro] = np.array(cf_prof[pro])
        cf_prof[pro] = np.hstack((provin_cell_genC[pro],cf_prof[pro]))

        provin_cf_sort[pro] = np.array(provin_cf_sort[pro])
        provin_cf_sort[pro] = provin_cf_sort[pro][np.argsort(provin_cf_sort[pro][:,14])]

        cf_prof[pro] = cf_prof[pro][np.argsort(cf_prof[pro][:,0])]
        cf_prof[pro] = np.delete(cf_prof[pro],0,axis=1)

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

            if sub_cap > 0:
                sub_cell_info[pro][s]['cf'] = sub_cfs/sub_cap
                sub_cell_info[pro][s]['cap'] = sub_cap
            else:
                sub_cell_info[pro][s]['cf'] = sub_cfs * 0
                sub_cell_info[pro][s]['cap'] = 0


    re_county = gpd.read_file(work_dir+'data_shp'+dir_flag+'re_county_level.shp')

    #print(len(provin_cf_sort['Zhejiang']))
    cell_shp = {'pro':[],'id':[],'geometry':[],'inted_cof':[],'cap':[],'cost':[]}
    for pro in provins:
        for i in range(len(provin_cf_sort[pro])):
            if provin_cf_sort[pro][i][2] == 0:
                lon = provin_cf_sort[pro][i][7]
                lat = provin_cf_sort[pro][i][8]
                coordinate = [(lon-0.15625,lat-0.125),(lon+0.15625,lat-0.125),
                                (lon+0.15625,lat+0.125),(lon-0.15625,lat+0.125)]
                polygon = shapely.geometry.Polygon(coordinate)
                cell_shp['pro'].append(pro)
                cell_shp['id'].append(provin_cf_sort[pro][i][0])
                cell_shp['geometry'].append(polygon)
                cell_shp['inted_cof'].append(provin_cf_sort[pro][i][13])
                cell_shp['cap'].append(provin_cf_sort[pro][i][3])
                cell_shp['cost'].append(provin_cf_sort[pro][i][14])

    cell_gdf = gpd.GeoDataFrame(cell_shp,geometry=cell_shp['geometry'],crs='EPSG:4326')

    county_cell_gdf = gpd.sjoin(left_df=cell_gdf,right_df=re_county,op='intersects')

    county_cell_dict = county_cell_gdf.to_dict('list')

    county_cell = {}
    county_cap = {}
    cell_inted_cof = {}

    for i in range(len(county_cell_dict['NAME_3'])):
        county_name = county_cell_dict['NAME_3'][i]

        if county_cell_dict[vre][i] != 0 and county_name not in county_cap:
            county_cap[county_name] = county_cell_dict[vre][i]

        if county_cell_dict['id'][i] not in cell_inted_cof:
            cell_inted_cof[int(county_cell_dict['id'][i])] = county_cell_dict['inted_cof'][i]

        if county_name not in county_cell.keys():
            county_cell[county_name] = []
        else:
            county_cell[county_name].append([county_cell_dict['id'][i],
                                             county_cell_dict['cap'][i],
                                             county_cell_dict['cost'][i]])
    for county in county_cell:
        county_cell[county] = np.array(county_cell[county])
        if len(county_cell[county]) > 1:
            county_cell[county] = county_cell[county][np.argsort(county_cell[county][:,2])]

    for county in county_cap:
        for i in range(len(county_cell[county])):
            deploy_cof = county_cap[county] / county_cell[county][i][1]

            if deploy_cof+cell_inted_cof[int(county_cell[county][i][0])] >= 1:
                 county_cap[county] -= (1-cell_inted_cof[int(county_cell[county][i][0])])*county_cell[county][i][1]
                 cell_inted_cof[int(county_cell[county][i][0])] = 1
            else:
                county_cap[county] = 0
                if deploy_cof > 0:
                    cell_inted_cof[int(county_cell[county][i][0])] += deploy_cof

    for pro in provins:
        for i in range(len(provin_cf_sort[pro])):
            if provin_cf_sort[pro][i][2] == 0:
                if int(provin_cf_sort[pro][i][0]) in cell_inted_cof:
                    if cell_inted_cof[int(provin_cf_sort[pro][i][0])] > 0:
                        provin_cf_sort[pro][i][13] = cell_inted_cof[int(provin_cf_sort[pro][i][0])]

    #处理缺失并网数据
    ppc_file = {'wind':'province_wind_data.csv','solar':'province_solar_data.csv'}
    ppc = {} #planned province cap

    ppc_dif = {}
    f_ppc = open(work_dir+'data_csv'+dir_flag+ppc_file[vre],'r+')
    for line in f_ppc:
        line = line.replace('\n','')
        line = line.split(',')
        ppc[line[0]] = 0.01 * eval(line[1])
    f_ppc.close()


    for pro in provins:
        cap_count = 0
        for cell in provin_cf_sort[pro]:
            cap_count += cell[3]*cell[13]

        ppc_dif[pro] = ppc[pro] - cap_count

    #print(ppc_dif)

    #print(provin_cf_sort['Anhui'][:10])

    for pro in provins:
        dif_cap = ppc_dif[pro]
        for i in range(len(provin_cf_sort[pro])):
            dif_per_inted = dif_cap/provin_cf_sort[pro][i][3]
            if dif_per_inted+provin_cf_sort[pro][i][13] >= 1:
                dif_cap = dif_cap - (1-provin_cf_sort[pro][i][13])*provin_cf_sort[pro][i][3]
                provin_cf_sort[pro][i][13] = 1
            else:
                dif_cap = 0
                if dif_per_inted > 0:
                    provin_cf_sort[pro][i][13] += dif_per_inted

    total_cap_inted = 0
    for pro in provins:
        for cell in provin_cf_sort[pro]:
            total_cap_inted += cell[3] * cell[13]

    print(vre+' inted: ',total_cap_inted)

    save_as_pkl = {'provin_cf_sort':provin_cf_sort,'cf_prof':cf_prof,'sub_cell_info':sub_cell_info}

    if save_in_data_pkl:

        with open(work_dir + "data_pkl" + dir_flag + vre+'_cell_'+vre_year+'.pkl', 'wb+') as fout:
            pickle.dump(save_as_pkl,fout)
        fout.close()

    with open(res_dir + vre+'_cell_'+vre_year+'.pkl', 'wb+') as fout:
        pickle.dump(save_as_pkl,fout)
    fout.close()


def initProvincialHydroBeta(total,sw,nw,e_c,other):
    pro_loc_in_china = {}

    f_province = open(work_dir+'data_csv'+dir_flag+'China_provinces_hz.csv','r+')
    next(f_province)

    for line in f_province:
        line = line.replace('\n','')
        line = line.split(',')

        if line[6] == 'East' or line[6] == 'Central':
            region = 'e_c'
        elif line[6] == 'SW' or line[6] == 'NW':
            region = line[6]
        else:
            region = 'other'

        pro_loc_in_china[line[1]] = region

    f_province.close()

    region_hydro = {}

    current_hydro = {}

    f_hydro = open(work_dir+'data_csv'+dir_flag+'hydro.csv','r+')

    for line in f_hydro:
        line = line.replace('\n','')
        line = line.split(',')

        if pro_loc_in_china[line[0]] not in region_hydro:
            region_hydro[pro_loc_in_china[line[0]]] = 0

        current_hydro[line[0]] = eval(line[1])
        region_hydro[pro_loc_in_china[line[0]]] += eval(line[1])

    f_hydro.close()

    region_hydro_2060 = {
        'SW':1000 * total * sw,
        'NW':1000 * total * nw,
        'e_c':1000 * total * e_c,
        'other':1000 * total * other
    }

    hydro_beta_province = {}

    for pro in current_hydro:
        region = pro_loc_in_china[pro]
        hydro_beta_province[pro] = region_hydro_2060[region] / region_hydro[region]

    with open(work_dir+'data_pkl'+dir_flag+'hydro_beta_province.pkl','wb+') as fout:
        pickle.dump(hydro_beta_province,fout)
    fout.close()


def initDemLayer(alpha,coalBeta,nuclearBeta,gasBeta,bioGama,nuclearTheta,coalTheta,ccsLoss,res_tag,year_tag,save_in_data_pkl):
    res_dir = getResDir(year_tag,res_tag) + dir_flag


    scale = 0.001

    #province demand
    grid4_dem = scio.loadmat(work_dir + "data_mat" + dir_flag + 'RegionDemand_Rev2.mat')
    grid4_dem = grid4_dem['Region_dem'][0]


    provins = pd.read_csv(work_dir+'data_csv'+dir_flag+'China_provinces_hz.csv')
    dem2030 = pd.read_csv(work_dir+'data_csv'+dir_flag+'province_dem.csv')

    provin_dem2030 = {}
    provin_hour_dem2030 = {}
    provin_hour_dem2060 = {}

    for i in range(len(dem2030['provin'])):
        provin_dem2030[dem2030['provin'][i]] = dem2030['dem'][i]

    provin_py = list(provins['provin_py'])
    provin_reg = list(provins['region'])
    regions = {'NE':0,'NW':1,'S':2,'SH':3}
    pro_reg = {} #T: xizang
    pro_reg_cof = {}
    reg_tot_dem2030 = {'NE':0,'NW':0,'S':0,'SH':0,'T':0}

    for i in range(len(provin_py)):
        pro_reg[provin_py[i]] = provin_reg[i]

    #Anhui:SH
    for pro in provin_dem2030:
        reg_tot_dem2030[pro_reg[pro]] += provin_dem2030[pro]

    for pro in pro_reg:
        pro_reg_cof[pro] = provin_dem2030[pro] / reg_tot_dem2030[pro_reg[pro]]

    for pro in pro_reg:
        if pro_reg[pro] != 'T':
            provin_hour_dem2030[pro] = scale * pro_reg_cof[pro] * grid4_dem[regions[pro_reg[pro]]][:]
        elif pro_reg[pro] == 'T':
            provin_hour_dem2030[pro] = scale * (provin_dem2030[pro] / reg_tot_dem2030['NE']) * grid4_dem[0][:]

    for pro in pro_reg:
        if pro not in provin_hour_dem2060:
            provin_hour_dem2060[pro] = []
        for i in range(len(provin_hour_dem2030[pro])):
            provin_hour_dem2030[pro][i][0] = format(provin_hour_dem2030[pro][i][0],'.4f')
            provin_hour_dem2060[pro].append(alpha*provin_hour_dem2030[pro][i][0])

    dem_folder = makeDir(work_dir+'data_csv'+dir_flag+'province_demand_by_hour_2060')+dir_flag

    for pro in provin_hour_dem2060:
        f_pro_dem = open(dem_folder+pro+'.csv','w+')
        for h in range(len(provin_hour_dem2060[pro])):
            f_pro_dem.write('%s,%s\n' % (h,provin_hour_dem2060[pro][h]))
        f_pro_dem.close()

    f_nation_dem_full = open(dem_folder+'nation_dem_full.csv','w+')

    for h in range(8760):
        dem_h = 0
        for pro in provin_hour_dem2060:
            dem_h += provin_hour_dem2060[pro][h]

        f_nation_dem_full.write(str(h)+','+str(dem_h)+'\n')

    f_nation_dem_full.close()

    with open(work_dir+'data_pkl'+dir_flag+'province_demand_full_2060.pkl','wb') as fout:
        pickle.dump(provin_hour_dem2060,fout)
    fout.close()

    sum_dem = 0
    for pro in pro_reg:
        sum_dem += sum(provin_hour_dem2060[pro])
    print('Total demand in 2060:',sum_dem)

    with open(work_dir+'data_pkl'+dir_flag+'tot_dem2060.pkl','wb+') as fout:
        pickle.dump({'tot_dem':sum_dem},fout)
    fout.close()

    #province layer capacity
    files = ['nuclear.csv','coal.csv','hydro.csv','bio.csv','gas.csv','beccs.csv']
    conv_count = {'nuclear.csv':0,'coal.csv':0,'hydro.csv':0,'bio.csv':0,'gas.csv':0,'beccs.csv':0}
    provin_conv = {}

    for file in files:
        fr = open(work_dir+'data_csv'+dir_flag+file,'r+')
        for line in fr:
            line = line.replace('\n','')
            line = line.split(',')
            if line[0] not in provin_conv.keys():
                provin_conv[line[0]] = []
            
            provin_conv[line[0]].append(eval(line[1]))
            conv_count[file] += eval(line[1])
        fr.close()

    
    

    #print(conv_count)

    mat_name = 'levels_reg_Rev2_CHPfree_CHPmid_05_peakwk5margin.mat'
    grid4_layer = scio.loadmat(work_dir + 'data_mat' + dir_flag + mat_name)
    grid4_layer = grid4_layer['levels_reg'][0]

    layer_cap_profile = []

    pro_layer = {}

    #print(conv_count)

    #print(conv_count['hydro.csv']*hydroBeta)

    for reg in regions:
        layer_cap_profile.append(np.zeros((len(grid4_layer[regions[reg]]),4),float))

    for reg in regions:
        layer_cap_profile[regions[reg]][:,:-1] = grid4_layer[regions[reg]][:,1:] - grid4_layer[regions[reg]][:,:-1]

    layer_cap = {'NW':[],'NE':[],'SH':[],'S':[]}

    for reg in layer_cap:
        layer_cap[reg].append(max(layer_cap_profile[regions[reg]][:,0]))
        layer_cap[reg].append(max(layer_cap_profile[regions[reg]][:,1]))
        layer_cap[reg].append(max(layer_cap_profile[regions[reg]][:,2]))
        layer_cap[reg].append(max(layer_cap_profile[regions[reg]][:,3]))

    pro_cap_profile = {}
    pro_layer_cap = {}

    for pro in provin_conv:
        if pro not in pro_cap_profile:
            pro_cap_profile[pro] = []

        if pro not in pro_layer_cap:
            pro_layer_cap[pro] = np.zeros((8760,4))

        for h in range(8760):
            if pro != 'Xizang':
                #nuclear_h = scale * provin_conv[pro][0] * layer_cap_profile[regions[pro_reg[pro]]][h][0] / layer_cap[pro_reg[pro]][0]
                nuclear_h = scale * provin_conv[pro][0]
                
                coal_h = scale * provin_conv[pro][1]
                
                hydro_h = 0.6 * scale * provin_conv[pro][2] * layer_cap_profile[regions[pro_reg[pro]]][h][1] / layer_cap[pro_reg[pro]][1]
                bio_h = scale * provin_conv[pro][3] * layer_cap_profile[regions[pro_reg[pro]]][h][2] / layer_cap[pro_reg[pro]][2]
                gass_h = scale * provin_conv[pro][4] * layer_cap_profile[regions[pro_reg[pro]]][h][2] / layer_cap[pro_reg[pro]][2]
            else:
                nuclear_h = scale * provin_conv[pro][0]
                coal_h = scale * provin_conv[pro][1] * layer_cap_profile[1][h][2] / layer_cap['NW'][2]
                hydro_h = 0.6 * scale * provin_conv[pro][2] * layer_cap_profile[1][h][1] / layer_cap['NW'][1]
                bio_h = scale * provin_conv[pro][3] * layer_cap_profile[1][h][2] / layer_cap['NW'][2]
                gass_h = scale * provin_conv[pro][4] * layer_cap_profile[1][h][2] / layer_cap['NW'][2]

            pro_cap_profile[pro].append([nuclear_h,coal_h,hydro_h,bio_h,gass_h])

        pro_cap_profile[pro] = np.array(pro_cap_profile[pro])

    winter_hour = []
    f_wh = open(work_dir+'data_csv'+dir_flag+'winter_hour.csv','r+')
    for line in f_wh:
        line = line.replace('\n','')
        line = eval(line)
        winter_hour.append(line)
    f_wh.close()

    chp_ccs = {}

    f_cc = open(work_dir+'data_csv'+dir_flag+'chp_ccs.csv','r+')
    for line in f_cc:
        line = line.replace('\n','')
        line = line.split(',')
        chp_ccs[line[0]] = scale * eval(line[1])
    f_cc.close()

    with open(work_dir+'data_pkl'+dir_flag+'hydro_beta_province.pkl','rb+') as fin:
        hydroBetaPro = pickle.load(fin)
    fin.close()

    pro_layer_cap_max = {}

    
    for pro in provin_conv:
        pro_layer_cap[pro][:,0] = np.round(coalTheta * pro_cap_profile[pro][:,1] + coalBeta * pro_cap_profile[pro][:,1],2)

        pro_layer_cap[pro][:,1] = np.round(hydroBetaPro[pro] * pro_cap_profile[pro][:,2],2)

        pro_layer_cap[pro][:,2] = np.round(nuclearTheta * nuclearBeta * pro_cap_profile[pro][:,0],2)

        pro_layer_cap[pro][:,3] = np.round(gasBeta * pro_cap_profile[pro][:,4])

        pro_layer_cap_max[pro] = [
            scale * (coalTheta * provin_conv[pro][1] + coalBeta * provin_conv[pro][1]) + chp_ccs[pro],
            scale *  hydroBetaPro[pro] * provin_conv[pro][2],
            scale * nuclearTheta * provin_conv[pro][0],
            scale * gasBeta * provin_conv[pro][4],
            chp_ccs[pro],
            bioGama * provin_conv[pro][5]
        ]

        for h in range(8760):
            provin_hour_dem2060[pro][h] = (
                provin_hour_dem2060[pro][h] -
                (1-nuclearTheta) * nuclearBeta * pro_cap_profile[pro][h][0] -
                (1-ccsLoss) * bioGama * provin_conv[pro][5]
            )

            if h in winter_hour:
                provin_hour_dem2060[pro][h] = provin_hour_dem2060[pro][h] - chp_ccs[pro]
            else:
                pro_layer_cap[pro][h][0] += chp_ccs[pro]

            provin_hour_dem2060[pro][h] = np.round(provin_hour_dem2060[pro][h],1)
            

    #print(pro_layer_cap['Anhui'][:,0])
    
    layer_cap_load = {'layer_lvl':pro_layer,
                      'layer_cap':pro_layer_cap,
                      'layer_load':pro_layer_cap,
                      'pro_layerCap_split':pro_cap_profile,
                      'layer_cap_max':pro_layer_cap_max}

    for pro in provin_hour_dem2060:
        for h in range(8760):
            if provin_hour_dem2060[pro][h] < 0:
                provin_hour_dem2060[pro][h] = 0.01

    if save_in_data_pkl:
        with open(work_dir+'data_pkl'+dir_flag+'provin_hour_dem2060.pkl','wb') as fout:
            pickle.dump(provin_hour_dem2060,fout)
        fout.close()

    with open(res_dir +'provin_hour_dem2060.pkl','wb') as fout:
        pickle.dump(provin_hour_dem2060,fout)
    fout.close()

    f_nation_dem_part = open(dem_folder+'nation_dem_part.csv','w+')

    for h in range(8760):
        dem_h = 0
        for pro in provin_hour_dem2060:
            dem_h += provin_hour_dem2060[pro][h]

        f_nation_dem_part.write(str(h)+','+str(dem_h)+'\n')

    f_nation_dem_part.close()

    if save_in_data_pkl:
        with open(work_dir+'data_pkl'+dir_flag+'layer_cap_load.pkl','wb') as fout:
            pickle.dump(layer_cap_load,fout)
        fout.close()

    with open(res_dir+'layer_cap_load.pkl','wb') as fout:
        pickle.dump(layer_cap_load,fout)
    fout.close()


    provin_conv_cap2060 = {}

    gen_count = {
        'nuclear':0,
        'coal':0,
        'hydro':0,
        'gas':0,
        'beccs':0
    }

    for pro in provin_conv:
        if pro not in provin_conv_cap2060:
            provin_conv_cap2060[pro] = {}

        provin_conv_cap2060[pro]['nuclear'] = 0.001*provin_conv[pro][0] * nuclearBeta
        gen_count['nuclear'] += 0.001*provin_conv[pro][0] * nuclearBeta

        provin_conv_cap2060[pro]['coal'] = chp_ccs[pro] + coalTheta * 0.001 * provin_conv[pro][1]

        gen_count['coal'] += chp_ccs[pro] + coalTheta * 0.001 * provin_conv[pro][1]

        provin_conv_cap2060[pro]['hydro']  = 0.001 * provin_conv[pro][2] * hydroBetaPro[pro]

        gen_count['hydro'] += 0.001 * provin_conv[pro][2] * hydroBetaPro[pro]

        provin_conv_cap2060[pro]['gas'] = 0.001 * provin_conv[pro][4] * gasBeta

        gen_count['gas'] += 0.001 * provin_conv[pro][4] * gasBeta

        provin_conv_cap2060[pro]['beccs'] = provin_conv[pro][5]

        gen_count['beccs'] += provin_conv[pro][5]

    #print(gen_count)

    if save_in_data_pkl:
        with open(work_dir+'data_pkl'+dir_flag+'conv_cap.pkl','wb') as fout:
            pickle.dump(provin_conv_cap2060,fout)
        fout.close()


    with open(res_dir+'conv_cap.pkl','wb') as fout:
        pickle.dump(provin_conv_cap2060,fout)
    fout.close()

    #print(provin_conv_cap2060)'''


def initModelExovar():
    scale = 0.001

    f_pi = open(work_dir+'data_csv'+dir_flag+'China_provinces_hz.csv') #province infomation
    grid_pro = {}
    next(f_pi)
    for line in f_pi:
        line = line.replace('\n','')
        line = line.split(',')
        if line[5] not in grid_pro:
            grid_pro[line[5]] = []
        grid_pro[line[5]].append(line[1])
    f_pi.close()

    nmr_load = {}
    M_layer_2 = {}
    M_layer_3 = {}
    M_layer_4 = {}
    M_load = {}

    with open(work_dir+'data_pkl'+dir_flag+'provin_hour_dem2060.pkl','rb') as fin:
        provin_dem = pickle.load(fin)
    fin.close()

    with open(work_dir+'data_pkl'+dir_flag+'layer_cap_load.pkl','rb') as fin:
        layer_cap_load = pickle.load(fin)
    fin.close()

    inter_pro_trans = {}
    finter_pro_trans = pd.read_csv(work_dir+'data_csv'+dir_flag+'inter_pro_trans.csv')

    for pro in finter_pro_trans['province']:
        for i in range(len(finter_pro_trans[pro])):
            inter_pro_trans[(pro,finter_pro_trans['province'][i])] = scale * finter_pro_trans[pro][i]


    provin_coord = {}
    f_province = open(work_dir+'data_csv'+dir_flag+'China_provinces_hz.csv','r+')
    next(f_province)
    for line in f_province:
        line = line.replace('\n','')
        line = line.split(',')
        provin_coord[line[1]] = []
        provin_coord[line[1]].append(eval(line[3]))
        provin_coord[line[1]].append(eval(line[4]))

    f_province.close()

    inter_pro_dis = {}

    fnew_trans_cap = pd.read_csv(work_dir+'data_csv'+dir_flag+'new_trans.csv')

    new_trans_cap = {}
    for pro in fnew_trans_cap['province']:
        for i in range(len(fnew_trans_cap[pro])):
            if fnew_trans_cap[pro][i] == 1.0:
                new_trans_cap[(pro,fnew_trans_cap['province'][i])] = 1
            else:
                new_trans_cap[(pro,fnew_trans_cap['province'][i])] = 0

    for pro in new_trans_cap:
        inter_pro_dis[pro] = geo_distance(provin_coord[pro[0]][1],provin_coord[pro[0]][0],provin_coord[pro[1]][1],provin_coord[pro[1]][0])


    provins = layer_cap_load['layer_load'].keys()

    for pro in provins:
        nmr_load[pro] = (layer_cap_load['layer_load'][pro][:,1]+
                         layer_cap_load['layer_load'][pro][:,2]+
                         layer_cap_load['layer_load'][pro][:,3])

    int_index = np.ones((8760,1)) # quzheng yinzi
    for pro in provins:
        M_layer_2[pro] = 2*int_index[:,0] + (layer_cap_load['layer_cap'][pro][:,1] // int_index[:,0])
        M_layer_3[pro] = 2*int_index[:,0] + (layer_cap_load['layer_cap'][pro][:,2] // int_index[:,0])
        M_layer_4[pro] = int_index[:,0] + (layer_cap_load['layer_load'][pro][:,3] // int_index[:,0])
        M_load[pro] = 2 * (provin_dem[pro][:] // int_index[:])

    voltage_convert = {}

    f_vc = open(work_dir+'data_csv'+dir_flag+'voltage_convert.csv','r+')

    for line in f_vc:
        line = line.replace('\n','')
        line = line.split(',')

        voltage_convert[line[0]] = line[1]

    f_vc.close()


    trans_voltage = {}

    f_tv = open(work_dir+'data_csv'+dir_flag+'trans_voltage.csv','r+',encoding='utf-8')

    tv_keys = []

    voltage_kind = []

    for line in f_tv:
        line = line.replace('\n','')
        line = line.split(',')
        start = extractProvinceName(line[1])
        end = extractProvinceName(line[2])

        key = (start,end)

        tv_keys.append(key)

        if line[0] in voltage_convert:
            line[0] = voltage_convert[line[0]]

        if eval(line[0]) not in voltage_kind:
            voltage_kind.append(eval(line[0]))

        if key not in trans_voltage:
            trans_voltage[key] = eval(line[0])
        elif eval(line[0]) > trans_voltage[key]:
            trans_voltage[key] = eval(line[0])
    f_tv.close()

    for pro in tv_keys:
        if (pro[1],pro[0]) not in trans_voltage:
            trans_voltage[(pro[1],pro[0])] = trans_voltage[pro]
        else:
            if trans_voltage[(pro[1],pro[0])] < trans_voltage[pro]:
                trans_voltage[(pro[1],pro[0])] = trans_voltage[pro]

    capex_trans_cap = {}

    f_ctc = open(work_dir+'data_csv'+dir_flag+'capex_trans_cap.csv','r+')

    for line in f_ctc:
        line = line.replace('\n','')
        line = line.split(',')

        capex_trans_cap[eval(line[0])] = eval(line[1]) * getCRF(6.2,25)

    f_ctc.close()

    capex_trans_dis = {}

    f_ctd = open(work_dir+'data_csv'+dir_flag+'capex_trans_dis.csv','r+')

    for line in f_ctd:
        line = line.replace('\n','')
        line = line.split(',')

        capex_trans_dis[eval(line[0])] = eval(line[1]) * getCRF(6.2,50)

    f_ctd.close()

    phs_ub = {}
    phs_lb = {}
    f_phs_ub = open(work_dir+'data_csv'+dir_flag+'phs_ub.csv','r+')
    for line in f_phs_ub:
        line = line.replace('\n','')
        line = line.split(',')
        phs_ub[line[0]] = 0.001 * eval(line[1])
    f_phs_ub.close()

    f_phs_lb = open(work_dir+'data_csv'+dir_flag+'phs_lb.csv','r+')
    for line in f_phs_lb:
        line = line.replace('\n','')
        line = line.split(',')
        phs_lb[line[0]] = 0.001 * eval(line[1])
    f_phs_lb.close()


    save_as_pkl = {'inter_pro_trans':inter_pro_trans,
                   'new_trans':new_trans_cap,
                   'trans_dis':inter_pro_dis,
                   'trans_voltage':trans_voltage,
                   'capex_trans_cap':capex_trans_cap,
                   'capex_trans_dis':capex_trans_dis,
                   'phs_ub':phs_ub,
                   'phs_lb':phs_lb,
                   'grid_pro':grid_pro}
    with open(work_dir+'data_pkl'+dir_flag+'model_exovar.pkl','wb') as fout:
        pickle.dump(save_as_pkl,fout)
    fout.close()




#InitSenerioParams('w2016_s2015','base12')


if __name__ == '__main__':

    winterHour()

    with open(work_dir+'data_pkl'+dir_flag+'China_solarpower_province__2015.pkl','rb+') as fin:
        solar = pickle.load(fin)
    fin.close()

    print(solar.keys())

    #seedHour(1,15,24)

    #SpurTrunkDis('wind','2015',0)

    #SpurTrunkDis('solar','2015',0)


    #initModelExovar()

    #initProvincialHydroBeta(580,0.444,0.085,0.209,0.262)

    #initDemLayer(1.54,0,5,2,3.3,0.8,0.25,0) #alpha,coalBeta,nuclearBeta,hydroBeta,gasBeta,bioGama,nuclearTheta,coalTheta

    #initIntegratedFile()
    #initIntegratedLocation()


    


