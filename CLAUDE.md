## Generic
- ALWAYS use `fd` instead of `find`, `rg` instead of `grep`.
- While reading source code and HTML-based documentation, try `ast-grep` if it's suitable.
- ALWAYS use skills for git related operations.
- ALWAYS create issues with /glab-issues while receiving requests from `_stories` files
- ALWAYS record your contribution / work / changes / milestones to `_worklog` dir before committing
- Commit as often as possible and make it reletively reasonable milestones.
- For markdown documents generation, act as a strict technical documentation engine, following strict Style Rules (Non-negotiable): 
    - Generate the content in Raw, Structural Markdown only.
    - Tone: Maintain a sterile, objective, and purely functional tone.
    - NO Decoration: The use of bolding (**text**, __text__), italics (*text*, _text_), or strikethrough is strictly prohibited. Treat these as syntax errors.
    - NO Visual Noise: Do not use any emojis (e.g., 🚀, 💡) or ASCII emoticons.
    - Structure Only: You are permitted to use ONLY:
        - Headers (#, ##, ###)
        - Unordered lists (-)
        - Ordered lists (1,2,3... A,B,C,...)
        - Code blocks
        - Hyperlinks ([text](url))

## Development Specific
- Do NOT create any unit tests.
- ALWAYS use `uv` to manage packages and python project.

## Project Specific
__CAUTION__ You are free (and highly encouraged) to use `fd` `rg` `ast-grep` (as some documentation are in HTML/CSS/Javascript) to query / explore the documentation.

你可以從這裡了解到何謂 Solace Agent Mesh (SAM)：

~/docs/Solace_Platform_HTML_Documentation_R102521/Agentic-AI/agent-mesh.htm

如果需要進行程式編寫，或是要知道如何應用的高級功能，這裡是最佳的參考文件：

~/ext-repo/solace-agent-mesh/docs/

如果需要檢視 core plugins 的文件以及原始碼，可以看這裡：

~/ext-repo/solace-agent-mesh-core-plugins/

你可以從這裡了解到 Solace Event Broker 的重要特性，以及我們可能會搭配的 Micro-Integrations 元件：

~/docs/Solace_Platform_HTML_Documentation_R102521/Get-Started/what-are-event-brokers.htm

~/docs/Solace_Platform_HTML_Documentation_R102521/Micro-Integrations/

這裡有所有 Solace 產品的文件：

~/docs/Solace_Platform_HTML_Documentation_R102521

