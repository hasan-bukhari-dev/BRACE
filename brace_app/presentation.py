"""Task-aware wording for views only; numerical records and IDs stay exact."""
from copy import deepcopy
NEUTRAL_WARNINGS={
    'INDEPENDENCE_NOT_ESTABLISHED':'Record independence is not documented; row-level intervals do not account for correlated groups or batches.'
}
def warning_view(warnings,generic=False):
    return [dict(w,message=NEUTRAL_WARNINGS.get(w.get('code'),w['message'])) for w in warnings] if generic else warnings
def uncertainty_view(metrics,generic=False):
    result={k:deepcopy(metrics.get(k)) for k in ('accuracy_wilson_95','macro_f1_bootstrap_95')}
    interval=result.get('macro_f1_bootstrap_95')
    if generic and isinstance(interval,dict) and 'assumption' in interval:
        interval['assumption']='Independent sampled rows; label-stratified and fixed observed class support. Does not capture group or batch clustering.'
    return result
