# Pending human and physical-hardware acceptance

Status: **NOT TESTED** with unfamiliar participants or the event projector. Automated developer runs are separate evidence. No participant names, timings or outcomes have been invented. Obtain at least two people who have not built BRACE; ask permission to take anonymous notes, and do not use private patient data.

## Three tasks — neutral prompts

A. Show the landing screen for approximately10seconds. “What do you think this tool does? What would you do first?” Success: participant describes checking a finding/model in another dataset without a clinical interpretation. Do not teach the acronyms first.

B. “Open the real public-data study, run its gene replication using the supplied files and inspect one gene.” Provide the local prepared-file directory and study README. Success: compatibility reviewed, run completed, gene measurements inspected; participant distinguishes source/target and saved versus new computation. Record assistance and confusion about manifests/group definitions.

C. “Open a model result, find an incorrect prediction, inspect its confidence, and export the evidence.” Success: real archived error, threshold/coverage interpretation and validZIP opened; participant understands no new original-model inference.

Record for each participant/task: anonymous code, task, start/end elapsed seconds, completed unaided/with assistance/not completed, wrong turns/errors, quotes/points of confusion, research-versus-clinical interpretation, proposed correction. Blank results template:

|Participant|Task|Elapsed seconds|Outcome|Errors/assistance|Confusion|
|---|---|---|---|---|---|
|Pending|A|Not measured|Not tested|—|—|
|Pending|B|Not measured|Not tested|—|—|
|Pending|C|Not measured|Not tested|—|—|

## Actual event hardware — do before presenting

- Confirm standard64-bit Python and all dependencies installed locally. Verify the release/source hashes and run Windows release checks.
- Start at127.0.0.1:8765; if occupied, identify your own existing BRACE process before stopping it, or explicitly use `BRACE_PORT=8766` and that address. Do not kill an unrelated service.
- Turn Wi-Fi off/unplug external network **on the event laptop yourself**; keep the local loopback interface available. Open the public example and run the six local inputs once; inspect FACE/TRACE and export/open EMBRACE.
- Test ten consecutive complete narrated demonstrations, refresh/reopen a saved run, stop withCtrl+C and restart. Record startup/runtime, failures and actual recovery. The developer's automated ten-run evidence is not a substitute for this hardware test.
- Attach the actual projector/external display. Check1280×720 and1440×900, 100% and intended presentation zoom, contrast, readable axes, visible keyboard focus and no clipped critical controls. Check browser download location and extracted offline report.
- Rehearse the150/180 second script aloud with a stopwatch, including clicks and questions. Record actual times; trim optionalACE if needed.
- Confirm organizers' prior-work/AI-assistance/team/disclosure requirements and submission format in writing; retain their response. Do not infer permission from public event advertising.
- Keep an extracted report and screenshots locally as a clearly labeled saved backup. A recording is optional; no recording is included in this release.
