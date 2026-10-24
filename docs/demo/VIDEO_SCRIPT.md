# Sprint One demo video: setup, script and checklist

Goal (Part-2 deliverables, items 2g and 2h): a screen recording of about **one minute** (up to about 90 seconds is acceptable) showing the working product. It uses fictional data only. The finished file is uploaded to this repository as `docs/video/sprint1-demo.mp4`.

## 1. Set up (not recorded, about 5 minutes)

You need Windows, Git, Python 3.12 and Chrome. Open PowerShell and run these one at a time.

```powershell
git clone https://github.com/Gagan-1718/SE-Team5-Admission-Automation.git
cd SE-Team5-Admission-Automation
git checkout main
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r requirements-https.txt

$env:ADMIN_SEED_PASSWORD = "demo-admin-password-1"
$env:DEMO_CANDIDATE_PASSWORD = "demo-candidate-password-1"
python scripts/prepare_demo.py --yes --with-candidate
python scripts/serve_https.py
```

Leave the last window running (it prints `HTTPS: https://localhost:8443/`). **Do not show this window in the video**, because it holds the passwords. If PowerShell blocks `Activate.ps1`, use `.venv\Scripts\python` in front of each `pip` and `python` command instead.

`prepare_demo.py` deletes only your local test database and rebuilds it with the fictional seed data, the administrator and one ready demo candidate. Run it again whenever you want to record a fresh take.

### Two browser windows
1. **Window A (candidate), normal Chrome:** open `https://localhost:8443`. Chrome warns the certificate is not trusted (it is a self-signed lab certificate): click **Advanced**, then **Proceed to localhost (unsafe)**. Stay logged out.
2. **Window B (administrator), Incognito:** open `https://localhost:8443`, accept the same warning, log in as `admin@example.test` with the `ADMIN_SEED_PASSWORD` value, then open **Review documents**. Leave it logged in.
3. Put the windows **side by side** (Win + Left in one, Win + Right in the other), zoom both to 100 percent or 110 percent so the text is readable at 1080p, and close every other tab and notification. Hide the bookmarks bar (Ctrl + Shift + B).

Files to upload are in `docs/demo/sample_files/` of the cloned repository: `marksheet.pdf`, `id_proof.png`, `category_certificate.jpg`, and `marksheet_corrected.pdf` for the resubmission.

### Data to type (all fictional)
| Where | Value |
|---|---|
| Candidate login | `demo.candidate@example.test`, password = the `DEMO_CANDIDATE_PASSWORD` value |
| Exam details | Exam type **KCET**, Rank **1000**, Category **General**, Score **185** |
| Application | Guardian name **Ravi Demo**, Guardian mobile **9876543210**, School **Demo PU College**, Board **CBSE**, Percentage **88.5** |
| Rejection reason | `Image is not readable` |

## 2. The script (what to do, in order)

Start recording with **Win + Shift + R** (Snipping Tool), select the area covering both windows, press Start. Move at a calm pace: pause about one second after each result so it is readable. Times are targets, not limits.

| Time | Window | Action | Must be visible on screen |
|---|---|---|---|
| 0:00 | A | Show the home page | `https://localhost:8443` in the address bar |
| 0:05 | A | **Log in** (email or mobile + password), click **Sign in** | The navigation bar with My profile, My application, My documents, Colleges, Eligibility |
| 0:12 | A | **My profile**, fill **Exam details** (KCET, 1000, General, 185), click **Save exam details** | The success message |
| 0:20 | A | **My application**, fill the five fields, click **Submit application** | "Application submitted. Your reference number is ADM-2026-000001." |
| 0:32 | A | **Upload a document**: Marksheet, then ID Proof, then Category Certificate, each with its file and **Upload document** | Three documents listed as Pending Verification on **My documents** |
| 0:45 | B | **Review documents**: Document 1 (Marksheet): type the rejection reason, click **Reject**. Document 2 and 3: click **Approve** | The queue changing as items are handled |
| 0:57 | A | Open **My documents** | Marksheet **Rejected** with "Rejection reason: Image is not readable" |
| 1:02 | A | **Replacement for Marksheet**: choose `marksheet_corrected.pdf`, click **Resubmit document** | "Replacement submitted..." |
| 1:08 | B | **Review documents**: click **Approve** on the marksheet | Empty queue or all Approved |
| 1:12 | A | Open **Eligibility**, reload the page | "Rank 1000 is within the General cut-off of 20000." |
| 1:18 | B | Open **Dashboard**, then **Audit log** | Counts (Submitted 1, Approved 3) and the entries document.reject and document.approve |
| 1:25 | (browser) | Optional: open the GitHub project board in a third tab | Cards #2, #3, #4 and #31 in Done |

