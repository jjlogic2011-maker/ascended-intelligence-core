# Assessment grade operations (A1)

## Fail-closed harness

```bash
chmod +x scripts/assessment_grade.sh
./scripts/assessment_grade.sh
```

Any missing mandatory evidence exits non-zero:

1. pytest green  
2. coverage run without `|| true`  
3. persistence_receipt (disk + reload)  
4. export CLI verify + tamper rejection  
5. concurrency claim one winner  

## Grade

- **A0** — reference kernel exists  
- **A1** — this harness passes on a cited commit **and** CI is green for that commit  

Documentation alone does not grant A1.
