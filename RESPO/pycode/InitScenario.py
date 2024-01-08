import io
import pickle
import sys


from uniqeFunction import (dirFlag,getResDir,getWorkDir,makeDir)

import json

dir_flag = dirFlag()
work_dir = getWorkDir()


def InitSenarioParams(vre_year,res_tag):
    res_dir = makeDir(getResDir(vre_year,res_tag))

    scen_params = {
        'trans':{},
        'storage':{},
        'vre':{},
        'nuclear':{},
        'demand':{},
        'resv':{},
        'coal':{},
        'ramp':{},
        'ccs':{},
        'shedding':{},
        'gas':{},
        'hydro':{},
        'biomass':{},
        'inertia':{},
        'to_ct':{}
    }
    
    scen_params['model_params'] = {
        'exovar_file':'model_exovar_trans_relax.pkl'
    }

    scen_params['trans'] = {
        'capex_spur_fixed': 1 * 262, #yuan/kw
        'capex_spur_var': 1 * 3,  #yuan/kw-km
        'capex_trunk_fixed': 1 * 159,
        'capex_trunk_var': 1 * 1.76,
        'trans_loss': 0.000032,
        'interprovincial_scale': 1,
        'is_full_inter_province':0,
        'trunk_inter_province':0
    }

    scen_params['storage'] = {
        'duration_phs': 1 * 8,
        'duration_bat': 1 * 4,
        'duration_lds': {'caes':1*20,'vrb':1*10},
        'sdiss_phs':0, #self discharge: %/h
        'sdiss_bat':0,
        'sdiss_lds':{'caes':1*0.00042,'vrb':1*0.00025},
        'capex_power_phs': 1 * 3840, #yuan/kw
        'capex_power_bat': 1 * 480,
        'capex_power_lds': {'caes':1*4800,'vrb':1*3000},
        'capex_energy_phs':1 * 0,
        'capex_energy_bat':1 * 480,
        'capex_energy_lds':{'caes':1*0,'vrb':1*0},
        'rt_effi_phs': 0 + 0.78,
        'rt_effi_bat': 0 + 0.95,
        'rt_effi_lds': {'caes':0+0.52,'vrb':0+0.78},
        'fixed_omc_phs': 1 * 39,
        'fixed_omc_bat': 1 * 18,
        'fixed_omc_lds': {'caes':1*5,'vrb':1*18},
        'var_omc_phs': 1.5 * 0.001,
        'var_omc_bat': 20 * 0.001,
        'var_omc_lds': {'caes':3*0.001,'vrb':20*0.001},
        'with_lds': 0,
        'with_caes':0,
        'with_vrb':0,
        'span_lds':{'caes':30,'vrb':15},
        'inertia_cons':{'phs':2.83,'bat':5.89,'caes':2.83,'vrb':5.89}
    }

    scen_params['vre'] = {
        'cap_scale_pv': 1,
        'cap_scale_wind': 1,
        'cap_scale_wind_ep':1,
        'cap_scale_pv_ep':1,
        'capex_equip_pv': 1 * 1100,
        'capex_equip_dpv': 1 * 1400,
        'capex_equip_on_wind': 1 * 2200,
        'capex_equip_off_wind': 1 * 3800,
        'capex_other_pv': 1 * 400,
        'capex_other_dpv': 1 * 600,
        'capex_other_on_wind': 1 * 800,
        'capex_other_off_wind': 1 * 1600,
        'capex_om_on_wind': 1 * 45,
        'capex_om_off_wind': 1 * 81,
        'capex_om_pv': 1 * 7.5,
        'capex_om_dpv': 1 * 10,
        'aggregated': 0,
        'inter_annual':0,
        'wind_with_xz':0,
        'wind_land_use':'mid',
        'solar_land_use':'mid',
        'is_solar_landuse_sw':1
    }

    scen_params['nuclear'] = {
        'must_run': 0 + 0.85,
        'ramp': 0 + 0.05,
        'var_cost':0.09,
        'beta':1,
        'inertia_cons':4.07
    }

    scen_params['gas'] = {
        'beta':3.3*1,
        'inertia_cons':4.97
    }

    scen_params['demand'] = {
        'scale': 1.0,
        'inertia_cons':3.5
    }

    scen_params['resv'] = {
        'vre_resv': 0.0 + 0.05,
        'demand_resv': 0.0 + 0.05,
        'with_demand_resv': 1,
        'with_vre_resv':1,
        'vre_resv_provincialy':0
    }


    scen_params['inertia'] = {
        'with_inertia':0,
        'inertia_alpha':0.5
    }

    scen_params['coal'] = {
        'min_coal': 0 + 0.15,
        'beta':0.1,
        'theta':0,
        'inertia_cons':5.89
    }

    scen_params['ramp'] = {
        'l1':0.25,
        'l2':0.25,
        'l3':0.05,
        'l4':0.5
    }

    scen_params['ccs'] = {
        'coal_loss':0.05,
        'gas_loss':0.05,
        'bio_loss':0.05,
        'coal_lcoe':0.3095,
        'gas_lcoe':0.62,
        'bio_lcoe':0.59,
        'beccs_cf':0.8
    }

    scen_params['shedding'] = {
        'with_shedding':0,
        'shedding_vom':1.2, #yuan/kWh
        'shedding_cof':0.1,
    }

    scen_params['hydro'] = {
        'inertia_cons':2.83
    }

    scen_params['biomass'] = {
        'inertia_cons':2.94
    }

    scen_params['to_ct'] = {
        'with_ct':0,
        'ct_loss':0,
        'effi':0.8,
        'cost_kwh':0.95 * 0.5
    }

    with open(res_dir+dir_flag+'scen_params.pkl','wb+') as fout:
        pickle.dump(scen_params,fout)
    fout.close()
    

    fout = open(res_dir+dir_flag+'scen_params.json','w+')
    fout.write(json.dumps(scen_params,sort_keys=True,indent=2))
    fout.close()


if __name__ == '__main__':
    InitSenarioParams('w2015_s2015','TransRelax_0122')