Stop the recording (Win + Shift + R again, or the red button). To get closer to **60 seconds**, skip the optional board step, skip the resubmission rows (0:57 to 1:08), and speak less. Keep the two logins and the exam-details step, because they are what the grader expects to see.

### Do not show or do
- The PowerShell window, environment variable values, or any password field with **Show** turned on.
- Real names, real email addresses, personal bookmarks or other tabs.
- Browser errors. If a page errors, stop, run `python scripts/prepare_demo.py --yes --with-candidate` again, restart the server, and redo the take.

## 3. After recording
1. Save the file as `sprint1-demo.mp4` and play it once to confirm the audio (if any) and all rows above are visible. Keep it under about 50 MB.
2. Send it to Gagan. Gagan (or Claude Code) commits it to `docs/video/sprint1-demo.mp4`, links it in the README and opens a pull request for the owner to merge.

## 4. Prompt for an AI agent that can drive the computer and record the screen

Copy everything below the line into the agent (for example Codex with computer use). Give it the cloned repository folder.

---

You are recording a short demo video of a web application running on this computer. Follow the steps exactly and report anything unexpected instead of improvising. Use fictional data only.

**Context.** The project is in the current folder (a Flask web app, Python 3.12). The demo site runs at `https://localhost:8443` (HTTPS with a self-signed certificate: your browser will warn; click Advanced then Proceed). Read `docs/demo/VIDEO_SCRIPT.md` first: it has the exact setup, data and timed script, and it is the source of truth.

**Step 1: prepare (do not record).**
1. In PowerShell, in the project folder, create and activate `.venv` with Python 3.12 and run `pip install -r requirements.txt` and `pip install -r requirements-https.txt`.
2. Set `$env:ADMIN_SEED_PASSWORD = "demo-admin-password-1"` and `$env:DEMO_CANDIDATE_PASSWORD = "demo-candidate-password-1"`.
3. Run `python scripts/prepare_demo.py --yes --with-candidate`, then start `python scripts/serve_https.py` in a separate hidden or minimised window that will NOT be part of the recording.
4. Open two Chrome windows side by side: window A (normal) and window B (Incognito). In both, open `https://localhost:8443` and accept the certificate warning. In window B log in as `admin@example.test` with the admin password and open "Review documents". Window A stays logged out. Hide the bookmarks bar and close all other tabs.

**Step 2: record.** Start a screen recording of the area containing both windows (Win + Shift + R, Snipping Tool), then perform the table in section 2 of `docs/demo/VIDEO_SCRIPT.md` in order, using the data in section 1. Pause about one second after each result so it can be read. The video should last about 60 to 90 seconds.

**Must be visible in the video:** the address bar showing `https://localhost:8443`; the candidate navigation bar; the saved exam details message; the reference number `ADM-2026-000001`; three documents pending; the administrator rejecting one document with the reason `Image is not readable` and approving the other two; the candidate seeing the rejection reason and resubmitting; the eligibility text "Rank 1000 is within the General cut-off of 20000."; the administrator dashboard counts; the audit log entries. Optionally end on the GitHub project board showing the finished cards in Done.

**Must NOT be visible:** the PowerShell window, any password value, "Show password" toggled on, real personal data, other browser tabs, notifications.

**Step 3: finish.** Stop the recording, save the video as `sprint1-demo.mp4` (under 50 MB), and check it: confirm the duration, and open it or sample frames to confirm every item above is visible and nothing forbidden appears. If anything is missing or wrong, redo the take (run `python scripts/prepare_demo.py --yes --with-candidate` again and restart the server first). Do not commit anything to Git, do not change any code, and do not use real accounts.

**Report back** with: the file path and size, the duration, a list of which required items appear (with approximate timestamps), and any problem you hit.
