"""Produce research figures from generated JSON. Requires matplotlib."""
import json
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
try:
    import matplotlib
except ModuleNotFoundError:
    sys.path.insert(0,str(HERE/'.plotdeps'))
    import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,
                     'axes.spines.right':False,'axes.spines.left':False,'axes.edgecolor':'#c3d1c7',
                     'axes.labelcolor':'#26453d','xtick.color':'#536c62','ytick.color':'#536c62',
                     'text.color':'#173e34','figure.facecolor':'white','axes.facecolor':'white',
                     'savefig.facecolor':'white','svg.fonttype':'none'})


def save(fig,name):
    fig.savefig(HERE/f'{name}.png',dpi=200,bbox_inches='tight')
    fig.savefig(HERE/f'{name}.svg',bbox_inches='tight')
    plt.close(fig)


def survey():
    d=json.loads((HERE/'brfss2023-results.json').read_text(encoding='utf-8'))
    age=d['cost_age_standardized']['strata']
    groups=['18–44','45–64','65+']
    dm=np.array([x['groups']['diabetes']['weighted_rate']*100 for x in age])
    no=np.array([x['groups']['no_diabetes']['weighted_rate']*100 for x in age])
    crude=[d['cost_rates']['diabetes']['weighted_rate']*100,d['cost_rates']['no_diabetes']['weighted_rate']*100]
    standard=np.array(d['cost_age_standardized']['standard_rates'])*100
    fig,(ax1,ax2)=plt.subplots(1,2,figsize=(11.6,5.7),gridspec_kw={'width_ratios':[1.2,1]})
    fig.suptitle('Doctor-visit cost barriers differ across age groups',x=.07,y=.96,ha='left',fontsize=17,fontweight='bold')
    fig.text(.07,.90,'2023 BRFSS · 48 participating states and DC · weighted descriptive estimates',fontsize=10,color='#667d70')
    x=np.arange(3); width=.32
    ax1.bar(x-width/2,dm,width,color='#246b57',label='Reports diabetes')
    ax1.bar(x+width/2,no,width,color='#a9cbbb',label='Reports no diabetes')
    for i,(a,b) in enumerate(zip(dm,no)):
        ax1.text(i-width/2,a+.45,f'{a:.1f}%',ha='center',fontsize=9)
        ax1.text(i+width/2,b+.45,f'{b:.1f}%',ha='center',fontsize=9)
    ax1.set_xticks(x,groups);ax1.set_ylim(0,28);ax1.set_ylabel('Reported cost barrier (%)');ax1.set_title('Within age groups',loc='left',fontweight='bold',pad=12)
    ax1.set_yticks([0,5,10,15,20,25]);ax1.yaxis.grid(True,color='#e6eee8');ax1.set_axisbelow(True);ax1.tick_params(length=0,pad=7)
    x2=np.arange(2)
    ax2.bar(x2-width/2,[crude[0],standard[0]],width,color='#246b57')
    ax2.bar(x2+width/2,[crude[1],standard[1]],width,color='#a9cbbb')
    for i,(a,b) in enumerate(zip([crude[0],standard[0]],[crude[1],standard[1]])):
        ax2.text(i-width/2,a+.45,f'{a:.1f}%',ha='center',fontsize=9)
        ax2.text(i+width/2,b+.45,f'{b:.1f}%',ha='center',fontsize=9)
    ax2.set_xticks(x2,['Crude','Age-standardized']);ax2.set_ylim(0,28);ax2.set_yticks([0,5,10,15,20,25]);ax2.set_title('Summary comparison',loc='left',fontweight='bold',pad=12)
    ax2.yaxis.grid(True,color='#e6eee8');ax2.set_axisbelow(True);ax2.tick_params(length=0,pad=7)
    fig.legend(loc='lower center',bbox_to_anchor=(.5,.155),ncol=2,frameon=False)
    fig.text(.07,.085,'Cost barrier: needed a doctor in the past year but could not afford a visit. Diabetes and access are self-reported.',fontsize=8,color='#536c62')
    fig.text(.07,.052,'Age standard: weighted age distribution of pooled respondents with known age. Point estimates only; no design-based CIs.',fontsize=8,color='#536c62')
    fig.text(.07,.020,'Source: CDC BRFSS 2023, third-party verified mirror. All diabetes types; associations are not causal.',fontsize=8,color='#536c62')
    fig.subplots_adjust(left=.07,right=.97,top=.79,bottom=.25,wspace=.26)
    save(fig,'figure_brfss_cost_barriers')


def hospital():
    d=json.loads((HERE/'results.json').read_text(encoding='utf-8')); rows=d['prior_inpatient']
    rates=np.array([x['rate']*100 for x in rows]);low=np.array([x['ci_low']*100 for x in rows]);high=np.array([x['ci_high']*100 for x in rows])
    fig,ax=plt.subplots(figsize=(8,5.5))
    fig.suptitle('Prior inpatient use and recorded readmission',x=.11,y=.96,ha='left',fontsize=17,fontweight='bold')
    fig.text(.11,.89,'Hospital records involving diabetes · 1999–2008',fontsize=10,color='#667d70')
    x=np.arange(3);ax.bar(x,rates,color=['#a9cbbb','#69a187','#246b57'],width=.57)
    ax.errorbar(x,rates,yerr=[rates-low,high-rates],fmt='none',ecolor='#173e34',capsize=4,lw=1.4)
    for i,r in enumerate(rows):ax.text(i,high[i]+.8,f"{rates[i]:.1f}%\nn = {r['n']:,}",ha='center',va='bottom',fontsize=9)
    ax.set_ylim(0,29);ax.set_yticks([0,5,10,15,20,25]);ax.set_ylabel('Recorded readmission within 30 days (%)');ax.set_xticks(x,['0','1','2 or more']);ax.set_xlabel('Inpatient visits in preceding year',labelpad=9)
    ax.yaxis.grid(True,color='#e6eee8');ax.set_axisbelow(True);ax.tick_params(length=0,pad=7)
    fig.text(.11,.10,'Bars show descriptive rates; error bars are 95% Wilson intervals, not intervals for differences.',fontsize=8,color='#536c62')
    fig.text(.11,.065,'One encounter per patient; death and hospice exclusions. No adjustment for illness or other factors.',fontsize=8,color='#536c62')
    fig.text(.11,.03,'Source: UCI Diabetes 130-US Hospitals. All diabetes types; associations are not causal.',fontsize=8,color='#536c62')
    fig.subplots_adjust(left=.11,right=.96,top=.78,bottom=.24)
    save(fig,'figure_hospital_readmission')


if __name__=='__main__':
    survey();hospital();print('Saved both PNG and SVG figures.')
