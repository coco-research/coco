---
description: View the latest N screenshots from Desktop (default 1)
argument-hint: "[N]"
---

The user wants to view the latest screenshots from their Desktop. The argument $ARGUMENTS specifies how many to show (default 1 if omitted).

Steps:
1. Determine N: if `$ARGUMENTS` is a number, use it. Otherwise default to 1.
2. Run: `ls -t $HOME/Desktop/Screenshot*.png | head -N` (substituting the actual number for N).
3. Read each screenshot file using the Read tool (which renders images visually).
4. Briefly describe what you see in each screenshot and ask how you can help.
