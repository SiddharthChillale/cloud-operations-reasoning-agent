1. [ ] Sessions picker doesn't scroll. It should scroll on arrow keys.

2. [ ] introduce /export-output command which exports array of {user-query+final-answer} for whole session. It must not include steps or codeactions etc. Exports happens as a file write to pwd where the application is run from. This should also save the token usage at the end of the file. Format of file must be jsonl. 

3. [ ] introduce /export-chat command which exports {user-query+steps+final-answer} everything to a file. same location as pwd. should also save the token usage at the bottom. Format of file must be jsonl.

4. [ ] introduce agent interruption through pressing [esc] key twice. naturally should also save state to db.

5. [ ] introduce auto-complete for commands. pressing slash should open up an auto-suggestion box above the query box attached on top. should allow selecting any command through arrow keys and pressing [Enter] will execute the command. e.g. pressing /se should show /sessions in auto suggestion along with other possible options. but /sessions is preselected. pressing [Enter] should open the sessions picker modal.

6. [ ] Introduce Modal as sandbox execution environment.

7. [ ] Build and package the app to be deployed to pypi. create a script that builds and deploys. use uv as package manager. 

8. [ ] Improve UX by showing Loading badges like "Thinking", "Executing Action", etc to show up 