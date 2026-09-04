"""
TUTIVRA offline test — validates all new modules without API calls.
Run: python tests/test_offline.py
"""
import sys
import os
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, '.')

PASS = 0
FAIL = 0

def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        print(f"  [PASS] {name}{' - ' + detail if detail else ''}")
        PASS += 1
    else:
        print(f"  [FAIL] {name}{' - ' + detail if detail else ''}")
        FAIL += 1

print("\n=== TUTIVRA Offline Module Tests ===\n")

# ── Imports ──────────────────────────────────────────────────
print("--- Imports ---")
try:
    from app.video.scene_planner import plan_lesson_scenes, _fallback_scenes
    from app.video.visual_generator import generate_visual
    from app.video.tts_provider import get_provider_info
    from app.video.avatar_provider import get_avatar_provider_info
    from app.ai.assessment_generator import generate_final_assessment, _fallback_assessment
    from app.ai.report_generator import generate_learning_report, _build_revision_plan
    from app.ai.openrouter_client import ask_ai
    from app.rag.retriever import Retriever
    from app.student.student_model import StudentModel
    from app.adaptation.difficulty_engine import get_adaptation_decision
    check("All new modules import", True)
except Exception as e:
    check("All new modules import", False, str(e))
    print("Cannot continue without imports.")
    sys.exit(1)

# ── Visual Generator ─────────────────────────────────────────
print("\n--- Visual Generator ---")
try:
    html = generate_visual('bullet_list', 'Point 1\nPoint 2\nPoint 3', 'Test')
    check("bullet_list visual", 'bullet' in html.lower())

    html2 = generate_visual('code', 'def hello():\n    print("world")', 'Code', 'python')
    check("code visual", 'code' in html2.lower())

    html3 = generate_visual('flowchart', 'Step 1\nStep 2\nStep 3')
    check("flowchart visual", 'mermaid' in html3.lower())

    html4 = generate_visual('equation', r'E = mc^2')
    check("equation visual", 'katex' in html4.lower())

    html5 = generate_visual('timeline', '1945: World War II ends\n1969: Moon landing')
    check("timeline visual", 'timeline' in html5.lower())

    html6 = generate_visual('comparison', 'Arrays vs Linked Lists\nO(1) vs O(n)\nRandom vs Sequential')
    check("comparison visual", 'comparison' in html6.lower() or 'table' in html6.lower())

    html7 = generate_visual('none', '')
    check("none visual returns empty", html7 == "")

    html8 = generate_visual('graph', 'Complexity: 5\nMemory: 3\nSpeed: 8')
    check("graph visual generated", len(html8) > 0)

except Exception as e:
    check("Visual generator suite", False, str(e))

# ── Fallback Scenes ──────────────────────────────────────────
print("\n--- Scene Planner (offline) ---")
try:
    scenes = _fallback_scenes('Binary Search', 'en', 'beginner')
    check("Fallback scenes count", len(scenes) == 3, f"{len(scenes)} scenes")
    check("Scene IDs valid", all('scene_id' in s for s in scenes))
    check("Last scene is interactive", scenes[-1]['interaction_required'] == True)
    check("Scene narration present", all(len(s.get('narration','')) > 10 for s in scenes))
    
    # Validate scene dict schema
    required_keys = ['scene_id', 'concept', 'scene_type', 'narration', 
                     'visual_type', 'visual_content', 'on_screen_text',
                     'duration_seconds', 'interaction_required', 'question',
                     'question_type', 'choices', 'difficulty', 'language']
    all_have_keys = all(all(k in s for k in required_keys) for s in scenes)
    check("All scene keys present", all_have_keys)
except Exception as e:
    check("Fallback scenes", False, str(e))

# ── Assessment (offline) ─────────────────────────────────────
print("\n--- Assessment Generator (offline) ---")
try:
    fallback_a = _fallback_assessment('Binary Trees', ['Trees', 'BST'], 5)
    check("Fallback assessment has questions", len(fallback_a.get('questions', [])) > 0)
    check("Fallback assessment has total_marks", 'total_marks' in fallback_a)
    check("Question has required fields",
          all(k in fallback_a['questions'][0] 
              for k in ['id','question_type','question','expected_answer','marks']))
except Exception as e:
    check("Fallback assessment", False, str(e))

