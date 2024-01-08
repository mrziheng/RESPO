#This function is for calculating electricity price required for 10% equity return given a specific capacity factor under various consumptions
#Unit: equipC: yuan/kW, otherC: yuan/kW, OMC: yuan/MWh, elePKWh: yuan/kWh
#Default constraction period is 3 years, year 1 invests 20% of the total static investment(owned fund), year 2 invest 80% of the total investment(bank loan), and outputs from year 3

import math
import numpy as np
import pickle
import scipy.io as scio

def cfEleP(cf,equipC,otherC,OMC,r,N,iN,dN):
	#Init cashflow: yuan/kW
	cash = [0]*N 
	#Init Enterprise income tax: yuan/kW
	EIT = [0]*N
	#Annual electricity generation: kWh/kW
	eleGen = cf*8760
	#Total capital cost: yuan/kW
	totCapCost = equipC+otherC
	#Total equipment cost: yuan/kW
	totEquipCost = equipC
	#Total debt: yuan/kW
	totDebt = totCapCost*0.8
	
	#Annual debt payment: yuan/kW
	#Annual principal: yuan/kW
	#Annual interestpayment: yuan/kW
	Loanpayment = [0]*N
	Principal = [0]*N
	Interestpayment = [0]*N
	
	for i in range(2,3+iN-1):
		Loanpayment[i] = (totDebt*r*((1+r)**iN)/((1+r)**iN-1))
	
	Principal[1] = totDebt
	for i in range(3,3+iN-1):
		Principal[i-1] = Principal[i-2]*(1+r)-Loanpayment[i]
		
	for i in range(2,3+iN-1):
		Interestpayment[i] = Principal[i-1]*r
		
	#Annual O&M cost: yuan/kW
	aOM = [0] * N
	for i in range(2,N):
		aOM[i] = round(OMC*0.001*eleGen,4)
	#Annual depreciation cost: 10,000 yuan
	aDepr = [0] * N
	for i in range(2,3+dN-1):
		aDepr[i] = (totEquipCost/dN)
		
	#Total VAT that can be deducted: yuan/kW
	totVAT = (totEquipCost/1.17)*0.17 
	#Initial electricity price: set an initial price for StopAsyncIteration
	#(yuan/kWh)
	elePMin = (aDepr[2]+aOM[2])/eleGen*1.17
	elePMax = 100
	eleP = elePMin
	step = (elePMax - elePMin) / 2
	NPV = 100
	
	while(abs(NPV) > 0.001):
		eleP += step
		NPV = 0
		cash = [0] * N
		
		#Tax calculation,Calculate total number of years that can get full VAT deducted
		# and the partially deducted number for last year
		#Wind power VAT 50% off
		annualVAT = eleP*eleGen/1.17*0.17*0.5
		#VAT of initial equipmemts 100% off
		numofDeducted = math.floor(totVAT/annualVAT)
		lastyearDeducted = totVAT-annualVAT*numofDeducted
	
		#VAT+surcharge cost, the urban construction and education surcharge is 10% of the VAT actually paid
		VAT = [0] * N
		for i in range(2,numofDeducted+3):
			VAT[i] = 0
		VAT[numofDeducted+3] = annualVAT-lastyearDeducted
		for i in range(numofDeducted+3+1,N):
			VAT[i] = annualVAT
		
		#Enterprise income tax
		IBT = [0] * N
		for i in range(2,N):
			IBT[i] = (eleP*eleGen-Interestpayment[i]-aOM[i]-aDepr[i])
			EIT[i] = IBT[i] * 0.25
		
		EIT[2:5] = [0,0,0]
		for i in range(5,8):
			EIT[i] = EIT[i+1] / 2
	
		cash[0] = -totCapCost*0.2
		cash[1] = totCapCost*0.8-totCapCost*0.8 #to check
	
		for i in range(2,N):
			cash[i] = eleP*eleGen-Loanpayment[i]-aOM[i]-EIT[i]-VAT[i]*(1+0.1)
		#Caculate NPV
		for i in range(N):
			NPV += cash[i] / ((1+0.1) ** (i))
		
		#Adjust electricity price for the next iteration
		if NPV > 0:
			elePMax = eleP
			step = (-elePMax + elePMin) / 2
		else:
			elePMin = eleP
			step = (elePMax - elePMin) / 2
	elePKWh = eleP
	
	return elePKWh

#print('onshore',cfEleP(0.23,2200,800,45,0.062,25,15,15))
#print('upv',cfEleP(0.19,1100,400,7.5,0.062,25,15,15))
#print('offshore',cfEleP(0.32,3800,1600,81,0.062,25,15,15))
#print('dpv',cfEleP(0.17,1400,600,10,0.062,25,15,15))