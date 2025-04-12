$(document).ready(function () {
const markdownText = `

<details>
<summary>TVBox 自用接口</summary>

\`自用
https://clun.top/box.json
\`

\`PG
https://clun.top/jsm.json
\`

\`18+
https://clun.top/fun.json
\`

\`饭总
https://clun.top/api.json
\`

</details>

`;

document.getElementById('markdown').innerHTML = marked.parse(markdownText);
});