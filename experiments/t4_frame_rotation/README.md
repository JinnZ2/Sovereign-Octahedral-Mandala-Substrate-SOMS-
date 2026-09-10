# T4 — Frame-of-reference rotation task (text)

Which reference frame does a text model default to when the array is
rotated with the viewer? Instrument for the Levinson/Brown rotation task
in text, four arms that differ only in which frame vocabulary is available.

```
stimulus: 3 objects on Table 1; viewer turns 180° to empty Table 2, "set out the same arrangement"
          candidates: verbatim words (relative SAME) | reversed words (absolute SAME) | distractor
arm A bare          arm B cardinal terms       arm C fixed landmark       arm D no frame words (floor)
H-corpus  -> relative in A;  shifts toward absolute in B?
H-Haun    -> base frame is allocentric; a model that tracks the base answers absolute in A
overlay   -> A reads the corpus default quotient; B minus A reads how much vocabulary moves it
```

**Status: unrun.** No model endpoint here; the authoring session is not a
blind subject. `runs/constructed.jsonl` is a constructed fixture
(`constructed: true`) that exercises the scorer; the score command banners it.

```bash
python experiments/t4_frame_rotation/rotation_task.py selftest
python experiments/t4_frame_rotation/rotation_task.py plan --seed 7
python experiments/t4_frame_rotation/rotation_task.py prompt rt-00 A
python experiments/t4_frame_rotation/rotation_task.py score experiments/t4_frame_rotation/runs/constructed.jsonl
```

Run protocol: one fresh session per plan row, paste the prompt verbatim,
record the one response as `{run_id, model, version, date, arm, stim_id,
order_index, raw_response, constructed:false}`. Score by verdicts only,
never by the explanation.

Open question the instrument leaves alone: whether Himba or other
absolute-frame-language populations were in the Sablé-Meyer 2021 samples;
that is a literature check, not a model run.
