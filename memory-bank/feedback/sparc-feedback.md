# SPARC Orchestrator Feedback
<!-- Entries below should be added reverse chronologically (newest first) -->
### [2025-04-29 19:05:07] User Feedback: Insufficient Detail in Delegation
- **Source:** User Feedback after `new_task` delegation to Architect mode was denied.
- **Issue:** User stated the instructions provided in the `new_task` message lacked sufficient detail ("more details in the instructions").
- **Action Taken:** Acknowledged feedback, will log intervention and craft a more detailed delegation message for the Architect mode.
- **Learning:** Delegation messages via `new_task` must be sufficiently detailed, outlining not just the objective and deliverables, but also specific areas of focus, context, and potential decision points for the target mode.
### [2025-04-29 19:03:42] User Feedback: Incorrect Role Execution
- **Source:** User Feedback after `attempt_completion` by Architect mode (which was incorrectly initiated by SPARC).
- **Issue:** SPARC Orchestrator performed architectural design instead of delegating to Architect mode. User stated: "You aren't supposed to make the architect plans yourself, you are supposed to delegate. Major failure. I need you to do your job as orchestrator."
- **Action Taken:** Acknowledged error, will log intervention and delegate task correctly using `new_task`.
- **Learning:** SPARC must strictly adhere to its role of delegation and coordination, not task execution. Mode switches should be followed by appropriate task delegation via `new_task`.