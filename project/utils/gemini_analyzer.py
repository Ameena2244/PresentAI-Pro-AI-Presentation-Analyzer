import os
import time
import json
import re
import requests

class GeminiError(Exception):
    pass


class GeminiAnalyzer:
    """Wrapper to call a Gemini-compatible generative API and parse structured JSON responses.

    Configuration via environment variables:
    - GEMINI_API_URL : full endpoint URL to call (POST)
    - GEMINI_API_KEY : API key to pass as Bearer token in Authorization header
    - GEMINI_MODEL   : optional model identifier used in prompt
    If API credentials are missing, a deterministic local analyzer is used as a fallback so the app remains functional.
    """
    def __init__(self):
        self.api_url = os.environ.get('GEMINI_API_URL')
        self.api_key = os.environ.get('GEMINI_API_KEY')
        self.model = os.environ.get('GEMINI_MODEL', 'gemini')
        # If API config is missing, enable local fallback analyzer instead of raising.
        self.enabled = bool(self.api_url and self.api_key)

    def _call_api(self, prompt: str, max_retries=3, timeout=30):
        if not self.enabled:
            raise GeminiError('Gemini API not configured')
        headers = {'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}
        payload = {
            'model': self.model,
            'prompt': prompt,
            'max_tokens': 1500,
            'temperature': 0.2,
            'top_p': 0.95
        }
        attempt = 0
        while attempt < max_retries:
            try:
                resp = requests.post(self.api_url, headers=headers, json=payload, timeout=timeout)
                if resp.status_code == 429:
                    # rate limited
                    backoff = (2 ** attempt) + (0.5 * attempt)
                    time.sleep(backoff)
                    attempt += 1
                    continue
                resp.raise_for_status()
                return resp.text
            except requests.RequestException as e:
                attempt += 1
                if attempt >= max_retries:
                    raise GeminiError(f'API request failed: {e}')
                time.sleep(1 + attempt)

    def _extract_json(self, text: str):
        # find first JSON object in text
        m = re.search(r"(\{[\s\S]*\})", text)
        if not m:
            raise GeminiError('No JSON object found in model response')
        raw = m.group(1)
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            # try to clean up common issues
            cleaned = raw.replace("\n", " ")
            try:
                return json.loads(cleaned)
            except Exception:
                raise GeminiError('Failed to parse JSON from model output')

    def analyze_presentation(self, text: str) -> dict:
        # If Gemini is available, call it; otherwise use a deterministic local analyzer.
        if self.enabled:
            prompt = self._build_analysis_prompt(text)
            out = self._call_api(prompt)
            parsed = self._extract_json(out)
            return parsed
        else:
            return self._local_analyze(text)

    def generate_viva(self, text: str) -> dict:
        if self.enabled:
            prompt = self._build_viva_prompt(text)
            out = self._call_api(prompt)
            parsed = self._extract_json(out)
            return parsed
        else:
            return self._local_generate_viva(text)

    def _build_analysis_prompt(self, text: str) -> str:
        # Prompt engineering: ask model to return strict JSON only, with specified fields
        instruction = {
            'task': 'Analyze the presentation content and return a JSON object',
            'format': 'Return ONLY valid JSON. Do not include any explanatory text.',
            'fields': {
                'scores': ['overall','clarity','professionalism','technical','innovation','confidence'],
                'critic': ['strengths','weaknesses','missing_topics','content_gaps','improvement_suggestions','grammar_suggestions'],
                'titles': ['professional','research','industry'],
                'judge': ['innovation_rating','practicality_rating','technical_rating','presentation_rating','final_comments'],
                'predictor': ['winning_probability','judge_interest','recommendations']
            }
        }
        prompt = f"{json.dumps(instruction)}\n\nPresentation Content:\n" + text
        return prompt

    def _build_viva_prompt(self, text: str) -> str:
        instruction = {
            'task': 'Generate Viva questions and answers for the given presentation',
            'format': 'Return ONLY valid JSON with arrays: basic, intermediate, advanced. Each item: question and answer.'
        }
        prompt = f"{json.dumps(instruction)}\n\nPresentation Content:\n" + text
        return prompt

    # --- Local deterministic fallback analyzers (no external API) ---
    def _local_analyze(self, text: str) -> dict:
        # Basic heuristics: word count, sentence length, keyword presence
        words = re.findall(r"\w+", text)
        word_count = len(words)
        sentences = re.split(r'[\.\?\!]\s+', text)
        avg_sentence_len = (sum(len(s.split()) for s in sentences) / max(1, len(sentences)))
        # simple scores based on heuristics
        def clamp(x):
            return max(0, min(100, int(x)))

        overall = clamp(50 + (word_count/200)*10 - (avg_sentence_len-15))
        clarity = clamp(40 + max(0, 20 - (avg_sentence_len-12)))
        professionalism = clamp(45 + min(25, word_count/400*25))
        technical = clamp(40 + min(30, sum(1 for w in words if w.lower() in ('model','architecture','algorithm','api','dataset'))*5))
        innovation = clamp(30 + min(40, sum(1 for w in words if w.lower() in ('novel','novelty','unique','first','prototype'))*8))
        confidence = clamp(50 + (overall-50)//2)

        # Generate critic lists using simple keyword heuristics
        strengths = []
        weaknesses = []
        missing = []
        suggestions = []
        if word_count > 800:
            strengths.append('Comprehensive content coverage')
        else:
            weaknesses.append('Limited content length')
            suggestions.append('Add more detailed sections and examples')
        if 'evaluation' in text.lower() or 'result' in text.lower():
            strengths.append('Includes evaluation/results')
        else:
            missing.append('Evaluation / Results section')
            suggestions.append('Include quantitative evaluation or case studies')

        return {
            'scores': {
                'overall': overall,
                'clarity': clarity,
                'professionalism': professionalism,
                'technical': technical,
                'innovation': innovation,
                'confidence': confidence
            },
            'critic': {
                'strengths': strengths,
                'weaknesses': weaknesses,
                'missing_topics': missing,
                'content_gaps': [],
                'improvement_suggestions': suggestions,
                'grammar_suggestions': []
            },
            'titles': {
                'professional': ["PresentAI Pro - Smart Presentation Critic"],
                'research': ["AI-driven Presentation Analysis Framework"],
                'industry': ["Enterprise Presentation QA Assistant"]
            },
            'judge': {
                'innovation_rating': round(innovation/10,1),
                'practicality_rating': round(professionalism/10,1),
                'technical_rating': round(technical/10,1),
                'presentation_rating': round(clarity/10,1),
                'final_comments': 'Automated heuristic analysis used (enable Gemini for richer results)'
            },
            'predictor': {
                'winning_probability': overall,
                'judge_interest': clamp(50 + (innovation//2)),
                'recommendations': suggestions
            }
        }

    def _local_generate_viva(self, text: str) -> dict:
        # Extract keywords and generate templated questions
        words = re.findall(r"\w+", text.lower())
        common = {}
        for w in words:
            if len(w) > 3:
                common[w] = common.get(w,0)+1
        sorted_kw = sorted(common.items(), key=lambda x:-x[1])[:10]
        top = [w for w,_ in sorted_kw]
        basic = [{'question': f'What problem does this project solve regarding {top[0] if top else "the domain"}?', 'answer': 'Explain the core problem and target users.'}]
        intermediate = [{'question': f'How does the solution handle {top[1] if len(top)>1 else "scaling"}?', 'answer': 'Discuss architecture and scalability considerations.'}]
        advanced = [{'question': f'What are the limitations and failure modes related to {top[2] if len(top)>2 else "model"}?', 'answer': 'Discuss evaluation, edge cases, and mitigation strategies.'}]
        return {'basic': basic, 'intermediate': intermediate, 'advanced': advanced}
