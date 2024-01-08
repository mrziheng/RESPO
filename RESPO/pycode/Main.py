import os
import pickle
import sys
import numpy as np
import gurobipy as gp
from gurobipy import GRB
from simplejson import load


from uniqeFunction import (dirFlag,makeDir,getWorkDir,
                           getResDir,GetHourSeed,VreYearSplit,
                           SplitMultipleVreYear,GetWinterHour)

from InitData import (initCellData,initDemLayer,initModelExovar,
                      getCRF,seedHour,SpurTrunkDis)

from InitMultipleYearCell import initMultipleYearCell



import json

#from visualization import (windsolarCellMap,GeneratorDistribution,storeProfile,loadProfile,
#                           TotalEnergyToHourVisual,storageCap)

dir_flag = dirFlag()
work_dir = getWorkDir()



def interProvinModel(vre_year,res_tag,init_data,is8760):
    res_dir = makeDir(getResDir(vre_year,res_tag))+dir_flag

    if 'base' in res_tag.lower():
        save_in_data_pkl = 1
    else:
        save_in_data_pkl = 0
    
    save_in_data_pkl = 1


    wind_year = VreYearSplit(vre_year)[0]
    solar_year = VreYearSplit(vre_year)[1]

    #InitSenarioParams(vre_year,res_tag)

    with open(res_dir+dir_flag+'scen_params.pkl','rb+') as fin:
        scen_params = pickle.load(fin)
    fin.close()
    print('is_solar_landuse_sw:',scen_params['vre']['is_solar_landuse_sw'])
    print('wind land use type:',scen_params['vre']['wind_land_use'])
    print('solar land use type:',scen_params['vre']['solar_land_use'])

    if scen_params['vre']['inter_annual'] == 1:
        wind_years = SplitMultipleVreYear(wind_year)
        solar_years = SplitMultipleVreYear(solar_year)
        save_in_data_pkl = 1
        year_count = len(wind_years)
    else:
        wind_years = [wind_year]
        solar_years = [solar_year]
        year_count = 1

    equip_wind = [scen_params['vre']['capex_equip_on_wind'],scen_params['vre']['capex_equip_off_wind']]

    other_wind = [scen_params['vre']['capex_other_on_wind'],scen_params['vre']['capex_other_off_wind']]

    om_wind = [scen_params['vre']['capex_om_on_wind'],scen_params['vre']['capex_om_off_wind']]

    equip_solar = [scen_params['vre']['capex_equip_pv'],scen_params['vre']['capex_equip_dpv']]

    other_solar = [scen_params['vre']['capex_other_pv'],scen_params['vre']['capex_other_dpv']]

    om_solar = [scen_params['vre']['capex_om_pv'],scen_params['vre']['capex_om_dpv']]
    
    with open(work_dir+'data_pkl'+dir_flag+scen_params['model_params']['exovar_file'],'rb') as fin:
        model_exovar = pickle.load(fin)
    fin.close()

    if init_data:
        print('Initializaing data...')
        
        #initCellData('solar',solar_year,equip_solar,other_solar,om_solar,scen_params['vre']['cap_scale_pv'],GetHourSeed(vre_year,res_tag))
        #SpurTrunkDis('wind','2015',scen_params['trans']['trunk_inter_province'])
        #initCellData('wind',wind_year,equip_wind,other_wind,om_wind,scen_params['vre']['cap_scale_wind'],GetHourSeed(vre_year,res_tag))

        initModelExovar()

        initDemLayer(
            scen_params['demand']['scale']*1.55, #alpha
            scen_params['coal']['beta'], #coalBeta
            scen_params['nuclear']['beta'], #nuclearBeta
            scen_params['gas']['beta'], #gasBeta 3.3 for base
            scen_params['ccs']['beccs_cf'], #bioGama
            1-scen_params['nuclear']['must_run'], #nuclearTheta
            scen_params['coal']['theta'], #coalTheta
            scen_params['ccs']['bio_loss'],
            res_tag,
            vre_year,
            save_in_data_pkl
        )

        if is8760 == 0:
            seedHour(vre_year,0,20,15,res_tag) #years, step, days
        else:
            seedHour(vre_year,year_count,28,15,res_tag)

        if scen_params['vre']['aggregated'] == 0:
            for year in wind_years:
                SpurTrunkDis('wind',year,scen_params['trans']['trunk_inter_province'])
            for year in solar_years:
                SpurTrunkDis('solar',year,scen_params['trans']['trunk_inter_province'])

            if scen_params['vre']['inter_annual'] == 0:
                initCellData(
                    'wind',
                    wind_year,
                    equip_wind,
                    other_wind,
                    om_wind,
                    scen_params['vre']['cap_scale_wind'],
                    scen_params['vre']['cap_scale_wind_ep'],
                    GetHourSeed(vre_year,res_tag),
                    res_tag,
                    vre_year,
                    save_in_data_pkl
                )
                initCellData(
                    'solar',
                    solar_year,
                    equip_solar,
                    other_solar,
                    om_solar,
                    scen_params['vre']['cap_scale_pv'],
                    scen_params['vre']['cap_scale_pv_ep'],
                    GetHourSeed(vre_year,res_tag),
                    res_tag,
                    vre_year,
                    save_in_data_pkl
                )
            else:
                initMultipleYearCell(
                    'solar',
                    solar_year,
                    equip_solar,
                    other_solar,
                    om_solar,
                    scen_params['vre']['cap_scale_pv'],
                    res_tag,
                    vre_year,
                    save_in_data_pkl
                )
                initMultipleYearCell(
                    'wind',
                    wind_year,
                    equip_wind,
                    other_wind,
                    om_wind,
                    scen_params['vre']['cap_scale_wind'],
                    res_tag,
                    vre_year,
                    save_in_data_pkl
                )

        print('Data initialization complete...')

    if scen_params['vre']['aggregated'] == 0:
        with open(res_dir+'wind_cell_'+wind_year+'.pkl','rb') as fin:
            wind_cell = pickle.load(fin)
        fin.close()

        with open(res_dir+'solar_cell_'+solar_year+'.pkl','rb') as fin:
            solar_cell = pickle.load(fin)
        fin.close()

    elif scen_params['vre']['aggregated'] == 1:
        with open(work_dir+'data_pkl'+dir_flag+'aggregated_cell.pkl','rb') as fin:
            aggregated_cell = pickle.load(fin)
        fin.close()

        wind_cell = aggregated_cell['wind']
        solar_cell = aggregated_cell['solar']


    with open(res_dir+'provin_hour_dem2060.pkl','rb') as fin:
        pro_dem = pickle.load(fin)
    fin.close()

    with open(work_dir+'data_pkl'+dir_flag+'province_demand_full_2060.pkl','rb+') as fin:
        pro_dem_full = pickle.load(fin)
    fin.close()

    with open(res_dir+'conv_cap.pkl','rb+') as fin:
        conv_cap = pickle.load(fin)
    fin.close()

    #print(conv_cap)

    if scen_params['vre']['inter_annual'] == 1:
        pro_dem_tmp = pro_dem
        pro_dem_full_tmp = pro_dem_full
        for pro in pro_dem:
            for i in range(year_count-1):
                pro_dem[pro] += pro_dem_tmp[pro]

                pro_dem_full[pro] += pro_dem_full_tmp[pro]

        pro_dem_tmp = None

    cap_trans = model_exovar['inter_pro_trans']

    trans_new = model_exovar['new_trans']
    trans_dis = model_exovar['trans_dis']

    trans_voltage = model_exovar['trans_voltage']
    capex_trans_cap = model_exovar['capex_trans_cap']
    capex_trans_dis = model_exovar['capex_trans_dis']

    phs_ub = model_exovar['phs_ub']
    phs_lb = model_exovar['phs_lb']
    grid_pro = model_exovar['grid_pro']

    with open(res_dir+'layer_cap_load.pkl','rb') as fin:
        layer_cap_load = pickle.load(fin)
    fin.close()

    layer_cap = layer_cap_load['layer_cap']
    layer_cap_max = layer_cap_load['layer_cap_max'] #only used in ramp control

    if scen_params['vre']['inter_annual'] == 1:
        layer_cap_tmp = layer_cap
        for pro in layer_cap:
            for i in range(year_count-1):
                layer_cap[pro] = np.vstack((layer_cap[pro],layer_cap_tmp[pro]))

        layer_cap_tmp = None

    provins = []

    provin_abbrev = open(work_dir+'data_csv'+dir_flag+'China_provinces_hz.csv')
    next(provin_abbrev)
    for line in provin_abbrev:
        line = line.replace('\n','')
        line = line.split(',')
        provins.append(line[1])
    provin_abbrev.close()


    hour_seed = GetHourSeed(vre_year,res_tag)

    with open(res_dir+'hour_pre.pkl','rb') as fin:
        hour_pre = pickle.load(fin)
    fin.close()

    Hour = 8760 * year_count

    hour_end = hour_seed[-1]

    print('Year count:',year_count)

    trans_to = {}
    trans_from = {}
    for pro in cap_trans:
        if pro[0] not in trans_to:
            trans_to[pro[0]] = []
        if pro[1] not in trans_from:
            trans_from[pro[1]] = []
        trans_to[pro[0]].append(pro[1])
        trans_from[pro[1]].append(pro[0])


    with_lds = scen_params['storage']['with_lds'] #是否有长时储能

    ru_c = {'l1':50*0.001,'l2':0,'l3':200*0.001,'l4':10*0.001} #yuan/kwh

    rd_c = {'l1':0,'l2':0,'l3':0,'l4':0}

    resv_p = {'l1':24*0.001,'l2':0,'l3':25*0.001,'l4':26*0.001}

    lds = []

    if scen_params['storage']['with_caes']:
        lds.append('caes')
    
    if scen_params['storage']['with_vrb']:
        lds.append('vrb')

    capex_power_phs = scen_params['storage']['capex_power_phs']*getCRF(7.4,40)
    capex_power_bat = scen_params['storage']['capex_power_bat']*getCRF(7.4,15)

    capex_energy_phs = scen_params['storage']['capex_energy_phs']*getCRF(7.4,40)
    capex_energy_bat = scen_params['storage']['capex_energy_bat']*getCRF(7.4,15)

    fixed_omc_phs = scen_params['storage']['fixed_omc_phs']
    fixed_omc_bat = scen_params['storage']['fixed_omc_bat']

    var_omc_phs = scen_params['storage']['var_omc_phs'] #yuan/kwh
    var_omc_bat = scen_params['storage']['var_omc_bat']
    
    rt_effi_phs = scen_params['storage']['rt_effi_phs']
    rt_effi_bat = scen_params['storage']['rt_effi_bat']

    duration_phs = scen_params['storage']['duration_phs']
    duration_bat = scen_params['storage']['duration_bat']

    capex_annual_power_phs = capex_power_phs + fixed_omc_phs + duration_phs * capex_energy_phs
    capex_annual_power_bat = capex_power_bat + fixed_omc_bat + duration_bat * capex_energy_bat
    

    sdiss_phs = scen_params['storage']['sdiss_phs']
    sdiss_bat = scen_params['storage']['sdiss_bat']
    

    capex_power_lds = {}
    capex_energy_lds = {}
    fixed_omc_lds = {}
    var_omc_lds = {}
    rt_effi_lds = {}
    duration_lds = {}
    capex_annual_power_lds = {}
    sdiss_lds = {}

    for st in lds:
        span = scen_params['storage']['span_lds'][st]
        capex_power_lds[st] = scen_params['storage']['capex_power_lds'][st]*getCRF(7.4,span)
        capex_energy_lds[st] = scen_params['storage']['capex_energy_lds'][st]*getCRF(7.4,span)
        fixed_omc_lds[st] = scen_params['storage']['fixed_omc_lds'][st]

        var_omc_lds[st] = scen_params['storage']['var_omc_lds'][st]
        rt_effi_lds[st] = scen_params['storage']['rt_effi_lds'][st]
        duration_lds[st] = scen_params['storage']['duration_lds'][st]

        capex_annual_power_lds[st] = capex_power_lds[st] + fixed_omc_lds[st] + duration_lds[st] * capex_energy_lds[st]

        sdiss_lds[st] = scen_params['storage']['sdiss_lds'][st]

    cap_phs = {}
    cap_bat = {}
    cap_lds = {}

    charge_phs = {'wind':{},'solar':{},'l1':{},'l2':{},'l3':{}}
    charge_bat = {'wind':{},'solar':{},'l1':{},'l2':{},'l3':{}}
    charge_lds = {}

    dischar_phs = {}
    dischar_bat = {}
    dischar_lds = {}

    resv_bat = {}
    resv_lds = {}
    resv_phs = {}

    tot_energy_phs = {}
    tot_energy_bat = {}
    tot_energy_lds = {}

    for st in lds:
        cap_lds[st] = {}
        charge_lds[st] = {'wind':{},'solar':{},'l1':{},'l2':{},'l3':{}}
        dischar_lds[st] = {}
        resv_lds[st] = {}
        tot_energy_lds[st] = {}


    #transmission params
    trans_loss =  scen_params['trans']['trans_loss']

    capex_spur_fixed = year_count * scen_params['trans']['capex_spur_fixed']*getCRF(7.4,25)
    capex_spur_var = scen_params['trans']['capex_spur_var']*getCRF(7.4,25) #yuan/(km*kw)

    capex_trunk_fixed = year_count * scen_params['trans']['capex_trunk_fixed']*getCRF(7.4,50)
    capex_trunk_var = scen_params['trans']['capex_trunk_var']*getCRF(7.4,50)

    #resv
    vre_resv = scen_params['resv']['vre_resv']
    demand_resv = scen_params['resv']['demand_resv']

    #coal
    min_coal = scen_params['coal']['min_coal']

    coal_ccs_loss = scen_params['ccs']['coal_loss']

    gas_ccs_loss = scen_params['ccs']['gas_loss']

    #decision vars
    ru = {'l1':{},'l2':{},'l3':{},'l4':{}}
    rd = {'l1':{},'l2':{},'l3':{},'l4':{}}
    load_conv = {'l1':{},'l2':{},'l3':{},'l4':{}}
    load_resv = {'l1':{},'l2':{},'l3':{},'l4':{}}
    trans_out = {'l1':{},'l2':{},'l3':{},'l4':{},'wind':{},'solar':{}}

    load_trans = {}
    cap_trans_new = {}


    interProvinModel = gp.Model('mip')

    wind_cell_num = {}
    solar_cell_num = {}

    for pro in provins:
        wind_cell_num[pro] = len(wind_cell['provin_cf_sort'][pro])
        solar_cell_num[pro] = len(solar_cell['provin_cf_sort'][pro])

    if not scen_params['vre']['wind_with_xz']:
        wind_cell_num['Xizang'] = 0

    for pro in cap_trans:
        load_trans[pro] = interProvinModel.addVars(Hour,lb=0,vtype=GRB.CONTINUOUS)

    for pro in trans_new:
        if scen_params['trans']['is_full_inter_province'] == 0:
            if trans_new[pro] == 0:
                cap_trans_new[pro] = interProvinModel.addVar(lb=0,ub=0,vtype=GRB.CONTINUOUS)
            else:
                cap_trans_new[pro] = interProvinModel.addVar(lb=0,vtype=GRB.CONTINUOUS)
        else:
            if pro[0] != pro[1]:
                cap_trans_new[pro] = interProvinModel.addVar(lb=0,vtype=GRB.CONTINUOUS)
            else:
                cap_trans_new[pro] = interProvinModel.addVar(lb=0,ub=0,vtype=GRB.CONTINUOUS)

    inte_wind = {}
    inte_solar = {}
    x_wind = {}
    x_solar = {}
    is_chp_online = {}

    load_shedding = {}
    for pro in provins:
        if conv_cap[pro]['coal'] == 0:
            ru['l1'][pro] = interProvinModel.addVars(Hour,lb=0,ub=0,vtype=GRB.CONTINUOUS)
            rd['l1'][pro] = interProvinModel.addVars(Hour,lb=0,ub=0,vtype=GRB.CONTINUOUS)
            load_conv['l1'][pro] = interProvinModel.addVars(Hour,lb=0,ub=0,vtype=GRB.CONTINUOUS)
            load_resv['l1'][pro] = interProvinModel.addVars(Hour,lb=0,ub=0,vtype=GRB.CONTINUOUS)
            is_chp_online[pro] = interProvinModel.addVars(Hour,lb=0,ub=0,vtype=GRB.CONTINUOUS)
        else:
            ru['l1'][pro] = interProvinModel.addVars(Hour,lb=0,vtype=GRB.CONTINUOUS)
            rd['l1'][pro] = interProvinModel.addVars(Hour,lb=0,vtype=GRB.CONTINUOUS)
            load_conv['l1'][pro] = interProvinModel.addVars(Hour,lb=0,vtype=GRB.CONTINUOUS)
            load_resv['l1'][pro] = interProvinModel.addVars(Hour,lb=0,vtype=GRB.CONTINUOUS)
            is_chp_online[pro] = interProvinModel.addVars(Hour,vtype=GRB.BINARY)

        if conv_cap[pro]['hydro'] == 0:
            ru['l2'][pro] = interProvinModel.addVars(Hour,lb=0,ub=0,vtype=GRB.CONTINUOUS)
            rd['l2'][pro] = interProvinModel.addVars(Hour,lb=0,ub=0,vtype=GRB.CONTINUOUS)
            load_conv['l2'][pro] = interProvinModel.addVars(Hour,lb=0,ub=0,vtype=GRB.CONTINUOUS)
            load_resv['l2'][pro] = interProvinModel.addVars(Hour,lb=0,ub=0,vtype=GRB.CONTINUOUS)
        else:
            ru['l2'][pro] = interProvinModel.addVars(Hour,lb=0,vtype=GRB.CONTINUOUS)
            rd['l2'][pro] = interProvinModel.addVars(Hour,lb=0,vtype=GRB.CONTINUOUS)
            load_conv['l2'][pro] = interProvinModel.addVars(Hour,lb=0,vtype=GRB.CONTINUOUS)
            load_resv['l2'][pro] = interProvinModel.addVars(Hour,lb=0,vtype=GRB.CONTINUOUS)
        
        if conv_cap[pro]['nuclear'] == 0:
            ru['l3'][pro] = interProvinModel.addVars(Hour,lb=0,ub=0,vtype=GRB.CONTINUOUS)
            rd['l3'][pro] = interProvinModel.addVars(Hour,lb=0,ub=0,vtype=GRB.CONTINUOUS)
            load_conv['l3'][pro] = interProvinModel.addVars(Hour,lb=0,ub=0,vtype=GRB.CONTINUOUS)
            load_resv['l3'][pro] = interProvinModel.addVars(Hour,lb=0,ub=0,vtype=GRB.CONTINUOUS)
        else:
            ru['l3'][pro] = interProvinModel.addVars(Hour,lb=0,vtype=GRB.CONTINUOUS)
            rd['l3'][pro] = interProvinModel.addVars(Hour,lb=0,vtype=GRB.CONTINUOUS)
            load_conv['l3'][pro] = interProvinModel.addVars(Hour,lb=0,vtype=GRB.CONTINUOUS)
            load_resv['l3'][pro] = interProvinModel.addVars(Hour,lb=0,vtype=GRB.CONTINUOUS)
        
        if conv_cap[pro]['gas'] == 0:
            ru['l4'][pro] = interProvinModel.addVars(Hour,lb=0,ub=0,vtype=GRB.CONTINUOUS)
            rd['l4'][pro] = interProvinModel.addVars(Hour,lb=0,ub=0,vtype=GRB.CONTINUOUS)
            load_conv['l4'][pro] = interProvinModel.addVars(Hour,lb=0,ub=0,vtype=GRB.CONTINUOUS)
            load_resv['l4'][pro] = interProvinModel.addVars(Hour,lb=0,ub=0,vtype=GRB.CONTINUOUS)
        else:
            ru['l4'][pro] = interProvinModel.addVars(Hour,lb=0,vtype=GRB.CONTINUOUS)
            rd['l4'][pro] = interProvinModel.addVars(Hour,lb=0,vtype=GRB.CONTINUOUS)
            load_conv['l4'][pro] = interProvinModel.addVars(Hour,lb=0,vtype=GRB.CONTINUOUS)
            load_resv['l4'][pro] = interProvinModel.addVars(Hour,lb=0,vtype=GRB.CONTINUOUS)
        
        if conv_cap[pro]['coal'] < 5:
            trans_out['l1'][pro] = interProvinModel.addVars(Hour,lb=0,ub=0,vtype=GRB.CONTINUOUS)
        else:
            trans_out['l1'][pro] = interProvinModel.addVars(Hour,lb=0,vtype=GRB.CONTINUOUS)
        
        if conv_cap[pro]['hydro'] < 5:
            trans_out['l2'][pro] = interProvinModel.addVars(Hour,lb=0,ub=0,vtype=GRB.CONTINUOUS)
        else:
            trans_out['l2'][pro] = interProvinModel.addVars(Hour,lb=0,vtype=GRB.CONTINUOUS)

        if conv_cap[pro]['nuclear'] < 5:
            trans_out['l3'][pro] = interProvinModel.addVars(Hour,lb=0,ub=0,vtype=GRB.CONTINUOUS)
        else:
            trans_out['l3'][pro] = interProvinModel.addVars(Hour,lb=0,vtype=GRB.CONTINUOUS)
        
        if conv_cap[pro]['gas'] < 5:
            trans_out['l4'][pro] = interProvinModel.addVars(Hour,lb=0,ub=0,vtype=GRB.CONTINUOUS)
        else:
            trans_out['l4'][pro] = interProvinModel.addVars(Hour,lb=0,vtype=GRB.CONTINUOUS)

        for l in ['wind','solar']:
            trans_out[l][pro] = interProvinModel.addVars(Hour,lb=0,vtype=GRB.CONTINUOUS)

        x_wind[pro] = interProvinModel.addVars(wind_cell_num[pro],lb=0,ub=1,vtype=GRB.CONTINUOUS)
        x_solar[pro] = interProvinModel.addVars(solar_cell_num[pro],lb=0,ub=1,vtype=GRB.CONTINUOUS)
        inte_wind[pro] = interProvinModel.addVars(Hour,lb=0,vtype=GRB.CONTINUOUS)
        inte_solar[pro] = interProvinModel.addVars(Hour,lb=0,vtype=GRB.CONTINUOUS)

        cap_phs[pro] = interProvinModel.addVar(lb=phs_lb[pro],ub=phs_ub[pro],vtype=GRB.CONTINUOUS)
        cap_bat[pro] = interProvinModel.addVar(lb=0,vtype=GRB.CONTINUOUS)

        for st in lds:
            cap_lds[st][pro] = interProvinModel.addVar(lb=0,vtype=GRB.CONTINUOUS)
        

        if scen_params['shedding']['with_shedding'] == 1:
            load_shedding[pro] = interProvinModel.addVars(Hour,lb=0,vtype=GRB.CONTINUOUS)
        else:
            load_shedding[pro] = interProvinModel.addVars(Hour,lb=0,ub=0,vtype=GRB.CONTINUOUS)

        for et in ['wind','solar','l1','l2','l3']:
            charge_phs[et][pro] = interProvinModel.addVars(Hour,lb=0,vtype=GRB.CONTINUOUS)
            charge_bat[et][pro] = interProvinModel.addVars(Hour,lb=0,vtype=GRB.CONTINUOUS)
            
            for st in lds:
                charge_lds[st][et][pro] = interProvinModel.addVars(Hour,lb=0,vtype=GRB.CONTINUOUS)
            
        dischar_phs[pro] = interProvinModel.addVars(Hour,lb=0,vtype=GRB.CONTINUOUS)
        dischar_bat[pro] = interProvinModel.addVars(Hour,lb=0,vtype=GRB.CONTINUOUS)
        
        for st in lds:
            dischar_lds[st][pro] = interProvinModel.addVars(Hour,lb=0,vtype=GRB.CONTINUOUS)
        

        resv_bat[pro] = interProvinModel.addVars(Hour,lb=0,vtype=GRB.CONTINUOUS)
        resv_phs[pro] = interProvinModel.addVars(Hour,lb=0,vtype=GRB.CONTINUOUS)

        for st in lds:
            resv_lds[st][pro] = interProvinModel.addVars(Hour,lb=0,vtype=GRB.CONTINUOUS)
        
        tot_energy_phs[pro] = interProvinModel.addVars(Hour,lb=0,vtype=GRB.CONTINUOUS)
        tot_energy_bat[pro] = interProvinModel.addVars(Hour,lb=0,vtype=GRB.CONTINUOUS)
        
        for st in lds:
            tot_energy_lds[st][pro] = interProvinModel.addVars(Hour,lb=0,vtype=GRB.CONTINUOUS)
        

    cap_to_ct = {}
    wind_to_ct = {}
    solar_to_ct = {}
    tot_to_ct = {}
    load_to_ct = {}
    resv_to_ct = {}
    ramp_up_to_ct = {}
    ramp_dn_to_ct = {}


    for pro in provins:
        if scen_params['to_ct']['with_ct'] == 1:
            cap_to_ct[pro] = interProvinModel.addVar(lb=0,vtype=GRB.CONTINUOUS)
            tot_to_ct[pro] = interProvinModel.addVars(Hour,lb=0,vtype=GRB.CONTINUOUS)
            wind_to_ct[pro] = interProvinModel.addVars(Hour,lb=0,vtype=GRB.CONTINUOUS)
            solar_to_ct[pro] = interProvinModel.addVars(Hour,lb=0,vtype=GRB.CONTINUOUS)
            load_to_ct[pro] =  interProvinModel.addVars(Hour,lb=0,vtype=GRB.CONTINUOUS)
            resv_to_ct[pro] = interProvinModel.addVars(Hour,lb=0,vtype=GRB.CONTINUOUS)
            ramp_dn_to_ct[pro] = interProvinModel.addVars(Hour,lb=0,vtype=GRB.CONTINUOUS)
            ramp_up_to_ct[pro] = interProvinModel.addVars(Hour,lb=0,vtype=GRB.CONTINUOUS)
        elif scen_params['to_ct']['with_ct'] == 0:
            cap_to_ct[pro] = interProvinModel.addVar(lb=0,ub=0,vtype=GRB.CONTINUOUS)
            tot_to_ct[pro] = interProvinModel.addVars(Hour,lb=0,ub=0,vtype=GRB.CONTINUOUS)
            wind_to_ct[pro] = interProvinModel.addVars(Hour,lb=0,ub=0,vtype=GRB.CONTINUOUS)
            solar_to_ct[pro] = interProvinModel.addVars(Hour,lb=0,ub=0,vtype=GRB.CONTINUOUS)
            load_to_ct[pro] =  interProvinModel.addVars(Hour,lb=0,ub=0,vtype=GRB.CONTINUOUS)
            resv_to_ct[pro] = interProvinModel.addVars(Hour,lb=0,ub=0,vtype=GRB.CONTINUOUS)
            ramp_dn_to_ct[pro] = interProvinModel.addVars(Hour,lb=0,ub=0,vtype=GRB.CONTINUOUS)
            ramp_up_to_ct[pro] = interProvinModel.addVars(Hour,lb=0,ub=0,vtype=GRB.CONTINUOUS)


    #风电总生产成本
    wind_gen_cost = [wind_cell['provin_cf_sort'][pro][c][5]*
                     wind_cell['provin_cf_sort'][pro][c][4]*
                     x_wind[pro][c]
                     for pro in provins for c in range(wind_cell_num[pro])]
    #光电总生产成本
    solar_gen_cost = [solar_cell['provin_cf_sort'][pro][c][5]*
                      solar_cell['provin_cf_sort'][pro][c][4]*
                      x_solar[pro][c]
                      for pro in provins for c in range(solar_cell_num[pro])]
    #爬坡与退坡成本
    ramp_up_cost = [ru_c[l]*ru[l][pro][h] for l in ['l1','l2','l3','l4'] for pro in provins for h in hour_seed]
    ramp_dn_cost = [rd_c[l]*rd[l][pro][h] for l in ['l1','l2','l3','l4'] for pro in provins for h in hour_seed]

    #储能系统固定总成本
    fixed_phs_cost = [year_count * capex_annual_power_phs*cap_phs[pro] for pro in provins]
    fixed_bat_cost = [year_count * capex_annual_power_bat*cap_bat[pro] for pro in provins]
    
    fixed_lds_cost = [year_count * capex_annual_power_lds[st]*cap_lds[st][pro] for st in lds for pro in provins]

    #储能系统可变成本
    var_phs_cost = [var_omc_phs * dischar_phs[pro][h]  for pro in provins for h in hour_seed]
    var_bat_cost = [var_omc_bat * dischar_bat[pro][h]  for pro in provins for h in hour_seed]
    var_lds_cost = [var_omc_lds[st] * dischar_lds[st][pro][h] for st in lds  for pro in provins for h in hour_seed]

    #var_phs_cost = [var_omc_phs*charge_phs[et][pro][h] for et in ['solar','wind','l2','l3'] for pro in provins for h in hour_seed]
    #var_bat_cost = [var_omc_bat*charge_bat[et][pro][h] for et in ['solar','wind','l2','l3'] for pro in provins for h in hour_seed]
    #var_lds_cost = [var_omc_lds*charge_lds[et][pro][h] for et in ['solar','wind','l2','l3'] for pro in provins for h in hour_seed]
    
    #储备总成本
    resv_cost = [resv_p[l]*load_resv[l][pro][h] for l in ['l1','l2','l4'] for pro in provins for h in hour_seed]

    lcoe_coal_ccs = scen_params['ccs']['coal_lcoe']

    coal_ccs_cost = [lcoe_coal_ccs*(load_conv['l1'][pro][h]+
                                    charge_phs['l1'][pro][h]+
                                    charge_bat['l1'][pro][h]+
                                    gp.quicksum([charge_lds[st]['l1'][pro][h] for st in lds])+ 
                                    trans_out['l1'][pro][h]) 
                    for pro in provins for h in hour_seed]

    coal_ccs_cost_fixed = [year_count * (17850*getCRF(7.4,40)+446)*conv_cap[pro]['coal'] for pro in provins]

    lcoe_gas_ccs = scen_params['ccs']['gas_lcoe']
    
    gas_ccs_cost = [lcoe_gas_ccs*(load_conv['l4'][pro][h]+trans_out['l4'][pro][h]) for pro in provins for h in hour_seed]

    gas_ccs_cost_fixed = [year_count * (10500*getCRF(7.4,30)+262)*conv_cap[pro]['gas'] for pro in provins]

    hydro_cost_fixed = [year_count * (9900*getCRF(7.4,50)+268)*conv_cap[pro]['hydro'] for pro in provins]

    nuclear_cost_fixed = [year_count * (15000*getCRF(7.4,50)+629)*conv_cap[pro]['nuclear'] for pro in provins]

    nuclear_cost_var = [scen_params['nuclear']['var_cost']*
                        (load_conv['l3'][pro][h]+trans_out['l3'][pro][h]+
                        charge_phs['l3'][pro][h]+charge_bat['l3'][pro][h]
                        +gp.quicksum([charge_lds[st]['l3'][pro][h] for st in lds ])) 
                        for pro in provins for h in hour_seed]

    beccs_cost_fixed = [year_count * (15700*getCRF(7.4,35)+750)*conv_cap[pro]['beccs'] for pro in provins]


    cpv_solar = {}

    for pro in provins:
        cpv_solar[pro] = []
        for c in range(solar_cell_num[pro]):
            if solar_cell['provin_cf_sort'][pro][c][2] == 0:
                cpv_solar[pro].append(c)


    if scen_params['vre']['aggregated'] == 0:
        #格点至变电站成本
        spur_cost_wind = [(x_wind[pro][c]-wind_cell['provin_cf_sort'][pro][c][13])*
                        wind_cell['provin_cf_sort'][pro][c][3]*
                        wind_cell['provin_cf_sort'][pro][c][11]*
                        max(wind_cell['cf_prof'][pro][c])*capex_spur_var
                        +(x_wind[pro][c]-wind_cell['provin_cf_sort'][pro][c][13])*
                        wind_cell['provin_cf_sort'][pro][c][3]*
                        max(wind_cell['cf_prof'][pro][c])*capex_spur_fixed
                        for pro in provins for c in range(wind_cell_num[pro])]

        spur_cost_solar =[
            (x_solar[pro][c]-solar_cell['provin_cf_sort'][pro][c][13])*
             solar_cell['provin_cf_sort'][pro][c][3]*
             solar_cell['provin_cf_sort'][pro][c][11]*
             max(solar_cell['cf_prof'][pro][c])*capex_spur_var+
             (x_solar[pro][c]-solar_cell['provin_cf_sort'][pro][c][13])*
             solar_cell['provin_cf_sort'][pro][c][3]*
             max(solar_cell['cf_prof'][pro][c])*capex_spur_fixed
            for pro in provins for c in cpv_solar[pro]
        ]

        #变电站至主干网成本
        sub_cell = {}

        for pro in wind_cell['sub_cell_info']:
            if pro != 'Xizang':
                if pro not in sub_cell:
                    sub_cell[pro] = {}
                for s in wind_cell['sub_cell_info'][pro]:
                    if s not in sub_cell[pro]:
                        sub_cell[pro][s] = {}

                    sub_cell[pro][s]['wind_cell'] = wind_cell['sub_cell_info'][pro][s]['cell']
                    sub_cell[pro][s]['dis'] = wind_cell['sub_cell_info'][pro][s]['dis']

                    if s in solar_cell['sub_cell_info'][pro]:
                        sub_cfs = (wind_cell['sub_cell_info'][pro][s]['cap']*wind_cell['sub_cell_info'][pro][s]['cf']+
                                solar_cell['sub_cell_info'][pro][s]['cap']*solar_cell['sub_cell_info'][pro][s]['cf'])

                        sub_cap = wind_cell['sub_cell_info'][pro][s]['cap'] + solar_cell['sub_cell_info'][pro][s]['cap']

                        sub_cell[pro][s]['max_cf'] = max(sub_cfs) / sub_cap

                        sub_cell[pro][s]['solar_cell'] = solar_cell['sub_cell_info'][pro][s]['cell']
                    else:
                        sub_cell[pro][s]['max_cf'] = max(wind_cell['sub_cell_info'][pro][s]['cf']) / wind_cell['sub_cell_info'][pro][s]['cap']
                        sub_cell[pro][s]['solar_cell'] = []

        for pro in solar_cell['sub_cell_info']:
            if pro not in sub_cell:
                sub_cell[pro] = {}
            for s in solar_cell['sub_cell_info'][pro]:
                if s not in sub_cell[pro]:
                    sub_cell[pro][s] = {}
                    sub_cell[pro][s]['solar_cell'] = solar_cell['sub_cell_info'][pro][s]['cell']
                    if solar_cell['sub_cell_info'][pro][s]['cap'] > 0:
                        sub_cell[pro][s]['max_cf'] = max(solar_cell['sub_cell_info'][pro][s]['cf']) / solar_cell['sub_cell_info'][pro][s]['cap']
                    else:
                        sub_cell[pro][s]['max_cf'] = 1
                    sub_cell[pro][s]['wind_cell'] = []
                    sub_cell[pro][s]['dis'] = solar_cell['sub_cell_info'][pro][s]['dis']

        trunk_cost = [((x_wind[pro][w]-wind_cell['provin_cf_sort'][pro][w][13])*
                    wind_cell['provin_cf_sort'][pro][w][3]+
                    (x_solar[pro][s]-solar_cell['provin_cf_sort'][pro][s][13])*
                    solar_cell['provin_cf_sort'][pro][s][3])*sub_cell[pro][sub]['max_cf']*
                    (sub_cell[pro][sub]['dis']*capex_trunk_var+capex_trunk_fixed)
                    for pro in provins
                    for sub in sub_cell[pro]
                    for w in sub_cell[pro][sub]['wind_cell']
                    for s in sub_cell[pro][sub]['solar_cell']]

    elif scen_params['vre']['aggregated'] == 1:
        spur_cost_wind = [(x_wind[pro][c]-wind_cell['provin_cf_sort'][pro][c][13])*
                        wind_cell['provin_cf_sort'][pro][c][3]*
                        wind_cell['provin_cf_sort'][pro][c][11]*
                        max(wind_cell['cf_prof'][pro][c])*capex_spur_var+
                        (x_wind[pro][c]-wind_cell['provin_cf_sort'][pro][c][13])*
                        wind_cell['provin_cf_sort'][pro][c][3]*
                        max(wind_cell['cf_prof'][pro][c])*capex_spur_fixed
                        for pro in provins for c in range(wind_cell_num[pro])]

        spur_cost_solar = [(x_solar[pro][c]-solar_cell['provin_cf_sort'][pro][c][13])*
                        solar_cell['provin_cf_sort'][pro][c][3]*
                        solar_cell['provin_cf_sort'][pro][c][11]*
                        max(solar_cell['cf_prof'][pro][c])*capex_spur_var+
                        (x_solar[pro][c]-solar_cell['provin_cf_sort'][pro][c][13])*
                        solar_cell['provin_cf_sort'][pro][c][3]*
                        max(solar_cell['cf_prof'][pro][c])*capex_spur_fixed
                        for pro in provins for c in range(solar_cell_num[pro])]

        trunk_cost_wind = [
            (x_wind[pro][c]-wind_cell['provin_cf_sort'][pro][c][13])
            *max(wind_cell['cf_prof'][pro][c])*wind_cell['provin_cf_sort'][pro][c][3]
            *(
                capex_trunk_fixed+capex_trunk_var*wind_cell['provin_cf_sort'][pro][c][12]
            )
            for pro in provins
            for c in range(wind_cell_num[pro])
        ]

        trunk_cost_solar = [
            (x_solar[pro][c]-solar_cell['provin_cf_sort'][pro][c][13])
            *max(solar_cell['cf_prof'][pro][c])*solar_cell['provin_cf_sort'][pro][c][3]
            *(
                capex_trunk_fixed+capex_trunk_var*solar_cell['provin_cf_sort'][pro][c][12]
            )
            for pro in provins
            for c in range(solar_cell_num[pro])
        ]

        trunk_cost = trunk_cost_wind + trunk_cost_solar

    trans_pair_count = []
    trans_cost = []

    intertrans_cost_scale = scen_params['trans']['interprovincial_scale']

    '''for pro in cap_trans:
        if trans_new[pro] != 0:
            if pro not in trans_voltage:
                voltage = 500
            else:
                voltage = trans_voltage[pro]
            
            trans_cost.append(
                intertrans_cost_scale*year_count*capex_trans_cap[voltage]*cap_trans[pro]
                +intertrans_cost_scale*year_count*capex_trans_dis[voltage]*trans_dis[pro]*cap_trans[pro]
            )'''

    for pro in trans_new:
        if trans_new[pro] != 0 and pro not in trans_pair_count:
            
            trans_pair_count.append((pro[1],pro[0]))
            if pro not in trans_voltage:
                voltage = 500
            else:
                voltage = trans_voltage[pro]
            if voltage < 500:
                voltage = 500
            trans_cost.append(
                2*intertrans_cost_scale*year_count*capex_trans_cap[voltage]
                *(cap_trans_new[pro]+cap_trans_new[(pro[1],pro[0])]+cap_trans[pro])
                +intertrans_cost_scale*year_count*capex_trans_dis[voltage]
                *trans_dis[pro]*(cap_trans_new[pro]+cap_trans_new[(pro[1],pro[0])]+cap_trans[pro])
            )

    other_tech_cost = [0]

    gas_ccs_cost_fixed = [year_count * (10500*getCRF(7.4,30)+262)*conv_cap[pro]['gas'] for pro in provins]

    if scen_params['shedding']['with_shedding'] == 1:
        load_shedding_cost = [
            load_shedding[pro][h]*scen_params['shedding']['shedding_vom']
            for pro in provins
            for h in hour_seed
        ]
        
        other_tech_cost += load_shedding_cost

    if scen_params['to_ct']['with_ct'] == 1:
        to_ct_cost = [
            cap_to_ct[pro] * ((1+0)*7500*getCRF(7.4,30)+262) for pro in provins
        ]

        other_tech_cost += to_ct_cost

        to_ct_fuel_cost = [
            load_to_ct[pro][h] * scen_params['to_ct']['cost_kwh']
            for pro in provins
            for h in hour_seed
        ]

        other_tech_cost += to_ct_fuel_cost

        to_ct_resv_cost = [
            resv_to_ct[pro][h] * resv_p['l4'] 
            for pro in provins
            for h in hour_seed
        ]

        other_tech_cost += to_ct_resv_cost

        to_ct_ramp_up_cost = [
            ramp_up_to_ct[pro][h] * ru_c['l4']
            for pro in provins
            for h in hour_seed
        ]

        other_tech_cost += to_ct_ramp_up_cost

        to_ct_ramp_dn_cost = [
            ramp_dn_to_ct[pro][h] * rd_c['l4']
            for pro in provins
            for h in hour_seed
        ]

        other_tech_cost += to_ct_ramp_dn_cost



    interProvinModel.setObjective(gp.quicksum(wind_gen_cost)+
                                  gp.quicksum(solar_gen_cost)+
                                  gp.quicksum(ramp_up_cost)+
                                  gp.quicksum(ramp_dn_cost)+
                                  gp.quicksum(fixed_phs_cost)+
                                  gp.quicksum(fixed_bat_cost)+
                                  gp.quicksum(fixed_lds_cost)+
                                  gp.quicksum(var_phs_cost)+
                                  gp.quicksum(var_bat_cost)+
                                  gp.quicksum(var_lds_cost)+
                                  gp.quicksum(resv_cost)+
                                  gp.quicksum(spur_cost_wind)+
                                  gp.quicksum(spur_cost_solar)+
                                  gp.quicksum(trunk_cost)+
                                  gp.quicksum(trans_cost)+
                                  gp.quicksum(coal_ccs_cost)+
                                  gp.quicksum(gas_ccs_cost)+
                                  gp.quicksum(coal_ccs_cost_fixed)+
                                  gp.quicksum(gas_ccs_cost_fixed)+
                                  gp.quicksum(nuclear_cost_var)+
                                  gp.quicksum(beccs_cost_fixed)+
                                  gp.quicksum(nuclear_cost_fixed)+
                                  gp.quicksum(hydro_cost_fixed)+
                                  gp.quicksum(other_tech_cost))

    #大于等于现有装机
    interProvinModel.addConstrs(x_wind[pro][c] >= wind_cell['provin_cf_sort'][pro][c][13] for pro in provins for c in range(wind_cell_num[pro]))
    interProvinModel.addConstrs(x_solar[pro][c] >= solar_cell['provin_cf_sort'][pro][c][13] for pro in provins for c in range(solar_cell_num[pro]))

    #期初与期末储能系统总储存能量相等
    interProvinModel.addConstrs(tot_energy_phs[pro][0] == tot_energy_phs[pro][hour_end] for pro in provins)

    interProvinModel.addConstrs(tot_energy_bat[pro][0] == tot_energy_bat[pro][hour_end] for pro in provins)

    for st in lds:
        interProvinModel.addConstrs(tot_energy_lds[st][pro][0] == tot_energy_lds[st][pro][hour_end] for pro in provins)

    #第1小时与第2小时放电量限制
    interProvinModel.addConstrs(
        resv_phs[pro][0]+dischar_phs[pro][0] +
        resv_phs[pro][1]+dischar_phs[pro][1] <= 
        tot_energy_phs[pro][0] +
        gp.quicksum([charge_phs[et][pro][0] for et in ['wind','solar','l2','l3']])
        for pro in provins)

    interProvinModel.addConstrs(
        resv_bat[pro][0]+dischar_bat[pro][0] +
        resv_bat[pro][1]+dischar_bat[pro][1] <=
        (1-sdiss_bat) * tot_energy_bat[pro][0] +
        gp.quicksum([charge_bat[et][pro][0] for et in ['wind','solar','l2','l3']]) 
        for pro in provins)


    for st in lds:
        interProvinModel.addConstrs(
            resv_lds[st][pro][0]+dischar_lds[st][pro][0] +
            resv_lds[st][pro][1]+dischar_lds[st][pro][1] <=
            (1-sdiss_lds[st]) * tot_energy_lds[st][pro][0] +
            gp.quicksum([charge_lds[st][et][pro][0] for et in ['wind','solar','l2','l3']]) 
            for pro in provins)

    #第2小时结束后储能系统中储存的能量
    interProvinModel.addConstrs(
        tot_energy_phs[pro][1] == tot_energy_phs[pro][0] - dischar_phs[pro][0] - dischar_phs[pro][1]
                                  + gp.quicksum([charge_phs[et][pro][0]+charge_phs[et][pro][1] for et in ['wind','solar','l1','l2','l3']])
                                  for pro in provins)

    interProvinModel.addConstrs(
        tot_energy_bat[pro][1] == (1-sdiss_bat) * tot_energy_bat[pro][0] - dischar_bat[pro][0] - dischar_bat[pro][1]
                                  + gp.quicksum([charge_bat[et][pro][0]+charge_bat[et][pro][1] for et in ['wind','solar','l1','l2','l3']])
                                  for pro in provins)

    for st in lds:
        interProvinModel.addConstrs(
            tot_energy_lds[st][pro][1] == (1-sdiss_lds[st]) * tot_energy_lds[st][pro][0] - dischar_lds[st][pro][0] - dischar_lds[st][pro][1]
                                    + gp.quicksum([charge_lds[st][et][pro][0]+charge_lds[st][et][pro][1] for et in ['wind','solar','l1','l2','l3']])
                                    for pro in provins)

    #第h小时结束后储能系统中存储的能量
    interProvinModel.addConstrs(
        tot_energy_phs[pro][h] == tot_energy_phs[pro][hour_pre[h]] - dischar_phs[pro][h] +
                                  gp.quicksum([charge_phs[et][pro][h] for et in ['wind','solar','l1','l2','l3']])
                                  for pro in provins for h in hour_seed[2:])

    interProvinModel.addConstrs(
        tot_energy_bat[pro][h] == (1-sdiss_bat)*tot_energy_bat[pro][hour_pre[h]] - dischar_bat[pro][h] +
                                  gp.quicksum([charge_bat[et][pro][h] for et in ['wind','solar','l1','l2','l3']])
                                  for pro in provins for h in hour_seed[2:])

    for st in lds:
        interProvinModel.addConstrs(
            tot_energy_lds[st][pro][h] == (1-sdiss_lds[st]) *tot_energy_lds[st][pro][hour_pre[h]] - dischar_lds[st][pro][h] +
                                    gp.quicksum([charge_lds[st][et][pro][h] for et in ['wind','solar','l1','l2','l3']])
                                    for pro in provins for h in hour_seed[2:])
    #放电约束
    interProvinModel.addConstrs(resv_phs[pro][h]+dischar_phs[pro][h] <= tot_energy_phs[pro][hour_pre[h]]
                                for pro in provins for h in hour_seed[2:])

    interProvinModel.addConstrs(resv_bat[pro][h]+dischar_bat[pro][h] <= tot_energy_bat[pro][hour_pre[h]]
                                for pro in provins for h in hour_seed[2:])

    for st in lds:
        interProvinModel.addConstrs(resv_lds[st][pro][h]+dischar_lds[st][pro][h] <= tot_energy_lds[st][pro][hour_pre[h]]
                                    for pro in provins for h in hour_seed[2:])

    #储能总量约束
    interProvinModel.addConstrs(tot_energy_phs[pro][h] <= duration_phs*cap_phs[pro]
                                for pro in provins for h in hour_seed)

    interProvinModel.addConstrs(tot_energy_bat[pro][h] <= duration_bat*cap_bat[pro]
                                for pro in provins for h in hour_seed)

    for st in lds:
        interProvinModel.addConstrs(tot_energy_lds[st][pro][h] <= duration_lds[st]*cap_lds[st][pro]
                                    for pro in provins for h in hour_seed)
    
    #容量约束
    interProvinModel.addConstrs(gp.quicksum([charge_phs[et][pro][h] for et in  ['wind','solar','l1','l2','l3']]) <= cap_phs[pro] 
                                for pro in provins for h in hour_seed)

    interProvinModel.addConstrs(rt_effi_phs*dischar_phs[pro][h] <= cap_phs[pro] for pro in provins for h in hour_seed)
    
    interProvinModel.addConstrs(rt_effi_phs*dischar_phs[pro][h]+rt_effi_phs*resv_phs[pro][h]
                                <= cap_phs[pro]+gp.quicksum([charge_phs[et][pro][h] for et in  ['wind','solar','l1','l2','l3']])
                                for pro in provins for h in hour_seed)
    
    interProvinModel.addConstrs(gp.quicksum([charge_bat[et][pro][h] for et in  ['wind','solar','l1','l2','l3']]) <= cap_bat[pro] 
                                for pro in provins for h in hour_seed)
    
    interProvinModel.addConstrs(rt_effi_bat*dischar_bat[pro][h] <= cap_bat[pro] for pro in provins for h in hour_seed)

    interProvinModel.addConstrs(rt_effi_bat*dischar_bat[pro][h]+rt_effi_bat*resv_bat[pro][h] 
                                <= cap_bat[pro]+gp.quicksum([charge_bat[et][pro][h] for et in  ['wind','solar','l1','l2','l3']])
                                for pro in provins for h in hour_seed)

    for st in lds:
        interProvinModel.addConstrs(gp.quicksum([charge_lds[st][et][pro][h] for et in  ['wind','solar','l1','l2','l3']]) <= cap_lds[st][pro] 
                                    for pro in provins for h in hour_seed)
        
        interProvinModel.addConstrs(rt_effi_lds[st]*dischar_lds[st][pro][h] <= cap_lds[st][pro] for pro in provins for h in hour_seed)
        
        interProvinModel.addConstrs(rt_effi_lds[st]*dischar_lds[st][pro][h]+rt_effi_lds[st]*resv_lds[st][pro][h]
                                    <= cap_lds[st][pro]+gp.quicksum([charge_lds[st][et][pro][h] for et in  ['wind','solar','l1','l2','l3']]) 
                                    for pro in provins for h in hour_seed)

    for pro in provins:
        if pro in trans_to.keys():
            interProvinModel.addConstrs(inte_wind[pro][h]+charge_phs['wind'][pro][h]+charge_bat['wind'][pro][h]
                                        +wind_to_ct[pro][h]+trans_out['wind'][pro][h]
                                        +gp.quicksum([charge_lds[st]['wind'][pro][h] for st in lds])     
                                        <= gp.quicksum([x_wind[pro][c]*wind_cell['provin_cf_sort'][pro][c][3]*wind_cell['cf_prof'][pro][c][h]
                                        for c in range(wind_cell_num[pro])])
                                        for h in hour_seed)

            interProvinModel.addConstrs(inte_solar[pro][h]+charge_phs['solar'][pro][h]+charge_bat['solar'][pro][h]
                                        +solar_to_ct[pro][h]
                                        +gp.quicksum([charge_lds[st]['solar'][pro][h] for st in lds])   
                                        +trans_out['solar'][pro][h]
                                        <= gp.quicksum([x_solar[pro][c]*solar_cell['provin_cf_sort'][pro][c][3]*solar_cell['cf_prof'][pro][c][h]
                                        for c in range(solar_cell_num[pro])])
                                        for h in hour_seed)

            interProvinModel.addConstrs(gp.quicksum([load_trans[(pro,pro2)][h] for pro2 in trans_to[pro]]) # important trans tag
                                        == trans_out['wind'][pro][h]+trans_out['solar'][pro][h]+trans_out['l2'][pro][h]+trans_out['l3'][pro][h]+
                                           (1-coal_ccs_loss) *trans_out['l1'][pro][h]+(1-gas_ccs_loss) *trans_out['l4'][pro][h]
                                        for h in hour_seed)
        else:
            interProvinModel.addConstrs(inte_wind[pro][h]+charge_phs['wind'][pro][h]+charge_bat['wind'][pro][h]
                                        +wind_to_ct[pro][h]
                                        +gp.quicksum([charge_lds[st]['wind'][pro][h] for st in lds]) 
                                        <=gp.quicksum([x_wind[pro][c]*wind_cell['provin_cf_sort'][pro][c][3]*wind_cell['cf_prof'][pro][c][h]
                                        for c in range(wind_cell_num[pro])])
                                        for h in hour_seed)

            interProvinModel.addConstrs(inte_solar[pro][h]+charge_phs['solar'][pro][h]+charge_bat['solar'][pro][h]
                                        +solar_to_ct[pro][h]
                                        +gp.quicksum([charge_lds[st]['solar'][pro][h] for st in lds])  
                                        <=gp.quicksum([x_solar[pro][c]*solar_cell['provin_cf_sort'][pro][c][3]*solar_cell['cf_prof'][pro][c][h]
                                        for c in range(solar_cell_num[pro])])
                                        for h in hour_seed)
    
    
    
    if scen_params['to_ct']['with_ct'] == 1:
        for pro in provins:
            tot_to_ct[pro][0] = tot_to_ct[pro][hour_end]
            
            for h in hour_seed[1:]:
                interProvinModel.addConstr(tot_to_ct[pro][h]==tot_to_ct[pro][hour_pre[h]]+0.8*(wind_to_ct[pro][hour_pre[h]] + solar_to_ct[pro][hour_pre[h]]))

                #interProvinModel.addConstr(tot_to_ct[pro][h] <= cap_to_ct[pro])

                interProvinModel.addConstr(ramp_up_to_ct[pro][h] >= load_to_ct[pro][h]-load_to_ct[pro][hour_pre[h]])
                interProvinModel.addConstr(ramp_dn_to_ct[pro][h] >= load_to_ct[pro][hour_pre[h]]-load_to_ct[pro][h])

                interProvinModel.addConstr(ramp_up_to_ct[pro][h] <= scen_params['ramp']['l4'] * cap_to_ct[pro])

            for h in hour_seed:
                interProvinModel.addConstr(load_to_ct[pro][h] + resv_to_ct[pro][h] <= tot_to_ct[pro][h])
                interProvinModel.addConstr(load_to_ct[pro][h] + resv_to_ct[pro][h] <= cap_to_ct[pro])

    
    demConstrs = {}

    for pro in provins:
        if pro in trans_from.keys():
            demConstrs[pro] = interProvinModel.addConstrs(
                (1-coal_ccs_loss) * load_conv['l1'][pro][h]+
                load_conv['l2'][pro][h]+
                load_conv['l3'][pro][h]+
                (1-gas_ccs_loss) * load_conv['l4'][pro][h]+
                gp.quicksum([(1-trans_loss)**trans_dis[(pro1,pro)]*load_trans[(pro1,pro)][h] for pro1 in trans_from[pro]])+
                inte_wind[pro][h]+
                inte_solar[pro][h]+
                scen_params['shedding']['with_shedding'] * load_shedding[pro][h]+
                rt_effi_phs*dischar_phs[pro][h]+
                rt_effi_bat*dischar_bat[pro][h]+
                gp.quicksum([rt_effi_lds[st]*dischar_lds[st][pro][h] for st in lds])+
                (1-scen_params['to_ct']['ct_loss']) * load_to_ct[pro][h]
                ==  pro_dem[pro][h]
                for h in hour_seed
            )
        else:
            demConstrs[pro] = interProvinModel.addConstrs(
                load_conv['l2'][pro][h] +
                (1-coal_ccs_loss) * load_conv['l1'][pro][h] +
                load_conv['l3'][pro][h] +
                (1-gas_ccs_loss) * load_conv['l4'][pro][h] +
                inte_wind[pro][h]+
                inte_solar[pro][h]+
                scen_params['shedding']['with_shedding'] * load_shedding[pro][h]+
                rt_effi_phs*dischar_phs[pro][h]+
                rt_effi_bat*dischar_bat[pro][h]+
                gp.quicksum([rt_effi_lds[st]*dischar_lds[st][pro][h] for st in lds])+
                (1-scen_params['to_ct']['ct_loss']) * load_to_ct[pro][h]
                ==  pro_dem[pro][h]
                for h in hour_seed)

    for pro_pair in cap_trans:
        interProvinModel.addConstrs(gp.quicksum([load_trans[(pro_pair[0],pro_pair[1])][h]+load_trans[(pro_pair[1],pro_pair[0])][h]]) 
                                    <= cap_trans[pro_pair]+cap_trans_new[(pro_pair[0],pro_pair[1])]+cap_trans_new[(pro_pair[1],pro_pair[0])] 
                                    for h in hour_seed)

    
    interProvinModel.addConstrs(load_conv['l1'][pro][h]+
                                trans_out['l1'][pro][h] >= 
                                is_chp_online[pro][h] * min_coal * 
                                layer_cap[pro][h][0] 
                                for pro in provins for h in hour_seed)

    #reserve
    interProvinModel.addConstrs(load_conv['l1'][pro][h]+
                                load_resv['l1'][pro][h]+
                                trans_out['l1'][pro][h] <= 
                                is_chp_online[pro][h]*
                                layer_cap[pro][h][0] 
                                for pro in provins for h in hour_seed)
    
    interProvinModel.addConstrs(load_conv['l1'][pro][h]+
                                load_resv['l1'][pro][h]+
                                trans_out['l1'][pro][h]+
                                charge_phs['l1'][pro][h]+
                                charge_bat['l1'][pro][h]+
                                gp.quicksum([charge_lds[st]['l1'][pro][h] for st in lds])
                                <= layer_cap[pro][h][0] for pro in provins for h in hour_seed)

    interProvinModel.addConstrs(load_resv['l2'][pro][h]+
                                load_conv['l2'][pro][h]+
                                charge_phs['l2'][pro][h]+
                                charge_bat['l2'][pro][h]+
                                gp.quicksum([charge_lds[st]['l2'][pro][h] for st in lds])+
                                trans_out['l2'][pro][h]
                                <= layer_cap[pro][h][1]
                                for pro in provins for h in hour_seed)

    interProvinModel.addConstrs(load_conv['l3'][pro][h]+
                                charge_phs['l3'][pro][h]+
                                charge_bat['l3'][pro][h]+
                                gp.quicksum([charge_lds[st]['l3'][pro][h] for st in lds])+
                                trans_out['l3'][pro][h]
                                <= layer_cap[pro][h][2]
                                for pro in provins for h in hour_seed)

    interProvinModel.addConstrs(load_conv['l4'][pro][h]+load_resv['l4'][pro][h]+trans_out['l4'][pro][h] <= layer_cap[pro][h][3] for pro in provins for h in hour_seed)

    
    
    credible_conv = {0:1,1:1,2:1,3:1}
    credible_solar = 1
    credible_wind = 1
    
    if scen_params['resv']['vre_resv_provincialy'] == 0:
        for g in grid_pro:
            interProvinModel.addConstrs(
                gp.quicksum([
                        gp.quicksum([credible_conv[l]*layer_cap[pro][h][l] for l in range(4)])
                        +credible_wind * gp.quicksum([x_wind[pro][c]*wind_cell['provin_cf_sort'][pro][c][3]*wind_cell['cf_prof'][pro][c][h] for c in range(wind_cell_num[pro])])
                        +credible_solar * gp.quicksum([x_solar[pro][c]*solar_cell['provin_cf_sort'][pro][c][3]*solar_cell['cf_prof'][pro][c][h] for c in range(solar_cell_num[pro])])
                        +scen_params['shedding']['with_shedding'] * gp.quicksum([load_shedding[pro][h]])
                        +rt_effi_phs*dischar_phs[pro][h]
                        +rt_effi_bat*dischar_bat[pro][h]
                        +(1-scen_params['to_ct']['ct_loss']) * resv_to_ct[pro][h]
                        +gp.quicksum([rt_effi_lds[st]*dischar_lds[st][pro][h] for st in lds])
                        +rt_effi_phs*resv_phs[pro][h]
                        +rt_effi_bat*resv_bat[pro][h]
                        +gp.quicksum([rt_effi_lds[st]*resv_lds[st][pro][h] for st in lds])
                        +gp.quicksum([(1-trans_loss)**trans_dis[(pro1,pro)]*load_trans[(pro1,pro)][h] for pro1 in trans_from[pro]])
                        -trans_out['wind'][pro][h]-trans_out['solar'][pro][h]-trans_out['l2'][pro][h]-trans_out['l3'][pro][h]
                        -trans_out['l1'][pro][h]-trans_out['l4'][pro][h]
                        for pro in grid_pro[g]  ])
                    >= gp.quicksum([(1+demand_resv)*pro_dem[pro][h]+demand_resv*(pro_dem_full[pro][h]-pro_dem[pro][h]) for pro in grid_pro[g]])
                for h in hour_seed)

            interProvinModel.addConstrs(
                gp.quicksum(
                    [
                        load_resv['l1'][pro][h]+load_resv['l2'][pro][h]+load_resv['l4'][pro][h]+
                        rt_effi_phs*resv_phs[pro][h]+
                        rt_effi_bat*resv_bat[pro][h]+
                        gp.quicksum([rt_effi_lds[st]*resv_lds[st][pro][h] for st in lds])
                        for pro in grid_pro[g]
                    ]
                )
                >= gp.quicksum(
                    [vre_resv * (inte_wind[pro][h]+inte_solar[pro][h]+trans_out['wind'][pro][h]+trans_out['solar'][pro][h])
                    for pro in grid_pro[g]])
                for h in hour_seed
            )
    else:
        interProvinModel.addConstrs(
                        gp.quicksum([credible_conv[l]*layer_cap[pro][h][l] for l in range(4)])
                        +credible_wind * gp.quicksum([x_wind[pro][c]*wind_cell['provin_cf_sort'][pro][c][3]*wind_cell['cf_prof'][pro][c][h] for c in range(wind_cell_num[pro])])
                        +credible_solar * gp.quicksum([x_solar[pro][c]*solar_cell['provin_cf_sort'][pro][c][3]*solar_cell['cf_prof'][pro][c][h] for c in range(solar_cell_num[pro])])
                        +scen_params['shedding']['with_shedding'] * load_shedding[pro][h]
                        +rt_effi_phs*dischar_phs[pro][h]
                        +rt_effi_bat*dischar_bat[pro][h]
                        +(1-scen_params['to_ct']['ct_loss']) * resv_to_ct[pro][h]
                        +gp.quicksum([rt_effi_lds[st]*dischar_lds[st][pro][h] for st in lds])
                        +rt_effi_phs*resv_phs[pro][h]
                        +rt_effi_bat*resv_bat[pro][h]
                        +gp.quicksum([rt_effi_lds[st]*resv_lds[st][pro][h] for st in lds])
                        +gp.quicksum([(1-trans_loss)**trans_dis[(pro1,pro)]*load_trans[(pro1,pro)][h] for pro1 in trans_from[pro]])
                        -trans_out['wind'][pro][h]-trans_out['solar'][pro][h]-trans_out['l2'][pro][h]-trans_out['l3'][pro][h]
                        -trans_out['l1'][pro][h]-trans_out['l4'][pro][h]
                        >= (1+demand_resv)*pro_dem[pro][h]+demand_resv*(pro_dem_full[pro][h]-pro_dem[pro][h])
                        for pro in provins for h in hour_seed)

        interProvinModel.addConstrs(
            load_resv['l1'][pro][h]+load_resv['l2'][pro][h]+load_resv['l4'][pro][h]+
            rt_effi_phs*resv_phs[pro][h]+
            rt_effi_bat*resv_bat[pro][h]+
            gp.quicksum([rt_effi_lds[st]*resv_lds[st][pro][h] for st in lds])
            >= vre_resv * (inte_wind[pro][h]+inte_solar[pro][h]+trans_out['wind'][pro][h]+trans_out['solar'][pro][h])
            for pro in provins for h in hour_seed)

    #ramp up and ramp down

    layer_index={'l1':0,'l2':1,'l3':2,'l4':3}

    for pro in provins:
        for h in hour_seed[1:]:
            for l in ['l1','l2','l3']:
                interProvinModel.addConstr(
                    ru[l][pro][h]
                    <= scen_params['ramp'][l]*layer_cap_max[pro][layer_index[l]]
                )
                interProvinModel.addConstr(
                    rd[l][pro][h]
                    <= scen_params['ramp'][l]*layer_cap_max[pro][layer_index[l]]
                )
    
    for pro in provins:
        if layer_cap_max[pro][3] > 0:
            for h in hour_seed[1:]:
                interProvinModel.addConstr(
                    ru['l4'][pro][h] <= scen_params['ramp']['l4'] * layer_cap_max[pro][3]
                )

                interProvinModel.addConstr(
                    rd['l4'][pro][h] <= scen_params['ramp']['l4'] * layer_cap_max[pro][3]
                )

                interProvinModel.addConstr(
                    ru['l4'][pro][h] >= load_conv['l4'][pro][h]+trans_out['l4'][pro][h]-
                                        load_conv['l4'][pro][hour_pre[h]]-trans_out['l4'][pro][hour_pre[h]]
                )

                interProvinModel.addConstr(
                    rd['l4'][pro][h] >= load_conv['l4'][pro][hour_pre[h]]+trans_out['l4'][pro][hour_pre[h]]-
                                        load_conv['l4'][pro][h]-trans_out['l4'][pro][h]
                )


    interProvinModel.addConstrs(ru[l][pro][h] >= 
                                load_conv[l][pro][h]+charge_phs[l][pro][h]+charge_bat[l][pro][h]
                                +gp.quicksum([charge_lds[st][l][pro][h] for st in lds])
                                +trans_out[l][pro][h]-
                                load_conv[l][pro][hour_pre[h]]-charge_phs[l][pro][hour_pre[h]]-
                                charge_bat[l][pro][hour_pre[h]]
                                -gp.quicksum([charge_lds[st][l][pro][hour_pre[h]] for st in lds])                         
                                -trans_out[l][pro][hour_pre[h]]
                                for l in ['l1','l2','l3'] for pro in provins for h in hour_seed[1:])

    interProvinModel.addConstrs(rd[l][pro][h] >= 
                                load_conv[l][pro][hour_pre[h]]+charge_phs[l][pro][hour_pre[h]]+
                                charge_bat[l][pro][hour_pre[h]]
                                +gp.quicksum([charge_lds[st][l][pro][hour_pre[h]] for st in lds])                  
                                +trans_out[l][pro][hour_pre[h]]-
                                load_conv[l][pro][h]-charge_phs[l][pro][h]-charge_bat[l][pro][h]
                                -gp.quicksum([charge_lds[st][l][pro][h] for st in lds])    
                                -trans_out[l][pro][h]
                                for l in ['l1','l2','l3'] for pro in provins for h in hour_seed[1:])

    
    #inertia constraints

    winter_hour = GetWinterHour()

    if scen_params['inertia']['with_inertia']:
        for pro in provins:
            for h in hour_seed:
                if h in winter_hour:
                    interProvinModel.addConstr(
                        scen_params['storage']['inertia_cons']['phs'] * cap_phs[pro] +
                        scen_params['storage']['inertia_cons']['bat'] * cap_bat[pro] +
                        scen_params['hydro']['inertia_cons'] * layer_cap_max[pro][1] +
                        scen_params['coal']['inertia_cons'] * (load_conv['l1'][pro][h]+
                                            charge_bat['l1'][pro][h]+charge_phs['l1'][pro][h]+
                                            gp.quicksum([charge_lds[st]['l1'][pro][h] for st in lds])+
                                            trans_out['l1'][pro][h] + layer_cap_max[pro][4])+
                        scen_params['gas']['inertia_cons'] * (load_conv['l4'][pro][h]+trans_out['l4'][pro][h]) +
                        scen_params['nuclear']['inertia_cons'] * (load_conv['l3'][pro][h]+
                                            charge_bat['l3'][pro][h]+charge_phs['l3'][pro][h]+
                                            gp.quicksum([charge_lds[st]['l3'][pro][h] for st in lds])+
                                            trans_out['l3'][pro][h])+
                        scen_params['ccs']['beccs_cf'] * scen_params['biomass']['inertia_cons'] * layer_cap_max[pro][5] >= 
                        scen_params['demand']['inertia_cons'] * scen_params['inertia']['inertia_alpha'] * pro_dem_full[pro][h]
                    )
                else:
                    interProvinModel.addConstr(
                        scen_params['storage']['inertia_cons']['phs'] * cap_phs[pro] +
                        scen_params['storage']['inertia_cons']['bat'] * cap_bat[pro] +
                        scen_params['hydro']['inertia_cons'] * layer_cap_max[pro][1] +
                        scen_params['coal']['inertia_cons'] * (load_conv['l1'][pro][h]+
                                            charge_bat['l1'][pro][h]+charge_phs['l1'][pro][h]+
                                            gp.quicksum([charge_lds[st]['l1'][pro][h] for st in lds])+
                                            trans_out['l1'][pro][h])+
                        scen_params['gas']['inertia_cons'] * (load_conv['l4'][pro][h]+trans_out['l4'][pro][h]) +
                        scen_params['nuclear']['inertia_cons'] * (load_conv['l3'][pro][h]+
                                            charge_bat['l3'][pro][h]+charge_phs['l3'][pro][h]+
                                            gp.quicksum([charge_lds[st]['l3'][pro][h] for st in lds])+
                                            trans_out['l3'][pro][h])+
                        scen_params['ccs']['beccs_cf'] * scen_params['biomass']['inertia_cons'] * layer_cap_max[pro][5] >= 
                        scen_params['demand']['inertia_cons'] * scen_params['inertia']['inertia_alpha'] * pro_dem_full[pro][h]
                    )
    
    #interProvinModel.addConstrs(ru[l][pro][h] >=load_conv[l][pro][h]+trans_out[l][pro][h]-load_conv[l][pro][hour_pre[h]]-trans_out[l][pro][hour_pre[h]]
    #                            for l in ['l1'] for pro in provins for h in hour_seed[1:])

    #interProvinModel.addConstrs(rd[l][pro][h] >= load_conv[l][pro][hour_pre[h]]+trans_out[l][pro][hour_pre[h]]-load_conv[l][pro][h]-trans_out[l][pro][h]
    #                            for l in ['l1'] for pro in provins for h in hour_seed[1:])

    if scen_params['shedding']['with_shedding'] == 1:
        with open(work_dir+'data_pkl'+dir_flag+'tot_dem2060.pkl','rb+') as fin:
            tot_dem = pickle.load(fin)
        fin.close()

        interProvinModel.addConstr(
            gp.quicksum([load_shedding[pro][h] for pro in provins for h in hour_seed])
            <= year_count*(len(hour_seed)/8760)*scen_params['shedding']['shedding_cof']*tot_dem['tot_dem']/365)


    print('start to solve')
    #interProvinModel.write('interProvinModel'+str(inte_target)+'.mps')
    interProvinModel.optimize()
    #interProvinModel.write(res_dir+'solution.sol')

    obj_value = interProvinModel.objVal

    beccs_cap = 0

    f_beccs_cap = open(work_dir+'data_csv'+dir_flag+'beccs.csv','r+')

    for line in f_beccs_cap:
        line = line.replace('\n','')
        line = line.split(',')
        beccs_cap += eval(line[1])
    f_beccs_cap

    var_beccs_cost = (
        len(hour_seed) *
        scen_params['ccs']['beccs_cf'] *
        beccs_cap *
        scen_params['ccs']['bio_lcoe']
    )

    nuclear_cap = 0

    f_nuclear_cap = open(work_dir+'data_csv'+dir_flag+'nuclear.csv','r+')

    for line in f_nuclear_cap:
        line = line.replace('\n','')
        line = line.split(',')
        nuclear_cap += scen_params['nuclear']['beta'] * 0.001 * eval(line[1])
    f_nuclear_cap.close()

    var_nuclear_cost = (
        len(hour_seed) *
        scen_params['nuclear']['must_run'] *
        scen_params['nuclear']['var_cost'] *
        nuclear_cap
    )

    obj_value = obj_value + var_beccs_cost + var_nuclear_cost

    #输出目标函数值
    f_objV = open(res_dir+'objValue.csv','w+')
    f_objV.write(str(obj_value))
    f_objV.close()


    obj_break = {
        'wind_gen_cost': gp.quicksum(wind_gen_cost).getValue(),
        'solar_gen_cost': gp.quicksum(solar_gen_cost).getValue(),
        'ramp_up_cost': gp.quicksum(ramp_up_cost).getValue(),
        'ramp_dn_cost': gp.quicksum(ramp_dn_cost).getValue(),
        'fixed_phs_cost': gp.quicksum(fixed_phs_cost).getValue(),
        'fixed_bat_cost': gp.quicksum(fixed_bat_cost).getValue(),
        'fixed_lds_cost': gp.quicksum(fixed_lds_cost).getValue(),
        'var_phs_cost':  gp.quicksum(var_phs_cost).getValue(),
        'var_bat_cost':gp.quicksum(var_bat_cost).getValue(),
        'var_lds_cost':gp.quicksum(var_lds_cost).getValue(),
        'resv_cost':gp.quicksum(resv_cost).getValue(),
        'spur_cost_wind': gp.quicksum(spur_cost_wind).getValue(),
        'spur_cost_solar':  gp.quicksum(spur_cost_solar).getValue(),
        'trunk_cost': gp.quicksum(trunk_cost).getValue(),
        'trans_csot':  gp.quicksum(trans_cost).getValue(),
        'coal_ccs_cost':gp.quicksum(coal_ccs_cost).getValue(),
        'gas_ccs_cost': gp.quicksum(gas_ccs_cost).getValue(),
        'coal_ccs_cost_fixed':gp.quicksum(coal_ccs_cost_fixed).getValue(),
        'gas_ccs_cost_fixed':gp.quicksum(gas_ccs_cost_fixed).getValue(),
        'nuclear_cost_var':gp.quicksum(nuclear_cost_var).getValue(),
        'beccs_cost_fixed':gp.quicksum(beccs_cost_fixed).getValue(),
        'nuclear_cost_fixed': gp.quicksum(nuclear_cost_fixed).getValue(),
        'hydro_cost_fixed':gp.quicksum(hydro_cost_fixed).getValue(),
        'other_tech_cost': gp.quicksum(other_tech_cost).getValue(),
        'var_beccs_cost': var_beccs_cost,
        'var_nuclear_cost': var_nuclear_cost
    }

    with open(res_dir+'obj_break.pkl','wb+') as fout:
        pickle.dump(obj_break,fout)
    fout.close()

    folder = makeDir(res_dir+'shadow_prices')+dir_flag

    for pro in demConstrs:
        f_sp = open(folder+pro+'.csv','w+')
        shadow_prices = shadow_prices = interProvinModel.getAttr('Pi',demConstrs[pro])
        for h in shadow_prices:
            f_sp.write(str(h)+','+str(shadow_prices[h])+'\n')

        f_sp.close()

    #write model results
    for l in load_conv:
        folder = makeDir(res_dir+'load_conv'+dir_flag+l)
        for pro in load_conv[l]:
            res_load_conv = open(folder+dir_flag+pro+'.csv','w+')
            for h in load_conv[l][pro]:
                res_load_conv.write('%s,%s\n'% (h,load_conv[l][pro][h].x))
            res_load_conv.close()

    for l in load_resv:
        folder = makeDir(res_dir+'load_resv'+dir_flag+l)
        for pro in load_resv[l]:
            res_load_resv = open(folder+dir_flag+pro+'.csv','w+')
            for h in load_resv[l][pro]:
                res_load_resv.write('%s,%s\n'% (h,load_resv[l][pro][h].x))
            res_load_resv.close()

    if scen_params['shedding']['with_shedding'] == 1:
        folder = makeDir(res_dir+'load_shedding'+dir_flag)
        for pro in load_shedding:
            res_load_shedding = open(folder+dir_flag+pro+'.csv','w+')

            for h in load_shedding[pro]:
                res_load_shedding.write('%s,%s\n' % (h,load_shedding[pro][h].x))

            res_load_shedding.close()

    cell_cof_dict = {'x_wind':x_wind,'x_solar':x_solar}
    for file in cell_cof_dict:
        folder = makeDir(res_dir+file)
        for pro in cell_cof_dict[file]:
            res_cell_cof = open(folder+dir_flag+pro+'.csv','w+')
            for c in cell_cof_dict[file][pro]:
                res_cell_cof.write('%s,%s\n'%(c,cell_cof_dict[file][pro][c].x))
            res_cell_cof.close()

    inte_dict = {'inte_wind':inte_wind,'inte_solar':inte_solar}
    for file in inte_dict:
        folder = makeDir(res_dir+file)
        for pro in inte_dict[file]:
            res_inte = open(folder+dir_flag+pro+'.csv','w+')
            for i in inte_dict[file][pro]:
                res_inte.write('%s,%s\n'%(i,inte_dict[file][pro][i].x))
            res_inte.close()

    es_cap = {'phs':cap_phs,'bat':cap_bat}
    es_cap_count = {'phs':0,'bat':0,'caes':0,'vrb':0}
    for file in es_cap:
        folder = makeDir(res_dir+'es_cap'+dir_flag)
        res_store = open(folder+dir_flag+'es_'+file+'_cap.csv','w+')
        
        for pro in es_cap[file]:
            res_store.write('%s,%s\n'%(pro,es_cap[file][pro].x))
            es_cap_count[file] += es_cap[file][pro].x
        
        res_store.close()
    
    for file in cap_lds:
        folder = makeDir(res_dir+'es_cap'+dir_flag)
        res_store = open(folder+dir_flag+'es_'+file+'_cap.csv','w+')
        
        for pro in cap_lds[file]:
            res_store.write('%s,%s\n'%(pro,cap_lds[file][pro].x))
            es_cap_count[file] += cap_lds[file][pro].x
        
        res_store.close()
    
    f_es_tot_cap = open(res_dir+'es_cap'+dir_flag+'es_tot_cap.csv','w+')

    for st in es_cap_count:
        f_es_tot_cap.write(st+','+str(es_cap_count[st])+'\n')
    f_es_tot_cap.close()

    es_char = {'phs':charge_phs,'bat':charge_bat}
    for file in es_char:
        for et in es_char[file]:
            folder = makeDir(res_dir+'es_char'+dir_flag+file+dir_flag+et)
            for pro in es_char[file][et]:
                res_es_char = open(folder+dir_flag+pro+'.csv','w+')
                for h in es_char[file][et][pro]:
                    res_es_char.write('%s,%s\n'%(h,es_char[file][et][pro][h].x))
                res_es_char.close()

    for file in charge_lds:
        for et in charge_lds[file]:
            folder = makeDir(res_dir+'es_char'+dir_flag+file+dir_flag+et)
            for pro in charge_lds[file][et]:
                res_es_char = open(folder+dir_flag+pro+'.csv','w+')
                for h in charge_lds[file][et][pro]:
                    res_es_char.write('%s,%s\n'%(h,charge_lds[file][et][pro][h].x))
                res_es_char.close()


    es_inte = {'phs':dischar_phs,'bat':dischar_bat}
    rtrip_efi = {'phs':rt_effi_phs,'bat':rt_effi_bat}

    for file in es_inte:
        folder = makeDir(res_dir+'es_inte'+dir_flag+file+dir_flag)
        for pro in es_inte[file]:
            res_es_inte = open(folder+dir_flag+pro+'.csv','w+')
            for h in es_inte[file][pro]:
                res_es_inte.write('%s,%s\n'%(h,rtrip_efi[file]*es_inte[file][pro][h].x))
            res_es_inte.close()
    
    for file in dischar_lds:
        folder = makeDir(res_dir+'es_inte'+dir_flag+file+dir_flag)
        for pro in dischar_lds[file]:
            res_es_inte = open(folder+dir_flag+pro+'.csv','w+')
            for h in dischar_lds[file][pro]:
                res_es_inte.write('%s,%s\n'%(h,rt_effi_lds[file]*dischar_lds[file][pro][h].x))
            res_es_inte.close()

    
    folder = makeDir(res_dir+'resv_phs'+dir_flag)
    for pro in resv_phs:
        res_resv_phs = open(folder+dir_flag+pro+'.csv','w+')

        for h in resv_phs[pro]:
            res_resv_phs.write('%s,%s\n' % (h,resv_phs[pro][h].x))

        res_resv_phs.close()
    
    for et in trans_out:
        folder = makeDir(res_dir+'trans_out'+dir_flag+et+dir_flag)+dir_flag
        for pro in trans_out[et]:
            f_trans_out = open(folder+pro+'.csv','w+')

            for h in trans_out[et][pro]:
                f_trans_out.write('%s,%s\n' % (h,trans_out[et][pro][h].x))
            f_trans_out.close()

    folder = makeDir(res_dir+'resv_bat'+dir_flag)
    for pro in resv_bat:
        res_resv_bat = open(folder+dir_flag+pro+'.csv','w+')

        for h in resv_bat[pro]:
            res_resv_bat.write('%s,%s\n' % (h,resv_bat[pro][h].x))
        res_resv_bat.close()

    
    for st in resv_lds:
        folder = makeDir(res_dir+'resv_'+st+dir_flag)
        for pro in resv_lds[st]:
            res_resv_lds = open(folder+dir_flag+pro+'.csv','w+')

            for h in resv_lds[st][pro]:
                res_resv_lds.write('%s,%s\n' % (h,resv_lds[st][pro][h].x))
            res_resv_lds.close()

    folder = makeDir(res_dir+'load_trans'+dir_flag)
    for pro in load_trans:
        res_trans = open(folder+dir_flag+pro[0]+'_'+pro[1]+'.csv','w+')
        for h in load_trans[pro]:
            res_trans.write('%s,%s\n'%(h,load_trans[pro][h].x))
        res_trans.close()
    
    
    es_tot = {'phs':tot_energy_phs,'bat':tot_energy_bat}

    for file in es_tot:
        folder = makeDir(res_dir+'es_tot'+dir_flag+file+dir_flag)
        for pro in es_tot[file]:
            res_es_tot = open(folder+pro+'.csv','w+')
            for h in es_tot[file][pro]:
                res_es_tot.write('%s,%s\n'%(h,es_tot[file][pro][h].x))
            res_es_tot.close()

    for file in tot_energy_lds:
        folder = makeDir(res_dir+'es_tot'+dir_flag+file+dir_flag)
        for pro in tot_energy_lds[file]:
            res_es_tot = open(folder+pro+'.csv','w+')
            for h in tot_energy_lds[file][pro]:
                res_es_tot.write('%s,%s\n'%(h,tot_energy_lds[file][pro][h].x))
            res_es_tot.close()

    folder = makeDir(res_dir+'new_trans_cap')
    res_new_cap_trans = open(folder+dir_flag+'cap_trans_new.csv','w+')
    for pro in cap_trans_new:
        res_new_cap_trans.write('%s,%s,%s\n'%(pro[0],pro[1],cap_trans_new[pro].x))
    res_new_cap_trans.close()

    


    ct_cap_json = {}

    for pro in provins:
        ct_cap_json[pro] = cap_to_ct[pro].X
    
    ct_cap_json['sum'] = sum(ct_cap_json.values())

    fout = open(res_dir+dir_flag+'to_ct_cap.json','w+')
    fout.write(json.dumps(ct_cap_json,sort_keys=True,indent=2))
    fout.close()

    folder = makeDir(res_dir+'to_ct'+dir_flag+'wind_to_ct')

    for pro in provins:
        res_wind_to_ct = open(folder+dir_flag+pro+'.csv','w+')

        for h in wind_to_ct[pro]:
            res_wind_to_ct.write('%s,%s\n' % (h,wind_to_ct[pro][h].X))
        
        res_wind_to_ct.close()

    folder = makeDir(res_dir+'to_ct'+dir_flag+'solar_to_ct')

    for pro in provins:
        res_solar_to_ct = open(folder+dir_flag+pro+'.csv','w+')

        for h in solar_to_ct[pro]:
            res_solar_to_ct.write('%s,%s\n' % (h,solar_to_ct[pro][h].X))
        
        res_solar_to_ct.close()

    
    folder = makeDir(res_dir+'to_ct'+dir_flag+'load_to_ct')

    for pro in provins:
        res_load_to_ct = open(folder+dir_flag+pro+'.csv','w+')

        for h in load_to_ct[pro]:
            res_load_to_ct.write('%s,%s\n' % (h,(1-scen_params['to_ct']['ct_loss'])*load_to_ct[pro][h].X))
        
        res_load_to_ct.close()


    print('Results processed...')