# ── Learning Report (offline) ────────────────────────────────
print("\n--- Learning Report (offline) ---")
try:
    plan = _build_revision_plan(
        weak_concepts=['linked list traversal'],
        misconceptions=['confused pointers with values'],
        topic='Linked Lists',
        status='needs_revision'
    )
    check("Revision plan generated", len(plan) > 0, f"{len(plan)} steps")

    plan2 = _build_revision_plan([], [], 'BST', 'excellent')
    check("Excellent revision plan", len(plan2) > 0)
except Exception as e:
    check("Revision plan", False, str(e))

# ── Student Model ────────────────────────────────────────────
print("\n--- Student Model ---")
try:
    s = StudentModel(name='TestStudent', level='beginner')
    s.initialize_topic('BST')
    s.update_from_evaluation('BST', True, '')
    check("Mastery increases on correct", s.mastery['BST'] == 15.0, f"{s.mastery['BST']}")
    
    s.update_from_evaluation('BST', False, 'confused root with leaf')
    check("Mastery decreases on wrong", s.mastery['BST'] == 10.0, f"{s.mastery['BST']}")
    check("Misconception recorded", 'confused root with leaf' in s.misconceptions['BST'])
    
    summary = s.get_summary('BST')
    check("Summary has all keys",
          all(k in summary for k in ['mastery','attempts','correct_answers','misconceptions']))
except Exception as e:
    check("Student model", False, str(e))

# ── Difficulty Engine ────────────────────────────────────────
print("\n--- Difficulty Engine ---")
try:
    dec = get_adaptation_decision(mastery=0, attempts=0, correct_answers=0)
    check("Low mastery -> easy", dec['difficulty'] == 'easy')
    
    dec2 = get_adaptation_decision(mastery=75, attempts=5, correct_answers=4)
    check("High mastery -> hard", dec2['difficulty'] == 'hard')
    
    dec3 = get_adaptation_decision(mastery=30, attempts=2, correct_answers=0,
                                    misconception_detected=True)
    check("Misconception -> simpler", dec3['difficulty'] in ['easy', 'medium'])
except Exception as e:
    check("Difficulty engine", False, str(e))

# ── Retriever (no hardcoding) ────────────────────────────────
print("\n--- Retriever (topic-agnostic check) ---")
try:
    import inspect
    src = inspect.getsource(Retriever)
    
    hardcoded = ['binary search tree', 'linked list', '"bfs"', '"dfs"',
                  'merge sort', 'backtracking', 'array access']
    found = [h for h in hardcoded if h in src.lower() and h not in
             # allow in docstring/comments
             [line.strip() for line in src.split('\n') if line.strip().startswith('#')]]
    
    check("No hardcoded DSA topics in retriever", len(found) == 0,
          f"Found: {found}" if found else "Clean")
    
    # Verify retriever has MIN_RELEVANCE_SCORE for out-of-scope filtering
    check("Has relevance threshold", 'MIN_RELEVANCE_SCORE' in src)
    check("Has meaningful_words method", '_meaningful_words' in src)
except Exception as e:
    check("Retriever audit", False, str(e))

# ── TTS Provider Info ────────────────────────────────────────
print("\n--- TTS Provider ---")
try:
    info = get_provider_info()
    check("Provider info returned", isinstance(info, dict))
    check("Provider is fish_audio", info.get('provider') == 'fish_audio')
    check("Supports multiple languages", len(info.get('supports_languages', [])) > 3)
    fish_key = os.getenv("FISH_AUDIO_API_KEY", "")
    check("Configured correctly reflects env", info['configured'] == bool(fish_key))
except Exception as e:
    check("TTS provider info", False, str(e))

# ── Avatar Provider Info ─────────────────────────────────────
print("\n--- Avatar Provider ---")
try:
    info = get_avatar_provider_info()
    check("Avatar provider info returned", isinstance(info, dict))
    check("Provider is did", info.get('provider') == 'did')
    did_key = os.getenv("DID_API_KEY", "")
    check("Configured correctly reflects env", info['configured'] == bool(did_key))
except Exception as e:
    check("Avatar provider info", False, str(e))

# ── Summary ──────────────────────────────────────────────────
print(f"\n{'='*50}")
print(f"  Passed: {PASS}  |  Failed: {FAIL}")
if FAIL == 0:
    print("  ALL TESTS PASSED")
else:
    print(f"  {FAIL} tests failed")
print(f"{'='*50}\n")

sys.exit(0 if FAIL == 0 else 1)
