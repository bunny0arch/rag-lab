import json, math, os, re, time, urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).parent
PUBLIC = ROOT / 'public'
STOP = set('a an the and or of to in on for with is are was were this that from by as be can into it its how what why does do using same both then than'.split())

def load_docs():
    return json.loads((PUBLIC/'sample_docs.json').read_text(encoding='utf-8'))

def tokenize(text):
    return [x.lower() for x in re.findall(r'[A-Za-z0-9_]+', text) if x.lower() not in STOP]

def chunks(docs, size=720, overlap=120):
    out=[]
    for d in docs:
        words=d['text'].split()
        step=max(1, size-overlap)
        for i in range(0, len(words), step):
            part=' '.join(words[i:i+size]).strip()
            if not part: continue
            out.append({'id':f"{d['id']}:{i//step+1}",'docId':d['id'],'name':d['name'],'type':d.get('type','TXT'),'section':d.get('section','Document'),'page':d.get('page'),'text':part})
            if i+size >= len(words): break
    return out

def bm25(query, passages, k=5):
    q=tokenize(query); terms=set(q); N=len(passages); avg=sum(len(tokenize(p['text'])) for p in passages)/max(1,N)
    df={t:sum(1 for p in passages if t in tokenize(p['text']) for _ in [0]) for t in terms}
    scored=[]
    for p in passages:
        toks=tokenize(p['text']); tf={t:toks.count(t) for t in terms}; dl=len(toks); score=0.0
        for t in terms:
            if not tf[t]: continue
            idf=math.log(1+(N-df[t]+0.5)/(df[t]+0.5)); score += idf*(tf[t]*2.0)/(tf[t]+1.2*(0.25+0.75*dl/max(avg,1)))
        if score>0: scored.append({**p,'score':round(score,4),'matched':sorted(t for t in terms if t in toks)})
    return sorted(scored,key=lambda x:x['score'],reverse=True)[:k]

def vector_search(query, passages, k=5):
    docs=[tokenize(p['text']) for p in passages]; q=tokenize(query); vocab=set(q)
    for ts in docs: vocab.update(ts)
    vocab=sorted(vocab); idf={t:math.log((1+len(docs))/(1+sum(t in ts for ts in docs)))+1 for t in vocab}
    def vec(ts):
        return {t:ts.count(t)*idf[t] for t in vocab if t in ts}
    qv=vec(q); qn=math.sqrt(sum(v*v for v in qv.values())) or 1
    scored=[]
    for p,ts in zip(passages,docs):
        v=vec(ts); den=math.sqrt(sum(x*x for x in v.values())) or 1
        sim=sum(qv.get(t,0)*v.get(t,0) for t in vocab)/(qn*den)
        if sim>0: scored.append({**p,'score':round(sim,4),'matched':sorted(set(q)&set(ts))})
    return sorted(scored,key=lambda x:x['score'],reverse=True)[:k]

def hybrid(query, passages, k=5):
    sparse=bm25(query,passages,max(k,8)); dense=vector_search(query,passages,max(k,8)); ranks={}
    for rank,p in enumerate(sparse,1): ranks.setdefault(p['id'],{'p':p,'score':0})['score']+=1/(60+rank)
    for rank,p in enumerate(dense,1): ranks.setdefault(p['id'],{'p':p,'score':0})['score']+=1/(60+rank)
    return [{**x['p'],'score':round(x['score'],5),'retrieval':'hybrid'} for x in sorted(ranks.values(),key=lambda x:x['score'],reverse=True)[:k]]

def rag_call(query, evidence):
    key=os.getenv('OPENAI_API_KEY','').strip()
    if not key: return {'llm_available':False,'status':'model_unavailable','answer':None,'citations':[],'message':'No OPENAI_API_KEY configured. Retrieval is available; generation is intentionally not fabricated.'}
    base=os.getenv('OPENAI_BASE_URL','https://api.openai.com/v1').rstrip('/')
    model=os.getenv('OPENAI_MODEL','gpt-4o-mini')
    context='\n\n'.join(f"[{p['id']}] {p['name']} — {p['text']}" for p in evidence)
    prompt=f"Answer only from the evidence. If unsupported, say insufficient evidence. Cite sources inline using exact IDs like [bm25:1].\nQuestion: {query}\nEvidence:\n{context}"
    body=json.dumps({'model':model,'temperature':0.2,'messages':[{'role':'system','content':'You are a grounded RAG lab assistant. Never invent facts or citations.'},{'role':'user','content':prompt}]}).encode()
    req=urllib.request.Request(base+'/chat/completions',data=body,headers={'Content-Type':'application/json','Authorization':'Bearer '+key},method='POST')
    try:
        with urllib.request.urlopen(req,timeout=30) as r: data=json.loads(r.read().decode())
        answer=data['choices'][0]['message']['content']; valid={p['id'] for p in evidence}; cites=[c for c in re.findall(r'\[([^\]]+)\]',answer) if c in valid]
        return {'llm_available':True,'status':'complete','answer':answer,'citations':cites,'model':model,'prompt':prompt}
    except Exception as e:
        return {'llm_available':True,'status':'generation_failed','answer':None,'citations':[],'message':str(e),'model':model,'prompt':prompt}

class Handler(SimpleHTTPRequestHandler):
    def end_json(self, obj, status=200):
        raw=json.dumps(obj).encode(); self.send_response(status); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(raw))); self.end_headers(); self.wfile.write(raw)
    def do_GET(self):
        if self.path=='/api/health': return self.end_json({'ok':True})
        if self.path=='/api/sample-docs': return self.end_json({'documents':load_docs()})
        return super().do_GET()
    def do_POST(self):
        length=int(self.headers.get('Content-Length','0')); body=json.loads(self.rfile.read(length) or '{}')
        query=body.get('query','').strip(); docs=body.get('documents') or load_docs(); passages=chunks(docs,int(body.get('chunkSize',720)),int(body.get('overlap',120))); k=int(body.get('topK',5)); start=time.perf_counter()
        if self.path=='/api/search':
            results=bm25(query,passages,k); return self.end_json({'query':query,'normalized':' '.join(tokenize(query)),'results':results,'passagesSearched':len(passages),'documentsSearched':len(docs),'elapsedMs':round((time.perf_counter()-start)*1000,2),'method':'BM25 lexical retrieval'})
        if self.path=='/api/rag':
            retrieval_start=time.perf_counter(); dense=vector_search(query,passages,k); sparse=bm25(query,passages,k); results=hybrid(query,passages,k) if body.get('hybrid',True) else dense; retrieval_ms=round((time.perf_counter()-retrieval_start)*1000,2); gen_start=time.perf_counter(); gen=rag_call(query,results); gen['retrievalMs']=retrieval_ms; gen['generationMs']=round((time.perf_counter()-gen_start)*1000,2); gen['totalMs']=round((time.perf_counter()-start)*1000,2); gen['results']=results; gen['candidateCount']=len(passages); gen['contextChunks']=len(results); gen['query']=query; gen['trace']={'query_embedding':'TF-IDF vector generated locally','dense_candidates':len(dense),'sparse_candidates':len(sparse),'fusion':'RRF-style rank fusion' if body.get('hybrid',True) else 'Disabled','context_budget':body.get('contextBudget',4000)}; return self.end_json(gen)
        return self.end_json({'error':'Not found'},404)

if __name__=='__main__':
    os.chdir(PUBLIC); port=int(os.getenv('RAG_PORT','3000')); ThreadingHTTPServer(('127.0.0.1',port),Handler).serve_forever()
