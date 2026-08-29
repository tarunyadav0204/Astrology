# Education, Exams and Research graph

This ontology is the authoritative Instant policy for education questions. It
separates static promise, aptitude, comparison, diagnosis, timing and remedy
routes so that a static question never fails for missing dasha/transit data and
a timing question never manufactures a result from D24 availability alone.

House scope is route-specific. H4 is limited to foundational/formal education,
learning environment, admission, interruption/resumption and remedies. Higher
education is led by H9, supported by H5 and realized through H11; subject fit,
competitive exams, foreign study and education-versus-work do not inherit H4.

Validate and compile:

```bash
python3 scripts/validate_education_ontology.py
```

The generated runtime bundle is `education-runtime-preview.json`.
