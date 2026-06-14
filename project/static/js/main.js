async function postFormData(url, formData){
  const resp = await fetch(url, {method:'POST', body: formData});
  return resp.json();
}

document.getElementById('uploadForm').addEventListener('submit', async (e)=>{
  e.preventDefault();
  const input = document.getElementById('fileInput');
  if(!input.files.length){alert('Select a file'); return}
  const f = input.files[0];
  const allowed = ['application/pdf','application/vnd.openxmlformats-officedocument.wordprocessingml.document','text/plain'];
  if(!allowed.includes(f.type) && !f.name.endsWith('.docx')){alert('Unsupported file type'); return}
  const fd = new FormData(); fd.append('file', f);
  document.getElementById('status').innerText='Uploading...';
  const up = await postFormData('/upload', fd);
  if(up.error){document.getElementById('status').innerText='Upload error: '+up.error; return}
  document.getElementById('status').innerText='Extracted '+up.text_length+' characters. Analyzing...';
  // Use extracted text returned by upload endpoint when available to avoid extra roundtrip
  let extractedText = up.text;
  if(!extractedText){
    extractedText = await fetchTextFromUpload(up.filename);
  }
  const analyzeResp = await fetch('/analyze', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({text: extractedText})});
  const json = await analyzeResp.json();
  if(json.error){document.getElementById('status').innerText='Analysis error: '+json.error; return}
  document.getElementById('status').innerText='Analysis complete';
  showResults(json);
});

async function fetchTextFromUpload(filename){
  // helper: request server to read the uploaded file and return text
  const resp = await fetch('/read_uploaded_text', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({filename})});
  const j = await resp.json();
  if(j.error) throw new Error(j.error);
  return j.text;
}

let radarChart = null;
let barChart = null;
let doughnutChart = null;

function showResults(data){
  document.getElementById('results').style.display='block';
  const critic = data.critic || {};

const suggestions = [
  ...(critic.improvement_suggestions || []),
  ...(critic.missing_topics || []),
  ...(critic.grammar_suggestions || [])
];
let readiness = 100;

readiness -= (critic.missing_topics || []).length * 15;
readiness -= (critic.weaknesses || []).length * 10;

if (readiness < 0) readiness = 0;

document.getElementById('readinessCard').innerHTML = `
<div class="card">
  <div class="card-body">
    <h4>🚀 Project Readiness: ${readiness}%</h4>

    <div class="progress mb-3">
      <div class="progress-bar"
           role="progressbar"
           style="width:${readiness}%">
        ${readiness}%
      </div>
    </div>

    <p>📌 Missing Topics: ${(critic.missing_topics || []).length}</p>
    <p>⚠️ Weak Areas: ${(critic.weaknesses || []).length}</p>
    <p>💡 Suggestions: ${suggestions.length}</p>
  </div>
</div>
`;

// PASTE HERE

const judgeQuestions = [];

if ((critic.missing_topics || []).includes("Evaluation / Results section")) {
    judgeQuestions.push("How did you evaluate your project?");
}

judgeQuestions.push("Why did you choose this approach?");
judgeQuestions.push("What are the limitations of your project?");
judgeQuestions.push("How can this project be improved in the future?");
judgeQuestions.push("What makes your solution unique?");

document.getElementById("judgeQuestions").innerHTML =
judgeQuestions.map(q => `
<div class="card mb-2">
  <div class="card-body">
    🎤 ${q}
  </div>
</div>
`).join("");

document.getElementById('quickSuggestions').innerHTML =
  suggestions.length
    ? `<ul>${suggestions.map(item => `<li>${item}</li>`).join('')}</ul>`
    : '<p>No suggestions available.</p>';
  const scores = data.scores || {};

// Winning Probability
let winningChance = readiness;

if ((scores.innovation || 0) > 80) winningChance += 5;
if ((scores.technical || 0) > 80) winningChance += 5;

if (winningChance > 100) winningChance = 100;

document.getElementById('winningCard').innerHTML = `
<div class="card">
  <div class="card-body">
    <h4>🏆 Winning Probability: ${winningChance}%</h4>

    <div class="progress mb-3">
      <div class="progress-bar bg-success"
           role="progressbar"
           style="width:${winningChance}%">
        ${winningChance}%
      </div>
    </div>

    <p>💡 Based on project completeness and AI analysis scores.</p>
  </div>
</div>
`;
  const scoreLabels = ['overall','clarity','professionalism','technical','innovation','confidence'];
  const scoreValues = scoreLabels.map(key => scores[key] || 0);

  const radarCtx = document.getElementById('radarChart').getContext('2d');
  if(radarChart){ radarChart.destroy(); }
  radarChart = new Chart(radarCtx, {
    type:'radar',
    data:{labels:['Overall','Clarity','Professionalism','Technical','Innovation','Confidence'], datasets:[{label:'Presentation Scores', data:scoreValues, backgroundColor:'rgba(0,245,255,0.18)', borderColor:'#00F5FF', pointBackgroundColor:'#00F5FF'}]},
    options:{responsive:true, scales:{r:{beginAtZero:true, max:100, grid:{color:'rgba(255,255,255,0.1)'}, angleLines:{color:'rgba(255,255,255,0.12)',}, pointLabels:{color:'#B8C1EC'}}}}
  });

  const barCtx = document.getElementById('barChart').getContext('2d');
  if(barChart){ barChart.destroy(); }
  barChart = new Chart(barCtx, {
    type:'bar',
    data:{labels:['Overall','Clarity','Professionalism','Technical','Innovation','Confidence'], datasets:[{label:'Score', data:scoreValues, backgroundColor:'rgba(0,245,255,0.4)', borderColor:'#00F5FF', borderWidth:1}]},
    options:{responsive:true, scales:{y:{beginAtZero:true, max:100, ticks:{color:'#fff'}}, x:{ticks:{color:'#fff'}}}, plugins:{legend:{display:false}}}
  });

  const doughnutValues = [
    (data.critic?.strengths?.length || 0) + 1,
    (data.critic?.weaknesses?.length || 0) + 1,
    (data.critic?.improvement_suggestions?.length || 0) + 1
  ];
  const doughnutCtx = document.getElementById('doughnutChart').getContext('2d');
  if(doughnutChart){ doughnutChart.destroy(); }
  doughnutChart = new Chart(doughnutCtx, {
    type:'doughnut',
    data:{labels:['Strengths','Weaknesses','Improvements'], datasets:[{data:doughnutValues, backgroundColor:['#00F5FF','#7B61FF','#00FF9D']} ]},
    options:{responsive:true, plugins:{legend:{position:'bottom', labels:{color:'#fff'}}}}
  });
}

