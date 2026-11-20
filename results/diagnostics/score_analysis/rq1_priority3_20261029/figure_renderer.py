"""Render standalone publication-friendly figures from the frozen score audit."""
import argparse
from pathlib import Path
import shutil

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import rq1_priority3_scores as scores

c=scores.common
COLORS={'linevul':'#1767a6','vulberta':'#cf6417'}
NAMES={'bigvul_test_sample_2000':'BigVul sample','primevul_test':'PrimeVul','llmvul_test':'LLMVul','cweval_test':'CWEval'}
MODELS={'linevul':'LineVul','vulberta':'VulBERTa'}


def run(source,destination):
    report=c.read_json(source/'summary.json'); assert report['status']=='pass'
    destination.mkdir(parents=True,exist_ok=True)
    jobs={(j['model'],j['dataset']):j for j in report['jobs']}
    input_source=c.ROOT/report['source_run']/'joined_inputs.csv'
    assert c.sha(input_source)==report['source_hashes']['joined_inputs.csv']
    joined=c.read_csv(input_source)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,
        'axes.spines.right':False,'axes.titlesize':11,'figure.dpi':140,'savefig.dpi':180,'pdf.fonttype':42})
    artifacts=[]
    def save(fig,name):
        for ext in ['png','pdf']:
            path=destination/(name+'.'+ext); fig.savefig(path,bbox_inches='tight',facecolor='white')
            artifacts.append(dict(path=path.relative_to(c.ROOT).as_posix(),sha256=c.sha(path)))
        plt.close(fig)
    def probability_axes(ax):
        ax.set_xlim(0,1); ax.set_ylim(0,1.03); ax.grid(alpha=.15)
    def getcurve(model,stem):
        return c.read_csv(source/(model+'_'+stem+'_curve.csv'))
    def values(rows,k): return np.array([float(r[k]) for r in rows])

    fig,axes=plt.subplots(2,4,figsize=(16,7.2),layout='constrained')
    fig.suptitle('RQ1 score ranking: ROC and precision–recall',fontsize=17)
    for col,stem in enumerate(scores.audit.STEMS):
        roc,pr=axes[:,col]
        roc.plot([0,1],[0,1],color='#999999',ls='--',lw=1)
        pi=jobs['linevul',stem]['point']['prevalence']
        pr.axhline(pi,color='#999999',ls='--',lw=1,label=f'Prevalence {pi:.1%}')
        for model in MODELS:
            if (model,stem) not in jobs: continue
            j=jobs[model,stem]; rows=getcurve(model,stem); color=COLORS[model]
            roc.plot(values(rows,'fpr'),values(rows,'recall'),color=color,lw=1.6,label=f"{MODELS[model]} AUC {j['point']['roc_auc']:.3f}")
            roc.scatter(j['point']['fpr'],j['point']['recall'],color=color,s=25,zorder=4)
            precision=values(rows,'precision'); precision[0]=1
            pr.step(values(rows,'recall'),precision,where='pre',color=color,lw=1.6,label=f"{MODELS[model]} AP {j['point']['average_precision']:.3f}")
            if j['point']['precision_defined']:
                pr.scatter(j['point']['recall'],j['point']['precision'],color=color,s=25,zorder=4)
        roc.set_title(f"{NAMES[stem]} · n={jobs['linevul',stem]['rows']:,}")
        for ax in [roc,pr]: probability_axes(ax); ax.legend(loc='lower right' if ax is roc else 'upper right',fontsize=8)
        roc.set(xlabel='False-positive rate',ylabel='Recall' if col==0 else '')
        pr.set(xlabel='Recall',ylabel='Precision' if col==0 else '')
    fig.supxlabel('Dots show the original threshold 0.5. AP uses non-interpolated average precision.',fontsize=10)
    save(fig,'ranking')

    fig,axes=plt.subplots(2,4,figsize=(16,7.5),layout='constrained')
    fig.suptitle('Score distributions by reference label',fontsize=17)
    for row,model in enumerate(MODELS):
        for col,stem in enumerate(scores.audit.STEMS):
            ax=axes[row,col]
            if (model,stem) not in jobs:
                ax.axis('off'); ax.text(.5,.5,'No selected VulBERTa\nBigVul evaluation',ha='center',va='center',transform=ax.transAxes,color='#666666'); continue
            data=[r for r in joined if r['model']==model and r['dataset']==stem]
            for label,color in [(0,'#457b9d'),(1,'#b52d40')]:
                v=np.sort([float(r['prob_vulnerable']) for r in data if int(r['label'])==label])
                ax.step(v,np.arange(1,len(v)+1)/len(v),where='post',color=color,label=f"{'Vulnerable' if label else 'Non-vulnerable'} (n={len(v):,})")
            ax.set_xscale('logit'); ax.set_xlim(1e-5,1-1e-5); ax.set_ylim(0,1.02)
            ax.axvline(.5,color='#888888',ls='--',lw=1)
            ax.set_xticks([.0001,.01,.5,.99,.9999],['0.0001','0.01','0.5','0.99','0.9999'])
            ax.tick_params(axis='x',labelsize=8); ax.grid(alpha=.15)
            ax.set_title(f'{MODELS[model]} / {NAMES[stem]}')
            ax.legend(fontsize=8,loc='lower right')
            ax.set(xlabel='Vulnerable score (logit scale)',ylabel='Cumulative fraction within class' if col==0 else '')
    fig.supxlabel('Curves are normalized separately within each label; class imbalance is shown by n.',fontsize=10)
    save(fig,'score_distributions')

    fig,axes=plt.subplots(2,4,figsize=(16,7.2),layout='constrained')
    fig.suptitle('Threshold and prevalence sensitivity',fontsize=17)
    for col,stem in enumerate(scores.audit.STEMS):
        upper,lower=axes[:,col]; pi=jobs['linevul',stem]['point']['prevalence']
        upper.axhline(2*pi/(1+pi),ls='--',color='#888888',lw=1,label='Always positive')
        upper.axvline(.5,color='#999999',ls=':',lw=1)
        for model in MODELS:
            if (model,stem) not in jobs: continue
            j=jobs[model,stem]; table=getcurve(model,stem); threshold=values(table,'threshold')
            mask=(threshold>0)&(threshold<=1)
            plotted_thresholds=threshold[mask]; plotted_f1=values(table,'f1')[mask]
            if plotted_thresholds[-1]>1e-5:
                plotted_thresholds=np.r_[plotted_thresholds,1e-5]
                plotted_f1=np.r_[plotted_f1,plotted_f1[-1]]
            upper.step(plotted_thresholds,plotted_f1,where='post',color=COLORS[model],label=MODELS[model])
            upper.scatter(.5,j['point']['f1'],color=COLORS[model],s=25)
            p=np.linspace(.001,.5,500); tpr=j['point']['recall']; fpr=j['point']['fpr']
            f1=2*p*tpr/(p*(1+tpr)+(1-p)*fpr)
            lower.plot(p,f1,color=COLORS[model],label=MODELS[model])
            lower.scatter(pi,j['point']['f1'],color=COLORS[model],s=25)
        upper.set(xscale='log',xlim=(1e-5,1),ylim=(0,1),xlabel='Threshold (log scale)',ylabel='F1' if col==0 else '',title=NAMES[stem])
        lower.axvline(.05,color='#999999',ls=':',lw=1,label='Common 5% prevalence')
        lower.set(xlim=(0,.5),ylim=(0,1),xlabel='Hypothetical positive prevalence',ylabel='F1 at original operating rates' if col==0 else '')
        lower.xaxis.set_major_formatter(PercentFormatter(1))
        for ax in [upper,lower]: ax.grid(alpha=.15); ax.legend(fontsize=8,loc='upper right' if ax is upper else 'lower right')
    fig.supxlabel('Top: exploratory test-set sweep, not selected deployment thresholds. Bottom: fixed TPR/FPR at threshold 0.5.',fontsize=10)
    save(fig,'threshold_prevalence')

    bins=c.read_csv(source/'reliability.csv')
    fig,axes=plt.subplots(2,4,figsize=(16,7.4),layout='constrained')
    fig.suptitle('Reliability: predicted score versus observed vulnerable rate',fontsize=17)
    for row,model in enumerate(MODELS):
        for col,stem in enumerate(scores.audit.STEMS):
            ax=axes[row,col]
            if (model,stem) not in jobs: ax.axis('off'); continue
            ax.plot([0,1],[0,1],color='#999999',ls='--',lw=1)
            for strategy,marker,alpha in [('uniform','o',1),('quantile','x',.65)]:
                b=[r for r in bins if r['model']==model and r['dataset']==stem and r['strategy']==strategy and int(r['count'])>0]
                ax.plot(values(b,'mean_score'),values(b,'observed_rate'),color=COLORS[model],marker=marker,alpha=alpha,lw=1,label='Equal width' if strategy=='uniform' else 'Quantile bins')
            j=jobs[model,stem]; ax.set_title(f"{MODELS[model]} / {NAMES[stem]}\nBrier {j['point']['brier']:.3f}; ECE {j['ece_uniform']:.3f}")
            probability_axes(ax); ax.legend(fontsize=8,loc='upper left')
            ax.set(xlabel='Mean vulnerable score in bin',ylabel='Observed vulnerable fraction' if col==0 else '')
    fig.supxlabel('Ten bins where available. Sparse bins and bin choices limit interpretation; no calibration model was fitted.',fontsize=10)
    save(fig,'reliability')

    pairs=c.read_csv(source/'cweval_pairs.csv')
    tasks=sorted({r['task'] for r in pairs})
    fig,axes=plt.subplots(1,2,figsize=(12,10),layout='constrained',sharey=True)
    fig.suptitle('CWEval matched pairs: unsafe score minus reference score',fontsize=16)
    for ax,model in zip(axes,MODELS):
        lookup={r['task']:r for r in pairs if r['model']==model}
        delta=np.array([float(lookup[t]['delta']) for t in tasks])
        factor=10000 if model=='linevul' else 1
        ax.barh(np.arange(len(tasks)),delta*factor,color=[COLORS[model] if d>0 else '#8b8b8b' for d in delta],height=.7)
        ax.axvline(0,color='#333333',lw=1)
        info=jobs[model,'cweval_test']['pairs']
        ax.set_title(f"{MODELS[model]}: unsafe higher in {info['ordering'].get('unsafe_higher',0)}/29 pairs")
        ax.set_xlabel('Score difference × 10,000' if factor>1 else 'Score difference')
        ax.grid(axis='x',alpha=.15)
    axes[0].set_yticks(np.arange(len(tasks)),[t.replace('cweval:','') for t in tasks],fontsize=8)
    axes[0].invert_yaxis()
    fig.supxlabel('Positive bars favor the unsafe variant. Twenty-nine tasks belong to 22 related families; horizontal scales differ.',fontsize=10)
    save(fig,'cweval_pairs')
    scores.write_json(source/'figure_manifest.json',dict(script_sha256=c.sha(Path(__file__)),artifacts=artifacts))
    shutil.copyfile(__file__,source/'figure_renderer.py')
    print('Rendered',len(artifacts),'PNG/PDF artifacts to',destination)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--destination',type=Path,required=True)
    args=parser.parse_args(); run(args.source.resolve(),args.destination.resolve())
