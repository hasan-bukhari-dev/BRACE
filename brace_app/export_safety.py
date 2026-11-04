"""Boundary encoding for downloadable CSV; internal scientific records stay exact."""
import csv
import io
from pathlib import Path

def csv_bytes(data:bytes):
    """Return spreadsheet-safe bytes plus the exact reversible changed-cell record.

    Ordinary files remain byte-identical. Numeric cells must remain numeric,
    including negative effects/coordinates; text identifiers retain exact
    originals in the encoding ledger and authoritative JSON.
    """
    rows=list(csv.reader(io.StringIO(data.decode('utf-8-sig'),newline='')))
    changes=[]
    numeric={'effect','source_effect','source_sign','p','q','source_q','t','df','hedges_g','source_mean','target_mean','source_median','target_median',
        'median_difference_target_minus_source','median_shift_per_source_iqr','ks_d','ks_p','ks_bh_q_exploratory',
        'pc1','pc2','source_scaled_pc_distance','threshold','coverage','selective_accuracy','selective_risk',
        'lower','upper','mean_confidence','accuracy','absolute_gap','precision','recall','f1','model_confidence',
        'precision_lower_95','precision_upper_95','recall_lower_95','recall_upper_95','min_distance','max_distance','error_rate'}
    header=rows[0] if rows else []
    for i,row in enumerate(rows):
        for j,value in enumerate(row):
            if not value:continue
            field=header[j] if j<len(header) else ''
            # Header cells and identifier/label fields are always text.
            if i and (field in numeric or field.startswith('prob_')):
                try:
                    float(value)
                    continue
                except ValueError:pass
            probe=value.lstrip(' \t\r\n\ufeff')
            if probe.startswith(('=','+','-','@')) or value.startswith(('\t','\r','\n')):
                row[j]="'"+value
                changes.append(dict(row=i+1,column=j+1,original=value,encoded=row[j]))
    if not changes:return data,[]
    stream=io.StringIO(newline='');csv.writer(stream,lineterminator='\r\n').writerows(rows)
    return stream.getvalue().encode('utf-8'),changes

def within(root:Path,path:Path):
    """Reject links/junction escapes at every existing component."""
    root=root.resolve();relative=path.absolute().relative_to(root)
    current=root
    for part in relative.parts:
        if part in ('..','.') or ':' in part:raise ValueError('Unsafe evidence path')
        current=current/part
        if current.is_symlink() or getattr(current,'is_junction',lambda:False)():raise ValueError('Linked evidence paths are not allowed')
    resolved=path.resolve()
    if not resolved.is_relative_to(root):raise ValueError('Evidence path escaped its run')
    return resolved
