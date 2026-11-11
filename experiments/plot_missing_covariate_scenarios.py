"""Make a standalone visual for the fixed-assignment stress-test scenarios."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE / '.plotdeps'), str(HERE / '.surveydeps')]
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def draw(values, fixed):
    labels = ['<$25k\ninsured', '<$25k\nuninsured', '$25–<50k\ninsured',
              '$25–<50k\nuninsured', '$50k+\ninsured', '$50k+\nuninsured']
    fig, ax = plt.subplots(figsize=(12.5, 8.5))
    fig.patch.set_facecolor('#f8fafc')
    fig.subplots_adjust(left=.19, right=.85, top=.74, bottom=.24)
    heat = ax.imshow(values, cmap='Blues', vmin=0, vmax=9, aspect='auto')
    ax.set_xticks(range(6), labels=labels, fontsize=10)
    ax.set_yticks(range(6), labels=labels, fontsize=10)
    ax.xaxis.tick_top()
    ax.tick_params(length=0, pad=10)
    for side in ax.spines.values():
        side.set_visible(False)
    ax.set_xticks(np.arange(-.5, 6, 1), minor=True)
    ax.set_yticks(np.arange(-.5, 6, 1), minor=True)
    ax.grid(which='minor', color='white', linewidth=2)
    ax.tick_params(which='minor', bottom=False, left=False)
    for row in range(6):
        for col in range(6):
            ax.text(col, row, f'{values[row, col]:+.1f}', ha='center', va='center',
                    fontsize=12, fontweight='bold', color='white' if values[row, col] > 5 else '#10243a')
    fig.text(.19, .96, 'Missing answers can change the comparison', fontsize=20, fontweight='bold', color='#10243a')
    fig.text(.19, .915, '36 fixed-assignment stress tests of income and insurance responses', fontsize=12, color='#41546a')
    fig.text(.52, .80, 'Assignment for respondents reporting diabetes', ha='center', fontsize=11, fontweight='bold', color='#263e55')
    fig.text(.045, .49, 'Assignment for respondents\nreporting no diabetes', ha='center', va='center',
             rotation=90, fontsize=11, fontweight='bold', color='#263e55')
    cax = fig.add_axes([.88, .26, .018, .47])
    bar = fig.colorbar(heat, cax=cax)
    bar.set_label('Difference, percentage points', fontsize=10, labelpad=10)
    bar.outline.set_visible(False)
    fig.text(.19, .16, 'Each number is the diabetes-minus-no-diabetes cost-barrier gap after standardization.', fontsize=10.5, color='#263e55')
    reference_note = ('All scenarios use the same complete-case standard population.' if fixed
                      else 'The pooled standard population changes with each scenario.')
    fig.text(.19, .13, reference_note, fontsize=10.5, color='#263e55')
    fig.text(.19, .10, 'These hypothetical assignments are not statistical bounds or estimates of the missing answers.', fontsize=10.5, fontweight='bold', color='#263e55')
    fig.text(.19, .065, '2023 BRFSS • 48 states + DC • known-age respondents • weighted point estimates', fontsize=9.5, color='#586a7c')
    stem = 'figure_missing_covariate_fixed' if fixed else 'figure_missing_covariate_scenarios'
    for ext in ('png', 'svg'):
        fig.savefig(HERE / f'{stem}.{ext}', dpi=170, facecolor=fig.get_facecolor())
    plt.close(fig)


def main():
    result = json.loads((HERE / 'missing-covariate-scenarios-results.json').read_text(encoding='utf-8'))
    for key, fixed in [('difference', False), ('fixed_reference_difference', True)]:
        values = np.full((6, 6), np.nan)
        for scenario in result['scenarios']:
            values[scenario['no_diabetes_setting'], scenario['diabetes_setting']] = 100 * scenario[key]
        if not np.isfinite(values).all():
            raise ValueError('Incomplete scenario matrix')
        draw(values, fixed)
    print('Saved varying- and fixed-reference scenario figures as PNG and SVG.')


if __name__ == '__main__':
    main()
