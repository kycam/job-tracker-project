import json
from datetime import date
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from mysql.connector import Error
from database import query, execute

app=Flask(__name__)
app.secret_key='local-class-project-key'
TABLES={
'companies':{'pk':'company_id','fields':['company_name','industry','website','city','state','notes'],'required':['company_name'],'labels':['Company name','Industry','Website','City','State','Notes']},
'jobs':{'pk':'job_id','fields':['company_id','job_title','job_description','job_type','salary_min','salary_max','job_url','date_posted','requirements'],'required':['company_id','job_title'],'labels':['Company','Job title','Description','Job type','Salary minimum','Salary maximum','Job URL','Date posted','Requirements (comma-separated skills)']},
'applications':{'pk':'application_id','fields':['job_id','application_date','status','resume_version','cover_letter_sent','interview_data','response_date','interview_date','notes'],'required':['job_id','application_date'],'labels':['Job','Application date','Status','Resume version','Cover letter sent','Interview data (JSON)','Response date','Interview date/time','Notes']},
'contacts':{'pk':'contact_id','fields':['company_id','contact_name','title','email','phone','linkedin_url','notes'],'required':['company_id','contact_name'],'labels':['Company','Contact name','Title','Email','Phone','LinkedIn','Notes']}}
OPTIONS={'job_type':['Full-time','Part-time','Contract','Internship'],'status':['Applied','Screening','Interview','Offer','Rejected','Withdrawn']}

def cfg(table):
    if table not in TABLES: abort(404)
    return TABLES[table]

def choices():
    return {'company_id':[(str(x['company_id']),x['company_name']) for x in query('SELECT company_id,company_name FROM companies ORDER BY company_name')], 'job_id':[(str(x['job_id']),f"{x['job_title']} — {x['company_name']}") for x in query('SELECT j.job_id,j.job_title,c.company_name FROM jobs j JOIN companies c ON c.company_id=j.company_id ORDER BY j.job_title')]}

def rows(table):
    sql={'companies':'SELECT * FROM companies ORDER BY company_id DESC','jobs':'SELECT j.*,c.company_name FROM jobs j JOIN companies c ON c.company_id=j.company_id ORDER BY j.job_id DESC','applications':'SELECT a.*,j.job_title,c.company_name FROM applications a JOIN jobs j ON a.job_id=j.job_id JOIN companies c ON c.company_id=j.company_id ORDER BY a.application_id DESC','contacts':'SELECT t.*,c.company_name FROM contacts t JOIN companies c ON t.company_id=c.company_id ORDER BY t.contact_id DESC'}[table]
    return query(sql)

def normalized(table,form):
    result={}
    for f in cfg(table)['fields']:
        v=form.get(f,'').strip()
        if f=='cover_letter_sent': result[f]=int(form.get(f)=='on');continue
        if f=='requirements':
            # Accept JSON array or a comma-separated skills list.
            if v.startswith('['):
                arr=json.loads(v)
                if not isinstance(arr,list): raise ValueError('Requirements must be a JSON array or comma-separated skills')
            else: arr=[s.strip() for s in v.split(',') if s.strip()]
            result[f]=json.dumps(arr)
            continue
        if f=='interview_data':
            obj=json.loads(v) if v else None
            result[f]=json.dumps(obj) if obj is not None else None
            continue
        if f=='interview_date' and v: v=v.replace('T',' ')
        result[f]=v or None
    for f in cfg(table)['required']:
        if not result[f]: raise ValueError(f'{f.replace("_"," ").title()} is required')
    if table=='jobs' and result['salary_min'] and result['salary_max'] and float(result['salary_min'])>float(result['salary_max']): raise ValueError('Minimum salary cannot exceed maximum')
    return result

@app.route('/')
def dashboard():
    counts={t:query(f'SELECT COUNT(*) AS n FROM {t}',one=True)['n'] for t in TABLES}
    statuses=query('SELECT status,COUNT(*) AS n FROM applications GROUP BY status')
    return render_template('dashboard.html',counts=counts,statuses=statuses,recent=rows('applications')[:5])

@app.route('/<table>')
def listing(table):
    c=cfg(table)
    return render_template('listing.html',table=table,cfg=c,rows=rows(table))

@app.route('/<table>/new',methods=['GET','POST'])
def create(table):
    c=cfg(table)
    if request.method=='POST':
        try:
            data=normalized(table,request.form)
            execute(f"INSERT INTO {table} ({','.join(data)}) VALUES ({','.join(['%s']*len(data))})",tuple(data.values()))
            flash('Record added successfully','success');return redirect(url_for('listing',table=table))
        except (ValueError,Error) as e: flash(str(e),'error')
    return render_template('form.html',table=table,cfg=c,record=request.form if request.method=='POST' else {},choices=choices(),options=OPTIONS)

@app.route('/<table>/<int:record_id>/edit',methods=['GET','POST'])
def edit(table,record_id):
    c=cfg(table)
    old=query(f"SELECT * FROM {table} WHERE {c['pk']}=%s",(record_id,),one=True)
    if not old: abort(404)
    if request.method=='POST':
        try:
            data=normalized(table,request.form)
            execute(f"UPDATE {table} SET {','.join(f+'=%s' for f in data)} WHERE {c['pk']}=%s",(*data.values(),record_id))
            flash('Record updated','success');return redirect(url_for('listing',table=table))
        except (ValueError,Error) as e: flash(str(e),'error')
    else:
        for field in ('requirements','interview_data'):
            if field in old and old[field] is not None and not isinstance(old[field],str): old[field]=json.dumps(old[field])
    return render_template('form.html',table=table,cfg=c,record=request.form if request.method=='POST' else old,choices=choices(),options=OPTIONS)

@app.route('/<table>/<int:record_id>/delete',methods=['POST'])
def delete(table,record_id):
    c=cfg(table)
    try:
        execute(f"DELETE FROM {table} WHERE {c['pk']}=%s",(record_id,))
        flash('Record deleted','success')
    except Error:
        flash('Cannot delete this record while related records exist. Delete dependent records first.','error')
    return redirect(url_for('listing',table=table))

def skills_from_json(raw):
    if not raw: return []
    try:
        data=json.loads(raw) if isinstance(raw,str) else raw
        if isinstance(data,list): return [str(s).strip() for s in data if str(s).strip()]
        if isinstance(data,dict):
            val=data.get('skills',data.get('required_skills',[]))
            return [str(s).strip() for s in val] if isinstance(val,list) else []
    except (ValueError,TypeError): pass
    return []

@app.route('/job-match',methods=['GET','POST'])
def job_match():
    entered=request.form.get('skills','')
    results=[]
    if request.method=='POST':
        own={s.strip().casefold() for s in entered.split(',') if s.strip()}
        if not own: flash('Enter at least one skill','error')
        else:
            for job in rows('jobs'):
                required=skills_from_json(job['requirements'])
                matched=[s for s in required if s.casefold() in own]
                missing=[s for s in required if s.casefold() not in own]
                pct=round(len(matched)*100/len(required)) if required else 0
                results.append(dict(job=job,matched=matched,missing=missing,percent=pct,total=len(required)))
            results.sort(key=lambda x:(-x['percent'],-len(x['matched'])))
    return render_template('job_match.html',skills=entered,results=results)

if __name__=='__main__': app.run(debug=True)
